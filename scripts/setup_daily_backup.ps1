# =============================================================================
# SETUP DAILY MYSQL BACKUP AUTOMATION
# =============================================================================
# This script sets up Windows Task Scheduler to run daily backups automatically
# =============================================================================

Write-Host "🗄️  Setting up Daily MySQL Backup Automation" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$scriptPath = "$PSScriptRoot\table_backup.ps1"
$taskName = "MySQL Crypto Database Daily Backup"

# Check if script exists
if (!(Test-Path $scriptPath)) {
    Write-Host "❌ Error: Backup script not found at $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "📄 Backup script: $scriptPath" -ForegroundColor Yellow
Write-Host "📅 Schedule: Daily at 2:00 AM" -ForegroundColor Yellow

try {
    # Create scheduled task for daily backup at 2 AM
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""
    $trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable -RunOnlyIfIdle:$false
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Daily MySQL backup for crypto_prices database - backs up important tables to C:\MySQL_Backups"
    
    # Register the task
    Register-ScheduledTask -TaskName $taskName -InputObject $task -Force
    
    Write-Host "✅ Daily backup task created successfully!" -ForegroundColor Green
    Write-Host "📋 Task Name: $taskName" -ForegroundColor Cyan
    Write-Host "⏰ Schedule: Every day at 2:00 AM" -ForegroundColor Cyan
    Write-Host "💾 Backup Location: C:\MySQL_Backups\" -ForegroundColor Cyan
    
    # Test the task
    Write-Host "`n🧪 Testing backup task..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $taskName
    
    Write-Host "✅ Test started! Check C:\MySQL_Backups\ for backup file" -ForegroundColor Green
    
    Write-Host "`n📊 Backup Summary:" -ForegroundColor Yellow
    Write-Host "• Daily automated backups: ENABLED" -ForegroundColor Green
    Write-Host "• Backup important tables: ml_features_materialized, price_data_real, technical_indicators, etc." -ForegroundColor White
    Write-Host "• Compression: Enabled (ZIP format)" -ForegroundColor White  
    Write-Host "• Location: C:\MySQL_Backups\" -ForegroundColor White
    Write-Host "• Schedule: 2:00 AM daily" -ForegroundColor White
    
    Write-Host "`n🔧 Management Commands:" -ForegroundColor Cyan
    Write-Host "• View task: Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host "• Run manual backup: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host "• Disable backup: Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host "• Remove task: Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error setting up scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}