<#
.SYNOPSIS
    Compila, firma digitalmente y calcula los checksums de MyBot para distribucion.

.DESCRIPTION
    Pasos:
      1) Compila el ejecutable con PyInstaller (MyBot.spec).
      2) Compila el instalador con Inno Setup (installer.iss) si esta instalado.
      3) Firma los binarios con signtool.exe usando un certificado de firma de codigo.
         -> FIRMAR es lo unico que elimina de verdad el aviso de Windows
            "Windows protegio su PC" / "editor desconocido".
      4) Genera tools\checksums.json con los hashes SHA-256 para que los usuarios
         puedan verificar las descargas.

.PARAMETER SkipBuild
    No compila; solo firma y calcula checksums de los binarios ya existentes.

.PARAMETER PfxPath
    Ruta a un certificado .pfx de firma de codigo.

.PARAMETER PfxPassword
    Contrasena del .pfx.

.PARAMETER CertThumbprint
    Huella de un certificado instalado en el almacen de Windows (para certificados
    EV en token USB/HSM).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\build_release.ps1 -PfxPath .\cert.pfx -PfxPassword "clave"

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\build_release.ps1 -SkipBuild -CertThumbprint "AB12CD..."
#>
[CmdletBinding()]
param(
    [switch]$SkipBuild,
    [string]$PfxPath,
    [string]$PfxPassword,
    [string]$CertThumbprint,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Get-SignTool {
    $candidatos = @(
        (Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName),
        (Get-ChildItem "$env:ProgramFiles\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName)
    ) | Where-Object { $_ }
    return $candidatos | Select-Object -First 1
}

function Invoke-Sign {
    param([string]$Ruta, [string]$SignTool)
    if (-not $SignTool) {
        Write-Warning "signtool.exe no encontrado (Windows SDK). '$Ruta' quedara SIN firmar."
        return $false
    }
    if ($PfxPath) {
        & $SignTool sign /fd SHA256 /f $PfxPath /p $PfxPassword /tr $TimestampUrl /td SHA256 $Ruta
    } elseif ($CertThumbprint) {
        & $SignTool sign /fd SHA256 /sha1 $CertThumbprint /tr $TimestampUrl /td SHA256 $Ruta
    } else {
        Write-Warning "No se indico certificado (-PfxPath o -CertThumbprint). '$Ruta' quedara SIN firmar."
        return $false
    }
    if ($LASTEXITCODE -ne 0) { throw "Error firmando '$Ruta' (codigo $LASTEXITCODE)." }
    Write-Host "  Firmado correctamente: $Ruta" -ForegroundColor Green
    return $true
}

# ---------------------------------------------------------------------------
# 1) Compilacion
# ---------------------------------------------------------------------------
if (-not $SkipBuild) {
    Write-Host "== Compilando ejecutable con PyInstaller =="
    python -m PyInstaller --noconfirm MyBot.spec
    if ($LASTEXITCODE -ne 0) { throw "Fallo PyInstaller." }

    $iscc = (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source
    if (-not $iscc) {
        $iscc = @(
            "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
        ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    }
    if ($iscc) {
        Write-Host "== Compilando instalador con Inno Setup =="
        & $iscc installer.iss
        if ($LASTEXITCODE -ne 0) { throw "Fallo Inno Setup." }
    } else {
        Write-Warning "Inno Setup no encontrado: se omite el instalador."
    }
}

# ---------------------------------------------------------------------------
# 2) Firma
# ---------------------------------------------------------------------------
$signTool = Get-SignTool
$binarios = @("dist\MyBot.exe")

# El instalador lleva la version en el nombre (MyBot_v1.2_Instalador.exe): firmamos el mas reciente.
$ultimoInstalador = Get-ChildItem "dist_installer\MyBot_v*_Instalador.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($ultimoInstalador) { $binarios += $ultimoInstalador.FullName }

$binarios = $binarios | Where-Object { Test-Path $_ }

if ($binarios.Count -eq 0) { throw "No se encontraron binarios para firmar. Ejecuta sin -SkipBuild." }

Write-Host "== Firmando binarios =="
foreach ($b in $binarios) { Invoke-Sign -Ruta (Resolve-Path $b).Path -SignTool $signTool }

# ---------------------------------------------------------------------------
# 3) Checksums SHA-256
# ---------------------------------------------------------------------------
Write-Host "== Calculando checksums SHA-256 =="
$checksums = [ordered]@{}
foreach ($b in $binarios) {
    $item = Get-Item $b
    $hash = (Get-FileHash -Algorithm SHA256 $item.FullName).Hash
    $checksums[$item.Name] = [ordered]@{
        sha256 = $hash
        bytes  = $item.Length
    }
    Write-Host ("  {0}  {1}" -f $hash, $item.Name)
}

$destino = Join-Path $PSScriptRoot "checksums.json"
$checksums | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $destino
Write-Host "Checksums guardados en: $destino" -ForegroundColor Green

if (-not ($PfxPath -or $CertThumbprint)) {
    Write-Host ""
    Write-Host "AVISO: los binarios NO se firmaron." -ForegroundColor Yellow
    Write-Host "Para eliminar el aviso de Windows ('editor desconocido' / SmartScreen)" -ForegroundColor Yellow
    Write-Host "necesitas un certificado de firma de codigo (OV o, mejor, EV) y volver a" -ForegroundColor Yellow
    Write-Host "ejecutar este script indicando -PfxPath o -CertThumbprint." -ForegroundColor Yellow
}
