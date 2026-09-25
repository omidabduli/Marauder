@echo off
TITLE Marauder - Team Status Monitor

echo ===========================================
echo    MARAUDER - STARTING SERVER...     
echo ===========================================

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install it from python.org
    pause
    exit /b
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate

:: Install dependencies
echo Checking dependencies...
pip install --quiet -r requirements.txt

:: Run the server
echo Server is starting...
echo Open http://127.0.0.1:5005 in your browser
echo ===========================================
python server.py

pause
