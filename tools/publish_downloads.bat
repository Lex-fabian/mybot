@echo off
REM ===========================================================================
REM  MyBot - Copia los binarios compilados a la carpeta de descargas del sitio
REM ===========================================================================
setlocal
cd /d "%~dp0.."
set "DEST=frontend-mybot\public\downloads"

if not exist "%DEST%" mkdir "%DEST%"

if not exist "dist_installer\MyBot_v*_Instalador.exe" (
  echo [ERROR] No existe ningun instalador en dist_installer
  exit /b 1
)

REM Solo se publica el instalador: la aplicacion es una carpeta (PyInstaller
REM onedir) y no existe un unico .exe portable que copiar.
del /q "%DEST%\*.exe" 2>nul
for %%F in ("dist_installer\MyBot_v*_Instalador.exe") do copy /Y "%%~F" "%DEST%\" >nul

echo == Contenido de %DEST% ==
dir /b "%DEST%"

echo.
echo == Tamano y SHA-256 ==
powershell -NoProfile -Command "Get-ChildItem '%DEST%\*.exe' | ForEach-Object { '{0}  {1} bytes' -f $_.Name, $_.Length }"
powershell -NoProfile -Command "Get-ChildItem '%DEST%\*.exe' | ForEach-Object { '{0}  {1}' -f (Get-FileHash -Algorithm SHA256 $_.FullName).Hash, $_.Name }"
