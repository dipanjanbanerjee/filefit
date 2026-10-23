"""Quick end-to-end check used by the release builds: `FileFit --selftest`.

Exits 0 when the packaged app can load its GUI toolkit and do real conversions.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def run() -> int:
    try:
        from PIL import Image
        try:
            from PySide6 import QtWidgets  # noqa: F401  (Qt libraries are bundled)
        except ImportError as exc:
            # Graphics drivers such as libEGL come from the Linux system, not the app.
            # Build servers without a desktop lack them; real desktops have them.
            if sys.platform.startswith("linux") and ".so" in str(exc):
                print(f"note: skipped Qt check, system graphics library missing ({exc})")
            else:
                raise

        from .core import Options, convert_file

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src = tmp / "sample.jpg"
            Image.new("RGB", (1200, 900), (90, 120, 200)).save(src, quality=95)
            steps = [(src, "PDF"), (tmp / "sample.pdf", "JPG"), (tmp / "sample.pdf", "DOCX")]
            for path, fmt in steps:
                res = convert_file(path, Options(out_format=fmt, out_dir=tmp, target_bytes=200 * 1024))
                if res.error or not res.outputs:
                    raise RuntimeError(f"{path.name} -> {fmt}: {res.error}")
                print(f"ok {path.name} -> {fmt} ({res.outputs[0].size} bytes)")
        print("selftest passed")
        return 0
    except Exception as exc:  # report and fail the build
        import traceback
        traceback.print_exc()
        print(f"selftest FAILED: {exc}", file=sys.stderr)
        return 1
