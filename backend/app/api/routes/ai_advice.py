from app.api.deps import get_current_active_user
from app.services.ai.ai_advice_service import generate_ai_advice

try:
    from fastapi import APIRouter, Depends
except ModuleNotFoundError:
    APIRouter = Depends = None

router = APIRouter(prefix="/ai", tags=["ai"]) if APIRouter else None


if router:
    @router.post("/advice")
    async def ai_advice(
        request: dict,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        return generate_ai_advice(request)
