from app.api.routes import analysis, auth, exercises, files, health, realtime, reports, sessions, videos

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
    router.include_router(analysis.router)
    router.include_router(videos.router)
    router.include_router(files.router)
    router.include_router(sessions.router)
    router.include_router(reports.router)
    router.include_router(realtime.router)
    return router
