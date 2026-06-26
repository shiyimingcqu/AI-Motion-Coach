from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class SessionSummary:
    session_id: str
    exercise: str
    duration_seconds: int
    total_count: int
    valid_count: int
    error_count: int
    average_score: int
    created_at: str

    def to_dict(self):
        return asdict(self)


class SessionService:
    def __init__(self):
        self._sessions = [
            SessionSummary("demo-session-1", "squat", 180, 32, 28, 4, 88, datetime.now(timezone.utc).isoformat()),
        ]

    def list_sessions(self):
        return self._sessions

    def get_session(self, session_id: str):
        for session in self._sessions:
            if session.session_id == session_id:
                return session
        return SessionSummary(session_id, "unknown", 0, 0, 0, 0, 0, datetime.now(timezone.utc).isoformat())

    def create_session(
        self,
        exercise: str,
        duration_seconds: int,
        total_count: int,
        valid_count: int,
        error_count: int,
        average_score: int,
    ) -> SessionSummary:
        session = SessionSummary(
            session_id=str(uuid4()),
            exercise=exercise,
            duration_seconds=duration_seconds,
            total_count=total_count,
            valid_count=valid_count,
            error_count=error_count,
            average_score=average_score,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._sessions.append(session)
        return session


session_service = SessionService()
