from pathlib import Path

from app.api.deps import get_current_active_user
from app.core.config import settings

try:
    from fastapi import APIRouter, Depends, HTTPException
    from fastapi.responses import FileResponse
except ModuleNotFoundError:
    APIRouter = Depends = None
    FileResponse = None
    HTTPException = Exception

router = APIRouter(prefix="/files", tags=["files"]) if APIRouter else None


def _resolve_storage_path(file_path: str) -> Path:
    storage_root = Path(settings.storage_root).resolve()
    target = Path(file_path)
    if not target.is_absolute():
        target = Path.cwd() / target
    target = target.resolve()

    if storage_root not in target.parents and target != storage_root:
        raise HTTPException(status_code=403, detail="file path is outside storage root")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return target


if router:
    @router.get("/{file_path:path}")
    def get_file(
        file_path: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        return FileResponse(_resolve_storage_path(file_path))
