# Setting Up Hourly Health Checks

This guide explains how to set up automatic hourly health checks for streaming links.

## Windows (Task Scheduler)

### Option 1: Automated Setup (Recommended)

1. **Run the setup script as Administrator:**
   - Right-click `setup_health_check_task.bat`
   - Select "Run as administrator"
   - The script will create a scheduled task automatically

### Option 2: Manual Setup

1. **Open Task Scheduler:**
   - Press `Win + R`, type `taskschd.msc`, press Enter
   - Or search "Task Scheduler" in Start menu

2. **Create Basic Task:**
   - Click "Create Basic Task..." in the right panel
   - Name: `StreamingLinkHealthCheck`
   - Description: `Runs hourly health check for streaming links`

3. **Set Trigger:**
   - Trigger: `Daily`
   - Start date: Today
   - Time: `00:00:00`
   - Recur every: `1 days`
   - **IMPORTANT:** Check "Repeat task every:" and set to `1 hour` for a duration of `Indefinitely`

4. **Set Action:**
   - Action: `Start a program`
   - Program/script: `D:\movie_streamming\streamline-pro\venv\Scripts\python.exe`
   - Add arguments: `D:\movie_streamming\streamline-pro\MovieBackend\manage.py check_link_health`
   - Start in: `D:\movie_streamming\streamline-pro\MovieBackend`

5. **Finish:**
   - Review settings and click "Finish"
   - The task will run every hour

### Verify Task

```powershell
# View task details
schtasks /Query /TN StreamingLinkHealthCheck /V /FO LIST

# Test run the task manually
schtasks /Run /TN StreamingLinkHealthCheck
```

### Delete Task (if needed)

```powershell
schtasks /Delete /TN StreamingLinkHealthCheck /F
```

## Linux/Mac (Cron)

### Option 1: Automated Setup

1. **Make script executable:**
   ```bash
   chmod +x setup_health_check_linux.sh
   ```

2. **Run the setup script:**
   ```bash
   ./setup_health_check_linux.sh
   ```

### Option 2: Manual Setup

1. **Open crontab:**
   ```bash
   crontab -e
   ```

2. **Add this line (runs every hour at minute 0):**
   ```cron
   0 * * * * cd /path/to/streamline-pro/MovieBackend && /path/to/streamline-pro/venv/bin/python manage.py check_link_health >> /path/to/streamline-pro/logs/health_check.log 2>&1
   ```

   **Example for your setup:**
   ```cron
   0 * * * * cd /d/movie_streamming/streamline-pro/MovieBackend && /d/movie_streamming/streamline-pro/venv/bin/python manage.py check_link_health >> /d/movie_streamming/streamline-pro/logs/health_check.log 2>&1
   ```

3. **Save and exit** (in vi: press `Esc`, type `:wq`, press Enter)

4. **Create logs directory:**
   ```bash
   mkdir -p /path/to/streamline-pro/logs
   ```

### Verify Cron Job

```bash
# View your cron jobs
crontab -l

# Check cron service status (Linux)
sudo systemctl status cron

# View logs
tail -f /path/to/streamline-pro/logs/health_check.log
```

### Delete Cron Job

```bash
# Edit crontab
crontab -e

# Remove the line with check_link_health, save and exit
```

## Testing

After setting up, test the command manually:

### Windows
```powershell
cd D:\movie_streamming\streamline-pro\MovieBackend
D:\movie_streamming\streamline-pro\venv\Scripts\python.exe manage.py check_link_health --limit 5
```

### Linux/Mac
```bash
cd /path/to/streamline-pro/MovieBackend
/path/to/streamline-pro/venv/bin/python manage.py check_link_health --limit 5
```

## Monitoring

### Check Task History (Windows)

1. Open Task Scheduler
2. Find `StreamingLinkHealthCheck` task
3. Click "History" tab to see execution logs

### Check Logs (Linux/Mac)

```bash
# View recent logs
tail -n 50 /path/to/streamline-pro/logs/health_check.log

# Follow logs in real-time
tail -f /path/to/streamline-pro/logs/health_check.log
```

## Troubleshooting

### Task Not Running (Windows)

1. **Check task status:**
   ```powershell
   schtasks /Query /TN StreamingLinkHealthCheck
   ```

2. **Check "Last Run Result":**
   - Should be `0x0` (success)
   - If `0x1` (error), check the task history

3. **Run manually to see errors:**
   ```powershell
   schtasks /Run /TN StreamingLinkHealthCheck
   ```

4. **Check Task Scheduler logs:**
   - Task Scheduler → View → Show All Tasks History

### Cron Job Not Running (Linux/Mac)

1. **Check if cron service is running:**
   ```bash
   sudo systemctl status cron  # Linux
   sudo launchctl list | grep cron  # Mac
   ```

2. **Check cron logs:**
   ```bash
   # Linux
   sudo tail -f /var/log/syslog | grep CRON
   
   # Mac
   log show --predicate 'process == "cron"' --last 1h
   ```

3. **Verify paths are correct:**
   ```bash
   # Test the command manually
   cd /path/to/streamline-pro/MovieBackend
   /path/to/streamline-pro/venv/bin/python manage.py check_link_health --limit 1
   ```

4. **Check file permissions:**
   ```bash
   chmod +x /path/to/streamline-pro/venv/bin/python
   ```

## Advanced Options

### Run Every 30 Minutes (Windows)

Edit the task in Task Scheduler:
- Change "Repeat task every:" to `30 minutes`

### Run Every 30 Minutes (Cron)

```cron
*/30 * * * * cd /path/to/streamline-pro/MovieBackend && /path/to/venv/bin/python manage.py check_link_health
```

### Run Only During Business Hours (9 AM - 9 PM)

```cron
0 9-21 * * * cd /path/to/streamline-pro/MovieBackend && /path/to/venv/bin/python manage.py check_link_health
```

### Limit Checks to Older Links

```cron
0 * * * * cd /path/to/streamline-pro/MovieBackend && /path/to/venv/bin/python manage.py check_link_health --older-than 24
```

This only checks links that haven't been checked in the last 24 hours, making it more efficient.

