@echo off
REM Alarm System Client Silent Startup Script
REM This file starts the alarm client GUI without any console windows

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Check if alarm_client.py exists
if not exist "alarm_client.py" (
    echo alarm_client.py not found in current directory
    echo Please ensure the alarm client script is in the same directory as this batch file
    pause
    exit /b 1
)

REM Start the alarm client GUI without console window
pythonw alarm_client.py

REM Optional: Log startup
echo %date% %time% - Alarm Client started >> alarm_client.log

REM Exit immediately
exit /b 0
