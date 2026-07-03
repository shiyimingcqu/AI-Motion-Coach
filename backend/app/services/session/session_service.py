"""Training session service — persisted to SQLite via SQLAlchemy ORM."""

from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.entities import SessionORM


class SessionService:
    def list_sessions(self, limit: int = 50, offset: int = 0, user_id: int | None = None) -> list[SessionORM]:
        if SessionLocal is None:
            return []
        db = SessionLocal()
        try:
            query = db.query(SessionORM)
            if user_id is not None:
                query = query.filter(SessionORM.user_id == user_id)
            sessions = (
                query
                .order_by(SessionORM.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return sessions
        finally:
            db.close()

    def get_session(self, session_id: str) -> SessionORM | None:
        if SessionLocal is None:
            return None
        db = SessionLocal()
        try:
            return db.query(SessionORM).filter(
                SessionORM.session_id == session_id
            ).first()
        finally:
            db.close()

    def create_session(
        self,
        exercise: str,
        duration_seconds: int,
        total_count: int,
        valid_count: int,
        error_count: int,
        average_score: int,
        user_id: int | None = None,
    ) -> SessionORM:
        if SessionLocal is None:
            raise RuntimeError("Database not available")

        db = SessionLocal()
        try:
            session = SessionORM(
                session_id=str(uuid4()),
                user_id=user_id,
                exercise=exercise,
                duration_seconds=duration_seconds,
                total_count=total_count,
                valid_count=valid_count,
                error_count=error_count,
                average_score=average_score,
                created_at=datetime.now(timezone.utc),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by session_id. Returns True if deleted, False if not found."""
        if SessionLocal is None:
            return False

        db = SessionLocal()
        try:
            session = db.query(SessionORM).filter(
                SessionORM.session_id == session_id
            ).first()
            if session is None:
                return False
            db.delete(session)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


session_service = SessionService()
