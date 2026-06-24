from dataclasses import dataclass
from datetime import datetime, timezone

try:
    from sqlalchemy import Column, Integer, String, Boolean, DateTime
    from sqlalchemy.orm import declarative_base
except ModuleNotFoundError:
    Column = Integer = String = Boolean = DateTime = None
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
