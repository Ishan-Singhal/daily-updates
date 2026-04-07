@echo off
REM === Daily Updates Agent - Windows Task Scheduler Setup ===
REM This creates a scheduled task that runs daily at 7:00 AM

set PYTHON_PATH=python
set SCRIPT_PATH=%~dp0daily_update.py

echo Creating scheduled task "DailyUpdatesAgent"...
schtasks /create /tn "DailyUpdatesAgent" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" /sc daily /st 07:00 /f

if %errorlevel% equ 0 (
    echo.
    echo Task created successfully!
    echo   Name:     DailyUpdatesAgent
    echo   Schedule: Daily at 7:00 AM
    echo   Script:   %SCRIPT_PATH%
    echo.
    echo To change the time, run:
    echo   schtasks /change /tn "DailyUpdatesAgent" /st HH:MM
    echo.
    echo To delete the task:
    echo   schtasks /delete /tn "DailyUpdatesAgent" /f
    echo.
    echo To run it now for testing:
    echo   schtasks /run /tn "DailyUpdatesAgent"
) else (
    echo Failed to create task. Try running this script as Administrator.
)
pause
