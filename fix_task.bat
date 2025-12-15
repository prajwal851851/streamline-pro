@echo off
REM Script to fix/recreate the health check task
REM Run this as Administrator

echo Fixing StreamingLinkHealthCheck task...
echo.

REM Delete existing task if it exists
echo Step 1: Removing existing task (if any)...
schtasks /Query /TN "StreamingLinkHealthCheck" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Task exists. Deleting...
    schtasks /Delete /TN "StreamingLinkHealthCheck" /F
    if %ERRORLEVEL% EQU 0 (
        echo ✓ Old task deleted successfully.
    ) else (
        echo ✗ Failed to delete task. You may need to delete it manually from Task Scheduler.
        echo Opening Task Scheduler...
        start taskschd.msc
        pause
        exit /b 1
    )
) else (
    echo No existing task found.
)

echo.
echo Step 2: Creating new task...

REM Get paths
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%
set BACKEND_DIR=%PROJECT_DIR%MovieBackend
set VENV_PYTHON=%PROJECT_DIR%venv\Scripts\python.exe
set MANAGE_PY=%BACKEND_DIR%\manage.py

REM Verify paths
if not exist "%VENV_PYTHON%" (
    echo ERROR: Python not found at %VENV_PYTHON%
    pause
    exit /b 1
)

if not exist "%MANAGE_PY%" (
    echo ERROR: manage.py not found at %MANAGE_PY%
    pause
    exit /b 1
)

REM Create the task
schtasks /Create /TN "StreamingLinkHealthCheck" /TR "\"%VENV_PYTHON%\" \"%MANAGE_PY%\" check_link_health" /SC HOURLY /ST 00:00 /RU SYSTEM /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ SUCCESS: Task created successfully!
    echo.
    echo Task Configuration:
    echo   Name: StreamingLinkHealthCheck
    echo   Schedule: Every hour starting at midnight
    echo   Command: %VENV_PYTHON% %MANAGE_PY% check_link_health
    echo   Working Directory: %BACKEND_DIR%
    echo.
    echo Verifying task...
    schtasks /Query /TN "StreamingLinkHealthCheck" /V /FO LIST | findstr /C:"Task Name" /C:"Status" /C:"Next Run Time"
    echo.
    echo ✓ Task is ready and will run automatically every hour!
) else (
    echo.
    echo ✗ ERROR: Failed to create task.
    echo Make sure you're running this script as Administrator.
    echo.
)

pause

