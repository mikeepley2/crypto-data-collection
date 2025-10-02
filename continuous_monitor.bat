@echo off
REM Continuous ML Features Monitoring Script for Windows
REM Runs monitoring checks every 10 minutes indefinitely

echo =====================================================
echo CRYPTO ML FEATURES CONTINUOUS MONITORING
echo =====================================================
echo Starting continuous monitoring...
echo Check interval: 10 minutes
echo Press Ctrl+C to stop monitoring
echo.

:MONITOR_LOOP
python monitor_ml_features.py
echo.
echo =====================================================
echo Next check in 10 minutes...
echo =====================================================
echo.
timeout /t 600 /nobreak
goto MONITOR_LOOP
