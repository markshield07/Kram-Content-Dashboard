@echo off
REM Setup Windows Task Scheduler for daily content generation at 6am PST

echo Creating scheduled task for KRAM Content Creator...
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%execution\daily_run.py

REM Create the scheduled task
REM Runs daily at 6:00 AM Pacific Time
schtasks /create /tn "KRAM_Daily_Content" /tr "pythonw \"%PYTHON_SCRIPT%\"" /sc daily /st 06:00 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! Task "KRAM_Daily_Content" created.
    echo.
    echo The task will run daily at 6:00 AM.
    echo.
    echo To verify: Open Task Scheduler and look for "KRAM_Daily_Content"
    echo To run now: schtasks /run /tn "KRAM_Daily_Content"
    echo To delete:  schtasks /delete /tn "KRAM_Daily_Content" /f
) else (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Try running this script as Administrator.
)

echo.
pause
