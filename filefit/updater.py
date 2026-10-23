"""Checks GitHub for a newer FileFit and installs it.

The only network request FileFit ever makes: one small call to the public GitHub
releases API. No file, name or usage data is sent.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import __version__

REPO = "dipanjanbanerjee/filefit"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
WEBSITE = "https://dipanjanbanerjee.github.io/filefit/"


@dataclass
class Release:
    version: str
    page: str
    notes: str = ""
    assets: dict[str, str] = field(default_factory=dict)  # file name -> download URL

    def asset(self, name: str) -> str | None:
        return self.assets.get(name)


def parse_version(text: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", text.split("-")[0].split("+")[0])
    return tuple(int(n) for n in nums[:3]) or (0,)


def is_newer(latest: str, current: str = __version__) -> bool:
    return parse_version(latest) > parse_version(current)


def fetch_latest(timeout: float = 8.0) -> Release:
    req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": f"FileFit/{__version__}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return Release(
        version=str(data.get("tag_name", "")).lstrip("vV"),
        page=data.get("html_url") or RELEASES_PAGE,
        notes=(data.get("body") or "").strip(),
        assets={a["name"]: a["browser_download_url"] for a in data.get("assets", [])},
    )


def check(timeout: float = 8.0) -> Release | None:
    """The newer release, or None when FileFit is up to date. Raises on network errors."""
    rel = fetch_latest(timeout)
    return rel if rel.version and is_newer(rel.version) else None


# ------------------------------------------------------------- how we were installed

def install_kind() -> str:
    """windows-installer, windows-portable, linux-app or pip."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable)
        if sys.platform == "win32":
            return "windows-installer" if any(exe.parent.glob("unins*.exe")) else "windows-portable"
        return "linux-app"
    return "pip"


def can_self_install() -> bool:
    return install_kind() in ("windows-installer", "windows-portable")


def download(url: str, dest: Path, progress: Callable[[int, int], None] | None = None,
             timeout: float = 30.0) -> Path:
    req = urllib.request.Request(url, headers={"User-Agent": f"FileFit/{__version__}"})
    part = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(part, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(256 * 1024):
            fh.write(chunk)
            done += len(chunk)
            if progress:
                progress(done, total)
    if total and done != total:
        part.unlink(missing_ok=True)
        raise OSError("The download was interrupted. Please try again.")
    os.replace(part, dest)
    return dest


def prepare(rel: Release, progress: Callable[[int, int], None] | None = None) -> Callable[[], None]:
    """Download the update. Returns a function that starts installing it; the app must quit right after."""
    kind = install_kind()
    if kind == "windows-installer":
        url = rel.asset("FileFit-Setup.exe")
        if not url:
            raise OSError("This release has no Windows installer yet.")
        setup = download(url, Path(tempfile.gettempdir()) / f"FileFit-Setup-{rel.version}.exe", progress)

        def run_installer():
            # /UPDATE=1 makes the installer start FileFit again when it is done.
            subprocess.Popen([str(setup), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                              "/CLOSEAPPLICATIONS", "/UPDATE=1"], close_fds=True)
        return run_installer

    if kind == "windows-portable":
        url = rel.asset("FileFit-Portable.exe")
        if not url:
            raise OSError("This release has no portable version yet.")
        exe = Path(sys.executable)
        new = download(url, exe.with_name(exe.stem + ".new.exe"), progress)

        def swap_and_restart():
            old = exe.with_name(exe.stem + ".old.exe")
            old.unlink(missing_ok=True)
            os.replace(exe, old)  # Windows allows renaming a running program
            os.replace(new, exe)
            subprocess.Popen([str(exe)], close_fds=True)
        return swap_and_restart

    raise OSError("Automatic install is only available on Windows.")


def cleanup_after_update() -> None:
    """Remove files left by a previous portable update."""
    if install_kind() == "windows-portable":
        exe = Path(sys.executable)
        for leftover in (exe.with_name(exe.stem + ".old.exe"), exe.with_name(exe.stem + ".new.exe.part")):
            try:
                leftover.unlink(missing_ok=True)
            except OSError:
                pass
