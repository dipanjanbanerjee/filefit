# PyInstaller recipe.
#   pyinstaller FileFit.spec                      -> dist/FileFit/ folder (used by the installer, starts fast)
#   set FILEFIT_ONEFILE=1 & pyinstaller FileFit.spec -> dist/FileFit.exe single portable file
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

ONEFILE = os.environ.get("FILEFIT_ONEFILE") == "1"

# Fill the Windows file-version details from filefit/__init__.py
_ns = {}
exec(open("filefit/__init__.py").read(), _ns)
_v = _ns["__version__"]
_vt = tuple(int(x) for x in (_v.split(".") + ["0", "0", "0"])[:4])
os.makedirs("build", exist_ok=True)
with open("build/version_info.txt", "w") as _f:
    _f.write(open("version_info.txt").read().replace("{vt}", str(_vt)).replace("{v}", _v))

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
              version="build/version_info.txt")

if ONEFILE:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, **common)
else:
    exe = EXE(pyz, a.scripts, exclude_binaries=True, **common)
    coll = COLLECT(exe, a.binaries, a.datas, name="FileFit", upx=False)
