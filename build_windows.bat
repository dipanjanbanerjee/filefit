@echo off
REM Builds FileFit.exe. Needs Python 3.10-3.13 from python.org (tick "Add python.exe to PATH").
cd /d "%~dp0"
if not exist .venv (
    py -3 -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt || goto :fail
set FILEFIT_ONEFILE=1
pyinstaller --noconfirm --clean FileFit.spec || goto :fail
echo.
echo Done! Your app is here: %cd%\dist\FileFit.exe
start "" "%cd%\dist"
pause
exit /b 0
:fail
echo.
echo Build failed. Scroll up to see the error.
pause
exit /b 1
