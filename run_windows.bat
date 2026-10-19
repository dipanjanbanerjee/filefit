@echo off
REM Runs FileFit from source without building an .exe (for quick testing).
cd /d "%~dp0"
if not exist .venv ( py -3 -m venv .venv || python -m venv .venv )
call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt
python main.py
