Write-Host "=== MySQL Database Table Backup ===" -ForegroundColor Green

# Configuration
$mysqldump = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
$mysqlHost = "192.168.230.162"
$user = "news_collector"
$password = "99Rules!"
$database = "crypto_prices"
$backupDir = "C:\MySQL_Backups"

# Important tables to backup (avoiding problematic views)
$importantTables = @(
    "ml_features_materialized",
    "price_data_real", 
    "technical_indicators",
    "ohlc_data",
    "crypto_onchain_data",
    "service_monitoring",
    "real_time_sentiment_signals",
    "crypto_onchain_data_enhanced",
    "trading_signals",
    "sentiment_aggregation",
    "crypto_assets",
    "macro_indicators"
)

# Create backup directory
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force
    Write-Host "Created backup directory: $backupDir" -ForegroundColor Yellow
}

# Generate backup filename
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir\crypto_prices_tables_backup_$timestamp.sql"

Write-Host "Starting backup..." -ForegroundColor Yellow
Write-Host "Database: $database"
Write-Host "Host: $mysqlHost"
Write-Host "Tables: $($importantTables.Count) important tables"
Write-Host "Output: $backupFile"

try {
    # Execute mysqldump for specific tables
    $startTime = Get-Date
    
    $tableList = $importantTables -join " "
    
    & $mysqldump --host=$mysqlHost --user=$user --password=$password --single-transaction --no-tablespaces --skip-lock-tables --add-drop-table $database $importantTables | Out-File -FilePath $backupFile -Encoding UTF8
    
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
            $compressionRatio = (1 - ($zipSize / $fileSize)) * 100
            
            Write-Host "Compressed to: $zipFile" -ForegroundColor Green
            Write-Host "Compressed size: $($zipSize.ToString('F2')) MB"
            Write-Host "Compression ratio: $($compressionRatio.ToString('F1'))%"
            
            # Remove uncompressed file
            Remove-Item $backupFile -Force
            Write-Host "Removed uncompressed file" -ForegroundColor Gray
        }
        
        Write-Host "=== Backup Successful ===" -ForegroundColor Green
        Write-Host "Backup location: $zipFile" -ForegroundColor Cyan
        
        # Show backup summary
        Write-Host "`nBackup Summary:" -ForegroundColor Yellow
        Write-Host "- Tables backed up: $($importantTables.Count)"
        Write-Host "- Total size: $($fileSize.ToString('F2')) MB"
        Write-Host "- Compressed size: $($zipSize.ToString('F2')) MB" 
        Write-Host "- File: $zipFile"
        
    } else {
        Write-Host "Backup failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
}
catch {
    Write-Host "Error during backup: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTo restore this backup:" -ForegroundColor Cyan
Write-Host "1. Extract the ZIP file"
Write-Host "2. Run: mysql -h $mysqlHost -u $user -p$password $database < extracted_file.sql"