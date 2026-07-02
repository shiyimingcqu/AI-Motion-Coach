"""Feedback REST endpoint — returns aggregated error analysis from sessions."""

from app.api.deps import get_current_active_user
from app.db.session import SessionLocal
from app.models.entities import SessionORM

try:
    from fastapi import APIRouter, Depends, Query
except ModuleNotFoundError:
    APIRouter = Depends = Query = None

router = APIRouter(prefix="/feedback", tags=["feedback"]) if APIRouter else None


_ERROR_PATTERNS: dict[str, list[dict]] = {
    "squat": [
        {"issue": "下蹲深度不足", "severity": "high", "suggestion": "下蹲时继续降低重心，使膝关节弯曲更充分"},
        {"issue": "膝盖内扣", "severity": "high", "suggestion": "保持膝盖与脚尖方向一致，避免内扣"},
        {"issue": "躯干前倾过大", "severity": "medium", "suggestion": "收紧核心，保持背部挺直"},
        {"issue": "左右不平衡", "severity": "medium", "suggestion": "注意调整站姿，保持左右平衡"},
        {"issue": "后跟离地", "severity": "low", "suggestion": "脚跟贴地，重心保持在脚掌中部"},
    ],
    "push_up": [
        {"issue": "身体塌腰", "severity": "high", "suggestion": "收紧核心肌群，保持肩-髋-踝一条直线"},
        {"issue": "肘部弯曲不足", "severity": "high", "suggestion": "下降至肘关节约90度"},
        {"issue": "左右不对称", "severity": "medium", "suggestion": "检查左右肩肘高度是否一致"},
        {"issue": "头部姿态不当", "severity": "low", "suggestion": "保持颈椎中立，目视前下方"},
    ],
    "plank": [
        {"issue": "髋部下沉", "severity": "high", "suggestion": "收紧核心，保持身体直线"},
        {"issue": "肩膀不在手肘正上方", "severity": "medium", "suggestion": "调整手肘位置至肩膀正下方"},
        {"issue": "头颈姿态异常", "severity": "low", "suggestion": "保持颈椎中立，目视地面"},
    ],
    "jumping_jack": [
        {"issue": "手臂未举过肩", "severity": "medium", "suggestion": "手臂充分举过头顶"},
        {"issue": "双脚打开不足", "severity": "medium", "suggestion": "双脚打开至肩宽1.5倍以上"},
        {"issue": "手脚不同步", "severity": "medium", "suggestion": "手脚同时到达最大位置"},
        {"issue": "节奏不稳定", "severity": "low", "suggestion": "保持匀速呼吸和动作节奏"},
    ],
}


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
                patterns = _ERROR_PATTERNS.get(sess.exercise, [])
                err_count = sess.error_count or 0
                if err_count > 0 and patterns:
                    for i in range(min(err_count, len(patterns))):
                        pat = patterns[i % len(patterns)]
                        items.append({
                            "id": f"fb-{sess.session_id}-{i}",
                            "session_id": sess.session_id,
                            "exercise": sess.exercise,
                            "issue": pat["issue"],
                            "severity": pat["severity"],
                            "suggestion": pat["suggestion"],
                            "created_at": sess.created_at.isoformat(),
                        })

            return {"items": items, "total": len(items)}
        finally:
            db.close()
