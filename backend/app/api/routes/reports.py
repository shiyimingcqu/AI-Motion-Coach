"""Report REST endpoints — returns aggregated session data."""

from app.api.deps import get_current_active_user, require_admin
from app.services.report.report_service import report_service

try:
    from fastapi import APIRouter, Depends, Query
    from fastapi.responses import HTMLResponse, PlainTextResponse
except ModuleNotFoundError:
    APIRouter = Depends = Query = None
    HTMLResponse = PlainTextResponse = None

router = APIRouter(prefix="/reports", tags=["reports"]) if APIRouter else None


if router:
    @router.get("")
    def list_reports(
        date_from: str = Query("", description="Start date (YYYY-MM-DD)"),
        date_to: str = Query("", description="End date (YYYY-MM-DD)"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        user_id = current_user.id if current_user else None
        summary = report_service.personal_summary(user_id=user_id, date_from=date_from or None, date_to=date_to or None)
        sessions = summary.get("recent_sessions", [])

        items = [
            {
                "id": "report-monthly",
                "title": "Monthly Performance Report",
                "subtitle": "本月训练表现报告",
                "type": "Monthly",
                "date": s.get("created_at", "")[:10],
                "exercises_count": 1,
                "sessions_count": len(sessions),
                "average_score": summary.get("average_score", 0),
                "size": "1.2 MB",
            }
            for s in (sessions[:1] or [{"created_at": ""}])
        ]

        return {"items": items}

    @router.get("/personal")
    def personal_report(
        date_from: str = Query("", description="Start date (YYYY-MM-DD)"),
        date_to: str = Query("", description="End date (YYYY-MM-DD)"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        user_id = current_user.id if current_user else None
        return report_service.personal_summary(user_id=user_id, date_from=date_from or None, date_to=date_to or None)

    @router.get("/export", response_class=HTMLResponse if HTMLResponse else None)
    def export_report(
        format: str = Query("pdf", description="Export format: pdf or csv"),
        date_from: str = Query("", description="Start date (YYYY-MM-DD)"),
        date_to: str = Query("", description="End date (YYYY-MM-DD)"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """Export training data as PDF (HTML for printing) or CSV."""
        user_id = current_user.id if current_user else None

        if format == "csv":
            csv_content = report_service.export_csv(user_id=user_id, date_from=date_from or None, date_to=date_to or None)
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=training_report.csv"},
            )

        # Default: PDF (HTML for browser print-to-PDF)
        html = report_service.export_pdf_html(user_id=user_id, date_from=date_from or None, date_to=date_to or None)
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": "inline; filename=training_report.html"},
        )

    @router.get("/class")
    def class_report(
        current_user=Depends(require_admin),
    ):
        return report_service.class_summary()
