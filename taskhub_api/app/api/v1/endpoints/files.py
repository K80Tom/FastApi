import asyncio
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from app.core.dependencies import CurrentUser, DbDep, SettingsDep
from app.core.errors import AppError, NotFoundError, PayloadTooLargeError
from app.db.transaction import transaction
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentRead
from app.schemas.common import DataResponse
from app.services.permission_service import require_project_role
from app.services.task_service import get_existing_task

router = APIRouter(tags=["attachments"])
ALLOWED_TYPES = {"text/plain", "text/csv", "application/pdf", "image/png", "image/jpeg"}


def validate_signature(content_type: str, first_chunk: bytes) -> None:
    signatures = {
        "application/pdf": (b"%PDF",),
        "image/png": (b"\x89PNG\r\n\x1a\n",),
        "image/jpeg": (b"\xff\xd8\xff",),
    }
    expected = signatures.get(content_type)
    if expected and not first_chunk.startswith(expected):
        raise AppError("File content does not match its declared type")


@router.post("/tasks/{task_id}/attachments", response_model=DataResponse[AttachmentRead], status_code=201)
async def upload_attachment(
    task_id: int, upload: UploadFile, current_user: CurrentUser, db: DbDep, settings: SettingsDep
):
    task = await get_existing_task(db, task_id)
    await require_project_role(db, current_user, task.project_id, "member")
    if upload.content_type not in ALLOWED_TYPES:
        raise AppError("Unsupported file type", details={"allowed": sorted(ALLOWED_TYPES)})

    upload_dir = settings.upload_dir.resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "").suffix[:20]
    stored_name = f"{uuid4().hex}{suffix}"
    temporary_path = upload_dir / f".{stored_name}.part"
    final_path = upload_dir / stored_name
    total = 0
    try:
        async with aiofiles.open(temporary_path, "wb") as output:
            while chunk := await upload.read(1024 * 1024):
                if total == 0:
                    validate_signature(upload.content_type, chunk)
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    raise PayloadTooLargeError(
                        "Uploaded file is too large", details={"max_bytes": settings.max_upload_bytes}
                    )
                await output.write(chunk)
        await asyncio.to_thread(temporary_path.replace, final_path)
        async with transaction(db):
            attachment = Attachment(
                task_id=task_id,
                uploader_id=current_user.id,
                original_name=Path(upload.filename or "upload.bin").name[:255],
                stored_name=stored_name,
                content_type=upload.content_type,
                size=total,
            )
            db.add(attachment)
            await db.flush()
        return {"data": AttachmentRead.model_validate(attachment), "message": "attachment uploaded"}
    except Exception:
        await asyncio.to_thread(lambda: temporary_path.unlink(missing_ok=True))
        await asyncio.to_thread(lambda: final_path.unlink(missing_ok=True))
        raise
    finally:
        await upload.close()


@router.get("/attachments/{attachment_id}")
async def download_attachment(attachment_id: int, current_user: CurrentUser, db: DbDep, settings: SettingsDep):
    attachment = await db.get(Attachment, attachment_id)
    if attachment is None:
        raise NotFoundError("Attachment not found")
    task = await get_existing_task(db, attachment.task_id)
    await require_project_role(db, current_user, task.project_id, "viewer")
    upload_dir = settings.upload_dir.resolve()
    path = (upload_dir / attachment.stored_name).resolve()
    if path.parent != upload_dir or not path.is_file():
        raise NotFoundError("Attachment content not found")
    return FileResponse(path, media_type="application/octet-stream", filename=attachment.original_name)
