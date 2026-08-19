@echo off
setlocal
set SCRIPT_DIR=%~dp0
"%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%modbus_meter_simulator_v5.py" --port 5023 --display-interval 1 %*
