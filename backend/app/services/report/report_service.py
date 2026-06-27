"""Report generation service — aggregates session data from the database."""

import csv
import io
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.entities import SessionORM


class ReportService:
    def personal_summary(self, user_id: int | None = None, date_from: str | None = None, date_to: str | None = None) -> dict:
        """Return summary statistics for a given user (or all sessions if None)."""
        if SessionLocal is None:
            return self._empty_summary()

        db = SessionLocal()
        try:
            query = db.query(SessionORM).order_by(SessionORM.created_at.desc())
            if user_id is not None:
                query = query.filter(SessionORM.user_id == user_id)
            if date_from:
                query = query.filter(SessionORM.created_at >= datetime.fromisoformat(date_from))
            if date_to:
                query = query.filter(SessionORM.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))
            sessions = query.all()
            if not sessions:
                return self._empty_summary()

            total = len(sessions)
            total_duration = sum(s.duration_seconds for s in sessions)
            avg_score = sum(s.average_score for s in sessions) / total
            total_count = sum(s.total_count for s in sessions)
            valid_count = sum(s.valid_count for s in sessions)

            # trend: last 7 days
            trend_map: dict[str, list[float]] = {}
            for s in sessions:
                day = s.created_at.strftime("%Y-%m-%d")
                trend_map.setdefault(day, []).append(s.average_score)
            trend = sorted(
                {"date": day, "score": round(sum(v) / len(v), 1)}
                for day, v in trend_map.items()
            )[-7:]

            # error aggregation
            error_count = total_count - valid_count

            return {
                "average_score": round(avg_score, 1),
                "total_sessions": total,
                "total_duration_minutes": round(total_duration / 60),
                "total_count": total_count,
                "valid_count": valid_count,
                "error_count": max(0, error_count),
                "trend": trend,
                "recent_sessions": [
                    {
                        "session_id": s.session_id,
                        "exercise": s.exercise,
                        "score": s.average_score,
                        "created_at": s.created_at.isoformat(),
                    }
                    for s in sessions[:5]
                ],
            }
        finally:
            db.close()

    def export_csv(self, user_id: int | None = None, date_from: str | None = None, date_to: str | None = None) -> str:
        """Generate a CSV string of training sessions."""
        if SessionLocal is None:
            return ""

        db = SessionLocal()
        try:
            query = db.query(SessionORM).order_by(SessionORM.created_at.desc())
            if user_id is not None:
                query = query.filter(SessionORM.user_id == user_id)
            if date_from:
                query = query.filter(SessionORM.created_at >= datetime.fromisoformat(date_from))
            if date_to:
                query = query.filter(SessionORM.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))
            sessions = query.all()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Session ID", "Exercise", "Date", "Duration (s)", "Total Reps", "Valid Reps", "Errors", "Avg Score"])
            for s in sessions:
                writer.writerow([
                    s.session_id, s.exercise, s.created_at.isoformat() if s.created_at else "",
                    s.duration_seconds, s.total_count, s.valid_count, s.error_count, s.average_score,
                ])
            return output.getvalue()
        finally:
            db.close()

    def export_pdf_html(self, user_id: int | None = None, date_from: str | None = None, date_to: str | None = None) -> str:
        """Generate an HTML document suitable for PDF conversion."""
        summary = self.personal_summary(user_id=user_id, date_from=date_from, date_to=date_to)

        rows_html = ""
        for s in summary.get("recent_sessions", []):
            rows_html += f"<tr><td>{s['session_id'][:8]}</td><td>{s['exercise']}</td><td>{s['created_at'][:10]}</td><td>{s['score']}</td></tr>"

        trend_html = ""
        for t in summary.get("trend", []):
            trend_html += f"<li>{t['date']}: {t['score']}</li>"

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Training Report</title>
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
<h1>Training Performance Report</h1>
<p>Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
<h2>Summary</h2>
<div class="stat-card"><strong>{summary['total_sessions']}</strong><span>Total Sessions</span></div>
<div class="stat-card"><strong>{summary['average_score']}</strong><span>Avg Score</span></div>
<div class="stat-card"><strong>{summary['total_duration_minutes']}</strong><span>Total Min</span></div>
<div class="stat-card"><strong>{summary['valid_count']}/{summary['total_count']}</strong><span>Valid Reps</span></div>
<h2>Recent Sessions</h2>
<table><thead><tr><th>ID</th><th>Exercise</th><th>Date</th><th>Score</th></tr></thead><tbody>{rows_html}</tbody></table>
<h2>Score Trend (Last 7 Days)</h2>
<ul>{trend_html}</ul>
</body></html>"""

    def class_summary(self) -> dict:
        """Return class-level summary (all users, admin only)."""
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
            "trend": [],
            "recent_sessions": [],
        }


report_service = ReportService()
