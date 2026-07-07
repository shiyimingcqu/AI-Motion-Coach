"""Feedback REST endpoint — returns aggregated error analysis from sessions."""

from app.api.deps import get_current_active_user
from app.db.session import SessionLocal
from app.models.entities import SessionORM

try:
    from fastapi import APIRouter, Depends, Query
except ModuleNotFoundError:
    APIRouter = Depends = Query = None

router = APIRouter(prefix="/feedback", tags=["feedback"]) if APIRouter else None

_SEVERITY_TO_API = {
    "error": "high",
    "warning": "medium",
    "info": "info",
    "high": "high",
    "medium": "medium",
    "low": "low",
}


def _map_severity(raw: str) -> str:
    return _SEVERITY_TO_API.get(raw, "medium")


def _fallback_feedback_items(sess: SessionORM) -> list[dict]:
    """当 feedback_summary 无结构化 items 时的兜底逻辑。"""
    total = sess.total_count or 0
    valid = sess.valid_count or 0

    if total <= 0:
        return [{
            "id": f"fb-{sess.session_id}-none",
            "session_id": sess.session_id,
            "exercise": sess.exercise,
            "issue": "未检测到完成的动作",
            "severity": "medium",
            "suggestion": "请确保身体完整出现在画面中，并完成至少一次完整动作",
            "created_at": sess.created_at.isoformat(),
        }]

    if valid > 0:
        return [{
            "id": f"fb-{sess.session_id}-ok",
            "session_id": sess.session_id,
            "exercise": sess.exercise,
            "issue": "",
            "severity": "info",
            "suggestion": "动作完成良好，继续保持良好的动作质量！",
            "created_at": sess.created_at.isoformat(),
        }]

    return [{
        "id": f"fb-{sess.session_id}-invalid",
        "session_id": sess.session_id,
        "exercise": sess.exercise,
        "issue": "动作未达到有效标准",
        "severity": "medium",
        "suggestion": "关注动作深度、身体姿态与节奏，优先保证每次动作质量",
        "created_at": sess.created_at.isoformat(),
    }]


if router:

    @router.get("")
    def list_feedbacks(
        session_id: str = Query("", description="Filter by session_id"),
        limit: int = Query(50, ge=1, le=200),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """Return aggregated error feedbacks."""
        if SessionLocal is None:
            return {"items": [], "total": 0}

        db = SessionLocal()
        try:
            if session_id:
                sess = db.query(SessionORM).filter(SessionORM.session_id == session_id).first()
                if not sess:
                    return {"items": [], "total": 0}
                if (
                    current_user
                    and current_user.role != "admin"
                    and sess.user_id is not None
                    and sess.user_id != current_user.id
                ):
                    return {"items": [], "total": 0}
                sessions = [sess]
            else:
                query = db.query(SessionORM).order_by(SessionORM.created_at.desc())
                user_id = current_user.id if current_user else None

                if user_id and current_user.role != "admin":
                    from sqlalchemy import or_
                    query = query.filter(
                        or_(SessionORM.user_id == user_id, SessionORM.user_id.is_(None))
                    )

                sessions = query.limit(limit).all()
            items: list[dict] = []

            for sess in sessions:
                if not sess.feedback_summary:
                    items.extend(_fallback_feedback_items(sess))
                    continue

                try:
                    import json
                    fb_data = json.loads(sess.feedback_summary)
                except Exception:
                    items.extend(_fallback_feedback_items(sess))
                    continue

                structured_items = fb_data.get("items") or []
                if structured_items:
                    for index, entry in enumerate(structured_items):
                        items.append({
                            "id": f"fb-{sess.session_id}-{index}",
                            "session_id": sess.session_id,
                            "exercise": sess.exercise,
                            "issue": entry.get("issue", ""),
                            "severity": _map_severity(entry.get("severity", "warning")),
                            "suggestion": entry.get("suggestion", ""),
                            "created_at": sess.created_at.isoformat(),
                        })
                    continue

                issues = fb_data.get("issues", [])
                suggestions = fb_data.get("suggestions", [])

                if issues:
                    for index, issue in enumerate(issues):
                        suggestion = suggestions[index] if index < len(suggestions) else ""
                        items.append({
                            "id": f"fb-{sess.session_id}-{index}",
                            "session_id": sess.session_id,
                            "exercise": sess.exercise,
                            "issue": issue,
                            "severity": "high" if index == 0 else "medium" if index == 1 else "low",
                            "suggestion": suggestion,
                            "created_at": sess.created_at.isoformat(),
                        })
                else:
                    items.extend(_fallback_feedback_items(sess))

            return {"items": items, "total": len(items)}
        finally:
            db.close()
