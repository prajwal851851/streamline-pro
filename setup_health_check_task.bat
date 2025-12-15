@echo off
REM Script to set up Windows Task Scheduler for link health checks
REM Run this script as Administrator

echo Setting up hourly health check task...

REM Get the current directory (should be streamline-pro)
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%
set BACKEND_DIR=%PROJECT_DIR%MovieBackend
set VENV_PYTHON=%PROJECT_DIR%venv\Scripts\python.exe
set MANAGE_PY=%BACKEND_DIR%\manage.py

REM Check if Python exists
if not exist "%VENV_PYTHON%" (
    echo ERROR: Python not found at %VENV_PYTHON%
    echo Please make sure the virtual environment is set up correctly.
    pause
    exit /b 1
)

REM Check if manage.py exists
if not exist "%MANAGE_PY%" (
    echo ERROR: manage.py not found at %MANAGE_PY%
    pause
    exit /b 1
)

REM Check if task already exists
schtasks /Query /TN "StreamingLinkHealthCheck" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Task already exists. Deleting old task...
    schtasks /Delete /TN "StreamingLinkHealthCheck" /F >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: Could not delete existing task. You may need to delete it manually.
        echo Opening Task Scheduler...
        start taskschd.msc
        pause
        exit /b 1
    )
    echo Old task deleted.
)

REM Create the task (runs every hour)
echo Creating new task...
schtasks /Create /TN "StreamingLinkHealthCheck" /TR "\"%VENV_PYTHON%\" \"%MANAGE_PY%\" check_link_health" /SC HOURLY /ST 00:00 /RU SYSTEM /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Task created successfully!
    echo.
    echo Task Name: StreamingLinkHealthCheck
    echo Schedule: Every hour starting at midnight
    echo Command: %VENV_PYTHON% %MANAGE_PY% check_link_health
    echo.
    echo To verify the task:
    echo   schtasks /Query /TN StreamingLinkHealthCheck
    echo.
    echo To delete the task (if needed):
    echo   schtasks /Delete /TN StreamingLinkHealthCheck /F
) else (
    echo.
    echo ERROR: Failed to create task. Make sure you're running as Administrator.
    echo.
    echo To run as Administrator:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
)

pause

