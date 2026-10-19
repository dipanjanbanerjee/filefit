"""Shrink images, PDFs and DOCX files so they fit under a byte limit."""
from __future__ import annotations

import io
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pymupdf
from PIL import Image

MIN_SIDE = 160  # never shrink an image below this many pixels on its longest side
QUALITY_STEPS = (92, 85, 78, 70, 62, 55, 48, 40, 32, 25)


@dataclass
class FitResult:
    data: bytes
    fits: bool
    note: str = ""


# ---------------------------------------------------------------- images

def prepare_for(img: Image.Image, pil_format: str) -> Image.Image:
    """Convert colour mode so the image can be saved in the given format."""
    if pil_format == "JPEG":
        if img.mode in ("RGBA", "LA", "P"):
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.getchannel("A"))
            return bg
        if img.mode not in ("RGB", "L"):
            return img.convert("RGB")
        return img
    if pil_format == "WEBP" and img.mode not in ("RGB", "RGBA"):
        return img.convert("RGBA" if "A" in img.getbands() or img.mode == "P" else "RGB")
    if pil_format == "PNG" and img.mode not in ("RGB", "RGBA", "L", "LA", "P", "1"):
        return img.convert("RGB")
    return img


def encode_image(img: Image.Image, pil_format: str, quality: int = 92, dpi=None) -> bytes:
    img = prepare_for(img, pil_format)
    buf = io.BytesIO()
    kwargs = {}
    if dpi:
        kwargs["dpi"] = dpi
    if pil_format == "JPEG":
        img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True, **kwargs)
    elif pil_format == "WEBP":
        img.save(buf, "WEBP", quality=quality, method=6)
    elif pil_format == "PNG":
        img.save(buf, "PNG", optimize=True, **kwargs)
    else:
        img.save(buf, pil_format, **kwargs)
    return buf.getvalue()


def scaled(img: Image.Image, factor: float) -> Image.Image:
    if factor >= 0.999:
        return img
    w, h = img.size
    nw, nh = max(1, round(w * factor)), max(1, round(h * factor))
    return img.resize((nw, nh), Image.LANCZOS)


def _best_quality_under(img: Image.Image, pil_format: str, target: int) -> bytes | None:
    """Binary-search the highest quality whose output is <= target."""
    lo, hi, best = 20, 95, None
    while lo <= hi:
        q = (lo + hi) // 2
        data = encode_image(img, pil_format, q)
        if len(data) <= target:
            best, lo = data, q + 1
        else:
            hi = q - 1
    return best


def fit_image(img: Image.Image, pil_format: str, target: int | None, quality: int = 92) -> FitResult:
    """Encode `img` so the result is at most `target` bytes (if given)."""
    first = encode_image(img, pil_format, quality)
    if target is None or len(first) <= target:
        return FitResult(first, True)

    work = img
    if pil_format == "PNG":
        # PNG is lossless: try fewer colours first, then smaller pixels.
        try:
            pal = prepare_for(img, "PNG").convert("RGBA").quantize(256, method=Image.Quantize.FASTOCTREE)
            data = encode_image(pal, "PNG")
            if len(data) <= target:
                return FitResult(data, True, "reduced to 256 colours")
            work, last = pal, data
        except Exception:
            last = first
        for _ in range(12):
            longest = max(work.size)
            if longest <= MIN_SIDE:
                break
            factor = max(math.sqrt(target / len(last)) * 0.95, MIN_SIDE / longest)
            factor = min(factor, 0.9)
            work = scaled(work.convert("RGBA"), factor).quantize(256, method=Image.Quantize.FASTOCTREE)
            last = encode_image(work, "PNG")
            if len(last) <= target:
                return FitResult(last, True, f"resized to {work.size[0]}x{work.size[1]}")
        return FitResult(last, False, "could not reach the size limit; try JPG for photos")

    # Lossy formats: lower quality first, then shrink dimensions.
    data = _best_quality_under(work, pil_format, target)
    if data is not None:
        return FitResult(data, True)
    last = encode_image(work, pil_format, 20)
    for _ in range(12):
        longest = max(work.size)
        if longest <= MIN_SIDE:
            break
        factor = max(math.sqrt(target / len(last)) * 0.92, MIN_SIDE / longest)
        factor = min(factor, 0.9)
        work = scaled(work, factor)
        data = _best_quality_under(work, pil_format, target)
        if data is not None:
            return FitResult(data, True, f"resized to {work.size[0]}x{work.size[1]}")
        last = encode_image(work, pil_format, 20)
    return FitResult(last, False, "could not reach the size limit")


