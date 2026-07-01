"""Feedback REST endpoint — returns aggregated error analysis from sessions."""

from app.api.deps import get_current_active_user
from app.db.session import SessionLocal
from app.models.entities import SessionORM

try:
    from fastapi import APIRouter, Depends, Query
except ModuleNotFoundError:
    APIRouter = Depends = Query = None

router = APIRouter(prefix="/feedback", tags=["feedback"]) if APIRouter else None


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
            query = db.query(SessionORM).order_by(SessionORM.created_at.desc())
            user_id = current_user.id if current_user else None

            # Non-admin users only see their own feedback
            if user_id and current_user.role != "admin":
                query = query.filter(SessionORM.user_id == user_id)

            if session_id:
                query = query.filter(SessionORM.session_id == session_id)

            sessions = query.limit(limit).all()
            items: list[dict] = []

            for sess in sessions:
                # 优先使用 session 中保存的真实反馈摘要
                if sess.feedback_summary:
                    try:
                        import json
                        fb_data = json.loads(sess.feedback_summary)
                        issues = fb_data.get("issues", [])
                        suggestions = fb_data.get("suggestions", [])

                        # 如果没有问题，显示正面反馈
                        if not issues:
                            items.append({
                                "id": f"fb-{sess.session_id}-ok",
                                "session_id": sess.session_id,
                                "exercise": sess.exercise,
                                "issue": "动作完成良好",
                                "severity": "low",
                                "suggestion": suggestions[0] if suggestions else "继续保持良好的动作质量！",
                                "created_at": sess.created_at.isoformat(),
                            })
                        else:
                            # 显示真实的问题和建议
                            for i, (issue, suggestion) in enumerate(zip(issues, suggestions)):
                                severity = "high" if i == 0 else "medium" if i == 1 else "low"
                                items.append({
                                    "id": f"fb-{sess.session_id}-{i}",
                                    "session_id": sess.session_id,
                                    "exercise": sess.exercise,
                                    "issue": issue,
                                    "severity": severity,
                                    "suggestion": suggestion,
                                    "created_at": sess.created_at.isoformat(),
                                })
                        continue
                    except Exception:
                        pass  # 解析失败时跳过，不再使用预设假数据

            return {"items": items, "total": len(items)}
        finally:
            db.close()
