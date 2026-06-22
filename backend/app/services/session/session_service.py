from dataclasses import asdict, dataclass


@dataclass
class SessionSummary:
    session_id: str
    exercise: str
    duration_seconds: int
    total_count: int
    valid_count: int
    error_count: int
    average_score: int

    def to_dict(self):
        return asdict(self)


class SessionService:
    def __init__(self):
        self._sessions = [
            SessionSummary("demo-session-1", "squat", 180, 32, 28, 4, 88),
        ]

    def list_sessions(self):
        return self._sessions

    def get_session(self, session_id: str):
        for session in self._sessions:
            if session.session_id == session_id:
                return session
        return SessionSummary(session_id, "unknown", 0, 0, 0, 0, 0)


session_service = SessionService()
