@echo off
setlocal
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo Instala primeiro o ambiente Python e requirements-gui.txt. Consulta o README.
    pause
    exit /b 1
)
start "" /D "%~dp0" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0src\gui.py"
