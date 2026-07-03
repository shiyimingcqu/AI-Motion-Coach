from typing import Generator

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.entities import UserORM

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import OAuth2PasswordBearer
    from sqlalchemy.orm import Session
except ModuleNotFoundError:
    Depends = HTTPException = status = None
    OAuth2PasswordBearer = None
    Session = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") if OAuth2PasswordBearer else None


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    if SessionLocal is None:
        raise RuntimeError("SQLAlchemy is not available")

    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme) if oauth2_scheme else None,
    db: Session = Depends(get_db) if get_db else None,
) -> UserORM:
    """通过 JWT token 获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(UserORM).filter(UserORM.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: UserORM = Depends(get_current_user) if get_current_user else None,
) -> UserORM:
    """获取当前活跃用户"""
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    return current_user


def require_admin(
    current_user: UserORM = Depends(get_current_active_user) if get_current_active_user else None,
) -> UserORM:
    """要求当前用户为管理员"""
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user
