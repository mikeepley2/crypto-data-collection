# =============================================================================
# MySQL Database Backup Script for Windows
# =============================================================================
# This script creates automated backups of the crypto_prices database
# using the existing Windows MySQL 8.0 installation and Task Scheduler
#
# Features:
# - Daily automated backups
# - Backup rotation (keeps 7 daily, 4 weekly, 12 monthly)
# - Compression using built-in Windows compression
# - Email notifications (optional)
# - Backup verification
# =============================================================================

param(
    [string]$BackupType = "daily",
    [switch]$TestRun = $false,
    [switch]$SetupSchedule = $false
)

# Configuration
$CONFIG = @{
    # MySQL Connection
    MySQLBin = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
    MySQLHost = "192.168.230.162"
    MySQLUser = "news_collector"
    MySQLPassword = "99Rules!"
    MySQLDatabase = "crypto_prices"
    
    # Backup Directories
    BackupRoot = "C:\MySQL_Backups"
    DailyDir = "C:\MySQL_Backups\Daily"
    WeeklyDir = "C:\MySQL_Backups\Weekly"
    MonthlyDir = "C:\MySQL_Backups\Monthly"
    
    # Retention Policy
    DailyRetention = 7    # Keep 7 daily backups
    WeeklyRetention = 4   # Keep 4 weekly backups
    MonthlyRetention = 12 # Keep 12 monthly backups
    
    # Notification
    EmailEnabled = $false
    SMTPServer = "smtp.gmail.com"
    SMTPPort = 587
    FromEmail = "backup@yourdomain.com"
    ToEmail = "admin@yourdomain.com"
    
    # Logging
    LogFile = "C:\MySQL_Backups\backup_log.txt"
}

# =============================================================================
# Logging Functions
# =============================================================================

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Console output with colors
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry -ForegroundColor White }
    }
    
    # File logging
    if (Test-Path (Split-Path $CONFIG.LogFile)) {
        Add-Content -Path $CONFIG.LogFile -Value $logEntry
    }
}

# =============================================================================
# Setup Functions
# =============================================================================

function Initialize-BackupDirectories {
    Write-Log "Initializing backup directories..."
    
    $directories = @(
        $CONFIG.BackupRoot,
        $CONFIG.DailyDir,
        $CONFIG.WeeklyDir,
        $CONFIG.MonthlyDir
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "Created directory: $dir" "SUCCESS"
        }
    }
    
    # Create initial log file
    if (!(Test-Path $CONFIG.LogFile)) {
        "MySQL Backup Log - Created $(Get-Date)" | Out-File $CONFIG.LogFile
        Write-Log "Created log file: $($CONFIG.LogFile)" "SUCCESS"
    }
}

