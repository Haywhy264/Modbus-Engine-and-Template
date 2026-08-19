@echo off
setlocal
set SCRIPT_DIR=%~dp0
"%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%modbus_meter_simulator_v4.py" --port 5022 --display-interval 1 %*
