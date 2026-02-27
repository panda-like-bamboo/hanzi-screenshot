@echo off
echo ========================================
echo    Screenshot Tool - Starting...
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found
    pause
    exit /b 1
)

echo Starting Screenshot Tool...
echo.
echo Tips:
echo - Press Ctrl+Shift+A to start screenshot
echo - Right-click tray icon for more options
echo - Close this window to exit
echo.

pythonw screenshot_tool.py

pause
