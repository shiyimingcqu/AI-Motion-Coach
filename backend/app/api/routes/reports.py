from app.services.report.report_service import report_service

try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None

router = APIRouter(prefix="/reports", tags=["reports"]) if APIRouter else None


if router:
    @router.get("/personal")
    def personal_report():
        return report_service.personal_summary()

    @router.get("/class")
    def class_report():
        return report_service.class_summary()
