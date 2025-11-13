# PowerShell script to check historical data completeness
# Run this in PowerShell ISE or PowerShell console

Write-Host "📊 HISTORICAL DATA COMPLETENESS ANALYSIS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

# Connection parameters - adjust as needed
$ServerName = "localhost"  # Change if different
$DatabaseName = "CryptoData"  # Change if different
$UseWindowsAuth = $true  # Set to $false if using SQL auth

try {
    if ($UseWindowsAuth) {
        $ConnectionString = "Server=$ServerName;Database=$DatabaseName;Integrated Security=True;"
    } else {
        # Uncomment and modify if using SQL Server authentication
        # $Username = "your_username"
        # $Password = "your_password" 
        # $ConnectionString = "Server=$ServerName;Database=$DatabaseName;User Id=$Username;Password=$Password;"
        Write-Host "❌ SQL Server authentication not configured. Please modify script." -ForegroundColor Red
        exit 1
    }

    # Load SQL Server assembly
    Add-Type -AssemblyName "System.Data"
    
    # Create connection
    $Connection = New-Object System.Data.SqlClient.SqlConnection
    $Connection.ConnectionString = $ConnectionString
    $Connection.Open()
    
    Write-Host "✅ Connected to SQL Server: $ServerName" -ForegroundColor Green
    Write-Host "✅ Database: $DatabaseName" -ForegroundColor Green
    Write-Host ""
    
    # Check if table exists
    $CheckTableQuery = @"
SELECT COUNT(*) as table_count
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'ml_features_materialized'
"@
    
    $Command = New-Object System.Data.SqlClient.SqlCommand($CheckTableQuery, $Connection)
    $TableExists = $Command.ExecuteScalar()
    
    if ($TableExists -eq 0) {
        Write-Host "❌ ml_features_materialized table not found!" -ForegroundColor Red
        
        # Look for similar tables
        $SimilarTablesQuery = @"
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE '%material%' 
   OR TABLE_NAME LIKE '%ml%'
   OR TABLE_NAME LIKE '%feature%'
ORDER BY TABLE_NAME
"@
        
        $SimilarCommand = New-Object System.Data.SqlClient.SqlCommand($SimilarTablesQuery, $Connection)
        $SimilarReader = $SimilarCommand.ExecuteReader()
        
        Write-Host "🔍 Looking for similar tables:" -ForegroundColor Yellow
        $foundTables = @()
        while ($SimilarReader.Read()) {
            $tableName = $SimilarReader["TABLE_NAME"]
            $foundTables += $tableName
            Write-Host "   📋 $tableName" -ForegroundColor Gray
        }
        $SimilarReader.Close()
        
        if ($foundTables.Count -eq 0) {
            Write-Host "❌ No similar tables found" -ForegroundColor Red
        }
        
        $Connection.Close()
        return
    }
    
    Write-Host "✅ ml_features_materialized table found" -ForegroundColor Green
    Write-Host ""
    
    # Get overall statistics
    Write-Host "📅 OVERALL DATE COVERAGE:" -ForegroundColor Cyan
    Write-Host ("-" * 50) -ForegroundColor Gray
    
    $OverallQuery = @"
SELECT 
    MIN(price_date) as earliest_date,
    MAX(price_date) as latest_date,
    COUNT(DISTINCT price_date) as total_days,
    COUNT(*) as total_records
FROM ml_features_materialized
"@
    
    $OverallCommand = New-Object System.Data.SqlClient.SqlCommand($OverallQuery, $Connection)
    $OverallReader = $OverallCommand.ExecuteReader()
    
    if ($OverallReader.Read()) {
        $EarliestDate = $OverallReader["earliest_date"]
        $LatestDate = $OverallReader["latest_date"]
        $TotalDays = $OverallReader["total_days"]
        $TotalRecords = $OverallReader["total_records"]
        
        Write-Host "📍 Earliest Record: $($EarliestDate.ToString('yyyy-MM-dd'))" -ForegroundColor White
        Write-Host "📍 Latest Record: $($LatestDate.ToString('yyyy-MM-dd'))" -ForegroundColor White
        Write-Host "📊 Total Days Covered: $($TotalDays.ToString('N0'))" -ForegroundColor White
        Write-Host "📈 Total Records: $($TotalRecords.ToString('N0'))" -ForegroundColor White
        
        # Calculate coverage percentage
        $TargetStart = Get-Date "2023-01-01"
        $Today = Get-Date
        $ExpectedDays = ($Today - $TargetStart).Days + 1
        $CoveragePct = ($TotalDays / $ExpectedDays) * 100
        
        Write-Host "🎯 Expected Days (since 2023-01-01): $ExpectedDays" -ForegroundColor White
        Write-Host "📊 Coverage Percentage: $($CoveragePct.ToString('F1'))%" -ForegroundColor White
    }
    $OverallReader.Close()
    
    Write-Host ""
    
    # Symbol coverage by year
    Write-Host "🪙 SYMBOL COVERAGE BY YEAR:" -ForegroundColor Cyan
    Write-Host ("-" * 50) -ForegroundColor Gray
    
    $YearlyQuery = @"
SELECT 
    YEAR(price_date) as year,
    COUNT(DISTINCT symbol) as symbols,
    COUNT(DISTINCT price_date) as days,
    COUNT(*) as records
FROM ml_features_materialized
WHERE YEAR(price_date) IN (2023, 2024, 2025)
GROUP BY YEAR(price_date)
ORDER BY YEAR(price_date)
"@
    
    $YearlyCommand = New-Object System.Data.SqlClient.SqlCommand($YearlyQuery, $Connection)
    $YearlyReader = $YearlyCommand.ExecuteReader()
    
    while ($YearlyReader.Read()) {
        $Year = $YearlyReader["year"]
        $Symbols = $YearlyReader["symbols"]
        $Days = $YearlyReader["days"]
        $Records = $YearlyReader["records"]
        
        Write-Host "📊 $Year`: $Symbols symbols, $Days days, $($Records.ToString('N0')) records" -ForegroundColor White
    }
    $YearlyReader.Close()
    
    Write-Host ""
    
    # Sample of oldest records
    Write-Host "📜 SAMPLE OF OLDEST RECORDS:" -ForegroundColor Cyan
    Write-Host ("-" * 50) -ForegroundColor Gray
    
    $OldestQuery = @"
SELECT TOP 10
    symbol, price_date, current_price, volume_24h
FROM ml_features_materialized
WHERE price_date >= '2023-01-01'
ORDER BY price_date ASC, symbol ASC
"@
    
    $OldestCommand = New-Object System.Data.SqlClient.SqlCommand($OldestQuery, $Connection)
    $OldestReader = $OldestCommand.ExecuteReader()
    
    while ($OldestReader.Read()) {
        $Symbol = $OldestReader["symbol"]
        $Date = $OldestReader["price_date"].ToString('yyyy-MM-dd')
        $Price = if ($OldestReader["current_price"] -ne [DBNull]::Value) { 
            "`${0:N2}" -f $OldestReader["current_price"] 
        } else { "N/A" }
        $Volume = if ($OldestReader["volume_24h"] -ne [DBNull]::Value -and $OldestReader["volume_24h"] -gt 0) { 
            "`${0:N1}B" -f ($OldestReader["volume_24h"] / 1e9) 
        } else { "N/A" }
        
        Write-Host "📅 $Date | $Symbol`: $Price | Vol: $Volume" -ForegroundColor White
    }
    $OldestReader.Close()
    
    Write-Host ""
    
    # Health assessment
    Write-Host "🎯 HISTORICAL COMPLETENESS ASSESSMENT:" -ForegroundColor Cyan
    Write-Host ("=" * 50) -ForegroundColor Gray
    
    $HealthQuery = @"
SELECT 
    COUNT(*) as total_records,
    COUNT(current_price) as price_records,
    COUNT(volume_24h) as volume_records
FROM ml_features_materialized
WHERE price_date >= '2023-01-01'
"@
    
    $HealthCommand = New-Object System.Data.SqlClient.SqlCommand($HealthQuery, $Connection)
    $HealthReader = $HealthCommand.ExecuteReader()
    
    if ($HealthReader.Read()) {
        $TotalRecs = $HealthReader["total_records"]
        $PriceRecs = $HealthReader["price_records"] 
        $VolumeRecs = $HealthReader["volume_records"]
        
        $PriceHealth = if ($TotalRecs -gt 0) { ($PriceRecs / $TotalRecs) * 100 } else { 0 }
        $VolumeHealth = if ($TotalRecs -gt 0) { ($VolumeRecs / $TotalRecs) * 100 } else { 0 }
        $OverallHealth = ($PriceHealth + $VolumeHealth) / 2
        
        Write-Host "💰 Price Data Health: $($PriceHealth.ToString('F1'))%" -ForegroundColor White
        Write-Host "📊 Volume Data Health: $($VolumeHealth.ToString('F1'))%" -ForegroundColor White
        Write-Host "🏥 Overall Health Score: $($OverallHealth.ToString('F1'))%" -ForegroundColor White
        
        $HealthStatus = if ($OverallHealth -ge 90) { "🟢 EXCELLENT" } 
                       elseif ($OverallHealth -ge 75) { "🟡 GOOD" } 
                       elseif ($OverallHealth -ge 60) { "🟠 FAIR" } 
                       else { "🔴 NEEDS ATTENTION" }
        
        Write-Host "📊 Status: $HealthStatus" -ForegroundColor White
    }
    $HealthReader.Close()
    
    Write-Host ""
    Write-Host "🏁 HISTORICAL COMPLETENESS CHECK COMPLETE" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Common issues:" -ForegroundColor Yellow
    Write-Host "   - Check SQL Server is running" -ForegroundColor Gray
    Write-Host "   - Verify server name: $ServerName" -ForegroundColor Gray
    Write-Host "   - Verify database name: $DatabaseName" -ForegroundColor Gray
    Write-Host "   - Check Windows Authentication permissions" -ForegroundColor Gray
} finally {
    if ($Connection -and $Connection.State -eq 'Open') {
        $Connection.Close()
    }
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")