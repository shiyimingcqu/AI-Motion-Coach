from app.api.routes import admin, ai_advice, analysis, auth, dashboard, exercises, feedback, files, health, realtime, reference_videos, reports, sessions, tts, videos

try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None


def create_api_router():
    if APIRouter is None:
        return None

    router = APIRouter()
    router.include_router(auth.router)
    router.include_router(health.router)
    router.include_router(exercises.router)
    router.include_router(feedback.router)
    router.include_router(admin.router)
    router.include_router(analysis.router)
    router.include_router(videos.router)
    router.include_router(files.router)
    router.include_router(sessions.router)
    router.include_router(dashboard.router)
    router.include_router(reports.router)
    router.include_router(realtime.router)
    router.include_router(reference_videos.router)
    router.include_router(ai_advice.router)
    router.include_router(tts.router)
    return router
