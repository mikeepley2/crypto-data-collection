# PowerShell script to start the progress monitor
Write-Host "Starting Materialized Updater Progress Monitor..." -ForegroundColor Green
Write-Host "This will check progress every 5 minutes" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
python monitor_updater_progress.py


