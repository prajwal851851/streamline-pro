#!/bin/bash
# Script to set up cron job for link health checks on Linux/Mac
# Run: chmod +x setup_health_check_linux.sh && ./setup_health_check_linux.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
BACKEND_DIR="$PROJECT_DIR/MovieBackend"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
MANAGE_PY="$BACKEND_DIR/manage.py"

# Check if Python exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Python not found at $VENV_PYTHON"
    echo "Please make sure the virtual environment is set up correctly."
    exit 1
fi

# Check if manage.py exists
if [ ! -f "$MANAGE_PY" ]; then
    echo "ERROR: manage.py not found at $MANAGE_PY"
    exit 1
fi

# Create the cron job (runs every hour at minute 0)
CRON_JOB="0 * * * * cd $BACKEND_DIR && $VENV_PYTHON $MANAGE_PY check_link_health >> $PROJECT_DIR/logs/health_check.log 2>&1"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "check_link_health"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "check_link_health" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "SUCCESS: Cron job created successfully!"
echo ""
echo "Cron job details:"
echo "  Schedule: Every hour at minute 0"
echo "  Command: cd $BACKEND_DIR && $VENV_PYTHON $MANAGE_PY check_link_health"
echo "  Log file: $PROJECT_DIR/logs/health_check.log"
echo ""
echo "To view your cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove this cron job:"
echo "  crontab -l | grep -v 'check_link_health' | crontab -"
echo ""

