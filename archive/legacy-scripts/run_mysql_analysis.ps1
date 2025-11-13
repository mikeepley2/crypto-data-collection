# PowerShell MySQL Database Analysis
# This script analyzes all your databases and technical indicators tables

Write-Host "🔍 MYSQL DATABASE ANALYSIS" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# MySQL connection parameters
$MySQLPath = ""
$PossiblePaths = @(
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    "C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe", 
    "C:\mysql\bin\mysql.exe",
    "C:\xampp\mysql\bin\mysql.exe",
    "C:\wamp64\bin\mysql\mysql8.0.31\bin\mysql.exe"
)

# Find MySQL executable
foreach ($Path in $PossiblePaths) {
    if (Test-Path $Path) {
        $MySQLPath = $Path
        Write-Host "✅ Found MySQL at: $MySQLPath" -ForegroundColor Green
        break
    }
}

if ($MySQLPath -eq "") {
    Write-Host "❌ MySQL executable not found!" -ForegroundColor Red
    Write-Host "💡 Checked these locations:" -ForegroundColor Yellow
    foreach ($Path in $PossiblePaths) {
        Write-Host "   $Path" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "Please run the SQL file 'mysql_complete_analysis.sql' manually in MySQL Workbench" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host ""
Write-Host "📋 STEP 1: LISTING ALL DATABASES" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

# Create temporary SQL file for database listing
$TempSQL1 = @"
SHOW DATABASES;
"@

$TempSQL1 | Out-File -FilePath "temp_db_list.sql" -Encoding UTF8

try {
    & $MySQLPath -u root -t -e "SHOW DATABASES;" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Databases listed successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Database listing may need password" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error running MySQL command" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔍 STEP 2: FINDING TECHNICAL INDICATORS TABLES" -ForegroundColor Yellow
Write-Host "-" * 50 -ForegroundColor Gray

# Create SQL for technical indicators analysis
$TechnicalSQL = @"
SELECT 
    CONCAT('📊 ', table_schema, '.', table_name) AS table_info,
    CONCAT('   📈 Rows: ', COALESCE(table_rows, 0)) AS row_info,
    CONCAT('   💾 Size: ', ROUND(COALESCE((data_length + index_length) / 1024 / 1024, 0), 2), ' MB') AS size_info
FROM information_schema.tables 
WHERE (LOWER(table_name) LIKE '%technical%' 
       OR LOWER(table_name) LIKE '%indicator%'
       OR LOWER(table_name) LIKE '%tech%')
   AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
ORDER BY COALESCE(table_rows, 0) DESC;
"@

$TechnicalSQL | Out-File -FilePath "temp_tech_analysis.sql" -Encoding UTF8

try {
    & $MySQLPath -u root -t -e $TechnicalSQL 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Technical indicators analysis complete" -ForegroundColor Green
    } else {
        Write-Host "⚠️  May need password for detailed analysis" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error in technical analysis" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 STEP 3: FINDING ALL CRYPTO/ML TABLES" -ForegroundColor Yellow
Write-Host "-" * 40 -ForegroundColor Gray

# Create SQL for crypto tables analysis
$CryptoSQL = @"
SELECT 
    CONCAT('📊 ', table_schema, '.', table_name) AS table_info,
    CONCAT('   📈 Rows: ', COALESCE(table_rows, 0)) AS row_info,
    CONCAT('   💾 Size: ', ROUND(COALESCE((data_length + index_length) / 1024 / 1024, 0), 2), ' MB') AS size_info
FROM information_schema.tables 
WHERE (LOWER(table_name) LIKE '%crypto%' 
       OR LOWER(table_name) LIKE '%price%'
       OR LOWER(table_name) LIKE '%market%'
       OR LOWER(table_name) LIKE '%ml%'
       OR LOWER(table_name) LIKE '%feature%'
       OR LOWER(table_name) LIKE '%material%'
       OR LOWER(table_name) LIKE '%btc%'
       OR LOWER(table_name) LIKE '%eth%')
   AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
ORDER BY COALESCE(table_rows, 0) DESC
LIMIT 15;
"@

try {
    & $MySQLPath -u root -t -e $CryptoSQL 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Crypto tables analysis complete" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Error in crypto analysis" -ForegroundColor Red
}

# Cleanup
Remove-Item "temp_db_list.sql" -ErrorAction SilentlyContinue
Remove-Item "temp_tech_analysis.sql" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🏆 RECOMMENDATIONS:" -ForegroundColor Green
Write-Host "-" * 30 -ForegroundColor Gray
Write-Host "1. ✅ Review the technical indicators tables above" -ForegroundColor White
Write-Host "2. 🎯 Choose the one with the most rows as your primary table" -ForegroundColor White
Write-Host "3. 🔄 Rename others to *_old (e.g., old_tech_indicators_old)" -ForegroundColor White
Write-Host "4. 📊 Run detailed analysis on your chosen primary table" -ForegroundColor White

Write-Host ""
Write-Host "📋 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "If you need password authentication, run this in MySQL Workbench:" -ForegroundColor Gray
Write-Host "   File: mysql_complete_analysis.sql" -ForegroundColor Yellow

Write-Host ""
Write-Host "🏁 ANALYSIS COMPLETE!" -ForegroundColor Green
Read-Host "Press Enter to continue"