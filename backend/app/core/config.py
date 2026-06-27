from dataclasses import dataclass, field
from datetime import timedelta
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "运动姿态评估与纠错系统"
    app_version: str = "0.1.0"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./pose_evaluation.db",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    storage_root: str = os.getenv("STORAGE_ROOT", "storage")
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])

    # JWT 配置
    secret_key: str = os.getenv("SECRET_KEY", "pose-evaluation-secret-key-dev-only")
    # WARNING: The default fallback key is insecure.
    # Set SECRET_KEY in your .env file (run: python3 -c "import secrets; print(secrets.token_urlsafe(48))")
    access_token_expire: timedelta = timedelta(days=int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7")))
    algorithm: str = "HS256"


settings = Settings()
