@echo off
echo MySQL Database Analysis
echo ========================

REM Find MySQL executable
if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" (
    set MYSQL_EXE="C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
    goto :found
)

if exist "C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe" (
    set MYSQL_EXE="C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe"
    goto :found
)

if exist "C:\mysql\bin\mysql.exe" (
    set MYSQL_EXE="C:\mysql\bin\mysql.exe"
    goto :found
)

echo MySQL not found in standard locations
echo Please run mysql_complete_analysis.sql in MySQL Workbench
pause
exit

:found
echo Found MySQL at: %MYSQL_EXE%
echo.

echo Listing databases...
%MYSQL_EXE% -u root -e "SHOW DATABASES;"

echo.
echo Finding technical indicators tables...
%MYSQL_EXE% -u root -e "SELECT table_schema, table_name, COALESCE(table_rows,0) as rows FROM information_schema.tables WHERE LOWER(table_name) LIKE '%%technical%%' OR LOWER(table_name) LIKE '%%indicator%%' ORDER BY rows DESC;"

echo.
echo Analysis complete!
pause