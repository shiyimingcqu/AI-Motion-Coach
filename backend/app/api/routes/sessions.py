"""Training session REST endpoints — persisted to SQLite."""

from app.api.deps import get_current_active_user
from app.services.session.session_service import session_service
from app.models.entities import SessionORM

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
    from pydantic import BaseModel
except ModuleNotFoundError:
    APIRouter = Depends = HTTPException = Query = None
    BaseModel = None

router = APIRouter(prefix="/sessions", tags=["sessions"]) if APIRouter else None


if router and BaseModel:
    class CreateSessionRequest(BaseModel):
        exercise: str
        duration_seconds: int
        total_count: int
        valid_count: int
        error_count: int
        average_score: int
        pose_replay: list[dict] | None = None
        pose_replay_meta: dict | None = None
        issues: list[str] = []
        suggestions: list[str] = []


if router:
    @router.get("")
    def list_sessions(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        exercise: str = Query("", description="Filter by exercise type"),
        date_from: str = Query("", description="Start date YYYY-MM-DD"),
        date_to: str = Query("", description="End date YYYY-MM-DD"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        from app.db.session import SessionLocal
        from datetime import datetime

        if SessionLocal is None:
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

        db = SessionLocal()
        try:
            query = db.query(SessionORM).order_by(SessionORM.created_at.desc())
            user_id = current_user.id if current_user else None

            if user_id and current_user.role != "admin":
                query = query.filter(SessionORM.user_id == user_id)

            if exercise:
                query = query.filter(SessionORM.exercise == exercise)
            if date_from:
                query = query.filter(SessionORM.created_at >= datetime.fromisoformat(date_from))
            if date_to:
                query = query.filter(SessionORM.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))

            total = query.count()
            sessions = query.offset(offset).limit(limit).all()
            return {
                "items": [s.to_dict() for s in sessions],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        finally:
            db.close()

    @router.get("/{session_id}")
    def get_session(
        session_id: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        session = session_service.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if current_user and current_user.role != "admin" and session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return session.to_dict()

    @router.get("/{session_id}/replay")
    def get_session_replay(
        session_id: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        session = session_service.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if current_user and current_user.role != "admin" and session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        replay = session_service.get_session_replay(session_id)
        if replay is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return replay

    @router.post("", status_code=201)
    def create_session(
        body: CreateSessionRequest,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        user_id = current_user.id if current_user else None
        session = session_service.create_session(
            exercise=body.exercise,
            duration_seconds=body.duration_seconds,
            total_count=body.total_count,
            valid_count=body.valid_count,
            error_count=body.error_count,
            average_score=body.average_score,
            user_id=user_id,
            pose_replay_frames=body.pose_replay,
            pose_replay_meta=body.pose_replay_meta,
        )

        if body.issues or body.suggestions:
            from app.db.session import SessionLocal
            from app.services.session.feedback_persistence import (
                build_feedback_data,
                save_session_feedback_summary,
            )

            formatted = {
                "errors": body.issues or [],
                "feedbacks": body.suggestions or [],
                "metrics": {},
                "score": body.average_score,
                "level": "unknown",
            }
            unified = {"items": []}
            feedback_data = build_feedback_data(unified, formatted)
            save_session_feedback_summary(
                session.session_id,
                feedback_data,
                generate_ai_async=True,
                exercise=body.exercise,
            )
            db = SessionLocal()
            try:
                sess = db.query(SessionORM).filter(
                    SessionORM.session_id == session.session_id
                ).first()
                if sess:
                    db.refresh(sess)
                    session = sess
            finally:
                db.close()

        return session.to_dict()

    @router.delete("/{session_id}")
    def delete_session(
        session_id: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        session = session_service.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if current_user and current_user.role != "admin" and session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        deleted = session_service.delete_session(session_id)
        return {"message": "Session deleted", "session_id": session_id}

    @router.put("/{session_id}/replay")
    def update_session_replay(
        session_id: str,
        body: dict,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        session = session_service.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if current_user and current_user.role != "admin" and session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        pose_replay = body.get("pose_replay")
        pose_replay_meta = body.get("pose_replay_meta")

        if not pose_replay or not isinstance(pose_replay, list) or len(pose_replay) == 0:
            raise HTTPException(status_code=400, detail="pose_replay must be a non-empty array")

        updated = session_service.update_session_replay(
            session_id=session_id,
            pose_replay_frames=pose_replay,
            pose_replay_meta=pose_replay_meta,
        )
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update replay data")
        return {"message": "Replay data saved", "session_id": session_id, "frame_count": len(pose_replay)}
