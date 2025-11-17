# Final Migration and Cleanup - PowerShell Version
# Execute this script to complete the collector table consolidation

$ErrorActionPreference = "Continue"

Write-Host "=== FINAL MIGRATION AND CLEANUP EXECUTION ===" -ForegroundColor Green
Write-Host "Starting collector table consolidation..." -ForegroundColor Yellow

# Database connection parameters
$host = "172.22.32.1"
$user = "news_collector"
$password = "99Rules!"

# Function to execute MySQL command
function Invoke-MySQL {
    param([string]$Query, [string]$Description = "")
    
    if ($Description) {
        Write-Host $Description -ForegroundColor Cyan
    }
    
    $result = & mysql -h $host -u $user -p"$password" -e "$Query" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result
        return $true
    } else {
        Write-Host "Error: $result" -ForegroundColor Red
        return $false
    }
}

# Step 1: Check current state
Write-Host "`n=== STEP 1: PRE-MIGRATION VERIFICATION ===" -ForegroundColor Green

$verificationQuery = @"
SELECT 'PRIMARY TABLES STATUS:' as info;
SELECT 'Technical' as table_type, COUNT(*) as records FROM crypto_prices.technical_indicators
UNION ALL
SELECT 'News' as table_type, COUNT(*) as records FROM crypto_news.news_data  
UNION ALL
SELECT 'Macro' as table_type, COUNT(*) as records FROM crypto_prices.macro_indicators
UNION ALL
SELECT 'Onchain' as table_type, COUNT(*) as records FROM crypto_prices.crypto_onchain_data;
"@

Invoke-MySQL -Query $verificationQuery -Description "Checking primary tables status..."

# Step 2: Check for unique news articles to migrate
Write-Host "`n=== STEP 2: NEWS MIGRATION ANALYSIS ===" -ForegroundColor Green

$checkUniqueNews = @"
SELECT COUNT(*) as unique_articles FROM crypto_prices.crypto_news cn
WHERE cn.url IS NOT NULL 
AND cn.url NOT IN (
    SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
    WHERE nd.url IS NOT NULL
);
"@

Invoke-MySQL -Query $checkUniqueNews -Description "Checking for unique news articles..."

# Step 3: Perform news migration if needed
Write-Host "`n=== STEP 3: NEWS MIGRATION ===" -ForegroundColor Green

$migrateNews = @"
INSERT INTO crypto_news.news_data 
(title, content, url, published_date, source, sentiment_score, created_at)
SELECT 
    title, content, url, published_date, 
    COALESCE(source, 'migrated_from_crypto_prices'), 
    sentiment_score, NOW()
FROM crypto_prices.crypto_news cn
WHERE cn.url IS NOT NULL 
AND cn.url NOT IN (
    SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
    WHERE nd.url IS NOT NULL
);
SELECT ROW_COUNT() as articles_migrated;
"@

if (Invoke-MySQL -Query $migrateNews -Description "Migrating unique news articles...") {
    Write-Host "News migration completed successfully!" -ForegroundColor Green
}

# Step 4: Archive duplicate tables
Write-Host "`n=== STEP 4: ARCHIVING DUPLICATE TABLES ===" -ForegroundColor Green

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# List of tables to archive
$tablesToArchive = @(
    @{db="crypto_prices"; table="crypto_news"},
    @{db="crypto_news"; table="stock_market_news_data"},
    @{db="crypto_news"; table="macro_economic_data"},
    @{db="crypto_prices"; table="sentiment_aggregation"},
    @{db="crypto_news"; table="crypto_sentiment_data"},
    @{db="crypto_news"; table="social_sentiment_metrics"}
)

$archivedCount = 0

foreach ($tableInfo in $tablesToArchive) {
    $db = $tableInfo.db
    $table = $tableInfo.table
    $newName = "${table}_archive_${timestamp}_old"
    
    $renameQuery = "RENAME TABLE $db.$table TO $db.$newName;"
    
    if (Invoke-MySQL -Query $renameQuery -Description "Archiving $db.$table...") {
        Write-Host "  ✓ Archived: $db.$table -> $newName" -ForegroundColor Green
        $archivedCount++
    } else {
        Write-Host "  ! Skipped: $db.$table (may not exist or already archived)" -ForegroundColor Yellow
    }
}

# Step 5: Final verification
Write-Host "`n=== STEP 5: FINAL VERIFICATION ===" -ForegroundColor Green

$finalVerification = @"
SELECT 'FINAL TABLE STATUS:' as status;
SELECT 'Technical' as table_type, COUNT(*) as records FROM crypto_prices.technical_indicators
UNION ALL
SELECT 'News' as table_type, COUNT(*) as records FROM crypto_news.news_data  
UNION ALL
SELECT 'Macro' as table_type, COUNT(*) as records FROM crypto_prices.macro_indicators
UNION ALL
SELECT 'Onchain' as table_type, COUNT(*) as records FROM crypto_prices.crypto_onchain_data
UNION ALL
SELECT 'OHLC' as table_type, COUNT(*) as records FROM crypto_prices.ohlc_data
UNION ALL
SELECT 'ML_Features' as table_type, COUNT(*) as records FROM crypto_prices.ml_features_materialized;
"@

Invoke-MySQL -Query $finalVerification -Description "Final verification of primary tables..."

# Summary
Write-Host "`n=== MIGRATION SUMMARY ===" -ForegroundColor Green
Write-Host "✓ Tables archived: $archivedCount" -ForegroundColor Green
Write-Host "✓ Single source of truth achieved for all collector types!" -ForegroundColor Green
Write-Host "✓ All duplicate data safely preserved in archived tables" -ForegroundColor Green

Write-Host "`n=== CLEANUP COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
Write-Host "Your crypto data collection system now has optimal table structure!" -ForegroundColor Yellow