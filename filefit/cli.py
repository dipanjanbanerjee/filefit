"""Command line interface:  filefit-cli photo.jpg --to pdf --max-size 2MB"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import __author__, __email__, __version__
from .core import OUTPUT_FORMATS, Options, combine_to_pdf, convert_file, human_size


def parse_size(text: str) -> int:
    m = re.fullmatch(r"\s*([\d.]+)\s*(b|kb|k|mb|m)?\s*", text.lower())
    if not m:
        raise argparse.ArgumentTypeError(f"cannot read size '{text}', use e.g. 500KB or 2MB")
    mult = {"b": 1, "kb": 1024, "k": 1024, "mb": 1024 ** 2, "m": 1024 ** 2, None: 1024}[m.group(2)]
    return int(float(m.group(1)) * mult)


def install_shortcut() -> int:
    """Add FileFit to the Linux application menu."""
    if not sys.platform.startswith("linux"):
        print("Shortcut install is only needed on Linux. On Windows use the installer.")
        return 1
    import shutil
    icon_src = Path(__file__).parent / "assets" / "icon.png"
    share = Path.home() / ".local" / "share"
    icon_dst = share / "icons" / "hicolor" / "256x256" / "apps" / "filefit.png"
    icon_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(icon_src, icon_dst)
    exe = shutil.which("filefit") or "filefit"
    desktop = share / "applications" / "filefit.desktop"
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop.write_text(
        "[Desktop Entry]\nType=Application\nName=FileFit\n"
        "Comment=Convert and compress files for upload portals\n"
        f"Exec={exe} %F\nIcon=filefit\nTerminal=false\nCategories=Utility;Office;Graphics;\n"
        "MimeType=image/jpeg;image/png;image/webp;application/pdf;"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document;\n")
    print(f"Added FileFit to your app menu ({desktop})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="filefit-cli", description="Convert and compress files for upload portals.")
    ap.add_argument("files", nargs="*", type=Path, help="files to convert")
    ap.add_argument("--to", dest="fmt", type=str.upper, choices=list(OUTPUT_FORMATS), default="PDF",
                    help="output format (default PDF)")
    ap.add_argument("--max-size", type=parse_size, help="size limit per file, e.g. 200KB or 2MB")
    ap.add_argument("--max-width", type=int)
    ap.add_argument("--max-height", type=int)
    ap.add_argument("--combine", action="store_true", help="merge all files into one PDF")
    ap.add_argument("-o", "--out-dir", type=Path, help="output folder (default: next to each file)")
    ap.add_argument("--install-shortcut", action="store_true", help="add FileFit to the Linux app menu")
    ap.add_argument("--version", action="version", version=f"FileFit {__version__} by {__author__} <{__email__}>")
    a = ap.parse_args(argv)
    if a.install_shortcut:
        return install_shortcut()
    if not a.files:
        ap.error("give at least one file")

    opts = Options(out_format=a.fmt, out_dir=a.out_dir, target_bytes=a.max_size,
                   max_width=a.max_width, max_height=a.max_height, combine=a.combine)
    results = [combine_to_pdf(a.files, opts)] if a.combine and len(a.files) > 1 else \
        [convert_file(f, opts) for f in a.files]
    failed = 0
    for r in results:
        if r.error:
            failed += 1
            print(f"✗ {r.source.name}: {r.error}", file=sys.stderr)
        for o in r.outputs:
            mark = "✓" if o.fits else "⚠ over limit"
            print(f"{mark} {o.path}  ({human_size(o.size)}{', ' + o.note if o.note else ''})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
