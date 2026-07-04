"""Professional PDF fitness assessment report generation."""

import io
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.services.evaluation.calorie_service import get_exercise_display_name
from app.services.evaluation.evaluation_service import build_evaluation, parse_evaluation


def _find_chinese_font() -> str | None:
    candidates = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _configure_matplotlib_font():
    try:
        import matplotlib.pyplot as plt
        font_path = _find_chinese_font()
        if font_path and font_path.endswith(".ttf"):
            from matplotlib import font_manager
            font_manager.fontManager.addfont(font_path)
            plt.rcParams["font.sans-serif"] = [font_manager.FontProperties(fname=font_path).get_name(), "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass


def _render_chart_images(summary: dict) -> dict[str, bytes]:
    """Render chart PNGs with matplotlib (non-interactive backend)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return {}

    _configure_matplotlib_font()

    charts = summary.get("charts", {})
    images: dict[str, bytes] = {}

    plt.rcParams.update({
        "figure.facecolor": "#0f172a",
        "axes.facecolor": "#1e293b",
        "axes.edgecolor": "#334155",
        "axes.labelcolor": "#cbd5e1",
        "xtick.color": "#94a3b8",
        "ytick.color": "#94a3b8",
        "text.color": "#f8fafc",
        "font.size": 10,
    })

    trend = charts.get("score_trend", [])
    if trend:
        fig, ax = plt.subplots(figsize=(7, 2.8))
        dates = [t["date"][5:] for t in trend]
        scores = [t["score"] for t in trend]
        ax.plot(dates, scores, color="#60a5fa", linewidth=2.5, marker="o", markersize=6)
        ax.fill_between(range(len(scores)), scores, alpha=0.15, color="#3b82f6")
        ax.set_ylim(0, 100)
        ax.set_title("近7日综合评分趋势", fontsize=12, fontweight="bold", pad=10)
        ax.set_ylabel("评分")
        ax.grid(True, alpha=0.2)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        images["trend"] = buf.getvalue()

    exercise_trends = charts.get("score_trend_by_exercise", [])
    if exercise_trends:
        fig, ax = plt.subplots(figsize=(7, 3.2))
        colors = ["#60a5fa", "#34d399", "#f59e0b", "#a78bfa"]
        for idx, item in enumerate(exercise_trends):
            trend_points = item.get("trend", [])
            if not trend_points:
                continue
            dates = [p["date"][5:] for p in trend_points]
            scores = [p["score"] for p in trend_points]
            ax.plot(
                dates, scores,
                label=item.get("name", item.get("exercise", "")),
                color=colors[idx % len(colors)],
                linewidth=2, marker="o", markersize=5,
            )
        ax.set_ylim(0, 100)
        ax.set_title("分动作 7 日评分趋势", fontsize=12, fontweight="bold", pad=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        images["trend_by_exercise"] = buf.getvalue()

    calories = charts.get("calorie_by_exercise", [])
    if calories:
        fig, ax = plt.subplots(figsize=(7, 2.8))
        names = [c["name"] for c in calories]
        values = [c["value"] for c in calories]
        colors = ["#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#3b82f6"]
        ax.bar(names, values, color=colors[: len(names)], edgecolor="none", width=0.55)
        ax.set_title("各动作卡路里消耗 (kcal)", fontsize=12, fontweight="bold", pad=10)
        ax.set_ylabel("kcal")
        plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
        ax.grid(axis="y", alpha=0.2)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        images["calories"] = buf.getvalue()

    radar = charts.get("quality_radar", {})
    dims = radar.get("dimensions", [])
    vals = radar.get("values", [])
    if dims and vals:
        import numpy as np

        angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
        vals_closed = vals + [vals[0]]
        angles_closed = angles + [angles[0]]
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={"projection": "polar"})
        ax.plot(angles_closed, vals_closed, color="#60a5fa", linewidth=2)
        ax.fill(angles_closed, vals_closed, alpha=0.25, color="#3b82f6")
        ax.set_xticks(angles)
        ax.set_xticklabels(dims, fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_title("动作质量雷达图", fontsize=12, fontweight="bold", pad=20)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        images["radar"] = buf.getvalue()

    return images


class PdfReportBuilder:
    def __init__(self):
        self.font_path = _find_chinese_font()

    def build(
        self,
        summary: dict,
        sessions: list,
        username: str = "学员",
        date_from: str | None = None,
        date_to: str | None = None,
        exercise: str | None = None,
    ) -> bytes:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=18)

        if self.font_path and self.font_path.endswith(".ttf"):
            pdf.add_font("zh", "", self.font_path)
            pdf.add_font("zh", "B", self.font_path)
            font_name = "zh"
        else:
            font_name = "Helvetica"

        chart_images = _render_chart_images(summary)
        temp_files: list[str] = []
        filter_label = self._filter_label(date_from, date_to, exercise)

        try:
            self._cover_page(pdf, font_name, username, summary, filter_label)
            self._summary_page(pdf, font_name, username, summary, filter_label)
            self._coach_page(pdf, font_name, summary, sessions)

            for key, title in [
                ("trend", "综合评分趋势（近7日）"),
                ("trend_by_exercise", "分动作评分趋势（近7日）"),
                ("calories", "各动作卡路里消耗分析"),
                ("radar", "动作质量维度雷达图"),
            ]:
                if key in chart_images:
                    self._chart_page(pdf, font_name, title, chart_images[key], temp_files)

            self._exercise_comparison_page(pdf, font_name, summary)
            self._feedback_page(pdf, font_name, summary)
            self._sessions_table(pdf, font_name, sessions)
            self._evaluation_details(pdf, font_name, sessions)

            return bytes(pdf.output())
        finally:
            for path in temp_files:
                try:
                    os.unlink(path)
                except OSError:
                    pass

    @staticmethod
    def _filter_label(date_from: str | None, date_to: str | None, exercise: str | None) -> str:
        parts = []
        if date_from and date_to and date_from == date_to:
            parts.append(f"日期：{date_from}")
        elif date_from or date_to:
            parts.append(f"日期：{date_from or '起始'} ~ {date_to or '今'}")
        else:
            parts.append("日期：全部记录")
        if exercise:
            parts.append(f"动作：{get_exercise_display_name(exercise)}")
        else:
            parts.append("动作：全部")
        return " · ".join(parts)

    def _set_font(self, pdf, font_name: str, size: int = 11, style: str = ""):
        pdf.set_font(font_name, style, size)

    def _text_width(self, pdf) -> float:
        return pdf.w - pdf.l_margin - pdf.r_margin

    def _multi(self, pdf, font_name: str, text: str, size: int = 10):
        self._set_font(pdf, font_name, size)
        pdf.multi_cell(self._text_width(pdf), 5, text)

    def _cover_page(self, pdf, font_name: str, username: str, summary: dict, filter_label: str):
        pdf.add_page()
        pdf.set_fill_color(15, 23, 42)
        pdf.rect(0, 0, 210, 297, "F")
        pdf.set_text_color(248, 250, 252)
        self._set_font(pdf, font_name, 28, "B")
        pdf.set_y(60)
        pdf.cell(0, 14, "运动姿态综合评估报告", ln=True, align="C")
        self._set_font(pdf, font_name, 13)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 10, "Pose Training AI · Comprehensive Fitness Report", ln=True, align="C")
        pdf.ln(20)
        pdf.set_text_color(203, 213, 225)
        self._set_font(pdf, font_name, 12)
        pdf.cell(0, 9, f"学员姓名：{username}", ln=True, align="C")
        pdf.cell(0, 9, f"报告日期：{datetime.now(timezone.utc).strftime('%Y-%m-%d')}", ln=True, align="C")
        pdf.cell(0, 9, f"筛选范围：{filter_label}", ln=True, align="C")
        pdf.cell(0, 9, f"训练次数：{summary.get('total_sessions', 0)} 次", ln=True, align="C")
        pdf.cell(0, 9, f"综合评分：{summary.get('average_score', 0)} 分", ln=True, align="C")
        pdf.cell(0, 9, f"总消耗：{summary.get('total_calories', 0)} kcal", ln=True, align="C")
        pdf.ln(20)
        pdf.set_text_color(100, 116, 139)
        self._set_font(pdf, font_name, 10)
        self._multi(
            pdf, font_name,
            "本报告综合实时姿态检测、视频上传分析、评估打分、卡路里估算与纠错建议，"
            "为健身爱好者及私人教练提供可执行的训练反馈。",
            10,
        )

    def _summary_page(self, pdf, font_name: str, username: str, summary: dict, filter_label: str):
        pdf.add_page()
        pdf.set_text_color(15, 23, 42)
        self._section_title(pdf, font_name, "一、训练概览")
        self._set_font(pdf, font_name, 10)
        self._multi(pdf, font_name, f"数据范围：{filter_label}", 10)
        pdf.ln(4)
        self._set_font(pdf, font_name, 11)

        metrics = [
            ("综合评分", f"{summary.get('average_score', 0)} 分"),
            ("训练次数", f"{summary.get('total_sessions', 0)} 次"),
            ("总时长", f"{summary.get('total_duration_minutes', 0)} 分钟"),
            ("总卡路里", f"{summary.get('total_calories', 0)} kcal"),
            ("有效次数", f"{summary.get('valid_count', 0)} / {summary.get('total_count', 0)}"),
            ("错误次数", f"{summary.get('error_count', 0)} 次"),
        ]
        col_w = 63
        for i in range(0, len(metrics), 3):
            row = metrics[i : i + 3]
            for label, value in row:
                pdf.set_fill_color(241, 245, 249)
                pdf.cell(col_w, 18, f"{label}\n{value}", border=1, fill=True)
            pdf.ln(18)

        pdf.ln(8)
        breakdown = summary.get("exercise_comparison") or summary.get("exercise_breakdown", [])
        if breakdown:
            self._set_font(pdf, font_name, 11, "B")
            pdf.cell(0, 8, "按动作类型统计", ln=True)
            self._set_font(pdf, font_name, 9)
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
            for col, w in [("动作", 28), ("次数", 16), ("均分", 16), ("最新", 16), ("最高", 16), ("有效率", 20), ("错误", 16), ("kcal", 22)]:
                pdf.cell(w, 8, col, border=1, fill=True)
            pdf.ln(8)
            pdf.set_text_color(15, 23, 42)
            for item in breakdown:
                pdf.cell(28, 8, str(item.get("name", ""))[:6], border=1)
                pdf.cell(16, 8, str(item.get("count", 0)), border=1)
                pdf.cell(16, 8, str(item.get("avg_score", 0)), border=1)
                pdf.cell(16, 8, str(item.get("latest_score", item.get("avg_score", 0))), border=1)
                pdf.cell(16, 8, str(item.get("best_score", item.get("avg_score", 0))), border=1)
                pdf.cell(20, 8, f"{item.get('valid_rate', 100)}%", border=1)
                pdf.cell(16, 8, str(item.get("total_errors", 0)), border=1)
                pdf.cell(22, 8, str(item.get("calories", 0)), border=1)
                pdf.ln(8)

    def _exercise_comparison_page(self, pdf, font_name: str, summary: dict):
        trends = summary.get("exercise_trends") or summary.get("charts", {}).get("score_trend_by_exercise", [])
        if not trends:
            return
        pdf.add_page()
        self._section_title(pdf, font_name, "三、分动作 7 日训练趋势")
        self._set_font(pdf, font_name, 10)
        for item in trends:
            name = item.get("name") or get_exercise_display_name(item.get("exercise", ""))
            trend = item.get("trend", [])
            if not trend:
                self._multi(pdf, font_name, f"· {name}：暂无近7日记录", 10)
                continue
            points = " → ".join(f"{p['date'][5:]}:{p['score']}" for p in trend)
            self._multi(pdf, font_name, f"· {name}：{points}", 10)
        pdf.ln(4)

    def _feedback_page(self, pdf, font_name: str, summary: dict):
        feedback = summary.get("feedback_summary", {})
        weaknesses = feedback.get("weaknesses", [])
        recommendations = feedback.get("recommendations", [])
        if not weaknesses and not recommendations:
            return
        pdf.add_page()
        self._section_title(pdf, font_name, "四、纠错分析与训练建议")
        self._set_font(pdf, font_name, 10)
        if weaknesses:
            self._set_font(pdf, font_name, 11, "B")
            pdf.cell(0, 8, "常见待改进项（来自姿态检测与评估）", ln=True)
            self._set_font(pdf, font_name, 10)
            for idx, item in enumerate(weaknesses, 1):
                self._multi(pdf, font_name, f"{idx}. {item}", 10)
            pdf.ln(4)
        if recommendations:
            self._set_font(pdf, font_name, 11, "B")
            pdf.cell(0, 8, "个性化训练建议", ln=True)
            self._set_font(pdf, font_name, 10)
            for idx, item in enumerate(recommendations, 1):
                self._multi(pdf, font_name, f"{idx}. {item}", 10)

    def _coach_page(self, pdf, font_name: str, summary: dict, sessions: list):
        pdf.add_page()
        self._section_title(pdf, font_name, "二、致健身教练")
        self._set_font(pdf, font_name, 10)
        self._multi(
            pdf, font_name,
            "以下评估结果基于学员实际训练数据与 AI 姿态分析。建议教练结合学员体能水平、"
            "伤病史与训练目标，重点关注「待改进项」并参考「训练建议」调整训练处方。",
            10,
        )
        pdf.ln(4)

        if not sessions:
            pdf.cell(0, 8, "暂无训练记录。", ln=True)
            return

        avg = summary.get("average_score", 0)
        if avg >= 85:
            level = "优秀 — 可适度增加训练强度与复杂度"
        elif avg >= 70:
            level = "良好 — 维持当前训练量，重点纠正细节"
        elif avg >= 60:
            level = "合格 — 建议降低强度，强化基础动作模式"
        else:
            level = "需改进 — 建议从标准动作示范与低负荷训练开始"

        pdf.set_fill_color(239, 246, 255)
        pdf.set_text_color(30, 64, 175)
        self._set_font(pdf, font_name, 11, "B")
        self._multi(pdf, font_name, f"整体评估等级：{level}", 11)
        pdf.set_text_color(15, 23, 42)

    def _chart_page(self, pdf, font_name: str, title: str, image_bytes: bytes, temp_files: list):
        pdf.add_page()
        self._section_title(pdf, font_name, title)
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(image_bytes)
        tmp.close()
        temp_files.append(tmp.name)
        pdf.image(tmp.name, x=15, w=180)

    def _sessions_table(self, pdf, font_name: str, sessions: list):
        if not sessions:
            return
        pdf.add_page()
        self._section_title(pdf, font_name, "五、训练记录明细")
        self._set_font(pdf, font_name, 9)
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        for col, w in [("日期", 28), ("动作", 28), ("次数", 18), ("评分", 18), ("等级", 22), ("kcal", 22), ("错误", 18)]:
            pdf.cell(w, 8, col, border=1, fill=True)
        pdf.ln(8)
        pdf.set_text_color(15, 23, 42)

        for session in sessions[:20]:
            evaluation = parse_evaluation(getattr(session, "evaluation_json", None))
            if not evaluation:
                evaluation = build_evaluation(
                    session.exercise,
                    session.average_score,
                    session.total_count,
                    session.valid_count,
                    session.error_count,
                    session.duration_seconds,
                )
            from app.services.evaluation.calorie_service import calculate_calories
            kcal = calculate_calories(session.exercise, session.duration_seconds, session.total_count)
            date_str = session.created_at.strftime("%Y-%m-%d") if session.created_at else "-"
            name = get_exercise_display_name(session.exercise)
            pdf.cell(28, 8, date_str, border=1)
            pdf.cell(28, 8, name[:6], border=1)
            pdf.cell(18, 8, str(session.total_count), border=1)
            pdf.cell(18, 8, str(int(session.average_score)), border=1)
            pdf.cell(22, 8, evaluation.get("grade_label", "-"), border=1)
            pdf.cell(22, 8, str(kcal), border=1)
            pdf.cell(18, 8, str(session.error_count), border=1)
            pdf.ln(8)

    def _evaluation_details(self, pdf, font_name: str, sessions: list):
        if not sessions:
            return
        pdf.add_page()
        self._section_title(pdf, font_name, "六、分项评估与训练建议")

        for session in sessions[:10]:
            evaluation = parse_evaluation(getattr(session, "evaluation_json", None))
            if not evaluation:
                evaluation = build_evaluation(
                    session.exercise,
                    session.average_score,
                    session.total_count,
                    session.valid_count,
                    session.error_count,
                    session.duration_seconds,
                )
            name = evaluation.get("exercise_name") or get_exercise_display_name(session.exercise)
            pdf.set_fill_color(241, 245, 249)
            self._set_font(pdf, font_name, 11, "B")
            pdf.cell(self._text_width(pdf), 9, f"> {name} | 评分 {int(session.average_score)} | {evaluation.get('grade_label', '')}", ln=True, fill=True)
            self._multi(pdf, font_name, evaluation.get("summary", ""), 9)
            pdf.ln(2)

            dims = evaluation.get("dimension_scores", {})
            if dims:
                dim_text = " | ".join(f"{k}: {v}" for k, v in dims.items())
                pdf.set_text_color(71, 85, 105)
                self._multi(pdf, font_name, f"维度评分: {dim_text}", 9)
                pdf.set_text_color(15, 23, 42)

            for label, key in [("优势", "strengths"), ("待改进", "weaknesses"), ("建议", "recommendations")]:
                items = evaluation.get(key, [])
                if items:
                    pdf.set_text_color(30, 64, 175 if key == "recommendations" else 15)
                    self._multi(pdf, font_name, f"{label}: " + "; ".join(items), 9)
                    pdf.set_text_color(15, 23, 42)
            pdf.ln(4)

    def _section_title(self, pdf, font_name: str, title: str):
        pdf.set_text_color(30, 64, 175)
        self._set_font(pdf, font_name, 14, "B")
        pdf.cell(0, 10, title, ln=True)
        pdf.set_draw_color(59, 130, 246)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)
        pdf.set_text_color(15, 23, 42)


pdf_report_builder = PdfReportBuilder()
