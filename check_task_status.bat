@echo off
REM Script to check the status of the health check task
echo Checking StreamingLinkHealthCheck task status...
echo.

REM Try to query the task
schtasks /Query /TN "StreamingLinkHealthCheck" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Task EXISTS and is configured!
    echo.
    echo Task Details:
    schtasks /Query /TN "StreamingLinkHealthCheck" /V /FO LIST | findstr /C:"Task Name" /C:"Status" /C:"Last Run Time" /C:"Next Run Time" /C:"Last Result" /C:"Task To Run"
    echo.
    echo To view full details:
    echo   schtasks /Query /TN StreamingLinkHealthCheck /V /FO LIST
    echo.
    echo To test run the task:
    echo   schtasks /Run /TN StreamingLinkHealthCheck
    echo.
    echo To delete and recreate:
    echo   schtasks /Delete /TN StreamingLinkHealthCheck /F
    echo   Then run setup_health_check_task.bat again
) else (
    echo ✗ Task NOT FOUND
    echo.
    echo The task does not exist. To create it:
    echo   1. Right-click setup_health_check_task.bat
    echo   2. Select "Run as administrator"
    echo.
)

pause

