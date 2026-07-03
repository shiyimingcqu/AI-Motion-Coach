from datetime import datetime, timezone

from app.api.deps import get_db, require_admin
from app.core.security import get_password_hash
from app.models.entities import UserORM, ActiveTemplateORM
from app.services.analysis.template_service import refresh_active_templates
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名长度需要在 3 到 32 位之间",
            )
        if len(password) < 6 or len(password) > 64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度需要在 6 到 64 位之间",
            )

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
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise
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
            if user.role == "admin" and request.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="管理员账号不能在用户管理中降级",
                )
            user.role = request.role

        if request.is_active is not None:
            if user.role == "admin" and not request.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="管理员账号不能在用户管理中禁用",
                )
            user.is_active = request.is_active
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="管理员账号不能在用户管理中删除",
            )

        db.delete(user)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return None

    @router.get(
        "/sessions",
        dependencies=[Depends(require_admin)],
    )
    def list_all_sessions(user_id: int | None = None, db: Session = Depends(get_db)):
        sessions = session_service.list_sessions(limit=200, user_id=user_id)
        result = []
        for s in sessions:
            username = "匿名用户"
            if s.user_id:
                u = db.query(UserORM).filter(UserORM.id == s.user_id).first()
                if u:
                    username = u.username
            row = s.to_dict() if hasattr(s, "to_dict") else {
                "session_id": s.session_id,
                "exercise": s.exercise,
                "duration_seconds": s.duration_seconds,
                "total_count": s.total_count,
                "valid_count": s.valid_count,
                "error_count": s.error_count,
                "average_score": s.average_score,
                "created_at": s.created_at.isoformat() + "Z" if s.created_at else None,
            }
            row["username"] = username
            result.append(row)
        return {"items": result}

    @router.get(
        "/dashboard",
        dependencies=[Depends(require_admin)],
    )
    def admin_dashboard(db: Session = Depends(get_db)):
        """Return aggregated admin dashboard statistics."""
        from datetime import datetime, timezone
        from app.models.entities import AnalysisTaskORM, ExerciseORM, ReferenceVideoORM, SessionORM

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        seven_days_ago = today_start.replace(day=today_start.day - 7) if today_start.day > 7 else today_start.replace(month=today_start.month - 1 or 12, day=1)

        # User stats
        total_users = db.query(UserORM).filter(UserORM.role == "user").count()
        admins = db.query(UserORM).filter(UserORM.role == "admin").count()
        new_users_week = db.query(UserORM).filter(
            UserORM.role == "user",
            UserORM.created_at >= seven_days_ago,
        ).count()

        # Session stats
        sessions = db.query(SessionORM).order_by(SessionORM.created_at.desc()).all()
        total_sessions = len(sessions)
        today_sessions = [s for s in sessions if s.created_at and s.created_at >= today_start]
        avg_score = round(sum(s.average_score for s in sessions) / total_sessions, 1) if total_sessions else 0
        total_duration_min = round(sum(s.duration_seconds for s in sessions) / 60)

        # Score trend vs last week
        prev_week_sessions = [s for s in sessions if s.created_at and s.created_at < seven_days_ago]
        prev_avg = round(sum(s.average_score for s in prev_week_sessions) / len(prev_week_sessions), 1) if prev_week_sessions else 0
        score_change = round(avg_score - prev_avg, 1)

        # Video analysis tasks
        video_total = db.query(AnalysisTaskORM).count()
        video_success = db.query(AnalysisTaskORM).filter(AnalysisTaskORM.status == "success").count()

        # Exercise count
        exercise_count = db.query(ExerciseORM).filter(ExerciseORM.is_active == True).count()

        # Recent sessions (with username)
        recent_sessions = []
        for s in sessions[:8]:
            username = "匿名用户"
            if s.user_id:
                u = db.query(UserORM).filter(UserORM.id == s.user_id).first()
                if u:
                    username = u.username
            recent_sessions.append({
                "session_id": s.session_id,
                "user": username,
                "exercise": s.exercise,
                "score": s.average_score,
                "error_count": s.error_count,
                "duration_seconds": s.duration_seconds,
                "created_at": s.created_at.isoformat() + "Z" if s.created_at else None,
            })

        # Error breakdown by exercise
        error_by_exercise: dict[str, int] = {}
        error_sessions_by_exercise: dict[str, int] = {}
        for s in sessions:
            label = s.exercise or "其他"
            if s.error_count > 0:
                error_by_exercise[label] = error_by_exercise.get(label, 0) + s.error_count
            error_sessions_by_exercise[label] = error_sessions_by_exercise.get(label, 0) + 1
        max_errors = max(error_by_exercise.values()) if error_by_exercise else 1
        total_errors = sum(error_by_exercise.values())
        error_stats = sorted(
            ({"name": k, "count": v, "rate": round(v / max(max_errors, 1) * 100),
              "sessions": error_sessions_by_exercise.get(k, 0)}
             for k, v in error_by_exercise.items()),
            key=lambda x: x["count"],
            reverse=True,
        )[:6]

        # Work queue items
        work_queue = []
        low_score_users = len([s for s in sessions if s.average_score < 70 and s.created_at and s.created_at >= seven_days_ago])
        if low_score_users:
            work_queue.append({
                "title": "查看低分训练",
                "desc": f"近 7 天有 {low_score_users} 条训练记录平均分低于 70。",
                "link": "/admin/sessions",
            })
        pending_templates = db.query(ReferenceVideoORM).filter(ReferenceVideoORM.is_active == False).count()
        if pending_templates:
            work_queue.append({
                "title": "审核停用模板",
                "desc": f"{pending_templates} 个标准视频模板处于停用状态。",
                "link": "/admin/templates",
            })
        if exercise_count < 4:
            work_queue.append({
                "title": "补充动作库",
                "desc": f"当前仅有 {exercise_count} 个动作，建议丰富动作类型。",
                "link": "/admin/rules",
            })
        if video_success > 0 and video_total > 0:
            work_queue.append({
                "title": "检查视频分析任务",
                "desc": f"共 {video_total} 个视频分析任务，{video_success} 个成功。",
                "link": "/admin/reports",
            })

        return {
            "user_count": total_users,
            "admin_count": admins,
            "new_users_week": new_users_week,
            "today_sessions": len(today_sessions),
            "total_sessions": total_sessions,
            "average_score": avg_score,
            "average_score_change": score_change,
            "total_duration_minutes": total_duration_min,
            "video_total": video_total,
            "video_success": video_success,
            "exercise_count": exercise_count,
            "recent_sessions": recent_sessions,
            "error_stats": error_stats,
            "total_errors": total_errors,
            "work_queue": work_queue,
        }

    @router.get(
        "/reports",
        dependencies=[Depends(require_admin)],
    )
    def list_all_reports(user_id: int | None = None, db: Session = Depends(get_db)):
        sessions = session_service.list_sessions(limit=200, user_id=user_id)
        items = []
        for session in sessions:
            username = "匿名用户"
            if session.user_id:
                u = db.query(UserORM).filter(UserORM.id == session.user_id).first()
                if u:
                    username = u.username
            items.append({
                "id": f"report-{session.session_id}",
                "session_id": session.session_id,
                "title": f"{session.exercise} 训练评估报告",
                "user": username,
                "created_at": session.created_at.isoformat() + "Z" if session.created_at else None,
                "average_score": session.average_score,
                "status": "需关注" if session.average_score < 70 or session.error_count > 5 else "已生成",
                "error_count": session.error_count,
            })
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

    # ── 模板启用/禁用 ─────────────────────────────────────────────

    @router.get("/templates/active", dependencies=[Depends(require_admin)])
    def list_active_templates(db: Session = Depends(get_db)):
        """获取所有已启用的模板配置"""
        records = db.query(ActiveTemplateORM).all()
        return {"items": [r.to_dict() for r in records]}

    @router.post("/templates/active", status_code=201, dependencies=[Depends(require_admin)])
    def set_active_template(
        body: dict,
        db: Session = Depends(get_db),
    ):
        """
        设置启用模板——每种动作只能启用一个模板。
        如果该动作已有启用的模板，自动替换。
        """
        action = body.get("action", "").strip()
        template_id = body.get("template_id", "").strip()
        if not action:
            raise HTTPException(status_code=400, detail="action 不能为空")
        if not template_id:
            raise HTTPException(status_code=400, detail="template_id 不能为空")

        existing = db.query(ActiveTemplateORM).filter(ActiveTemplateORM.action == action).first()
        if existing:
            existing.template_id = template_id
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            refresh_active_templates(db)
            return existing.to_dict()

        record = ActiveTemplateORM(
            action=action,
            template_id=template_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        refresh_active_templates(db)
        return record.to_dict()

    @router.delete("/templates/active/{action}", status_code=204, dependencies=[Depends(require_admin)])
    def remove_active_template(
        action: str,
        db: Session = Depends(get_db),
    ):
        """取消启用模板"""
        record = db.query(ActiveTemplateORM).filter(ActiveTemplateORM.action == action).first()
        if not record:
            raise HTTPException(status_code=404, detail="该动作尚未启用模板")
        db.delete(record)
        db.commit()
        refresh_active_templates(db)
        return None
