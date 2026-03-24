"""
File upload utility — safe image ingest.

Security layers
───────────────
1.  MIME type guard   — rejects obviously wrong content-type headers immediately.
2.  Size guard        — rejects files > MAX_SIZE_MB before any image work.
3.  Pillow verify()   — opens the raw bytes through PIL; rejects corrupt or
                        non-image data even when the MIME header was spoofed.
4.  Re-encode         — saves through Pillow without copying metadata, which
                        strips EXIF (GPS, camera model, etc.) automatically.
5.  Downsample        — caps each axis at MAX_DIMENSION px to bound disk use.

Usage
─────
    url = save_upload(file, "profiles")   # → "/uploads/profiles/<uuid>.jpg"
    url = save_upload(file, "restaurants")
    url = save_upload(file, "reviews")
"""

import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from ..config import settings

# ── Constants ────────────────────────────────────────────────────────────────
ALLOWED_MIME_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
})

MAX_SIZE_MB    = 5
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
MAX_DIMENSION  = 1920   # px — longer axis is capped here

# Per-entity photo limits
MAX_PHOTOS_PER_RESTAURANT = 10
MAX_PHOTOS_PER_REVIEW     = 5


# ── Main entry point ─────────────────────────────────────────────────────────

def save_upload(file: UploadFile, subfolder: str) -> str:
    """
    Validate, sanitise, and persist an uploaded image.

    Parameters
    ----------
    file      : The FastAPI UploadFile from the request.
    subfolder : Destination sub-directory under UPLOAD_DIR
                (``"profiles"``, ``"restaurants"``, or ``"reviews"``).

    Returns
    -------
    str
        Public URL path, e.g. ``"/uploads/restaurants/a1b2c3.jpg"``.

    Raises
    ------
    HTTPException 400
        On unsupported type, oversized file, empty file, or image that
        cannot be decoded by Pillow.
    """
    # ── 1. MIME type guard ───────────────────────────────────────────────────
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                "Please upload a JPEG, PNG, WEBP, or GIF image."
            ),
        )

    # ── 2. Read + size guard ─────────────────────────────────────────────────
    raw = file.file.read()

    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(raw) > MAX_SIZE_BYTES:
        mb = len(raw) / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File is {mb:.1f} MB — maximum allowed size is {MAX_SIZE_MB} MB.",
        )

    # ── 3-5. Pillow: verify → re-encode (strips EXIF) → downsample ──────────
    processed, extension = _process_image(raw)

    # ── Write to disk ────────────────────────────────────────────────────────
    filename = f"{uuid.uuid4().hex}{extension}"
    dest_dir  = Path(settings.UPLOAD_DIR) / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    with open(dest_dir / filename, "wb") as fh:
        fh.write(processed)

    return f"/uploads/{subfolder}/{filename}"


# ── Internal helpers ─────────────────────────────────────────────────────────

def _process_image(raw: bytes) -> tuple[bytes, str]:
    """
    Open raw bytes through Pillow, verify, strip metadata, downsample.

    Returns ``(processed_bytes, extension)`` where extension is ``.jpg``
    or ``.png``.
    """
    try:
        from PIL import Image, UnidentifiedImageError

        # verify() detects truncated / malformed files; re-open afterwards
        # because verify() exhausts the internal stream.
        try:
            Image.open(io.BytesIO(raw)).verify()
        except (UnidentifiedImageError, Exception) as exc:
            raise _bad_image(exc)

        img = Image.open(io.BytesIO(raw))

        # Animated GIFs — keep first frame only
        if getattr(img, "is_animated", False):
            img.seek(0)

        # Normalise mode
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")

        # Downsample if needed (thumbnail is in-place, preserves aspect ratio)
        if max(img.width, img.height) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

        # Choose output format: PNG for images with transparency, JPEG for rest
        if img.mode == "RGBA":
            fmt, ext = "PNG", ".png"
            save_kw: dict = {"optimize": True}
        else:
            img  = img.convert("RGB")   # ensure no alpha channel for JPEG
            fmt, ext = "JPEG", ".jpg"
            save_kw = {"quality": 88, "optimize": True, "progressive": True}

        out = io.BytesIO()
        img.save(out, format=fmt, **save_kw)
        return out.getvalue(), ext

    except HTTPException:
        raise
    except Exception as exc:
        raise _bad_image(exc)


def _bad_image(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=(
            "The file could not be read as a valid image. "
            "Please upload a JPEG, PNG, WEBP, or GIF file."
        ),
    )
