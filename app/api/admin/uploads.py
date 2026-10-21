import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.config import settings
from app.core.dependencies import require_admin
from app.schemas.common import ApiResponse
from app.services.exceptions import BadRequestError


router = APIRouter(
    prefix=f"{settings.api_prefix}/admin/uploads",
    tags=["Admin - Uploads"],
    dependencies=[Depends(require_admin)],
)

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
CHUNK_SIZE = 1024 * 1024


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[dict])
async def upload_image(
    file: UploadFile = File(...),
    folder: Literal["products", "categories", "collections", "banners"] = Form("products"),
):
    """Upload a jpg/png/webp (max 5 MB). Put the returned url into a product's
    image_urls (or a category / collection / banner image_url)."""
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if extension is None:
        raise BadRequestError("Only JPG, PNG or WEBP images are allowed")

    target_dir = settings.media_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4().hex}{extension}"
    target_path = target_dir / file_name

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    written = 0
    try:
        with target_path.open("wb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                written += len(chunk)
                if written > max_bytes:
                    raise BadRequestError(f"Image must be smaller than {settings.max_upload_size_mb} MB")
                output.write(chunk)
    except BadRequestError:
        target_path.unlink(missing_ok=True)
        raise

    return {
        "success": True,
        "message": "Image uploaded",
        "data": {"url": f"{settings.media_url}/{folder}/{file_name}"},
    }
