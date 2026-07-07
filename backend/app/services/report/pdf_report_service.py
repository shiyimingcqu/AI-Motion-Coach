"""Professional PDF fitness assessment report generation."""

import io
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.services.evaluation.calorie_service import calculate_calories, get_exercise_display_name
from app.services.evaluation.evaluation_service import build_evaluation, parse_evaluation
from app.services.session.feedback_display import build_session_feedback_view


def _strip_markdown(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            lines.append("")
            continue
        if line.startswith("##"):
            title = re.sub(r"^#+\s*", "", line)
            title = re.sub(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]", "", title).strip()
            lines.append(f"【{title}】")
            continue
        line = re.sub(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]", "", line)
        line = line.replace("**", "").replace("*", "")
        lines.append(line)
    return "\n".join(lines)


def _normalize_text(text: str) -> str:
    """压缩多余空白，避免中英文混排时空格过大。"""
    text = re.sub(r"[ \t]+", " ", str(text).strip())
    text = re.sub(r" *\n *", "\n", text)
    return text


def _exercise_daily_trend_text(summary: dict) -> str:
    trends = summary.get("exercise_trends") or summary.get("charts", {}).get("score_trend_by_exercise", [])
    if not trends:
        return "暂无分动作趋势数据。"
    lines = []
    for item in trends:
        name = item.get("name") or get_exercise_display_name(item.get("exercise", ""))
        trend = item.get("trend", [])
        if not trend:
            lines.append(f"{name}：暂无近7日记录")
            continue
        daily = "，".join(f"{p['date'][5:]}日{int(p['score'])}分" for p in trend)
        lines.append(f"{name}：{daily}")
    return "\n".join(lines)


def _grade_level_text(avg_score: float) -> str:
    if avg_score >= 85:
        return "优秀 — 动作整体规范，可适度提升训练强度与动作复杂度。"
    if avg_score >= 70:
        return "良好 — 基础动作模式较稳定，建议针对薄弱维度做专项纠正。"
    if avg_score >= 60:
        return "合格 — 存在较明显技术偏差，建议降低负荷并强化标准动作练习。"
    return "需改进 — 建议从示范讲解、分解练习与低强度重复开始系统纠正。"


def _dimension_comment(dim_name: str, score: float) -> str:
    if score >= 85:
        level = "表现优秀"
    elif score >= 70:
        level = "基本达标"
    elif score >= 60:
        level = "有待加强"
    else:
        level = "需要重点改进"
    return f"{dim_name}（{score:.0f}分）：{level}。"


def _trend_narrative(trend: list[dict], label: str = "综合评分") -> str:
    if not trend:
        return f"当前筛选范围内暂无{label}趋势数据，完成更多训练后将自动生成走势分析。"
    scores = [p["score"] for p in trend]
    avg = sum(scores) / len(scores)
    if len(scores) >= 2:
        delta = scores[-1] - scores[0]
        if delta > 3:
            change = f"呈上升趋势（+{delta:.1f}分），训练质量持续改善。"
        elif delta < -3:
            change = f"呈下降趋势（{delta:.1f}分），建议回顾近期错误反馈并调整训练节奏。"
        else:
            change = "整体波动不大，表现较为稳定。"
    else:
        change = "记录天数较少，建议保持规律训练以观察长期变化。"
    best_day = max(trend, key=lambda p: p["score"])
    return (
        f"近{len(trend)}日{label}均值为 {avg:.1f} 分，{change}"
        f"最佳表现出现在 {best_day['date']}（{best_day['score']:.1f}分）。"
    )


def _quality_overall_narrative(summary: dict) -> str:
    radar = summary.get("charts", {}).get("quality_radar", {})
    dims = radar.get("dimensions", [])
    vals = radar.get("values", [])
    avg = summary.get("average_score", 0)
    parts = [
        f"本次筛选范围内综合评分为 {avg:.1f} 分，整体等级判定为：{_grade_level_text(avg).split('—')[0].strip()}。",
        "动作质量从多个技术维度进行量化评估，分数越高代表该维度越接近标准动作模式。",
    ]
    if dims and vals:
        paired = list(zip(dims, vals))
        best = max(paired, key=lambda x: x[1])
        weak = min(paired, key=lambda x: x[1])
        parts.append(
            f"优势维度为「{best[0]}」（{best[1]:.0f}分），"
            f"优先改进维度为「{weak[0]}」（{weak[1]:.0f}分）。"
        )
        parts.append("各维度解读如下：")
        for d, v in paired[:6]:
            parts.append(_dimension_comment(d, v))
    valid_total = summary.get("total_count", 0)
    valid_count = summary.get("valid_count", 0)
    if valid_total > 0:
        rate = valid_count / valid_total * 100
        parts.append(
            f"动作有效率 {rate:.0f}%（{valid_count}/{valid_total}），"
            f"错误动作 {summary.get('error_count', 0)} 次，"
            f"建议将纠正重点放在高频错误类型上。"
        )
    return "\n".join(parts)


def _calorie_narrative(summary: dict) -> str:
    items = summary.get("charts", {}).get("calorie_by_exercise", [])
    total = summary.get("total_calories", 0)
    if not items:
        return f"本期总消耗约 {total:.0f} kcal，完成更多训练后可查看分动作消耗对比。"
    top = max(items, key=lambda x: x.get("value", 0))
    names = [i["name"] for i in items[:3]]
    return (
        f"本期累计消耗 {total:.0f} kcal。"
        f"消耗最高动作为「{top['name']}」（{top['value']:.0f} kcal）。"
        f"主要贡献动作包括：{'、'.join(names)}。"
        "建议在高消耗动作后安排充分拉伸与恢复。"
    )


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

    import numpy as np

    plt.rcParams.update({
        "figure.facecolor": "#ffffff",
        "axes.facecolor": "#f8fafc",
        "axes.edgecolor": "#cbd5e1",
        "axes.labelcolor": "#334155",
        "xtick.color": "#475569",
        "ytick.color": "#475569",
        "text.color": "#1e293b",
        "font.size": 9,
    })

    trend = charts.get("score_trend", [])
    if trend:
        fig, ax = plt.subplots(figsize=(5.5, 2.2))
        dates = [t["date"][5:] for t in trend]
        scores = [t["score"] for t in trend]
        ax.plot(dates, scores, color="#3b82f6", linewidth=2, marker="o", markersize=4)
        ax.fill_between(range(len(scores)), scores, alpha=0.12, color="#60a5fa")
        ax.set_ylim(0, 100)
        ax.set_title("近7日综合评分趋势", fontsize=10, fontweight="bold", color="#1e40af", pad=8)
        ax.set_ylabel("评分", fontsize=8)
        ax.grid(True, alpha=0.35)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=120, facecolor="white")
        plt.close(fig)
        images["trend"] = buf.getvalue()

    exercise_trends = charts.get("score_trend_by_exercise", [])
    if exercise_trends:
        fig, ax = plt.subplots(figsize=(5.5, 2.4))
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
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
                linewidth=1.8, marker="o", markersize=3,
            )
        ax.set_ylim(0, 100)
        ax.set_title("分动作 7 日评分趋势", fontsize=10, fontweight="bold", color="#1e40af", pad=8)
        ax.legend(fontsize=7, loc="upper left")
        ax.grid(True, alpha=0.35)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=120, facecolor="white")
        plt.close(fig)
        images["trend_by_exercise"] = buf.getvalue()

    calories = charts.get("calorie_by_exercise", [])
    if calories:
        fig, ax = plt.subplots(figsize=(5.5, 2.2))
        names = [c["name"] for c in calories]
        values = [c["value"] for c in calories]
        bar_colors = ["#3b82f6", "#60a5fa", "#93c5fd", "#2563eb", "#1d4ed8"]
        ax.bar(names, values, color=bar_colors[: len(names)], edgecolor="none", width=0.5)
        ax.set_title("各动作卡路里消耗 (kcal)", fontsize=10, fontweight="bold", color="#1e40af", pad=8)
        ax.set_ylabel("kcal", fontsize=8)
        plt.setp(ax.get_xticklabels(), rotation=12, ha="right", fontsize=7)
        ax.grid(axis="y", alpha=0.35)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=120, facecolor="white")
        plt.close(fig)
        images["calories"] = buf.getvalue()

    radar = charts.get("quality_radar", {})
    dims = radar.get("dimensions", [])
    vals = radar.get("values", [])
    if dims and vals:
        angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
        vals_closed = vals + [vals[0]]
        angles_closed = angles + [angles[0]]
        fig, ax = plt.subplots(figsize=(3.8, 3.8), subplot_kw={"projection": "polar"})
        ax.plot(angles_closed, vals_closed, color="#3b82f6", linewidth=1.8)
        ax.fill(angles_closed, vals_closed, alpha=0.18, color="#60a5fa")
        ax.set_xticks(angles)
        ax.set_xticklabels(dims, fontsize=7)
        ax.set_ylim(0, 100)
        ax.set_title("动作质量雷达图", fontsize=10, fontweight="bold", color="#1e40af", pad=14)
        ax.grid(color="#cbd5e1", alpha=0.6)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=120, facecolor="white")
        plt.close(fig)
        images["radar"] = buf.getvalue()

    per_exercise = charts.get("per_exercise_radar", {})
    for exercise_key, radar_data in per_exercise.items():
        p_dims = radar_data.get("dimensions", [])
        p_vals = radar_data.get("values", [])
        if not p_dims or not p_vals:
            continue
        angles = np.linspace(0, 2 * np.pi, len(p_dims), endpoint=False).tolist()
        vals_closed = p_vals + [p_vals[0]]
        angles_closed = angles + [angles[0]]
        fig, ax = plt.subplots(figsize=(3.2, 3.2), subplot_kw={"projection": "polar"})
        ax.plot(angles_closed, vals_closed, color="#2563eb", linewidth=1.6)
        ax.fill(angles_closed, vals_closed, alpha=0.15, color="#93c5fd")
        ax.set_xticks(angles)
        ax.set_xticklabels(p_dims, fontsize=6)
        ax.set_ylim(0, 100)
        name = get_exercise_display_name(exercise_key)
        ax.set_title(f"{name}质量分析", fontsize=9, fontweight="bold", color="#1e40af", pad=12)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=120, facecolor="white")
        plt.close(fig)
        images[f"radar_{exercise_key}"] = buf.getvalue()

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
        *,
        single_session: bool = False,
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
            self._cover_page(pdf, font_name, username, summary, filter_label, single_session=single_session)
            self._summary_page(pdf, font_name, username, summary, filter_label, single_session=single_session)
            if not single_session:
                self._analysis_and_charts_page(pdf, font_name, summary, sessions, chart_images, temp_files)
            self._quality_analysis_page(pdf, font_name, summary, chart_images, temp_files, single_session=single_session)
            self._training_records_and_evaluation(pdf, font_name, sessions, summary, single_session=single_session)

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

    def _reset_x(self, pdf):
        pdf.set_x(pdf.l_margin)

    def _multi(self, pdf, font_name: str, text: str, size: int = 10, line_h: float = 5):
        if not text:
            return
        self._set_font(pdf, font_name, size)
        self._reset_x(pdf)
        pdf.multi_cell(self._text_width(pdf), line_h, _normalize_text(text))

    def _paragraph(self, pdf, font_name: str, text: str, size: int = 10, line_h: float = 5):
        self._multi(pdf, font_name, text, size, line_h)

    def _bullet_list(self, pdf, font_name: str, title: str, items: list[str], size: int = 9, line_h: float = 5):
        if not items:
            return
        self._ensure_space(pdf, 12 + line_h * min(len(items), 3))
        self._set_font(pdf, font_name, size, "B")
        self._reset_x(pdf)
        pdf.multi_cell(self._text_width(pdf), line_h, title)
        self._set_font(pdf, font_name, size)
        for item in items:
            self._ensure_space(pdf, line_h * 2)
            self._paragraph(pdf, font_name, f"  - {item}", size, line_h)

    def _table_row(
        self,
        pdf,
        font_name: str,
        widths: list[float],
        cells: list[str],
        *,
        header: bool = False,
        size: int = 8,
        line_h: float = 5,
    ):
        """绘制支持自动换行的表格行，避免长文本横向溢出。"""
        self._set_font(pdf, font_name, size, "B" if header else "")
        x0 = pdf.l_margin
        y0 = pdf.get_y()

        line_counts: list[int] = []
        for width, text in zip(widths, cells):
            lines = pdf.multi_cell(width, line_h, str(text), split_only=True)
            line_counts.append(max(1, len(lines)))
        row_h = line_h * max(line_counts)

        if y0 + row_h > pdf.h - pdf.b_margin:
            pdf.add_page()
            y0 = pdf.get_y()

        if header:
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_text_color(15, 23, 42)

        x = x0
        for width, text in zip(widths, cells):
            pdf.set_xy(x, y0)
            pdf.multi_cell(width, row_h, str(text), border=1, align="L", fill=header)
            x += width
        pdf.set_xy(x0, y0 + row_h)

    def _session_evaluation(self, session) -> dict:
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
        return evaluation

    def _ensure_space(self, pdf, needed: float = 40):
        if pdf.get_y() + needed > pdf.h - pdf.b_margin:
            pdf.add_page()
            self._reset_x(pdf)

    def _cover_page(self, pdf, font_name: str, username: str, summary: dict, filter_label: str, *, single_session: bool = False):
        pdf.add_page()
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 0, 210, 297, "F")
        pdf.set_fill_color(30, 64, 175)
        pdf.rect(0, 0, 210, 28, "F")

        pdf.set_text_color(255, 255, 255)
        self._set_font(pdf, font_name, 11)
        pdf.set_xy(10, 9)
        pdf.cell(0, 8, "Pose Training AI  |  运动姿态评估系统", ln=True)

        pdf.set_text_color(30, 64, 175)
        self._set_font(pdf, font_name, 26, "B")
        pdf.set_y(48)
        pdf.cell(0, 14, "单次训练评估报告" if single_session else "运动姿态综合评估报告", ln=True, align="C")

        self._set_font(pdf, font_name, 11)
        pdf.set_text_color(100, 116, 139)
        subtitle = "Single Training Assessment Report" if single_session else "Comprehensive Fitness Assessment Report"
        pdf.cell(0, 8, subtitle, ln=True, align="C")
        pdf.ln(12)

        info_items = [
            ("学员姓名", username),
            ("报告日期", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            ("筛选范围", filter_label),
            ("训练次数", f"{summary.get('total_sessions', 0)} 次"),
            ("综合评分", f"{summary.get('average_score', 0)} 分"),
            ("总消耗", f"{summary.get('total_calories', 0)} kcal"),
        ]
        box_w = 88
        start_x = (210 - box_w * 2 - 8) / 2
        pdf.set_text_color(15, 23, 42)
        for i, (label, value) in enumerate(info_items):
            col = i % 2
            row = i // 2
            x = start_x + col * (box_w + 8)
            y = 95 + row * 26
            pdf.set_xy(x, y)
            pdf.set_fill_color(239, 246, 255)
            pdf.set_draw_color(191, 219, 254)
            pdf.rect(x, y, box_w, 22, style="DF")
            self._set_font(pdf, font_name, 9)
            pdf.set_text_color(100, 116, 139)
            pdf.set_xy(x + 4, y + 3)
            pdf.cell(box_w - 8, 5, label)
            self._set_font(pdf, font_name, 11, "B")
            pdf.set_text_color(30, 64, 175)
            pdf.set_xy(x + 4, y + 10)
            pdf.cell(box_w - 8, 8, str(value))

        pdf.set_y(175)
        pdf.set_text_color(71, 85, 105)
        self._set_font(pdf, font_name, 10)
        self._reset_x(pdf)
        self._multi(
            pdf, font_name,
            "本报告综合实时姿态检测、视频分析、动作质量评估、卡路里估算与纠错建议生成。"
            "报告采用图表与文字分析结合的方式，为学员与教练提供可执行的训练反馈。",
            10,
        )

    def _summary_page(self, pdf, font_name: str, username: str, summary: dict, filter_label: str, *, single_session: bool = False):
        pdf.add_page()
        pdf.set_text_color(15, 23, 42)
        title = "一、本次训练概览" if single_session else "一、训练概览"
        self._section_title(pdf, font_name, title)
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
            self._paragraph(pdf, font_name, "按动作类型统计", 11)
            widths = [24, 14, 14, 14, 14, 18, 14, 18]
            headers = ["动作", "次数", "均分", "最新", "最高", "有效率", "错误", "kcal"]
            self._table_row(pdf, font_name, widths, headers, header=True, size=8)
            for item in breakdown:
                self._table_row(
                    pdf,
                    font_name,
                    widths,
                    [
                        str(item.get("name", "")),
                        str(item.get("count", 0)),
                        str(item.get("avg_score", 0)),
                        str(item.get("latest_score", item.get("avg_score", 0))),
                        str(item.get("best_score", item.get("avg_score", 0))),
                        f"{item.get('valid_rate', 100)}%",
                        str(item.get("total_errors", 0)),
                        str(item.get("calories", 0)),
                    ],
                    size=8,
                )

        pdf.ln(6)
        avg = summary.get("average_score", 0)
        self._set_font(pdf, font_name, 10, "B")
        self._paragraph(pdf, font_name, "概览分析", 10)
        self._paragraph(
            pdf, font_name,
            f"本期共完成 {summary.get('total_sessions', 0)} 次训练，累计时长 "
            f"{summary.get('total_duration_minutes', 0)} 分钟，综合评分 {avg:.1f} 分。"
            f"{_grade_level_text(avg)}",
            10,
        )
        fb = summary.get("feedback_summary") or {}
        if fb.get("weaknesses"):
            self._paragraph(
                pdf, font_name,
                "跨训练高频薄弱点：" + "；".join(fb["weaknesses"][:4]) + "。",
                9,
            )

    def _subsection_title(self, pdf, font_name: str, title: str):
        self._ensure_space(pdf, 16)
        pdf.set_text_color(30, 64, 175)
        self._set_font(pdf, font_name, 11, "B")
        self._paragraph(pdf, font_name, title, 11)
        pdf.set_text_color(15, 23, 42)

    def _embed_chart(
        self,
        pdf,
        font_name: str,
        title: str,
        analysis: str,
        image_bytes: bytes,
        temp_files: list,
        *,
        img_width: float = 155,
    ):
        self._ensure_space(pdf, 75)
        self._subsection_title(pdf, font_name, title)
        for paragraph in analysis.split("\n"):
            paragraph = paragraph.strip()
            if paragraph:
                self._paragraph(pdf, font_name, paragraph, 9)
        pdf.ln(2)

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(image_bytes)
        tmp.close()
        temp_files.append(tmp.name)
        x = pdf.l_margin + (self._text_width(pdf) - img_width) / 2
        pdf.image(tmp.name, x=x, w=img_width)
        pdf.ln(2)

    def _analysis_and_charts_page(
        self,
        pdf,
        font_name: str,
        summary: dict,
        sessions: list,
        chart_images: dict,
        temp_files: list,
    ):
        pdf.add_page()
        self._section_title(pdf, font_name, "二、综合评估与趋势分析")

        avg = summary.get("average_score", 0)
        self._paragraph(
            pdf, font_name,
            "本节结合训练数据与图表，对本期整体表现进行解读。"
            "评估基于姿态关键点检测、动作规范性打分与有效次数统计。",
            10,
        )
        pdf.set_fill_color(239, 246, 255)
        self._set_font(pdf, font_name, 10, "B")
        self._reset_x(pdf)
        pdf.multi_cell(self._text_width(pdf), 7, f"教练评语：{_grade_level_text(avg)}", fill=True)
        pdf.ln(3)

        trend = summary.get("trend") or summary.get("charts", {}).get("score_trend", [])
        if "trend" in chart_images:
            self._embed_chart(
                pdf, font_name,
                "综合评分走势",
                _trend_narrative(trend),
                chart_images["trend"],
                temp_files,
            )

        if "trend_by_exercise" in chart_images:
            exercise_trends = summary.get("exercise_trends") or []
            lines = ["以下展示各动作近7日评分变化，便于发现单项技术的进步或退步。"]
            for item in exercise_trends[:4]:
                name = item.get("name") or get_exercise_display_name(item.get("exercise", ""))
                pts = item.get("trend", [])
                if pts:
                    lines.append(_trend_narrative(pts, label=name))
            self._embed_chart(
                pdf, font_name,
                "分动作评分走势",
                "\n".join(lines),
                chart_images["trend_by_exercise"],
                temp_files,
            )

        exercise_detail = _exercise_daily_trend_text(summary)
        if exercise_detail and exercise_detail != "暂无分动作趋势数据。":
            self._subsection_title(pdf, font_name, "分动作每日评分明细")
            self._paragraph(
                pdf, font_name,
                "以下按动作汇总近7日每日得分，便于横向对比单项进步情况。",
                9,
            )
            for line in exercise_detail.split("\n"):
                self._paragraph(pdf, font_name, line, 9)
            pdf.ln(2)

        if "calories" in chart_images:
            self._embed_chart(
                pdf, font_name,
                "能量消耗分析",
                _calorie_narrative(summary),
                chart_images["calories"],
                temp_files,
            )

    def _quality_analysis_page(
        self,
        pdf,
        font_name: str,
        summary: dict,
        chart_images: dict,
        temp_files: list,
        *,
        single_session: bool = False,
    ):
        radar = summary.get("charts", {}).get("quality_radar", {})
        per_exercise = summary.get("charts", {}).get("per_exercise_radar", {})
        if "radar" not in chart_images and not per_exercise:
            return

        pdf.add_page()
        title = "二、动作质量分析" if single_session else "三、动作质量深度分析"
        self._section_title(pdf, font_name, title)
        self._paragraph(pdf, font_name, _quality_overall_narrative(summary), 10)
        pdf.ln(3)

        if "radar" in chart_images:
            self._embed_chart(
                pdf, font_name,
                "综合质量雷达",
                "雷达图展示各技术维度的综合得分，面积越大代表整体动作质量越高。",
                chart_images["radar"],
                temp_files,
                img_width=120,
            )

        breakdown = summary.get("exercise_breakdown") or []
        if breakdown and not single_session:
            self._subsection_title(pdf, font_name, "分动作质量评述")
            for item in breakdown[:6]:
                name = item.get("name", "")
                avg_score = item.get("avg_score", 0)
                valid_rate = item.get("valid_rate", 100)
                errors = item.get("total_errors", 0)
                text = (
                    f"{name}：本期训练 {item.get('count', 0)} 次，均分 {avg_score:.1f}，"
                    f"有效率 {valid_rate:.0f}%，累计错误 {errors} 次。"
                )
                if avg_score >= 85:
                    text += " 动作质量稳定，可尝试增加负重或节奏变化。"
                elif avg_score >= 70:
                    text += " 整体达标，建议针对薄弱维度做分解练习。"
                else:
                    text += " 建议降低强度，先纠正基础姿态再增加训练量。"
                self._paragraph(pdf, font_name, text, 9)

        per_keys = [k for k in chart_images if k.startswith("radar_")][:4]
        if per_keys and not single_session:
            self._subsection_title(pdf, font_name, "分动作质量雷达")
            self._paragraph(
                pdf, font_name,
                "以下为各动作独立的质量维度分析，可精确定位该技术环节的优势与短板。",
                9,
            )
            for key in per_keys:
                exercise_key = key.replace("radar_", "")
                radar_data = per_exercise.get(exercise_key, {})
                dims = radar_data.get("dimensions", [])
                vals = radar_data.get("values", [])
                name = get_exercise_display_name(exercise_key)
                analysis_lines = [f"{name}各维度表现："]
                for d, v in zip(dims, vals):
                    analysis_lines.append(_dimension_comment(d, v))
                self._embed_chart(
                    pdf, font_name,
                    name,
                    "\n".join(analysis_lines),
                    chart_images[key],
                    temp_files,
                    img_width=105,
                )

    def _training_records_and_evaluation(self, pdf, font_name: str, sessions: list, summary: dict, *, single_session: bool = False):
        if not sessions:
            return

        pdf.add_page()
        title = "三、评估与纠错明细" if single_session else "四、训练记录与评估纠错明细"
        self._section_title(pdf, font_name, title)
        intro = (
            "以下为本次训练的评估摘要、维度评分、纠错建议与 AI 指导。"
            if single_session
            else "下表汇总筛选范围内的训练记录；每条记录后附分项评估、纠错建议与 AI 指导，排版已自动换行。"
        )
        self._paragraph(pdf, font_name, intro, 10)
        pdf.ln(3)

        fb = summary.get("feedback_summary") or {}
        weaknesses = fb.get("weaknesses") or []
        recommendations = fb.get("recommendations") or []
        if (weaknesses or recommendations) and not single_session:
            self._set_font(pdf, font_name, 10, "B")
            self._paragraph(pdf, font_name, "整体薄弱点与训练建议（汇总）", 10)
            self._bullet_list(pdf, font_name, "常见薄弱点：", weaknesses[:6], size=9)
            self._bullet_list(pdf, font_name, "综合训练建议：", recommendations[:6], size=9)
            pdf.ln(4)

        record_widths = [22, 20, 12, 12, 14, 14, 12, 16]
        record_headers = ["日期", "动作", "总次", "有效", "评分", "等级", "错误", "卡路里"]
        if not single_session:
            self._table_row(pdf, font_name, record_widths, record_headers, header=True, size=8)

            for session in sessions[:20]:
                evaluation = self._session_evaluation(session)
                kcal = round(
                    calculate_calories(session.exercise, session.duration_seconds, session.total_count),
                    1,
                )
                date_str = session.created_at.strftime("%m-%d %H:%M") if session.created_at else "-"
                name = evaluation.get("exercise_name") or get_exercise_display_name(session.exercise)
                self._table_row(
                    pdf, font_name, record_widths,
                    [
                        date_str,
                        name,
                        str(session.total_count),
                        str(session.valid_count),
                        str(int(session.average_score)),
                        evaluation.get("grade_label", "-"),
                        str(session.error_count),
                        str(kcal),
                    ],
                    size=8,
                )

            pdf.ln(4)
        self._set_font(pdf, font_name, 11, "B")
        section_label = "本次评估与纠错建议" if single_session else "分项评估与纠错建议"
        self._paragraph(pdf, font_name, section_label, 11)
        pdf.ln(2)

        session_limit = 1 if single_session else 15
        for session in sessions[:session_limit]:
            evaluation = self._session_evaluation(session)
            feedback = build_session_feedback_view(session)
            name = evaluation.get("exercise_name") or get_exercise_display_name(session.exercise)
            date_str = session.created_at.strftime("%Y-%m-%d %H:%M") if session.created_at else "-"

            self._ensure_space(pdf, 55)
            pdf.set_fill_color(241, 245, 249)
            self._set_font(pdf, font_name, 11, "B")
            self._reset_x(pdf)
            pdf.multi_cell(
                self._text_width(pdf), 8,
                f"【{name}】{date_str}，评分{int(session.average_score)}分，{evaluation.get('grade_label', '')}",
                border=0, fill=True,
            )
            pdf.ln(1)

            summary_text = evaluation.get("summary", "")
            if summary_text:
                self._set_font(pdf, font_name, 9, "B")
                self._paragraph(pdf, font_name, "评估摘要", 9)
                self._paragraph(pdf, font_name, summary_text, 9)

            dims = evaluation.get("dimension_scores", {})
            if dims:
                self._set_font(pdf, font_name, 9, "B")
                self._paragraph(pdf, font_name, "质量维度评分", 9)
                dim_widths = [60, 30]
                self._table_row(pdf, font_name, dim_widths, ["维度", "得分"], header=True, size=8)
                for dim_name, dim_score in dims.items():
                    self._table_row(pdf, font_name, dim_widths, [dim_name, str(dim_score)], size=8)
                for d, v in dims.items():
                    self._paragraph(pdf, font_name, _dimension_comment(d, v), 9)
                pdf.ln(1)

            self._bullet_list(pdf, font_name, "动作优势：", evaluation.get("strengths", []), size=9)
            self._bullet_list(pdf, font_name, "待改进项：", evaluation.get("weaknesses", []), size=9)
            self._bullet_list(pdf, font_name, "训练建议：", evaluation.get("recommendations", []), size=9)

            error_cards = [c for c in feedback.get("cards", []) if c.get("kind") == "error"]
            if error_cards:
                self._set_font(pdf, font_name, 9, "B")
                self._paragraph(pdf, font_name, "纠错反馈", 9)
                for card in error_cards:
                    self._ensure_space(pdf, 20)
                    label = card.get("label", "问题")
                    self._set_font(pdf, font_name, 9, "B")
                    self._paragraph(pdf, font_name, f"[{label}]", 9)
                    problem = card.get("problem", "")
                    if problem:
                        self._set_font(pdf, font_name, 9)
                        self._paragraph(pdf, font_name, f"问题：{problem}", 9)
                    suggestion = card.get("suggestion", "")
                    if suggestion:
                        pdf.set_text_color(30, 64, 175)
                        self._paragraph(pdf, font_name, f"纠正建议：{suggestion}", 9)
                        pdf.set_text_color(15, 23, 42)

            if feedback.get("error_analysis"):
                types = [
                    f"{item['type']}（{item['percent']}%）"
                    for item in feedback["error_analysis"]
                ]
                self._bullet_list(pdf, font_name, "错误类型分布：", types, size=9)

            ai_advice = feedback.get("ai_advice", "")
            if ai_advice:
                self._ensure_space(pdf, 30)
                self._set_font(pdf, font_name, 9, "B")
                pdf.set_text_color(30, 64, 175)
                self._paragraph(pdf, font_name, "AI 智能建议", 9)
                pdf.set_text_color(15, 23, 42)
                for block in _strip_markdown(ai_advice).split("\n"):
                    block = block.strip()
                    if block:
                        self._paragraph(pdf, font_name, block, 9)

            pdf.ln(3)
            pdf.set_draw_color(226, 232, 240)
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(2)

    def _section_title(self, pdf, font_name: str, title: str):
        pdf.set_text_color(30, 64, 175)
        self._set_font(pdf, font_name, 14, "B")
        self._reset_x(pdf)
        pdf.multi_cell(self._text_width(pdf), 8, title)
        pdf.set_draw_color(59, 130, 246)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)
        pdf.set_text_color(15, 23, 42)


pdf_report_builder = PdfReportBuilder()
