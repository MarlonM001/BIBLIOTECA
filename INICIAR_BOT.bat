@echo off
chcp 65001 >nul
title Bot Scopus SENA
cd /d "%~dp0"

echo ================================================
echo              BOT SCOPUS - BIBLIOTECA SENA
echo ================================================
echo.

REM ---- Buscar Python ----
set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY (py --version >nul 2>&1 && set "PY=py")
if not defined PY (
    echo No se encontro Python.
    echo Instalelo desde https://www.python.org/downloads/
    echo IMPORTANTE: marque la casilla "Add python.exe to PATH" al instalar.
    echo.
    pause
    exit /b 1
)

REM ---- Instalar Playwright la primera vez ----
%PY% -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo Instalando Playwright, solo pasa la primera vez...
    %PY% -m pip install --upgrade playwright
    echo.
)

REM ---- Datos (Enter = usar el valor entre parentesis) ----
set "BOT_USUARIO="
:pedir_usuario
set /p "BOT_USUARIO=Usuario: "
if not defined BOT_USUARIO (
    echo    El usuario es obligatorio.
    goto pedir_usuario
)

set "BOT_CONTRASENA="
set /p "BOT_CONTRASENA=Contrasena (Enter = igual al usuario): "
if not defined BOT_CONTRASENA set "BOT_CONTRASENA=%BOT_USUARIO%"

set "BOT_BUSQUEDA="
set /p "BOT_BUSQUEDA=Que desea buscar (computadores): "
if not defined BOT_BUSQUEDA set "BOT_BUSQUEDA=computadores"

set "BOT_DOCUMENTOS="
set /p "BOT_DOCUMENTOS=Cuantos documentos abrir (1): "
if not defined BOT_DOCUMENTOS set "BOT_DOCUMENTOS=1"

set "BOT_MINUTOS="
set /p "BOT_MINUTOS=Minutos de lectura por documento (3): "
if not defined BOT_MINUTOS set "BOT_MINUTOS=3"

echo.
%PY% "%~dp0codigo\bot_scopus.py"
echo.
pause
