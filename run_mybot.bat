@echo off
REM ===========================================================================
REM  MyBot - Lanzador de desarrollo (ejecuta la aplicacion desde el codigo fuente)
REM  Para la version distribuible usa el instalador o dist\MyBot.exe.
REM ===========================================================================
title MyBot - TikTok Live TTS y Donaciones Pro
cd /d "%~dp0"

echo ============================================================
echo   MyBot - Lector de Comentarios y Donaciones TikTok Live
echo ============================================================
echo.

REM --- Localizar un Python real (el alias de la Microsoft Store no sirve) ---
set "PYEXE="
python -c "import sys; print(1)" >nul 2>nul
if not errorlevel 1 set "PYEXE=python"
if not defined PYEXE (
  py -3 -c "import sys; print(1)" >nul 2>nul
  if not errorlevel 1 set "PYEXE=py -3"
)
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"

if not defined PYEXE (
  echo [ERROR] No se encontro un Python 3.10 o superior funcional.
  echo         Instalalo desde https://www.python.org/downloads/ y marca
  echo         "Add python.exe to PATH" durante la instalacion.
  echo.
  pause
  exit /b 1
)

echo Python detectado: %PYEXE%
echo.

REM --- Dependencias de Python (solo en la primera ejecucion) ---
%PYEXE% -c "import TikTokLive, aiohttp, webview" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias de Python ^(primera ejecucion^)...
  %PYEXE% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Fallo al instalar las dependencias de Python.
    pause
    exit /b 1
  )
)

echo Iniciando MyBot...
%PYEXE% mybot_app.py
