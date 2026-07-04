"""Report REST endpoints — evaluation reports with charts and calorie data."""

from app.api.deps import get_current_active_user, require_admin
from app.services.report.report_service import report_service
from app.services.session.session_service import session_service

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
    from fastapi.responses import HTMLResponse, PlainTextResponse, Response
except ModuleNotFoundError:
    APIRouter = Depends = HTTPException = Query = None
    HTMLResponse = PlainTextResponse = Response = None

router = APIRouter(prefix="/reports", tags=["reports"]) if APIRouter else None


if router:
    @router.get("")
    def list_reports(
        date_from: str = Query("", description="Start date (YYYY-MM-DD)"),
        date_to: str = Query("", description="End date (YYYY-MM-DD)"),
        exercise: str = Query("", description="Filter by exercise key"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        user_id = current_user.id if current_user else None
        include_all = bool(current_user and current_user.role == "admin")
        return report_service.list_reports(
            user_id=user_id,
            date_from=date_from or None,
            date_to=date_to or None,
            include_all_users=include_all,
            exercise=exercise or None,
        )

    @router.get("/personal")
    def personal_report(
        date_from: str = Query("", description="Start date (YYYY-MM-DD)"),
        date_to: str = Query("", description="End date (YYYY-MM-DD)"),
        exercise: str = Query("", description="Filter by exercise key"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        user_id = current_user.id if current_user else None
        include_all = bool(current_user and current_user.role == "admin")
        return report_service.personal_summary(
            user_id=user_id,
            date_from=date_from or None,
            date_to=date_to or None,
            include_all_users=include_all,
            exercise=exercise or None,
        )

    @router.get("/export")
    def export_report(
        format: str = Query("pdf", description="Export format: pdf or csv"),
        date_from: str = Query("", description="Start date (YYYY-MM-DD)"),
        date_to: str = Query("", description="End date (YYYY-MM-DD)"),
        exercise: str = Query("", description="Filter by exercise key"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        user_id = current_user.id if current_user else None
        username = current_user.username if current_user else "学员"
        include_all = bool(current_user and current_user.role == "admin")
        exercise_key = exercise or None

        if format == "csv":
            csv_content = report_service.export_csv(
                user_id=user_id,
                date_from=date_from or None,
                date_to=date_to or None,
                include_all_users=include_all,
                exercise=exercise_key,
            )
            return PlainTextResponse(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=training_report.csv"},
            )

        if format == "pdf":
            try:
                pdf_bytes = report_service.export_pdf(
                    user_id=user_id,
                    date_from=date_from or None,
                    date_to=date_to or None,
                    username=username,
                    include_all_users=include_all,
                    exercise=exercise_key,
                )
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"PDF 生成失败: {exc}") from exc

            date_str = date_from or "all"
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="fitness_report_{date_str}.pdf"',
                },
            )

        html = report_service.export_pdf_html(
            user_id=user_id,
            date_from=date_from or None,
            date_to=date_to or None,
            include_all_users=include_all,
            exercise=exercise_key,
        )
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": "inline; filename=training_report.html"},
        )

    @router.get("/class")
    def class_report(
        current_user=Depends(require_admin),
    ):
        return report_service.class_summary()

    @router.get("/{session_id}/export")
    def export_session_report(
        session_id: str,
        format: str = Query("pdf"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        session = session_service.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="报告不存在")
        if (
            current_user
            and current_user.role != "admin"
            and session.user_id is not None
            and session.user_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="无权访问该报告")

        username = current_user.username if current_user else "学员"
        if format == "pdf":
            from app.services.report.pdf_report_service import pdf_report_builder

            summary = report_service.personal_summary(user_id=session.user_id)
            pdf_bytes = pdf_report_builder.build(summary, [session], username=username)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="report_{session_id[:8]}.pdf"',
                },
            )
        raise HTTPException(status_code=400, detail="仅支持 pdf 格式")

    @router.get("/{session_id}")
    def get_report_detail(
        session_id: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        session = session_service.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="报告不存在")

        if (
            current_user
            and current_user.role != "admin"
            and session.user_id is not None
            and session.user_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="无权访问该报告")

        report = report_service.get_session_report(session)
        report["report_item"] = report_service._session_to_report_item(session)
        return report
