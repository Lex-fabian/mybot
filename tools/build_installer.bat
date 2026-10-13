@echo off
REM ===========================================================================
REM  MyBot - Compila el instalador con Inno Setup (installer.iss)
REM ===========================================================================
setlocal
cd /d "%~dp0.."

set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"

if not exist "%ISCC%" (
  echo [ERROR] No se encontro Inno Setup ^(ISCC.exe^).
  exit /b 1
)

echo == Compilando instalador con: %ISCC% ==
"%ISCC%" installer.iss
if errorlevel 1 (
  echo [ERROR] Fallo la compilacion del instalador.
  exit /b 1
)

echo.
echo == Instalador generado ==
dir /b dist_installer
