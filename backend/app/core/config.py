from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "运动姿态评估与纠错系统"
    app_version: str = "0.1.0"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://pose:pose@mysql:3306/pose_evaluation",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    storage_root: str = os.getenv("STORAGE_ROOT", "storage")
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])


settings = Settings()
