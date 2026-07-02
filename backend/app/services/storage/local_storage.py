from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    async def save_upload(self, upload_file):
        upload_dir = self.root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(upload_file.filename or "upload.bin").suffix
        target = upload_dir / f"{uuid4()}{suffix}"
        content = await upload_file.read()
        target.write_bytes(content)
        print(f"[upload] saved {len(content)} bytes to {target}")
        return str(target.resolve()).replace("\\", "/")


local_storage = LocalStorage(settings.storage_root)
