@echo off
echo ========================================
echo    Screenshot Tool - Install
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo Installation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Installation completed!
echo ========================================
echo.
echo Run start.bat to launch the tool
echo.
pause
