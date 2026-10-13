@echo off
title MyBot - TikTok Live TTS ^& Donaciones Pro
cd /d "%~dp0"

echo ============================================================
echo   MyBot - Lector de Comentarios y Donaciones TikTok Live
echo ============================================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js no esta instalado o no esta en el PATH.
  echo         Descargalo en https://nodejs.org/ ^(version LTS^)
  echo.
  pause
  exit /b 1
)

REM --- Localizar un Python REAL (el alias de la Microsoft Store no sirve) ---
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
  echo [ERROR] No se encontro un Python 3.10+ funcional.
  echo         El alias de la Microsoft Store no sirve.
  echo         Instala Python desde https://www.python.org/downloads/
  echo         y marca "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

echo Python detectado: %PYEXE%
echo.

if not exist "node_modules\electron" (
  echo Instalando dependencias de Node.js ^(primera ejecucion^)...
  call npm install
  if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias de Node.js.
    pause
    exit /b 1
  )
)

echo Comprobando dependencias de Python...
%PYEXE% -c "import TikTokLive, edge_tts, pyttsx3" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias de Python ^(primera ejecucion^)...
  %PYEXE% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias de Python.
    pause
    exit /b 1
  )
)

echo Iniciando MyBot Desktop App...
call npm start

