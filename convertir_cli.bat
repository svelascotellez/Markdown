@echo off
cd /d "%~dp0"
chcp 65001 > nul
title Convertidor a Markdown CLI

IF NOT EXIST "%~dp0.venv\Scripts\python.exe" (
    echo [!] Creando entorno virtual e instalando dependencias...
    python -m venv .venv
    "%~dp0.venv\Scripts\pip.exe" install -r requirements.txt
)

if "%~1"=="" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0cli.py"
) else (
    "%~dp0.venv\Scripts\python.exe" "%~dp0cli.py" %*
)

echo.
pause
