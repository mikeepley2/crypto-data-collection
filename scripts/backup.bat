@echo off
REM =============================================================================
REM MySQL Backup for Windows - Batch Wrapper
REM =============================================================================
REM This batch file provides easy access to the PowerShell backup script
REM Run without parameters for daily backup, or specify backup type
REM =============================================================================

echo.
echo ================================================
echo   MySQL Database Backup for Windows
echo ================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if PowerShell script exists
if not exist "mysql_backup_windows.ps1" (
    echo ERROR: mysql_backup_windows.ps1 not found!
    echo Please ensure the PowerShell script is in the same directory.
    pause
    exit /b 1
)

REM Parse command line arguments
set BACKUP_TYPE=daily
set EXTRA_ARGS=

if "%1"=="setup" (
    set EXTRA_ARGS=-SetupSchedule
    echo Setting up automated backup schedule...
) else if "%1"=="test" (
    set EXTRA_ARGS=-TestRun
    echo Running test backup...
) else if "%1"=="daily" (
    set BACKUP_TYPE=daily
    echo Running daily backup...
) else if "%1"=="weekly" (
    set BACKUP_TYPE=weekly
    echo Running weekly backup...
) else if "%1"=="monthly" (
    set BACKUP_TYPE=monthly
    echo Running monthly backup...
) else if "%1"=="help" (
    goto :show_help
) else if "%1"=="/?" (
    goto :show_help
) else if not "%1"=="" (
    echo Unknown parameter: %1
    goto :show_help
) else (
    echo Running default daily backup...
)

echo.

REM Execute PowerShell script with appropriate parameters
powershell.exe -ExecutionPolicy Bypass -File "mysql_backup_windows.ps1" -BackupType %BACKUP_TYPE% %EXTRA_ARGS%

REM Check exit code
if %ERRORLEVEL% equ 0 (
    echo.
    echo ================================================
    echo   Backup completed successfully!
    echo ================================================
) else (
    echo.
    echo ================================================
    echo   Backup failed! Check the log for details.
    echo ================================================
)

echo.
pause
exit /b %ERRORLEVEL%

:show_help
echo.
echo USAGE: backup.bat [option]
echo.
echo OPTIONS:
echo   (no option)  - Run daily backup (default)
echo   daily        - Run daily backup
echo   weekly       - Run weekly backup  
echo   monthly      - Run monthly backup
echo   test         - Run test backup
echo   setup        - Setup automated backup schedule
echo   help         - Show this help
echo.
echo EXAMPLES:
echo   backup.bat           (daily backup)
echo   backup.bat setup     (setup automation)
echo   backup.bat test      (test backup)
echo   backup.bat weekly    (weekly backup)
echo.
echo BACKUP LOCATIONS:
echo   Daily:   C:\MySQL_Backups\Daily\
echo   Weekly:  C:\MySQL_Backups\Weekly\
echo   Monthly: C:\MySQL_Backups\Monthly\
echo   Logs:    C:\MySQL_Backups\backup_log.txt
echo.
pause
exit /b 0