"""File type definitions shared by the engine and the GUI."""
from __future__ import annotations

from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic", ".heif"}
PDF_EXTS = {".pdf"}
DOCX_EXTS = {".docx"}

INPUT_EXTS = IMAGE_EXTS | PDF_EXTS | DOCX_EXTS

# Output choices shown to the user: label -> (file extension, Pillow format or kind)
OUTPUT_FORMATS = {
    "JPG": (".jpg", "JPEG"),
    "JPEG": (".jpeg", "JPEG"),
    "PNG": (".png", "PNG"),
    "WEBP": (".webp", "WEBP"),
    "PDF": (".pdf", "PDF"),
    "DOCX": (".docx", "DOCX"),
}

IMAGE_OUTPUTS = {"JPG", "JPEG", "PNG", "WEBP"}


def kind_of(path: str | Path) -> str:
    """Return 'image', 'pdf', 'docx' or raise ValueError."""
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in PDF_EXTS:
        return "pdf"
    if ext in DOCX_EXTS:
        return "docx"
    raise ValueError(f"Unsupported file type: {ext or '(no extension)'}")


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"
