@echo off
REM ===========================================================================
REM  MyBot - Compila y despliega el sitio en Firebase Hosting
REM  Proyecto: mybot-79861  ->  https://mybot-79861.web.app
REM ===========================================================================
setlocal
cd /d "%~dp0..\frontend-mybot"

REM --- Asegurar que Node.js este en el PATH (por si la sesion es antigua) ---
where node >nul 2>nul
if errorlevel 1 (
  for /d %%P in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_*") do (
    for /d %%N in ("%%P\node-v*-win-x64") do set "PATH=%%N;%PATH%"
  )
)
if exist "%ProgramFiles%\nodejs\node.exe" set "PATH=%ProgramFiles%\nodejs;%PATH%"
if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js no esta en el PATH. Reinicia el equipo o instala Node.js LTS.
  pause
  exit /b 1
)

echo == 1/4 Instalando dependencias (solo si faltan) ==
call npm install
if errorlevel 1 ( echo [ERROR] npm install & pause & exit /b 1 )

echo.
echo == 2/4 Compilando el sitio (Vite) ==
call npm run build
if errorlevel 1 ( echo [ERROR] npm run build & pause & exit /b 1 )

echo.
echo == 3/4 Comprobando sesion de Firebase ==
:check_login
call firebase login:list | findstr /I "@" >nul 2>nul
if not errorlevel 1 goto listo_login

echo ---------------------------------------------------------------
echo  No hay sesion iniciada en Firebase. Para iniciarla:
echo    1) Ejecuta:                    firebase login
echo    2) Abre la URL que aparezca y autoriza con tu cuenta Google.
echo    3) Copia el codigo y ejecuta:  firebase login ^<CODIGO^>
echo  Cuando hayas iniciado sesion, pulsa una tecla para continuar.
echo ---------------------------------------------------------------
pause
goto check_login

:listo_login
echo Sesion de Firebase OK.

echo.
echo == 4/4 Desplegando en Firebase Hosting ==
call firebase deploy --only hosting --project mybot-79861
if errorlevel 1 ( echo [ERROR] Fallo el despliegue. & pause & exit /b 1 )

echo.
REM La build copia public\downloads a dist\downloads (~190 MB). Ya esta subido a
REM Firebase, asi que se borra la copia local para no duplicar los instaladores.
REM public\downloads sigue siendo la unica fuente: la build la vuelve a copiar.
if exist "dist\downloads" rmdir /s /q "dist\downloads"

echo.
echo ===========================================================
echo  Despliegue completado: https://mybot-79861.web.app
echo ===========================================================
