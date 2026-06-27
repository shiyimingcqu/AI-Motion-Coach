"""Admin endpoints — user management."""

from app.api.deps import get_current_active_user, require_admin
from app.db.session import SessionLocal
from app.models.entities import UserORM

try:
    from fastapi import APIRouter, Depends, HTTPException
except ModuleNotFoundError:
    APIRouter = Depends = HTTPException = None

router = APIRouter(prefix="/admin", tags=["admin"]) if APIRouter else None


if router:
    @router.get("/users")
    def list_users(
        current_user=Depends(require_admin) if require_admin else None,
    ):
        if SessionLocal is None:
            return {"items": []}
        db = SessionLocal()
        try:
            users = db.query(UserORM).order_by(UserORM.created_at.desc()).all()
            return {"items": [u.to_dict() for u in users]}
        finally:
            db.close()

    @router.put("/users/{user_id}")
    def update_user(
        user_id: int,
        data: dict,
        current_user=Depends(require_admin) if require_admin else None,
    ):
        if SessionLocal is None:
            raise HTTPException(status_code=500, detail="DB unavailable")
        db = SessionLocal()
        try:
            user = db.query(UserORM).filter(UserORM.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if "role" in data:
                user.role = data["role"]
            if "is_active" in data:
                user.is_active = data["is_active"]
            db.commit()
            db.refresh(user)
            return user.to_dict()
        finally:
            db.close()

    @router.delete("/users/{user_id}")
    def delete_user(
        user_id: int,
        current_user=Depends(require_admin) if require_admin else None,
    ):
        if SessionLocal is None:
            raise HTTPException(status_code=500, detail="DB unavailable")
        db = SessionLocal()
        try:
            user = db.query(UserORM).filter(UserORM.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            db.delete(user)
            db.commit()
            return {"message": "User deleted", "user_id": user_id}
        finally:
            db.close()
