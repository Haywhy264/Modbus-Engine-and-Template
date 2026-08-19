@echo off
setlocal
set SCRIPT_DIR=%~dp0
"%SCRIPT_DIR%.venv\Scripts\pythonw.exe" "%SCRIPT_DIR%modbus_simulator_v4_gui.py"
