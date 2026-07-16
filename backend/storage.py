"""Cloudinary storage helper for image uploads."""
import os
import logging
import requests
import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)

MIME_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp",
}

UPLOAD_FOLDER = os.environ.get("CLOUDINARY_UPLOAD_FOLDER", "pelangi/blog")
_configured = False


def init_storage():
    global _configured
    if _configured:
        return
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
    api_key = os.environ.get("CLOUDINARY_API_KEY")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
    if not all([cloud_name, api_key, api_secret]):
        raise RuntimeError(
            "CLOUDINARY_CLOUD_NAME/CLOUDINARY_API_KEY/CLOUDINARY_API_SECRET not configured"
        )
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    _configured = True
    logger.info("Cloudinary storage initialized")


def _public_id(path: str) -> str:
    return f"{UPLOAD_FOLDER}/{path}".rsplit(".", 1)[0]


def put_object(path: str, data: bytes, content_type: str) -> dict:
    init_storage()
    result = cloudinary.uploader.upload(
        data,
        public_id=_public_id(path),
        resource_type="image",
        overwrite=True,
    )
    return {"path": path, "url": result.get("secure_url")}


def get_object(path: str):
    init_storage()
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "jpg"
    url = cloudinary.CloudinaryImage(_public_id(path)).build_url(format=ext, secure=True)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    content_type = MIME_TYPES.get(ext, resp.headers.get("Content-Type", "application/octet-stream"))
    return resp.content, content_type