# ---------------------------------------------------------------- PDFs

def _save_pdf(doc: pymupdf.Document) -> bytes:
    return doc.tobytes(garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, clean=True)


def rasterize_pdf(src: bytes, dpi: int, quality: int) -> bytes:
    """Rebuild a PDF from JPEG snapshots of each page (text stops being selectable)."""
    with pymupdf.open(stream=src, filetype="pdf") as doc, pymupdf.open() as out:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples) if pix.n < 4 else \
                Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
            jpg = encode_image(img, "JPEG", quality)
            new = out.new_page(width=page.rect.width, height=page.rect.height)
            new.insert_image(new.rect, stream=jpg)
        return _save_pdf(out)


def fit_pdf(src: bytes, target: int | None, log: Callable[[str], None] = lambda s: None) -> FitResult:
    with pymupdf.open(stream=src, filetype="pdf") as doc:
        data = _save_pdf(doc)
    if len(data) > len(src):
        data = src
    if target is None or len(data) <= target:
        return FitResult(data, True)

    # Step 1: recompress pictures inside the PDF, keep text as text.
    for dpi, q in ((150, 75), (120, 65), (96, 55), (72, 45), (60, 35)):
        try:
            with pymupdf.open(stream=src, filetype="pdf") as doc:
                doc.rewrite_images(dpi_threshold=dpi + 10, dpi_target=dpi, quality=q)
                cand = _save_pdf(doc)
        except Exception as exc:  # older PyMuPDF or odd images
            log(f"image recompression skipped: {exc}")
            break
        if len(cand) < len(data):
            data = cand
        if len(data) <= target:
            return FitResult(data, True, f"images recompressed ({dpi} dpi)")

    # Step 2: turn each page into a picture at lower and lower resolution.
    log("still too large, converting pages to compressed images")
    for dpi, q in ((150, 70), (130, 60), (110, 55), (96, 50), (80, 45), (72, 38), (60, 32), (50, 28)):
        cand = rasterize_pdf(src, dpi, q)
        if len(cand) < len(data):
            data = cand
        if len(data) <= target:
            return FitResult(data, True, f"pages flattened to images ({dpi} dpi), text no longer selectable")
    return FitResult(data, False, "could not reach the size limit")


# ---------------------------------------------------------------- DOCX

def _recompress_docx(src: bytes, quality: int, max_side: int) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(src)) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for item in zin.infolist():
            raw = zin.read(item.filename)
            name = item.filename.lower()
            if name.startswith("word/media/") and name.endswith((".jpg", ".jpeg", ".png")):
                try:
                    img = Image.open(io.BytesIO(raw))
                    img.load()
                    if max(img.size) > max_side:
                        img = scaled(img, max_side / max(img.size))
                    if name.endswith(".png"):
                        has_alpha = "A" in img.getbands() or img.mode == "P"
                        if has_alpha:
                            new = encode_image(img.convert("RGBA").quantize(256), "PNG")
                        else:
                            # keep the .png name so document links stay valid; content is still PNG
                            new = encode_image(img.convert("RGB").quantize(256), "PNG")
                    else:
                        new = encode_image(img, "JPEG", quality)
                    if len(new) < len(raw):
                        raw = new
                except Exception:
                    pass
            zout.writestr(item, raw, compress_type=zipfile.ZIP_DEFLATED)
    return out.getvalue()


def fit_docx(src: bytes, target: int | None) -> FitResult:
    if target is None or len(src) <= target:
        return FitResult(src, True)
    data = src
    for q, side in ((80, 2000), (70, 1600), (60, 1280), (50, 1024), (40, 800), (30, 640), (25, 480)):
        cand = _recompress_docx(src, q, side)
        if len(cand) < len(data):
            data = cand
        if len(data) <= target:
            return FitResult(data, True, "pictures inside the document were compressed")
    return FitResult(data, False, "could not reach the size limit (the text itself may be too large)")
