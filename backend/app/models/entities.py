from dataclasses import dataclass
from datetime import datetime, timezone
import json

try:
    from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.dialects.mysql import MEDIUMTEXT as MySQLMediumText
except ModuleNotFoundError:
    Column = Integer = String = Boolean = DateTime = Float = None
    declarative_base = None
    MySQLMediumText = None


@dataclass
class User:
    id: str
    username: str
    role: str


@dataclass
class TrainingSession:
    id: str
    user_id: str
    exercise: str
    duration_seconds: int
    total_count: int
    valid_count: int
    error_count: int
    average_score: float


Base = None
if declarative_base is not None:
    Base = declarative_base()


def _isoformat_utc(value):
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


class UserORM(Base if Base is not None else object):
    if Base is not None:
        __tablename__ = "users"
        id = Column(Integer, primary_key=True, index=True)
        username = Column(String(64), unique=True, index=True, nullable=False)
        hashed_password = Column(String(255), nullable=True)
        openid = Column(String(64), unique=True, nullable=True, index=True)
        role = Column(String(16), nullable=False, default="user")
        is_active = Column(Boolean, default=True, nullable=False)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "role": self.role, "is_active": self.is_active, "created_at": _isoformat_utc(self.created_at)}


class ExerciseORM(Base if Base is not None else object):
    if Base is not None:
        __tablename__ = "exercises"
        id = Column(Integer, primary_key=True, index=True)
        key = Column(String(32), unique=True, index=True, nullable=False)
        name = Column(String(64), nullable=False)
        category = Column(String(32), nullable=False, default="下肢")
        level = Column(String(16), nullable=False, default="中级")
        duration = Column(String(16), nullable=False, default="10 分钟")
        description = Column(Text, nullable=False, default="")
        modes = Column(String(128), nullable=False, default="摄像头实时检测,视频上传分析")
        errors = Column(String(256), nullable=False, default="")
        accent = Column(String(16), nullable=False, default="#3b82f6")
        is_active = Column(Boolean, default=True, nullable=False)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
        updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {"id": self.id, "key": self.key, "name": self.name, "category": self.category, "level": self.level, "duration": self.duration, "description": self.description, "modes": [m.strip() for m in self.modes.split(",") if m.strip()], "errors": [e.strip() for e in self.errors.split(",") if e.strip()], "accent": self.accent, "is_active": self.is_active, "created_at": _isoformat_utc(self.created_at), "updated_at": _isoformat_utc(self.updated_at)}


class AnalysisTaskORM(Base if Base is not None else object):
    if Base is not None:
        __tablename__ = "analysis_tasks"
        id = Column(Integer, primary_key=True, index=True)
        task_id = Column(String(64), unique=True, index=True, nullable=False)
        exercise = Column(String(32), nullable=False, default="squat")
        source_uri = Column(String(512), nullable=False, default="")
        status = Column(String(32), nullable=False, default="pending")
        output_uri = Column(String(512), nullable=True)
        error_message = Column(Text, nullable=True)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
        updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {"task_id": self.task_id, "exercise": self.exercise, "source_uri": self.source_uri, "status": self.status, "output_uri": self.output_uri, "error_message": self.error_message, "created_at": _isoformat_utc(self.created_at)}


class ActiveTemplateORM(Base if Base is not None else object):
    if Base is not None:
        __tablename__ = "active_templates"
        id = Column(Integer, primary_key=True, index=True)
        action = Column(String(32), unique=True, index=True, nullable=False)
        template_id = Column(String(128), nullable=False)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
        updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {"id": self.id, "action": self.action, "template_id": self.template_id, "created_at": _isoformat_utc(self.created_at), "updated_at": _isoformat_utc(self.updated_at)}


class SessionORM(Base if Base is not None else object):
    if Base is not None:
        __tablename__ = "sessions"
        id = Column(Integer, primary_key=True, index=True)
        session_id = Column(String(64), unique=True, index=True, nullable=False)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
        exercise = Column(String(32), nullable=False, default="squat")
        duration_seconds = Column(Integer, default=0, nullable=False)
        total_count = Column(Integer, default=0, nullable=False)
        valid_count = Column(Integer, default=0, nullable=False)
        error_count = Column(Integer, default=0, nullable=False)
        average_score = Column(Float, default=0.0, nullable=False)
        pose_replay_json = Column(MySQLMediumText if MySQLMediumText else Text, nullable=True)
        pose_replay_meta_json = Column(MySQLMediumText if MySQLMediumText else Text, nullable=True)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        try:
            raw = self.pose_replay_json or ""
            if raw.strip() and raw.strip() != "null":
                parsed = json.loads(raw)
                has_pose_replay = isinstance(parsed, list) and len(parsed) > 0
            else:
                has_pose_replay = False
        except (json.JSONDecodeError, TypeError):
            has_pose_replay = bool(self.pose_replay_json)
        return {"session_id": self.session_id, "user_id": self.user_id, "exercise": self.exercise, "duration_seconds": self.duration_seconds, "total_count": self.total_count, "valid_count": self.valid_count, "error_count": self.error_count, "average_score": self.average_score, "has_pose_replay": has_pose_replay, "created_at": _isoformat_utc(self.created_at)}
