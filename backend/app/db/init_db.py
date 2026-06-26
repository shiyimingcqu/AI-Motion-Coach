from app.db.session import engine
from app.core.security import get_password_hash
from app.models.entities import Base, UserORM

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:
    Session = None


def init_db():
    """初始化数据库：创建表并添加默认账号"""
    if engine is None or Base is None or Session is None:
        return

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建默认账号
    db = Session(bind=engine)
    try:
        _create_default_users(db)
    finally:
        db.close()


def _create_default_users(db: Session):
    """如果用户表为空，创建默认管理员和普通用户"""
    existing_user = db.query(UserORM).first()
    if existing_user is not None:
        return

    default_users = [
        {
            "username": "admin",
            "password": "admin123",
            "role": "admin",
        },
        {
            "username": "user",
            "password": "user123",
            "role": "user",
        },
    ]

    for user_data in default_users:
        user = UserORM(
            username=user_data["username"],
            hashed_password=get_password_hash(user_data["password"]),
            role=user_data["role"],
        )
        db.add(user)

    db.commit()
