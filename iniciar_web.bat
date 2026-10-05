@echo off
cd /d "%~dp0"
chcp 65001 > nul
title DocToMarkdown Studio - Servidor Web

echo ========================================================
echo   Iniciando DocToMarkdown Studio (Web)
echo   Puerto: 8011
echo ========================================================
echo.

IF NOT EXIST "%~dp0.venv\Scripts\python.exe" (
    echo [!] No se encontro el entorno virtual .venv.
    echo Creando entorno virtual e instalando dependencias...
    python -m venv .venv
    "%~dp0.venv\Scripts\pip.exe" install -r requirements.txt
)

echo [OK] Entorno virtual detectado.
echo [>] Iniciando servidor y abriendo navegador en http://localhost:8011 ...
echo.

"%~dp0.venv\Scripts\python.exe" "%~dp0app.py" --port 8011
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] El servidor finalizo con codigo de error %ERRORLEVEL%.
    pause
)
