@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run.py
  exit /b %ERRORLEVEL%
)

where py >nul 2>&1 && (
  py -3 run.py
  exit /b %ERRORLEVEL%
)

where python >nul 2>&1 && (
  python run.py
  exit /b %ERRORLEVEL%
)

echo Не найден Python. Создайте venv: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
exit /b 1
