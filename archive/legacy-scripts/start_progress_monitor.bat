@echo off
REM Start the progress monitor script
echo Starting Materialized Updater Progress Monitor...
echo This will check progress every 5 minutes
echo Press Ctrl+C to stop
echo.
python monitor_updater_progress.py
pause


