from dataclasses import dataclass
from datetime import datetime, timezone

try:
    from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
    from sqlalchemy.orm import declarative_base
except ModuleNotFoundError:
    Column = Integer = String = Boolean = DateTime = Float = None
    declarative_base = None


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


# SQLAlchemy ORM 模型
Base = None
if declarative_base is not None:
    Base = declarative_base()


class UserORM(Base if Base is not None else object):
    """用户数据库模型"""
    if Base is not None:
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, index=True)
        username = Column(String(64), unique=True, index=True, nullable=False)
        hashed_password = Column(String(255), nullable=False)
        role = Column(String(16), nullable=False, default="user")
        is_active = Column(Boolean, default=True, nullable=False)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ExerciseORM(Base if Base is not None else object):
    """可管理的动作库数据库模型"""
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
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "category": self.category,
            "level": self.level,
            "duration": self.duration,
            "description": self.description,
            "modes": [m.strip() for m in self.modes.split(",") if m.strip()],
            "errors": [e.strip() for e in self.errors.split(",") if e.strip()],
            "accent": self.accent,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnalysisTaskORM(Base if Base is not None else object):
    """分析任务数据库模型"""
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
        return {
            "task_id": self.task_id,
            "exercise": self.exercise,
            "source_uri": self.source_uri,
            "status": self.status,
            "output_uri": self.output_uri,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SessionORM(Base if Base is not None else object):
    """训练记录数据库模型"""
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
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "exercise": self.exercise,
            "duration_seconds": self.duration_seconds,
            "total_count": self.total_count,
            "valid_count": self.valid_count,
            "error_count": self.error_count,
            "average_score": self.average_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
