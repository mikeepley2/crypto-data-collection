@echo off
echo Running Historical Data Completeness Check...
echo.

REM Try to run with sqlcmd (assuming SQL Server is installed locally)
sqlcmd -S localhost -d CryptoData -E -i check_historical_completeness.sql

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error running with sqlcmd
    echo 💡 Alternative options:
    echo    1. Open check_historical_completeness.sql in SQL Server Management Studio
    echo    2. Adjust server name/database name in the command above
    echo    3. Use Windows Authentication or add -U username -P password
    echo.
    echo Example with different server:
    echo sqlcmd -S YOUR_SERVER_NAME -d YOUR_DATABASE_NAME -E -i check_historical_completeness.sql
    pause
) else (
    echo.
    echo ✅ Analysis complete!
    pause
)