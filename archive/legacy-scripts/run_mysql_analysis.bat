@echo off
echo Running MySQL Database Analysis...
echo.

REM Try to find MySQL installation
set MYSQL_PATH=""
if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" (
    set MYSQL_PATH="C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
)
if exist "C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe" (
    set MYSQL_PATH="C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe"
)
if exist "C:\mysql\bin\mysql.exe" (
    set MYSQL_PATH="C:\mysql\bin\mysql.exe"
)

if %MYSQL_PATH%=="" (
    echo ❌ MySQL executable not found in common locations
    echo 💡 Please check your MySQL installation path
    echo.
    echo Common locations:
    echo   - C:\Program Files\MySQL\MySQL Server 8.0\bin\
    echo   - C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\
    echo   - C:\mysql\bin\
    echo.
    pause
    exit /b 1
)

echo ✅ Found MySQL at: %MYSQL_PATH%
echo.

REM Create temporary SQL file
echo -- Database Analysis > temp_analysis.sql
echo SHOW DATABASES; >> temp_analysis.sql
echo. >> temp_analysis.sql
echo SELECT 'TECHNICAL INDICATORS TABLES:' AS info; >> temp_analysis.sql
echo SELECT >> temp_analysis.sql
echo     table_schema AS database_name, >> temp_analysis.sql
echo     table_name, >> temp_analysis.sql
echo     COALESCE(table_rows, 0) AS estimated_rows, >> temp_analysis.sql
echo     ROUND(COALESCE((data_length + index_length) / 1024 / 1024, 0), 2) AS size_mb, >> temp_analysis.sql
echo     CONCAT(table_schema, '.', table_name) AS full_table_name >> temp_analysis.sql
echo FROM information_schema.tables >> temp_analysis.sql
echo WHERE (LOWER(table_name) LIKE '%%technical%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%indicator%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%tech%%') >> temp_analysis.sql
echo    AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys') >> temp_analysis.sql
echo ORDER BY estimated_rows DESC, size_mb DESC; >> temp_analysis.sql
echo. >> temp_analysis.sql
echo SELECT 'ALL CRYPTO/ML RELATED TABLES:' AS info2; >> temp_analysis.sql
echo SELECT >> temp_analysis.sql
echo     table_schema AS database_name, >> temp_analysis.sql
echo     table_name, >> temp_analysis.sql
echo     COALESCE(table_rows, 0) AS estimated_rows, >> temp_analysis.sql
echo     ROUND(COALESCE((data_length + index_length) / 1024 / 1024, 0), 2) AS size_mb >> temp_analysis.sql
echo FROM information_schema.tables >> temp_analysis.sql
echo WHERE (LOWER(table_name) LIKE '%%crypto%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%price%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%market%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%ml%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%feature%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%btc%%' >> temp_analysis.sql
echo        OR LOWER(table_name) LIKE '%%eth%%') >> temp_analysis.sql
echo    AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys') >> temp_analysis.sql
echo ORDER BY estimated_rows DESC, size_mb DESC >> temp_analysis.sql
echo LIMIT 20; >> temp_analysis.sql

echo Running analysis...
%MYSQL_PATH% -u root -t < temp_analysis.sql

echo.
echo Cleaning up...
del temp_analysis.sql

echo.
echo 🏁 Analysis complete!
pause