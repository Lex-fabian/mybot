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

REM --- 1. Localizar el ejecutable de Python real ---
set "PYEXE="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
  set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
  set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
  set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
  set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) else if exist "%ProgramFiles%\Python312\python.exe" (
  set "PYEXE=%ProgramFiles%\Python312\python.exe"
) else if exist "%ProgramFiles%\Python311\python.exe" (
  set "PYEXE=%ProgramFiles%\Python311\python.exe"
) else (
  where python >nul 2>nul
  if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE (
  echo [ERROR] No se encontro un Python 3.10 o superior funcional.
  echo         Instalalo desde https://www.python.org/downloads/ y marca
  echo         "Add python.exe to PATH" durante la instalacion.
  echo.
  pause
  exit /b 1
)

echo Python detectado: "%PYEXE%"
echo.

REM --- 2. Verificar dependencias principales ---
"%PYEXE%" -c "import TikTokLive, aiohttp, webview" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias necesarias con pip...
  "%PYEXE%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al instalar las dependencias de Python.
    echo Revisa tu conexion a Internet o permisos de usuario.
    echo.
    pause
    exit /b 1
  )
)

REM --- 3. Arrancar la aplicacion de escritorio ---
echo Iniciando MyBot...
"%PYEXE%" mybot_app.py
if errorlevel 1 (
  echo.
  echo [Aviso] La aplicacion se ha cerrado.
  pause
)
