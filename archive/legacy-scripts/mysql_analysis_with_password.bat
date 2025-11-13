@echo off
echo MySQL Database Analysis (with password prompt)
echo ===============================================

REM Find MySQL executable
if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" (
    set MYSQL_EXE="C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
    goto :found
)

if exist "C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe" (
    set MYSQL_EXE="C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe"
    goto :found
)

echo MySQL not found in standard locations
pause
exit

:found
echo Found MySQL at: %MYSQL_EXE%
echo.

echo NOTE: You will be prompted for MySQL root password
echo.

echo Listing databases...
%MYSQL_EXE% -u root -p -e "SHOW DATABASES;"

if errorlevel 1 (
    echo.
    echo Login failed. Please check your MySQL password.
    echo.
    echo Alternative: Open MySQL Workbench and run this query:
    echo SELECT table_schema, table_name, table_rows FROM information_schema.tables 
    echo WHERE LOWER(table_name) LIKE '%%technical%%' OR LOWER(table_name) LIKE '%%indicator%%' 
    echo ORDER BY table_rows DESC;
    pause
    exit
)

echo.
echo Finding technical indicators tables...
%MYSQL_EXE% -u root -p -e "SELECT table_schema as 'Database', table_name as 'Table', COALESCE(table_rows,0) as 'Rows', ROUND(COALESCE((data_length + index_length) / 1024 / 1024, 0), 2) as 'Size_MB' FROM information_schema.tables WHERE (LOWER(table_name) LIKE '%%technical%%' OR LOWER(table_name) LIKE '%%indicator%%' OR LOWER(table_name) LIKE '%%tech%%') AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys') ORDER BY Rows DESC;"

echo.
echo Analysis complete!
echo.
echo NEXT STEPS:
echo 1. Identify the table with the most rows as your primary table
echo 2. Rename other technical tables to *_old 
echo 3. Update your applications to use the primary table
echo.
pause