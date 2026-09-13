import base64
import zlib
from binascii import Error as BinasciiError

from fastapi import HTTPException, status

MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB raw image limit
ALLOWED_AVATAR_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}


def compress_avatar(data: bytes) -> bytes:
    return zlib.compress(data, level=9)


def decompress_avatar(data: bytes) -> bytes:
    return zlib.decompress(data)


def decode_image_base64(data: str) -> bytes:
    try:
        raw = base64.b64decode(data, validate=True)
    except (ValueError, BinasciiError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 image data"
        )
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Image data is empty"
        )
    if len(raw) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image exceeds {MAX_AVATAR_BYTES // (1024 * 1024)}MB limit",
        )
    return raw