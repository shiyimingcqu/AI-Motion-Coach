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

    @router.post("", status_code=201)
    def create_session(
        exercise: str,
        duration_seconds: int,
        total_count: int,
        valid_count: int,
        error_count: int,
        average_score: int,
    ):
        session = session_service.create_session(
            exercise=exercise,
            duration_seconds=duration_seconds,
            total_count=total_count,
            valid_count=valid_count,
            error_count=error_count,
            average_score=average_score,
        )
        return session.to_dict()