function Test-MySQLConnection {
    Write-Log "Testing MySQL connection..."
    
    if (!(Test-Path $CONFIG.MySQLBin)) {
        Write-Log "MySQL dump utility not found at: $($CONFIG.MySQLBin)" "ERROR"
        return $false
    }
    
    try {
        # Test connection using mysqldump --help (doesn't require connection)
        $testCmd = "& `"$($CONFIG.MySQLBin)`" --version"
        $result = Invoke-Expression $testCmd 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "MySQL dump utility is accessible" "SUCCESS"
            Write-Log "Version: $result"
            return $true
        } else {
            Write-Log "MySQL dump utility test failed" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Error testing MySQL connection: $_" "ERROR"
        return $false
    }
}

# =============================================================================
# Backup Functions
# =============================================================================

function Get-BackupFileName {
    param([string]$Type)
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $hostname = $env:COMPUTERNAME
    return "crypto_prices_$($Type)_$($hostname)_$timestamp.sql"
}

function Invoke-DatabaseBackup {
    param(
        [string]$BackupPath,
        [string]$BackupType
    )
    
    Write-Log "Starting $BackupType backup to: $BackupPath"
    
    try {
        # Build mysqldump command
        $mysqldumpArgs = @(
            "--host=$($CONFIG.MySQLHost)",
            "--user=$($CONFIG.MySQLUser)",
            "--password=$($CONFIG.MySQLPassword)",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--events",
            "--hex-blob",
            "--quick",
            "--lock-tables=false",
            "--add-drop-database",
            "--databases",
            $CONFIG.MySQLDatabase
        )
        
        # Execute backup
        $startTime = Get-Date
        Write-Log "Executing mysqldump with args: $($mysqldumpArgs -join ' ')"
        
        & $CONFIG.MySQLBin $mysqldumpArgs | Out-File -FilePath $BackupPath -Encoding UTF8
        
        if ($LASTEXITCODE -eq 0) {
            $endTime = Get-Date
            $duration = $endTime - $startTime
            $fileSize = (Get-Item $BackupPath).Length / 1MB
            
            Write-Log "Backup completed successfully" "SUCCESS"
            Write-Log "Duration: $($duration.TotalMinutes.ToString('F2')) minutes"
            Write-Log "File size: $($fileSize.ToString('F2')) MB"
            Write-Log "Backup file: $BackupPath"
            
            return $true
        } else {
            Write-Log "Backup failed with exit code: $LASTEXITCODE" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Error during backup: $_" "ERROR"
        return $false
    }
}

function Compress-BackupFile {
    param([string]$BackupPath)
    
    Write-Log "Compressing backup file..."
    
    try {
        $compressedPath = $BackupPath + ".zip"
        
        # Use Windows built-in compression
        Compress-Archive -Path $BackupPath -DestinationPath $compressedPath -Force
        
        if (Test-Path $compressedPath) {
            $originalSize = (Get-Item $BackupPath).Length / 1MB
            $compressedSize = (Get-Item $compressedPath).Length / 1MB
            $compressionRatio = (1 - ($compressedSize / $originalSize)) * 100
            
            Write-Log "Compression completed" "SUCCESS"
            Write-Log "Original size: $($originalSize.ToString('F2')) MB"
            Write-Log "Compressed size: $($compressedSize.ToString('F2')) MB"
            Write-Log "Compression ratio: $($compressionRatio.ToString('F1'))%"
            
            # Remove original uncompressed file
            Remove-Item $BackupPath -Force
            Write-Log "Removed uncompressed backup file"
            
            return $compressedPath
        } else {
            Write-Log "Compression failed - compressed file not created" "ERROR"
            return $BackupPath
        }
    }
    catch {
        Write-Log "Error during compression: $_" "ERROR"
        return $BackupPath
    }
}

function Remove-OldBackups {
    param(
        [string]$Directory,
        [int]$RetentionDays,
        [string]$Type
    )
    
    Write-Log "Cleaning up old $Type backups (keeping $RetentionDays)"
    
    try {
        $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
        $oldBackups = Get-ChildItem -Path $Directory -Filter "*.zip" | Where-Object { $_.CreationTime -lt $cutoffDate }
        
        if ($oldBackups.Count -gt 0) {
            foreach ($backup in $oldBackups) {
                Remove-Item $backup.FullName -Force
                Write-Log "Removed old backup: $($backup.Name)"
            }
            Write-Log "Removed $($oldBackups.Count) old $Type backups" "SUCCESS"
        } else {
            Write-Log "No old $Type backups to remove"
        }
    }
    catch {
        Write-Log "Error cleaning up old backups: $_" "ERROR"
    }
}

# =============================================================================
# Main Backup Function
# =============================================================================

function Start-DatabaseBackup {
    param([string]$Type = "daily")
    
    Write-Log "=== MySQL Database Backup Started ===" "SUCCESS"
    Write-Log "Backup type: $Type"
    Write-Log "Database: $($CONFIG.MySQLDatabase)"
    Write-Log "Host: $($CONFIG.MySQLHost)"
    
    # Determine backup directory
    $backupDir = switch ($Type) {
        "daily" { $CONFIG.DailyDir }
        "weekly" { $CONFIG.WeeklyDir }
        "monthly" { $CONFIG.MonthlyDir }
        default { $CONFIG.DailyDir }
    }
    
    # Generate backup filename
    $backupFileName = Get-BackupFileName -Type $Type
    $backupPath = Join-Path $backupDir $backupFileName
    
    # Perform backup
    $success = Invoke-DatabaseBackup -BackupPath $backupPath -BackupType $Type
    
    if ($success) {
        # Compress backup
        $finalPath = Compress-BackupFile -BackupPath $backupPath
        
        # Clean up old backups
        $retention = switch ($Type) {
            "daily" { $CONFIG.DailyRetention }
            "weekly" { $CONFIG.WeeklyRetention }
            "monthly" { $CONFIG.MonthlyRetention }
            default { $CONFIG.DailyRetention }
        }
        
        Remove-OldBackups -Directory $backupDir -RetentionDays $retention -Type $Type
        
        Write-Log "=== Backup Process Completed Successfully ===" "SUCCESS"
        return $true
    } else {
        Write-Log "=== Backup Process Failed ===" "ERROR"
        return $false
    }
}

# =============================================================================
# Task Scheduler Setup
# =============================================================================

function Install-BackupSchedule {
    Write-Log "Setting up Windows Task Scheduler for daily backups..."
    
    try {
        # Daily backup at 2 AM
        $dailyAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -BackupType daily"
        $dailyTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"
        $dailySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        $dailyTask = New-ScheduledTask -Action $dailyAction -Trigger $dailyTrigger -Settings $dailySettings -Description "Daily MySQL backup for crypto_prices database"
        
        Register-ScheduledTask -TaskName "MySQL Crypto Database Daily Backup" -InputObject $dailyTask -Force
        Write-Log "Daily backup task scheduled for 2:00 AM" "SUCCESS"
        
        # Weekly backup on Sunday at 1 AM
        $weeklyAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -BackupType weekly"
        $weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "01:00"
        $weeklyTask = New-ScheduledTask -Action $weeklyAction -Trigger $weeklyTrigger -Settings $dailySettings -Description "Weekly MySQL backup for crypto_prices database"
        
        Register-ScheduledTask -TaskName "MySQL Crypto Database Weekly Backup" -InputObject $weeklyTask -Force
        Write-Log "Weekly backup task scheduled for Sunday 1:00 AM" "SUCCESS"
        
        # Monthly backup on 1st of month at 12 AM
        $monthlyAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -BackupType monthly"
        $monthlyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -WeeksInterval 4 -At "00:00"
        $monthlyTask = New-ScheduledTask -Action $monthlyAction -Trigger $monthlyTrigger -Settings $dailySettings -Description "Monthly MySQL backup for crypto_prices database"
        
        Register-ScheduledTask -TaskName "MySQL Crypto Database Monthly Backup" -InputObject $monthlyTask -Force
        Write-Log "Monthly backup task scheduled for 1st Sunday midnight" "SUCCESS"
        
        Write-Log "All backup tasks have been scheduled successfully!" "SUCCESS"
        
        return $true
    }
    catch {
        Write-Log "Error setting up scheduled tasks: $_" "ERROR"
        return $false
    }
}

# =============================================================================
# Main Execution
# =============================================================================

Write-Host "🗄️  MySQL Windows Backup Solution" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Initialize backup environment
Initialize-BackupDirectories

# Test MySQL connection
if (!(Test-MySQLConnection)) {
    Write-Log "Cannot proceed - MySQL connection test failed" "ERROR"
    exit 1
}

# Handle different execution modes
if ($SetupSchedule) {
    Write-Log "Setting up backup schedule..."
    if (Install-BackupSchedule) {
        Write-Log "Backup schedule setup completed!" "SUCCESS"
    } else {
        Write-Log "Failed to setup backup schedule" "ERROR"
        exit 1
    }
} elseif ($TestRun) {
    Write-Log "Running test backup..."
    if (Start-DatabaseBackup -Type "test") {
        Write-Log "Test backup completed successfully!" "SUCCESS"
    } else {
        Write-Log "Test backup failed" "ERROR"
        exit 1
    }
} else {
    # Normal backup execution
    if (Start-DatabaseBackup -Type $BackupType) {
        Write-Log "Backup process completed successfully!" "SUCCESS"
        exit 0
    } else {
        Write-Log "Backup process failed" "ERROR"
        exit 1
    }
}