# PyInstaller recipe.
#   pyinstaller FileFit.spec                      -> dist/FileFit/ folder (used by the installer, starts fast)
#   set FILEFIT_ONEFILE=1 & pyinstaller FileFit.spec -> dist/FileFit.exe single portable file
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

ONEFILE = os.environ.get("FILEFIT_ONEFILE") == "1"

hidden = collect_submodules("pdf2docx") + ["pillow_heif"]
if sys.platform == "win32":
    hidden += ["win32com", "win32com.client", "pythoncom", "pywintypes"]

a = Analysis(
    ["main.py"],
    datas=[("filefit/assets", "filefit/assets")],
    hiddenimports=hidden,
    excludes=["tkinter", "matplotlib", "IPython", "pytest",
              "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore",
              "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia", "PySide6.QtCharts"],
)
pyz = PYZ(a.pure)
common = dict(name="FileFit", icon="filefit/assets/icon.ico", console=False, upx=False,
              version="version_info.txt")

if ONEFILE:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, **common)
else:
    exe = EXE(pyz, a.scripts, exclude_binaries=True, **common)
    coll = COLLECT(exe, a.binaries, a.datas, name="FileFit", upx=False)
