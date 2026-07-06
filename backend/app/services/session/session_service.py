"""Training session service — persisted to SQLite via SQLAlchemy ORM."""

from datetime import datetime, timezone
import json
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.entities import SessionORM, _isoformat_utc
from app.services.evaluation.calorie_service import calculate_calories
from app.services.report.error_frame_service import ensure_meta_error_snapshots


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
        average_score: int | float,
        user_id: int | None = None,
        pose_replay_frames: list[dict] | None = None,
        pose_replay_meta: dict | None = None,
    ) -> SessionORM:
        if SessionLocal is None:
            raise RuntimeError("Database not available")

        calories = calculate_calories(
            exercise=exercise,
            duration_seconds=duration_seconds,
            total_count=total_count,
        )
        evaluation = build_evaluation(
            exercise=exercise,
            average_score=float(average_score),
            total_count=total_count,
            valid_count=valid_count,
            error_count=error_count,
            duration_seconds=duration_seconds,
        )

        replay_meta = ensure_meta_error_snapshots(
            pose_replay_meta,
            pose_replay_frames,
            float(average_score),
        ) if (pose_replay_meta or pose_replay_frames) else pose_replay_meta

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
                average_score=float(average_score),
                pose_replay_json=self._dump_replay_frames(pose_replay_frames),
                pose_replay_meta_json=self._dump_replay_meta(
                    replay_meta,
                    pose_replay_frames,
                ),
                calories_burned=calories,
                evaluation_json=serialize_evaluation(evaluation),
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

    def update_session_replay(
        self,
        session_id: str,
        pose_replay_frames: list[dict],
        pose_replay_meta: dict | None = None,
    ) -> bool:
        """Update an existing session's replay data independently."""
        if SessionLocal is None:
            return False

        db = SessionLocal()
        try:
            session = db.query(SessionORM).filter(
                SessionORM.session_id == session_id
            ).first()
            if session is None:
                return False

            normalized = []
            for index, frame in enumerate(pose_replay_frames[:60000]):
                landmarks = frame.get("landmarks")
                if not isinstance(landmarks, list) or len(landmarks) < 33:
                    continue
                normalized.append({
                    "timestamp_ms": int(frame.get("timestamp_ms", index * 100)),
                    "landmarks": landmarks[:33],
                })

            if not normalized:
                return False

            session.pose_replay_json = json.dumps(
                normalized, ensure_ascii=False, separators=(",", ":")
            )

            meta_payload = {
                "schema_version": 1,
                "source": "miniprogram_realtime",
                "sample_interval_ms": 100,
                "frame_count": len(normalized),
            }
            if pose_replay_meta:
                meta_payload.update(pose_replay_meta)
            meta_payload = ensure_meta_error_snapshots(
                meta_payload,
                normalized,
                float(session.average_score),
            )
            session.pose_replay_meta_json = json.dumps(
                meta_payload, ensure_ascii=False, separators=(",", ":")
            )

            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_session_replay(self, session_id: str) -> dict | None:
        session = self.get_session(session_id)
        if session is None:
            return None

        frames = self._load_json(session.pose_replay_json, [])
        meta = self._load_json(session.pose_replay_meta_json, {})
        has_replay = isinstance(frames, list) and len(frames) > 0
        return {
            "session_id": session.session_id,
            "exercise": session.exercise,
            "created_at": _isoformat_utc(session.created_at),
            "has_replay": has_replay,
            "meta": meta if has_replay else None,
            "frames": frames if has_replay else [],
        }

    def _dump_replay_frames(self, frames: list[dict] | None) -> str | None:
        if not frames:
            return None

        normalized = []
        for index, frame in enumerate(frames[:60000]):
            landmarks = frame.get("landmarks")
            if not isinstance(landmarks, list) or len(landmarks) < 33:
                continue
            normalized.append({
                "timestamp_ms": int(frame.get("timestamp_ms", index * 100)),
                "landmarks": landmarks[:33],
            })

        if not normalized:
            return None

        return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))

    def _dump_replay_meta(
        self,
        meta: dict | None,
        frames: list[dict] | None,
    ) -> str | None:
        has_snapshots = bool(
            meta
            and (
                meta.get("error_snapshots")
                or meta.get("highlight_snapshots")
            )
        )
        if not frames and not has_snapshots:
            return None

        frame_list = frames or []
        payload = {
            "schema_version": 1,
            "source": "web_realtime",
            "sample_interval_ms": 100,
            "frame_count": len(frame_list),
        }
        if meta:
            payload.update(meta)

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    def _load_json(self, raw: str | None, fallback):
        if not raw:
            return fallback
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return fallback


session_service = SessionService()
