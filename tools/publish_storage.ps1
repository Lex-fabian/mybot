<#
.SYNOPSIS
    Publica el instalador de MyBot en Cloud Storage for Firebase.

.DESCRIPTION
    Sube el instalador mas reciente de dist_installer a
    gs://mybot-79861.firebasestorage.app/instaladores/, lo marca como lectura
    publica, le aplica cacheo de un ano y muestra su SHA-256.

    Se usa Cloud Storage y no Hosting porque, con 69 MB por archivo, servirlo
    desde Hosting consumiria la cuota de transferencia del sitio completo
    (10 GB/mes), de modo que un pico de descargas afectaria a la propia pagina.

    Autenticacion: reutiliza la sesion del CLI de Firebase
    (%USERPROFILE%\.config\configstore\firebase-tools.json) en lugar de pedir
    un token aparte. El token se envia a curl por entrada estandar para que no
    aparezca en el listado de procesos.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\publish_storage.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\publish_storage.ps1 -Archivo .\dist_installer\MyBot_v1.3_Instalador.exe
#>
[CmdletBinding()]
param(
    [string]$Archivo = "",
    [string]$Bucket = "mybot-79861.firebasestorage.app",
    [string]$Carpeta = "instaladores"
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

# --- 0. Asegurar que el CLI de Firebase y Node.js esten accesibles ----------
# Igual que hace tools\deploy_firebase.bat: en sesiones antiguas puede que
# Node.js no este en el PATH aunque este instalado.
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    $candidatos = @(
        "$env:ProgramFiles\nodejs",
        "$env:LOCALAPPDATA\Programs\nodejs",
        "$env:APPDATA\npm"
    )
    $winget = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_*\node-v*-win-x64" -Directory -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName
    $candidatos += $winget
    foreach ($c in $candidatos) {
        if ($c -and (Test-Path $c)) { $env:PATH = "$c;$env:PATH" }
    }
}
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    throw "No se encuentra el CLI de Firebase. Instalalo con: npm install -g firebase-tools"
}

# --- 1. Localizar el instalador ------------------------------------------
if (-not $Archivo) {
    $candidatos = Get-ChildItem "dist_installer\MyBot_v*_Instalador.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    if (-not $candidatos) { throw "No hay ningun instalador en dist_installer. Ejecuta antes tools\build_installer.bat." }
    $Archivo = $candidatos[0].FullName
}
$Archivo = (Resolve-Path $Archivo).Path
$item = Get-Item $Archivo
Write-Host "Instalador: $($item.Name)  ($([math]::Round($item.Length / 1MB, 1)) MB)"

# --- 2. Renovar la sesion de Firebase ------------------------------------
# El token de acceso caduca cada hora. Ejecutar un comando autenticado hace que
# el CLI lo renueve y lo vuelva a escribir en su configuracion.
# Se invoca a traves de cmd.exe por dos motivos: evita el envoltorio firebase.ps1
# y evita que el progreso que el CLI escribe en stderr se interprete como error.
Write-Host "Renovando la sesion de Firebase..."
$previoError = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $env:ComSpec /c "firebase projects:list >nul 2>nul"
$codigoLogin = $LASTEXITCODE
$ErrorActionPreference = $previoError
if ($codigoLogin -ne 0) { throw "El CLI de Firebase no tiene sesion activa. Ejecuta: firebase login" }

$rutaCfg = "$env:USERPROFILE\.config\configstore\firebase-tools.json"
if (-not (Test-Path $rutaCfg)) { throw "No se encuentra la configuracion del CLI de Firebase en $rutaCfg" }
$cfg = Get-Content $rutaCfg -Raw | ConvertFrom-Json
$token = $cfg.tokens.access_token
if (-not $token) { throw "No se pudo obtener el token de acceso. Ejecuta: firebase login" }

# --- 3. Subir el objeto ---------------------------------------------------
$nombre = "$Carpeta/$($item.Name)"
$urlSubida = "https://storage.googleapis.com/upload/storage/v1/b/${Bucket}/o" +
             "?uploadType=media&name=$([uri]::EscapeDataString($nombre))&predefinedAcl=publicRead"

Write-Host "Subiendo a gs://$Bucket/$nombre ..."
$conf = "header = ""Authorization: Bearer $token"""
$salida = $conf | curl.exe -K - -sS -X POST `
    -H "Content-Type: application/octet-stream" `
    --data-binary "@$Archivo" $urlSubida `
    -w "`nhttp=%{http_code}" 2>&1

$codigo = ($salida | Select-String -Pattern "http=(\d+)").Matches.Groups[1].Value
if ($codigo -ne "200") {
    Write-Host $salida
    throw "La subida fallo (codigo HTTP $codigo)."
}
Write-Host "  Subida correcta."

# --- 4. Metadatos: cacheo largo y nombre al descargar --------------------
$obj = [uri]::EscapeDataString($nombre)
$h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$meta = @{
    cacheControl       = "public, max-age=31536000, immutable"
    contentDisposition = "attachment; filename=""$($item.Name)"""
} | ConvertTo-Json
Invoke-RestMethod -Uri "https://storage.googleapis.com/storage/v1/b/${Bucket}/o/${obj}" `
    -Headers $h -Method Patch -Body ([System.Text.Encoding]::UTF8.GetBytes($meta)) | Out-Null
Write-Host "  Metadatos aplicados (cacheo de un ano)."

# --- 5. Resumen ----------------------------------------------------------
$hash = (Get-FileHash -Algorithm SHA256 $Archivo).Hash
Write-Host ""
Write-Host "Descarga publica:"
Write-Host "  https://storage.googleapis.com/$Bucket/$nombre"
Write-Host ""
Write-Host "Actualiza frontend-mybot\public\version.json con estos valores:"
Write-Host "  ""download_url"": ""https://storage.googleapis.com/$Bucket/$nombre"","
Write-Host "  ""sha256"":       ""$hash"","
Write-Host "  ""size_bytes"":   $($item.Length),"
