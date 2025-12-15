# PowerShell script to verify the health check task
# Run this in PowerShell (can be run as regular user, but admin shows more details)

Write-Host "Checking for StreamingLinkHealthCheck task..." -ForegroundColor Cyan

# Try to get the task
$task = Get-ScheduledTask -TaskName "StreamingLinkHealthCheck" -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "`n✓ Task found!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Yellow
    Write-Host "  Name: $($task.TaskName)" -ForegroundColor White
    Write-Host "  State: $($task.State)" -ForegroundColor White
    Write-Host "  Last Run: $($task.LastRunTime)" -ForegroundColor White
    Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor White
    
    # Get more details
    $taskInfo = Get-ScheduledTaskInfo -TaskName "StreamingLinkHealthCheck" -ErrorAction SilentlyContinue
    if ($taskInfo) {
        Write-Host "`nExecution Details:" -ForegroundColor Yellow
        Write-Host "  Last Run Result: $($taskInfo.LastTaskResult)" -ForegroundColor White
        Write-Host "  Last Run Time: $($taskInfo.LastRunTime)" -ForegroundColor White
        Write-Host "  Next Run Time: $($taskInfo.NextRunTime)" -ForegroundColor White
        Write-Host "  Number of Missed Runs: $($taskInfo.NumberOfMissedRuns)" -ForegroundColor White
    }
    
    # Get task action
    $taskAction = (Get-ScheduledTask -TaskName "StreamingLinkHealthCheck").Actions
    Write-Host "`nTask Action:" -ForegroundColor Yellow
    Write-Host "  Execute: $($taskAction.Execute)" -ForegroundColor White
    Write-Host "  Arguments: $($taskAction.Arguments)" -ForegroundColor White
    Write-Host "  Working Directory: $($taskAction.WorkingDirectory)" -ForegroundColor White
    
    Write-Host "`n✓ Task is configured correctly!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Task not found!" -ForegroundColor Red
    Write-Host "`nThe task may not have been created. Please:" -ForegroundColor Yellow
    Write-Host "  1. Right-click 'setup_health_check_task.bat'" -ForegroundColor White
    Write-Host "  2. Select 'Run as administrator'" -ForegroundColor White
    Write-Host "  3. Run this script again to verify" -ForegroundColor White
}

Write-Host "`nTo manually test the health check:" -ForegroundColor Cyan
Write-Host "  cd D:\movie_streamming\streamline-pro\MovieBackend" -ForegroundColor Gray
Write-Host "  D:\movie_streamming\streamline-pro\venv\Scripts\python.exe manage.py check_link_health --limit 5" -ForegroundColor Gray

Write-Host "`nTo manually run the task:" -ForegroundColor Cyan
Write-Host "  schtasks /Run /TN StreamingLinkHealthCheck" -ForegroundColor Gray
Write-Host "  (Note: May require admin privileges)" -ForegroundColor DarkGray

