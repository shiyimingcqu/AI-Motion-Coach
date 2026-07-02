from app.api.deps import get_db, require_admin
from app.core.security import get_password_hash
from app.models.entities import UserORM
from app.services.session.session_service import session_service

try:
    from fastapi import APIRouter, Depends, HTTPException, status
    from pydantic import BaseModel
    from sqlalchemy.orm import Session
except ModuleNotFoundError:
    APIRouter = Depends = HTTPException = status = None
    BaseModel = None
    Session = None

router = APIRouter(prefix="/admin", tags=["admin"]) if APIRouter else None


if router and BaseModel:
    class AdminUserResponse(BaseModel):
        id: int
        username: str
        role: str
        is_active: bool
        created_at: str | None = None

    class AdminUsersResponse(BaseModel):
        items: list[AdminUserResponse]

    class AdminUserUpdateRequest(BaseModel):
        is_active: bool | None = None
        role: str | None = None

    class AdminUserCreateRequest(BaseModel):
        username: str
        password: str

    def _to_admin_user_response(user: UserORM) -> AdminUserResponse:
        return AdminUserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )

    @router.get(
        "/users",
        response_model=AdminUsersResponse,
        dependencies=[Depends(require_admin)],
    )
    def list_users(db: Session = Depends(get_db)):
        users = (
            db.query(UserORM)
            .order_by(UserORM.id.asc())
            .all()
        )
        return AdminUsersResponse(
            items=[_to_admin_user_response(user) for user in users]
        )

    @router.post(
        "/users",
        response_model=AdminUserResponse,
        dependencies=[Depends(require_admin)],
        status_code=201,
    )
    def create_user(request: AdminUserCreateRequest, db: Session = Depends(get_db)):
        username = request.username.strip()
        password = request.password

        if len(username) < 3 or len(username) > 32:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名长度需要在 3 到 32 位之间")
        if len(password) < 6 or len(password) > 64:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度需要在 6 到 64 位之间")

        existing_user = db.query(UserORM).filter(UserORM.username == username).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

        user = UserORM(
            username=username,
            hashed_password=get_password_hash(password),
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return _to_admin_user_response(user)

    @router.get(
        "/admins",
        response_model=AdminUsersResponse,
        dependencies=[Depends(require_admin)],
    )
    def list_admins(db: Session = Depends(get_db)):
        admins = (
            db.query(UserORM)
            .filter(UserORM.role == "admin")
            .order_by(UserORM.id.asc())
            .all()
        )
        return AdminUsersResponse(
            items=[_to_admin_user_response(admin) for admin in admins]
        )

    @router.patch(
        "/users/{user_id}",
        response_model=AdminUserResponse,
    )
    def update_user_status(
        user_id: int,
        request: AdminUserUpdateRequest,
        db: Session = Depends(get_db),
        current_admin: UserORM = Depends(require_admin),
    ):
        user = db.query(UserORM).filter(UserORM.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        if request.role is not None:
            if request.role not in {"user", "admin"}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色只能是 user 或 admin")
            user.role = request.role

        if request.is_active is not None:
            user.is_active = request.is_active
        db.commit()
        db.refresh(user)
        return _to_admin_user_response(user)

    @router.put(
        "/users/{user_id}",
        response_model=AdminUserResponse,
    )
    def replace_user(
        user_id: int,
        request: AdminUserUpdateRequest,
        db: Session = Depends(get_db),
        current_admin: UserORM = Depends(require_admin),
    ):
        return update_user_status(user_id, request, db, current_admin)

    @router.delete(
        "/users/{user_id}",
        status_code=204,
    )
    def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_admin: UserORM = Depends(require_admin),
    ):
        user = db.query(UserORM).filter(UserORM.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        if user.role == "admin":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="管理员账号不能在用户管理中删除")

        db.delete(user)
        db.commit()
        return None

    @router.get(
        "/sessions",
        dependencies=[Depends(require_admin)],
    )
    def list_all_sessions():
        return {"items": [session.to_dict() for session in session_service.list_sessions()]}

    @router.get(
        "/reports",
        dependencies=[Depends(require_admin)],
    )
    def list_all_reports():
        sessions = session_service.list_sessions()
        items = [
            {
                "id": f"report-{session.session_id}",
                "session_id": session.session_id,
                "title": f"{session.exercise} 训练评估报告",
                "user": "系统记录",
                "created_at": session.created_at,
                "average_score": session.average_score,
                "status": "需关注" if session.average_score < 70 or session.error_count > 5 else "已生成",
                "error_count": session.error_count,
            }
            for session in sessions
        ]
        low_score_count = sum(1 for session in sessions if session.average_score < 70)
        high_error_count = sum(1 for session in sessions if session.error_count > 5)
        return {
            "items": items,
            "highlights": [
                f"{low_score_count} 份报告平均分低于 70。" if low_score_count else "暂无低分报告。",
                f"{high_error_count} 份报告错误次数偏高。" if high_error_count else "暂无高错误次数报告。",
                "报告数据来自当前后端训练记录，用户归属将在训练会话落库后进一步关联。",
            ],
        }
