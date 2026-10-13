@echo off
REM ===========================================================================
REM  MyBot - Publica el instalador en Cloud Storage for Firebase
REM
REM  Sustituye a la copia en frontend-mybot\public\downloads. Los instaladores
REM  ya no viajan dentro del sitio: se suben al bucket y se sirven desde
REM  https://storage.googleapis.com/mybot-79861.firebasestorage.app/instaladores/
REM ===========================================================================
setlocal
cd /d "%~dp0.."

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_storage.ps1" %*
if errorlevel 1 (
  echo [ERROR] No se pudo publicar el instalador.
  pause
  exit /b 1
)

echo.
echo Recuerda actualizar frontend-mybot\public\version.json con el sha256 y
echo el tamano que se muestran arriba, y despues ejecutar tools\deploy_firebase.bat
