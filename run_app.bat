@echo off
setlocal
cd /d "%~dp0"
echo Starting ExpensePulse Financial Application...

if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" run.py
) else if exist "D:\sandbox\my-fin-stats\venv\Scripts\python.exe" (
    "D:\sandbox\my-fin-stats\venv\Scripts\python.exe" run.py
) else (
    python run.py
)

pause
