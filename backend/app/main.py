from app.api.router import create_api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.services.analysis.template_service import refresh_active_templates

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ModuleNotFoundError:
    FastAPI = None
    CORSMiddleware = None


class DependencyMissingApp:
    """Import-safe placeholder used when FastAPI is not installed locally."""

    title = settings.app_name


def create_app():
    if FastAPI is None:
        return DependencyMissingApp()

    application = FastAPI(title=settings.app_name, version=settings.app_version)

    # 初始化数据库（创建表和默认账号）
    init_db()
    db = SessionLocal()
    try:
        refresh_active_templates(db)
    finally:
        db.close()

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(create_api_router(), prefix="/api")
    return application


app = create_app()
