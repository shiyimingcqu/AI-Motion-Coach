from app.api.deps import get_current_active_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import SessionLocal
from app.models.entities import UserORM

try:
    from fastapi import APIRouter, Depends, Form, HTTPException, status
    from pydantic import BaseModel, Field, field_validator
    from sqlalchemy.orm import Session
except ModuleNotFoundError:
    APIRouter = Depends = Form = HTTPException = status = None
    BaseModel = Field = field_validator = None
    Session = None


router = APIRouter(prefix="/auth", tags=["auth"]) if APIRouter else None


def _get_db() -> Session:
    """获取数据库会话"""
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="数据库未初始化")
    return SessionLocal()


if router and BaseModel:
    class UserRegisterRequest(BaseModel):
        username: str = Field(..., min_length=3, max_length=32)
        password: str = Field(..., min_length=6, max_length=64)
        role: str = Field(default="user")

        @field_validator("role")
        @classmethod
        def validate_role(cls, v: str) -> str:
            if v not in ("user", "admin"):
                raise ValueError("role 必须是 user 或 admin")
            return v

    class UserResponse(BaseModel):
        id: int
        username: str
        role: str
        is_active: bool

        class Config:
            from_attributes = True

    class TokenResponse(BaseModel):
        access_token: str
        token_type: str
        user: UserResponse

    class ChangePasswordRequest(BaseModel):
        old_password: str
        new_password: str

    class WechatLoginRequest(BaseModel):
        code: str = Field(..., min_length=1)

    class UpdateProfileRequest(BaseModel):
        nickname: str | None = None
        avatar_mode: str | None = None
        avatar_image: str | None = None
        occupation: str | None = None
        height: str | None = None
        weight: str | None = None
        training_goal: str | None = None
        training_preferences: str | None = None  # JSON array string


if router:
    @router.post("/register", response_model=UserResponse if UserResponse else None, status_code=201)
    def register(request: UserRegisterRequest if UserRegisterRequest else None):
        """用户注册"""
        if Session is None or request is None:
            raise HTTPException(status_code=500, detail="依赖不可用")

        db = _get_db()
        try:
            # 检查用户名是否已存在
            existing_user = db.query(UserORM).filter(UserORM.username == request.username).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="用户名已存在")

            import json

            # 创建新用户，预设默认个人资料
            user = UserORM(
                username=request.username,
                hashed_password=get_password_hash(request.password),
                role=request.role,
                nickname=request.username,
                occupation="健身爱好者",
                height="0",
                weight="0",
                training_preferences=json.dumps(["增肌塑形"], ensure_ascii=False),
                avatar_mode="default",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return UserResponse(
                id=user.id,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
            )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.post("/login", response_model=TokenResponse if TokenResponse else None)
    def login(
        username: str = Form(...),
        password: str = Form(...),
    ):
        """用户登录，返回 JWT token"""
        if Session is None:
            raise HTTPException(status_code=500, detail="依赖不可用")

        db = _get_db()
        try:
            user = db.query(UserORM).filter(UserORM.username == username).first()
            if user is None or not verify_password(password, user.hashed_password or ""):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

            access_token = create_access_token(data={"sub": user.username, "role": user.role})

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse(
                    id=user.id,
                    username=user.username,
                    role=user.role,
                    is_active=user.is_active,
                ),
            )
        finally:
            db.close()

    @router.post("/wechat-login", response_model=TokenResponse if TokenResponse else None)
    def wechat_login(request: WechatLoginRequest if WechatLoginRequest else None):
        """微信小程序登录：code → openid → JWT"""
        import json
        import os
        import urllib.request
        import urllib.parse

        if Session is None or request is None:
            raise HTTPException(status_code=500, detail="依赖不可用")

        appid = os.getenv("WECHAT_APPID", "")
        secret = os.getenv("WECHAT_SECRET", "")

        if not appid or not secret:
            raise HTTPException(
                status_code=500,
                detail="微信小程序配置未设置（WECHAT_APPID / WECHAT_SECRET）",
            )

        try:
            wx_url = "https://api.weixin.qq.com/sns/jscode2session"
            wx_params = {
                "appid": appid,
                "secret": secret,
                "js_code": request.code,
                "grant_type": "authorization_code",
            }
            full_url = f"{wx_url}?{urllib.parse.urlencode(wx_params)}"
            with urllib.request.urlopen(full_url, timeout=10) as resp:
                wx_data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"微信服务调用失败: {str(exc)}")

        if "errcode" in wx_data and wx_data["errcode"] != 0:
            raise HTTPException(
                status_code=400,
                detail=f"微信登录失败: {wx_data.get('errmsg', '未知错误')}",
            )

        openid = wx_data.get("openid")
        if not openid:
            raise HTTPException(status_code=400, detail="获取 openid 失败")

        db = _get_db()
        try:
            user = db.query(UserORM).filter(UserORM.openid == openid).first()

            if user is None:
                username = f"wx_{openid[:16]}"
                counter = 0
                while db.query(UserORM).filter(UserORM.username == username).first():
                    counter += 1
                    username = f"wx_{openid[:12]}{counter}"

                user = UserORM(
                    username=username,
                    hashed_password=get_password_hash(openid),
                    openid=openid,
                    role="user",
                    nickname=username,
                    occupation="健身爱好者",
                    height="0",
                    weight="0",
                    training_preferences=json.dumps(["增肌塑形"], ensure_ascii=False),
                    avatar_mode="default",
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

            access_token = create_access_token(data={"sub": user.username, "role": user.role})

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse(
                    id=user.id,
                    username=user.username,
                    role=user.role,
                    is_active=user.is_active,
                ),
            )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.get("/me", response_model=UserResponse if UserResponse else None)
    def get_me(current_user: UserORM = Depends(get_current_active_user) if get_current_active_user else None):
        """获取当前登录用户信息"""
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            role=current_user.role,
            is_active=current_user.is_active,
        )

    @router.get("/profile")
    def get_profile(current_user: UserORM = Depends(get_current_active_user) if get_current_active_user else None):
        """获取当前用户完整个人资料"""
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
        return current_user.to_dict(include_profile=True)

    @router.put("/profile")
    def update_profile(
        request: UpdateProfileRequest,
        current_user: UserORM = Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """更新当前用户个人资料"""
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

        db = _get_db()
        try:
            user = db.query(UserORM).filter(UserORM.id == current_user.id).first()
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")

            # 仅更新请求中提供的字段
            for field in ("nickname", "avatar_mode", "avatar_image", "occupation",
                          "height", "weight", "training_goal", "training_preferences"):
                value = getattr(request, field, None)
                if value is not None:
                    setattr(user, field, value)

            db.commit()
            db.refresh(user)
            return user.to_dict(include_profile=True)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.post("/change-password")
    def change_password(
        request: ChangePasswordRequest,
        current_user: UserORM = Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """修改当前用户密码"""
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

        if not verify_password(request.old_password, current_user.hashed_password or ""):
            raise HTTPException(status_code=400, detail="当前密码错误")

        if len(request.new_password) < 6:
            raise HTTPException(status_code=400, detail="新密码至少6位")

        db = _get_db()
        try:
            user = db.query(UserORM).filter(UserORM.id == current_user.id).first()
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            user.hashed_password = get_password_hash(request.new_password)
            db.commit()
            return {"message": "密码修改成功"}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
