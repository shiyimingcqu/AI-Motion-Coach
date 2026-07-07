"""Report generation service — aggregates session data and builds evaluation reports."""

import csv
import io
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.entities import SessionORM
from app.services.evaluation.calorie_service import (
    calculate_calories,
    get_exercise_display_name,
)
from app.services.evaluation.evaluation_service import (
    build_evaluation,
    parse_evaluation,
)


class ReportService:
    def _query_sessions(
        self,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_all_users: bool = False,
        exercise: str | None = None,
    ) -> list[SessionORM]:
        if SessionLocal is None:
            return []

        db = SessionLocal()
        try:
            query = db.query(SessionORM).order_by(SessionORM.created_at.desc())
            if user_id is not None and not include_all_users:
                query = query.filter(SessionORM.user_id == user_id)
            if exercise:
                query = query.filter(SessionORM.exercise == exercise)
            if date_from:
                query = query.filter(SessionORM.created_at >= datetime.fromisoformat(date_from))
            if date_to:
                query = query.filter(
                    SessionORM.created_at <= datetime.fromisoformat(date_to + "T23:59:59")
                )
            return query.all()
        finally:
            db.close()

    @staticmethod
    def _build_daily_trend(trend_map: dict[str, list[float]], limit: int = 7) -> list[dict]:
        return sorted(
            (
                {"date": day, "score": round(sum(values) / len(values), 1)}
                for day, values in trend_map.items()
            ),
            key=lambda item: item["date"],
        )[-limit:]

    def _aggregate_personal_data(self, sessions: list[SessionORM]) -> dict:
        total = len(sessions)
        total_duration = sum(s.duration_seconds for s in sessions)
        avg_score = sum(s.average_score for s in sessions) / total
        total_count = sum(s.total_count for s in sessions)
        valid_count = sum(s.valid_count for s in sessions)
        total_calories = 0.0

        trend_map: dict[str, list[float]] = {}
        trend_by_exercise: dict[str, dict[str, list[float]]] = {}
        calorie_map: dict[str, float] = {}
        exercise_stats: dict[str, dict] = {}
        error_map: dict[str, int] = {}
        radar_accumulator: dict[str, list[float]] = {}
        per_exercise_radar: dict[str, dict[str, list[float]]] = {}
        feedback_weaknesses: list[str] = []
        feedback_recommendations: list[str] = []

        for session in sessions:
            calories, evaluation = self._ensure_session_metrics(session)
            total_calories += calories

            day = session.created_at.strftime("%Y-%m-%d")
            trend_map.setdefault(day, []).append(session.average_score)
            trend_by_exercise.setdefault(session.exercise, {}).setdefault(day, []).append(
                session.average_score
            )

            exercise_name = evaluation.get("exercise_name") or get_exercise_display_name(session.exercise)
            calorie_map[exercise_name] = calorie_map.get(exercise_name, 0) + calories
            error_map[exercise_name] = error_map.get(exercise_name, 0) + session.error_count

            stats = exercise_stats.setdefault(
                session.exercise,
                {
                    "exercise": session.exercise,
                    "name": exercise_name,
                    "count": 0,
                    "total_score": 0.0,
                    "calories": 0.0,
                    "total_errors": 0,
                    "valid_count": 0,
                    "total_count": 0,
                    "duration_seconds": 0,
                    "scores": [],
                },
            )
            stats["count"] += 1
            stats["total_score"] += session.average_score
            stats["calories"] += calories
            stats["total_errors"] += session.error_count
            stats["valid_count"] += session.valid_count
            stats["total_count"] += session.total_count
            stats["duration_seconds"] += session.duration_seconds
            stats["scores"].append(session.average_score)

            for label, value in evaluation.get("dimension_scores", {}).items():
                radar_accumulator.setdefault(label, []).append(float(value))
                per_exercise_radar.setdefault(session.exercise, {}).setdefault(label, []).append(
                    float(value)
                )

            for item in evaluation.get("weaknesses", []):
                if item and item not in feedback_weaknesses:
                    feedback_weaknesses.append(item)
            for item in evaluation.get("recommendations", []):
                if item and item not in feedback_recommendations:
                    feedback_recommendations.append(item)

        trend = self._build_daily_trend(trend_map)
        exercise_trends = [
            {
                "exercise": exercise_key,
                "name": get_exercise_display_name(exercise_key),
                "trend": self._build_daily_trend(day_map),
            }
            for exercise_key, day_map in trend_by_exercise.items()
        ]

        exercise_breakdown = [
            {
                "exercise": key,
                "name": value["name"],
                "count": value["count"],
                "avg_score": round(value["total_score"] / value["count"], 1),
                "calories": round(value["calories"], 1),
                "total_errors": value["total_errors"],
                "valid_rate": round(
                    (value["valid_count"] / value["total_count"] * 100)
                    if value["total_count"] > 0 else 100.0,
                    1,
                ),
                "best_score": round(max(value["scores"]), 1),
                "latest_score": round(value["scores"][0], 1) if value["scores"] else 0,
                "duration_minutes": round(value["duration_seconds"] / 60, 1),
            }
            for key, value in exercise_stats.items()
        ]
        exercise_breakdown.sort(key=lambda item: item["count"], reverse=True)

        exercise_comparison = exercise_breakdown

        radar_dimensions = list(radar_accumulator.keys())
        radar_values = [
            round(sum(values) / len(values), 1) for values in radar_accumulator.values()
        ]
        if not radar_dimensions:
            radar_dimensions = ["动作规范", "节奏控制", "稳定性"]
            radar_values = [round(avg_score, 1)] * 3

        per_exercise_radar_output = {
            exercise_key: {
                "dimensions": list(dim_map.keys()),
                "values": [
                    round(sum(values) / len(values), 1) for values in dim_map.values()
                ],
            }
            for exercise_key, dim_map in per_exercise_radar.items()
        }

        return {
            "average_score": round(avg_score, 1),
            "total_sessions": total,
            "total_duration_minutes": round(total_duration / 60),
            "total_count": total_count,
            "valid_count": valid_count,
            "error_count": max(0, total_count - valid_count),
            "total_calories": round(total_calories, 1),
            "trend": trend,
            "exercise_breakdown": exercise_breakdown,
            "exercise_comparison": exercise_comparison,
            "exercise_trends": exercise_trends,
            "feedback_summary": {
                "weaknesses": feedback_weaknesses[:8],
                "recommendations": feedback_recommendations[:8],
            },
            "recent_sessions": [
                {
                    "session_id": s.session_id,
                    "exercise": s.exercise,
                    "score": s.average_score,
                    "calories": self._ensure_session_metrics(s)[0],
                    "created_at": s.created_at.isoformat(),
                }
                for s in sessions[:5]
            ],
            "charts": {
                "score_trend": trend,
                "score_trend_by_exercise": exercise_trends,
                "calorie_by_exercise": [
                    {"name": name, "value": round(value, 1)}
                    for name, value in sorted(calorie_map.items(), key=lambda x: x[1], reverse=True)
                ],
                "exercise_distribution": [
                    {"name": item["name"], "value": item["count"]}
                    for item in exercise_breakdown
                ],
                "quality_radar": {
                    "dimensions": radar_dimensions,
                    "values": radar_values,
                },
                "per_exercise_radar": per_exercise_radar_output,
                "error_by_exercise": [
                    {"name": name, "value": count}
                    for name, count in error_map.items()
                ],
            },
        }

    def _ensure_session_metrics(self, session: SessionORM) -> tuple[float, dict]:
        evaluation = parse_evaluation(session.evaluation_json)
        calories = calculate_calories(
            session.exercise,
            session.duration_seconds,
            session.total_count,
        )

        if evaluation is None:
            evaluation = build_evaluation(
                exercise=session.exercise,
                average_score=session.average_score,
                total_count=session.total_count,
                valid_count=session.valid_count,
                error_count=session.error_count,
                duration_seconds=session.duration_seconds,
            )
        return calories, evaluation

    def _session_to_report_item(self, session: SessionORM) -> dict:
        calories, evaluation = self._ensure_session_metrics(session)
        exercise_name = evaluation.get("exercise_name") or get_exercise_display_name(session.exercise)
        grade_label = evaluation.get("grade_label", "—")

        return {
            "id": session.session_id,
            "session_id": session.session_id,
            "title": f"{exercise_name} 训练评估报告",
            "subtitle": f"评分 {session.average_score:.0f} · {grade_label}",
            "type": "Session",
            "date": session.created_at.strftime("%Y-%m-%d") if session.created_at else "",
            "exercise": session.exercise,
            "exercise_name": exercise_name,
            "exercises_count": 1,
            "sessions_count": 1,
            "average_score": round(session.average_score, 1),
            "calories": calories,
            "size": f"{calories:.0f} kcal",
            "grade": evaluation.get("grade"),
            "grade_label": grade_label,
            "duration_minutes": evaluation.get("duration_minutes", 0),
            "error_count": session.error_count,
        }

    def list_reports(
        self,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_all_users: bool = False,
        exercise: str | None = None,
    ) -> dict:
        sessions = self._query_sessions(
            user_id, date_from, date_to, include_all_users, exercise
        )
        items = [self._session_to_report_item(session) for session in sessions]
        return {"items": items, "total": len(items)}

    def get_session_report(self, session: SessionORM) -> dict:
        calories, evaluation = self._ensure_session_metrics(session)
        dimension_scores = evaluation.get("dimension_scores", {})
        radar_dimensions = list(dimension_scores.keys())
        radar_values = list(dimension_scores.values())

        if session.exercise == "plank":
            rep_labels = ["有效保持", "姿态问题"]
            rep_values = [session.valid_count, max(0, session.error_count)]
        else:
            rep_labels = ["有效次数", "错误次数"]
            rep_values = [session.valid_count, max(0, session.error_count)]

        return {
            "session_id": session.session_id,
            "exercise": session.exercise,
            "exercise_name": evaluation.get("exercise_name"),
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "duration_seconds": session.duration_seconds,
            "total_count": session.total_count,
            "valid_count": session.valid_count,
            "error_count": session.error_count,
            "average_score": round(session.average_score, 1),
            "calories_burned": calories,
            "evaluation": evaluation,
            "charts": {
                "quality_radar": {
                    "dimensions": radar_dimensions,
                    "values": radar_values,
                },
                "rep_breakdown": {
                    "labels": rep_labels,
                    "values": rep_values,
                },
                "score_gauge": {
                    "value": round(session.average_score, 1),
                    "max": 100,
                },
            },
        }

    def personal_summary(
        self,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_all_users: bool = False,
        exercise: str | None = None,
    ) -> dict:
        sessions = self._query_sessions(
            user_id, date_from, date_to, include_all_users, exercise
        )
        if not sessions:
            return self._empty_summary()
        return self._aggregate_personal_data(sessions)

    def export_csv(
        self,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_all_users: bool = False,
        exercise: str | None = None,
    ) -> str:
        sessions = self._query_sessions(
            user_id, date_from, date_to, include_all_users, exercise
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Session ID", "Exercise", "Date", "Duration (s)", "Total Reps",
            "Valid Reps", "Errors", "Avg Score", "Calories (kcal)", "Grade",
        ])
        for session in sessions:
            calories, evaluation = self._ensure_session_metrics(session)
            writer.writerow([
                session.session_id,
                session.exercise,
                session.created_at.isoformat() if session.created_at else "",
                session.duration_seconds,
                session.total_count,
                session.valid_count,
                session.error_count,
                session.average_score,
                calories,
                evaluation.get("grade_label", ""),
            ])
        return output.getvalue()

    def export_pdf_html(
        self,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_all_users: bool = False,
        exercise: str | None = None,
    ) -> str:
        summary = self.personal_summary(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            include_all_users=include_all_users,
            exercise=exercise,
        )

        rows_html = ""
        for session in summary.get("recent_sessions", []):
            rows_html += (
                f"<tr><td>{session['session_id'][:8]}</td>"
                f"<td>{session['exercise']}</td>"
                f"<td>{session['created_at'][:10]}</td>"
                f"<td>{session['score']}</td>"
                f"<td>{session.get('calories', 0)}</td></tr>"
            )

        trend_html = ""
        for item in summary.get("trend", []):
            trend_html += f"<li>{item['date']}: {item['score']}</li>"

        exercise_html = ""
        for item in summary.get("exercise_breakdown", []):
            exercise_html += (
                f"<li>{item['name']}: {item['count']} 次, "
                f"均分 {item['avg_score']}, 消耗 {item['calories']} kcal</li>"
            )

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>训练评估报告</title>
<style>
body {{ font-family: sans-serif; padding: 40px; }}
h1 {{ color: #1e40af; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; }}
th {{ background: #f1f5f9; }}
.stat-card {{ display: inline-block; padding: 16px 24px; margin: 8px; background: #f8fafc; border-radius: 8px; text-align: center; }}
.stat-card strong {{ font-size: 24px; display: block; color: #1e40af; }}
</style></head>
<body>
<h1>运动姿态训练评估报告</h1>
<p>生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
<h2>训练概览</h2>
<div class="stat-card"><strong>{summary['total_sessions']}</strong><span>训练次数</span></div>
<div class="stat-card"><strong>{summary['average_score']}</strong><span>平均评分</span></div>
<div class="stat-card"><strong>{summary['total_duration_minutes']}</strong><span>总时长(分钟)</span></div>
<div class="stat-card"><strong>{summary['total_calories']}</strong><span>总消耗(kcal)</span></div>
<div class="stat-card"><strong>{summary['valid_count']}/{summary['total_count']}</strong><span>有效次数</span></div>
<h2>按动作统计</h2>
<ul>{exercise_html}</ul>
<h2>最近训练</h2>
<table><thead><tr><th>ID</th><th>动作</th><th>日期</th><th>评分</th><th>卡路里</th></tr></thead><tbody>{rows_html}</tbody></table>
<h2>近7日评分趋势</h2>
<ul>{trend_html}</ul>
</body></html>"""

    def export_pdf(
        self,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        username: str = "学员",
        include_all_users: bool = False,
        exercise: str | None = None,
    ) -> bytes:
        from app.services.report.pdf_report_service import pdf_report_builder

        summary = self.personal_summary(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            include_all_users=include_all_users,
            exercise=exercise,
        )
        sessions = self._query_sessions(
            user_id, date_from, date_to, include_all_users, exercise
        )
        from app.services.report.error_frame_service import error_frame_service

        assessment_data = error_frame_service.list_error_frames(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            include_all_users=include_all_users,
            exercise=exercise,
            limit=80,
            session_scan=30,
        )
        return pdf_report_builder.build(
            summary,
            sessions,
            username=username,
            date_from=date_from,
            date_to=date_to,
            exercise=exercise,
            assessment_data=assessment_data,
        )

    def export_session_pdf(self, session: SessionORM, username: str = "学员") -> bytes:
        from app.services.report.pdf_report_service import pdf_report_builder

        summary = self._aggregate_personal_data([session])
        date_str = session.created_at.strftime("%Y-%m-%d") if session.created_at else None
        from app.services.report.error_frame_service import error_frame_service

        assessment_data = error_frame_service.list_error_frames(
            user_id=session.user_id,
            date_from=date_str,
            date_to=date_str,
            exercise=session.exercise,
            limit=20,
            session_scan=1,
        )
        return pdf_report_builder.build(
            summary,
            [session],
            username=username,
            date_from=date_str,
            date_to=date_str,
            exercise=session.exercise,
            single_session=True,
            assessment_data=assessment_data,
        )

    def class_summary(self) -> dict:
        return self.personal_summary(user_id=None)

    @staticmethod
    def _empty_summary() -> dict:
        return {
            "average_score": 0,
            "total_sessions": 0,
            "total_duration_minutes": 0,
            "total_count": 0,
            "valid_count": 0,
            "error_count": 0,
            "total_calories": 0,
            "trend": [],
            "exercise_breakdown": [],
            "exercise_comparison": [],
            "exercise_trends": [],
            "feedback_summary": {"weaknesses": [], "recommendations": []},
            "recent_sessions": [],
            "charts": {
                "score_trend": [],
                "score_trend_by_exercise": [],
                "calorie_by_exercise": [],
                "exercise_distribution": [],
                "quality_radar": {"dimensions": [], "values": []},
                "per_exercise_radar": {},
                "error_by_exercise": [],
            },
        }


report_service = ReportService()
