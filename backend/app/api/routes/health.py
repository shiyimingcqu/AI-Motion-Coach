try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None

router = APIRouter(tags=["health"]) if APIRouter else None


if router:
    @router.get("/health")
    def health_check():
        return {"status": "ok", "service": "pose-evaluation-api"}
