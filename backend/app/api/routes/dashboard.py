"""Dashboard stats endpoint — aggregates session data from the database."""

from app.api.deps import get_current_active_user
from app.db.session import SessionLocal
from app.models.entities import SessionORM

try:
    from fastapi import APIRouter, Depends
except ModuleNotFoundError:
    APIRouter = Depends = None

router = APIRouter(prefix="/dashboard", tags=["dashboard"]) if APIRouter else None


if router:
    @router.get("/stats")
    def dashboard_stats(
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """Return aggregated dashboard statistics from the sessions table."""
        if SessionLocal is None:
            return _empty_stats()

        db = SessionLocal()
        try:
            query = db.query(SessionORM).order_by(SessionORM.created_at.desc())
            user_id = current_user.id if current_user else None

            # Non-admin users only see their own sessions
            if user_id and current_user.role != "admin":
                query = query.filter(SessionORM.user_id == user_id)

            sessions = query.all()
            total = len(sessions)
            if total == 0:
                return _empty_stats()

            # overall averages
            avg_score = sum(s.average_score for s in sessions) / total
            total_duration = sum(s.duration_seconds for s in sessions)

            # today's sessions
            from datetime import date
            today = date.today()
            today_sessions = [
                s for s in sessions
                if s.created_at and s.created_at.date() == today
            ]

            # trend (last 7 days)
            trend_map: dict[str, list[float]] = {}
            for s in sessions:
                day = s.created_at.strftime("%Y-%m-%d")
                trend_map.setdefault(day, []).append(s.average_score)
            trend = sorted(
                ({"date": day, "score": round(sum(v) / len(v), 1)}
                 for day, v in trend_map.items()),
                key=lambda x: x["date"],
            )[-7:]

            # score change vs previous session
            score_change = 0.0
            if len(sessions) >= 2:
                score_change = sessions[0].average_score - sessions[1].average_score

            return {
                "today_sessions": len(today_sessions),
                "total_sessions": total,
                "average_score": round(avg_score, 1),
                "average_score_change": round(score_change, 1),
                "total_duration_minutes": round(total_duration / 60),
                "recent_trend": trend,
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


def _empty_stats():
    return {
        "today_sessions": 0,
        "total_sessions": 0,
        "average_score": 0,
        "average_score_change": 0,
        "total_duration_minutes": 0,
        "recent_trend": [],
        "recent_sessions": [],
    }
