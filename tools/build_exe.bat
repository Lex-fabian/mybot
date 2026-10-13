@echo off
REM ===========================================================================
REM  MyBot - Compila el ejecutable (PyInstaller) desde la raiz del proyecto
REM ===========================================================================
setlocal
cd /d "%~dp0.."

set "PY=python"
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

echo == Python: %PY% ==
"%PY%" -m PyInstaller --noconfirm --clean MyBot.spec
if errorlevel 1 (
  echo [ERROR] Fallo la compilacion.
  pause
  exit /b 1
)

echo.
echo == Generando checksums SHA-256 ==
REM El instalador lleva la version en el nombre (ej. MyBot_v1.3_Instalador.exe)
for %%F in ("dist\MyBot.exe" "dist_installer\MyBot_v*_Instalador.exe") do (
  if exist "%%~F" (
    for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 '%%~F').Hash"`) do (
      echo   %%H  %%~nxF
    )
  )
)

echo.
echo Compilacion completada.
