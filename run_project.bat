@echo off
title CineStream Movie Recommendation Platform
color 0A

echo =====================================================================
echo           CINESTREAM MOVIE RECOMMENDATION PLATFORM
echo                     Skill Lab Review 2
echo =====================================================================
echo.

:: Ensure we run from the batch file's directory
cd /d "%~dp0"

:: 1. Check Python installation
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Python is not found in your system PATH.
    echo Please install Python 3.10+ or add it to PATH.
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking database status...
if not exist "movies.db" (
    echo [INFO] Database not found. Running automated MovieLens import...
    python "datasets\download_and_import.py"
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [ERROR] Failed to initialize database.
        pause
        exit /b 1
    )
) else (
    echo [OK] Database 'movies.db' found and verified.
)

echo.
echo [2/3] Launching web browser at http://127.0.0.1:5000 ...
start "" http://127.0.0.1:5000

echo.
echo [3/3] Starting CineStream Flask REST API and Web Server...
echo =====================================================================
echo  URL: http://127.0.0.1:5000
echo.
echo  Demo Credentials:
echo    - Regular User : demo_user / user123
echo    - Administrator: admin / admin123
echo.
echo  Press CTRL+C in this console window to stop the server anytime.
echo =====================================================================
echo.

python server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [NOTICE] Server terminated with error code %ERRORLEVEL%.
    pause
)
