Write-Host "=== MySQL Database Backup ===" -ForegroundColor Green

# Configuration
$mysqldump = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
$mysqlHost = "192.168.230.162"
$user = "news_collector"
$password = "99Rules!"
$database = "crypto_prices"
$backupDir = "C:\MySQL_Backups"

# Create backup directory
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force
    Write-Host "Created backup directory: $backupDir" -ForegroundColor Yellow
}

# Generate backup filename
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir\crypto_prices_backup_$timestamp.sql"

Write-Host "Starting backup..." -ForegroundColor Yellow
Write-Host "Database: $database"
Write-Host "Host: $mysqlHost"
Write-Host "Output: $backupFile"

try {
    # Execute mysqldump
    $startTime = Get-Date
    
    & $mysqldump --host=$mysqlHost --user=$user --password=$password --single-transaction --no-tablespaces --skip-lock-tables --databases $database | Out-File -FilePath $backupFile -Encoding UTF8
    
    if ($LASTEXITCODE -eq 0) {
        $endTime = Get-Date
        $duration = $endTime - $startTime
        $fileSize = (Get-Item $backupFile).Length / 1MB
        
        Write-Host "Backup completed successfully!" -ForegroundColor Green
        Write-Host "Duration: $($duration.TotalMinutes.ToString('F2')) minutes"
        Write-Host "File size: $($fileSize.ToString('F2')) MB"
        Write-Host "Location: $backupFile"
        
        # Compress backup
        $zipFile = $backupFile + ".zip"
        Compress-Archive -Path $backupFile -DestinationPath $zipFile -Force
        
        if (Test-Path $zipFile) {
            $zipSize = (Get-Item $zipFile).Length / 1MB
            Write-Host "Compressed to: $zipFile" -ForegroundColor Green
            Write-Host "Compressed size: $($zipSize.ToString('F2')) MB"
            
            # Remove uncompressed file
            Remove-Item $backupFile -Force
            Write-Host "Removed uncompressed file"
        }
        
        Write-Host "=== Backup Successful ===" -ForegroundColor Green
    } else {
        Write-Host "Backup failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
}
catch {
    Write-Host "Error during backup: $($_.Exception.Message)" -ForegroundColor Red
}