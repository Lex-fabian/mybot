@echo off
REM Ejecuta el script de compilacion/firma saltando la politica de ejecucion de PowerShell.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_release.ps1" %*
