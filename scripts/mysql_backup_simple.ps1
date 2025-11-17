# =============================================================================
# MySQL Database Backup Script for Windows (Simplified Version)
# =============================================================================
# This script creates automated backups of the crypto_prices database
# using the existing Windows MySQL 8.0 installation
# =============================================================================

param(
    [string]$BackupType = "daily",
    [switch]$TestRun = $false,
    [switch]$SetupSchedule = $false
)

# Configuration
$MySQLBin = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
$MySQLHost = "192.168.230.162"
$MySQLUser = "news_collector"
$MySQLPassword = "99Rules!"
$MySQLDatabase = "crypto_prices"
$BackupRoot = "C:\MySQL_Backups"
$LogFile = "C:\MySQL_Backups\backup_log.txt"

function Write-BackupLog {
    param([string]$Message, [string]$Level = "INFO")
    
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
    if (Test-Path (Split-Path $LogFile)) {
        Add-Content -Path $LogFile -Value $logEntry
    }
}

function Initialize-BackupEnvironment {
    Write-BackupLog "Initializing backup environment..."
    
    # Create backup directories
    $directories = @(
        $BackupRoot,
        "$BackupRoot\Daily",
        "$BackupRoot\Weekly", 
        "$BackupRoot\Monthly"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-BackupLog "Created directory: $dir" "SUCCESS"
        }
    }
    
    # Create log file
    if (!(Test-Path $LogFile)) {
        "MySQL Backup Log - Created $(Get-Date)" | Out-File $LogFile
        Write-BackupLog "Created log file: $LogFile" "SUCCESS"
    }
}

function Test-MySQLAccess {
    Write-BackupLog "Testing MySQL access..."
    
    if (!(Test-Path $MySQLBin)) {
        Write-BackupLog "MySQL dump utility not found at: $MySQLBin" "ERROR"
        return $false
    }
    
    try {
        $version = & $MySQLBin --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-BackupLog "MySQL dump utility accessible: $version" "SUCCESS"
            return $true
        } else {
            Write-BackupLog "MySQL dump utility test failed" "ERROR"
            return $false
        }
    }
    catch {
        Write-BackupLog "Error testing MySQL: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Start-MySQLBackup {
    param([string]$Type = "daily")
    
    Write-BackupLog "=== Starting MySQL Database Backup ===" "SUCCESS"
    Write-BackupLog "Backup type: $Type"
    Write-BackupLog "Database: $MySQLDatabase"
    Write-BackupLog "Host: $MySQLHost"
    
    # Determine backup directory
    $backupDir = switch ($Type) {
        "daily" { "$BackupRoot\Daily" }
        "weekly" { "$BackupRoot\Weekly" }
        "monthly" { "$BackupRoot\Monthly" }
        "test" { "$BackupRoot\Daily" }
        default { "$BackupRoot\Daily" }
    }
    
    # Generate backup filename
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $hostname = $env:COMPUTERNAME
    $backupFileName = "crypto_prices_$($Type)_$($hostname)_$timestamp.sql"
    $backupPath = Join-Path $backupDir $backupFileName
    
    Write-BackupLog "Backup file: $backupPath"
    
    try {
        # Execute mysqldump
        $startTime = Get-Date
        
        $arguments = @(
            "--host=$MySQLHost",
            "--user=$MySQLUser", 
            "--password=$MySQLPassword",
            "--single-transaction",
            "--routines",
            "--triggers", 
            "--events",
            "--quick",
            "--lock-tables=false",
            "--databases",
            $MySQLDatabase
        )
        
        Write-BackupLog "Executing backup command..."
        
        # Use Start-Process for better control
        $process = Start-Process -FilePath $MySQLBin -ArgumentList $arguments -RedirectStandardOutput $backupPath -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            $endTime = Get-Date
            $duration = $endTime - $startTime
            $fileSize = (Get-Item $backupPath).Length / 1MB
            
            Write-BackupLog "Backup completed successfully!" "SUCCESS"
            Write-BackupLog "Duration: $($duration.TotalMinutes.ToString('F2')) minutes"
            Write-BackupLog "File size: $($fileSize.ToString('F2')) MB"
            
            # Compress the backup
            $compressedPath = $backupPath + ".zip"
            Compress-Archive -Path $backupPath -DestinationPath $compressedPath -Force
            
            if (Test-Path $compressedPath) {
                $compressedSize = (Get-Item $compressedPath).Length / 1MB
                $compressionRatio = (1 - ($compressedSize / $fileSize)) * 100
                
                Write-BackupLog "Backup compressed successfully" "SUCCESS" 
                Write-BackupLog "Compressed size: $($compressedSize.ToString('F2')) MB"
                Write-BackupLog "Compression ratio: $($compressionRatio.ToString('F1'))%"
                
                # Remove uncompressed file
                Remove-Item $backupPath -Force
                
                Write-BackupLog "Final backup file: $compressedPath" "SUCCESS"
            }
            
            return $true
        } else {
            Write-BackupLog "Backup failed with exit code: $($process.ExitCode)" "ERROR"
            return $false
        }
    }
    catch {
        Write-BackupLog "Error during backup: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Install-BackupTasks {
    Write-BackupLog "Setting up Windows Task Scheduler for automated backups..."
    
    try {
        # Daily backup at 2 AM
        $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -BackupType daily"
        $trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
        $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description "Daily MySQL backup for crypto_prices database"
        
        Register-ScheduledTask -TaskName "MySQL Crypto Database Daily Backup" -InputObject $task -Force
        Write-BackupLog "Daily backup task scheduled for 2:00 AM" "SUCCESS"
        
        Write-BackupLog "Backup automation setup completed!" "SUCCESS"
        return $true
    }
    catch {
        Write-BackupLog "Error setting up scheduled tasks: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# =============================================================================
# Main Execution
# =============================================================================

Write-Host ""
Write-Host "🗄️  MySQL Windows Backup Solution" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Initialize environment
Initialize-BackupEnvironment

# Test MySQL access
if (!(Test-MySQLAccess)) {
    Write-BackupLog "Cannot proceed - MySQL access test failed" "ERROR"
    exit 1
}

# Execute based on parameters
if ($SetupSchedule) {
    Write-BackupLog "Setting up backup schedule..."
    if (Install-BackupTasks) {
        Write-BackupLog "Backup schedule setup completed!" "SUCCESS"
        exit 0
    } else {
        Write-BackupLog "Failed to setup backup schedule" "ERROR"
        exit 1
    }
} else {
    # Run backup
    if (Start-MySQLBackup -Type $BackupType) {
        Write-BackupLog "Backup process completed successfully!" "SUCCESS"
        exit 0
    } else {
        Write-BackupLog "Backup process failed" "ERROR"
        exit 1
    }
}