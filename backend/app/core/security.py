from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from jose import JWTError, jwt
except ModuleNotFoundError:
    jwt = JWTError = None

try:
    import bcrypt as _bcrypt
except ModuleNotFoundError:
    _bcrypt = None

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希密码是否匹配"""
    if _bcrypt is None:
        return plain_password == hashed_password
    try:
        return _bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    if _bcrypt is None:
        return password
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """生成 JWT access token"""
    if jwt is None:
        raise RuntimeError("python-jose is not installed")

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or settings.access_token_expire)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """解码 JWT token，失败返回 None"""
    if jwt is None:
        return None

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
