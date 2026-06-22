from app.services.session.session_service import session_service

try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None

router = APIRouter(prefix="/sessions", tags=["sessions"]) if APIRouter else None


if router:
    @router.get("")
    def list_sessions():
        return {"items": [session.to_dict() for session in session_service.list_sessions()]}

    @router.get("/{session_id}")
    def get_session(session_id: str):
        return session_service.get_session(session_id).to_dict()
