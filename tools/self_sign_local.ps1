<#
.SYNOPSIS
    Firma MyBot con un certificado AUTOFIRMADO, solo para pruebas locales.

.DESCRIPTION
    ADVERTENCIA IMPORTANTE:
      Un certificado autofirmado NO es de confianza en otros equipos. Windows
      seguirá mostrando "editor desconocido" / SmartScreen a tus usuarios. Esto
      sirve únicamente para probar el flujo de firma y para que el aviso
      desaparezca en TU equipo si usas -TrustLocal.

    El certificado se crea en Cert:\CurrentUser\My. Con -TrustLocal también se
    copia a Cert:\CurrentUser\Root y Cert:\CurrentUser\TrustedPublisher, lo que
    hace que tu usuario confíe en cualquier binario firmado con esa clave.
    No lo uses en un equipo compartido.

.PARAMETER TrustLocal
    Instala el certificado como de confianza para el usuario actual.

.PARAMETER SkipBuild
    No recompila; firma los binarios existentes. Si firmas el .exe pero no
    reconstruyes el instalador, el instalador seguirá llevando el .exe anterior.

.PARAMETER Remove
    Elimina el certificado local y sus entradas de confianza.

.PARAMETER ExePath
    Ruta del ejecutable a firmar. Por defecto dist\MyBot\MyBot.exe.

.PARAMETER InstallerPath
    Ruta del instalador. Si se omite, se busca el más reciente en dist_installer.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\self_sign_local.ps1 -TrustLocal

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\self_sign_local.ps1 -Remove
#>
[CmdletBinding()]
param(
    [switch]$TrustLocal,
    [switch]$SkipBuild,
    [switch]$Remove,
    [string]$Subject = "CN=MyBot Local Test",
    [string]$ExePath = "dist\MyBot\MyBot.exe",
    [string]$InstallerPath = "",
    [string]$TimestampServer = "http://timestamp.digicert.com",
    [switch]$NoTimestamp
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Remove-CertificadoLocal {
    $almacenes = @(
        "Cert:\CurrentUser\My",
        "Cert:\CurrentUser\Root",
        "Cert:\CurrentUser\TrustedPublisher"
    )
    foreach ($almacen in $almacenes) {
        Get-ChildItem $almacen -ErrorAction SilentlyContinue |
            Where-Object { $_.Subject -eq $Subject } |
            ForEach-Object {
                Write-Host "Eliminando $($_.Thumbprint) de $almacen"
                Remove-Item -LiteralPath $_.PSPath -Force
            }
    }
}

if ($Remove) {
    Remove-CertificadoLocal
    Write-Host "Certificados de prueba eliminados." -ForegroundColor Green
    exit 0
}

function Get-Iscc {
    $candidatos = @(
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    return $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
}

function Invoke-FirmaLocal {
    param([string]$Ruta, [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificado)

    if (-not (Test-Path -LiteralPath $Ruta)) {
        throw "No existe el archivo a firmar: $Ruta"
    }

    $parametros = @{
        FilePath      = (Resolve-Path -LiteralPath $Ruta).Path
        Certificate   = $Certificado
        HashAlgorithm = "SHA256"
    }
    if (-not $NoTimestamp -and $TimestampServer) {
        $parametros.TimestampServer = $TimestampServer
    }

    Write-Host "== Firmando $Ruta =="
    $firma = Set-AuthenticodeSignature @parametros
    Write-Host "   Estado: $($firma.Status)"

    if ($firma.Status -eq "Valid") {
        Write-Host "   Firma válida y de confianza en este equipo." -ForegroundColor Green
    } elseif ($firma.Status -in @("UnknownError", "NotTrusted")) {
        Write-Warning "   La firma existe, pero el certificado no es de confianza en este equipo."
        Write-Warning "   Usa -TrustLocal si quieres que desaparezca el aviso SOLO en tu PC."
    } else {
        throw "No se pudo firmar '$Ruta' (estado: $($firma.Status))."
    }
}

# ---------------------------------------------------------------------------
# 1) Certificado
# ---------------------------------------------------------------------------
$cert = Get-ChildItem "Cert:\CurrentUser\My" -ErrorAction SilentlyContinue |
    Where-Object { $_.Subject -eq $Subject } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if (-not $cert -or $cert.NotAfter -lt (Get-Date).AddDays(30)) {
    Write-Host "== Creando certificado autofirmado de prueba =="
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $Subject `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyExportPolicy Exportable `
        -KeyUsage DigitalSignature `
        -NotAfter (Get-Date).AddYears(2)
    Write-Host "   Huella: $($cert.Thumbprint)"
} else {
    Write-Host "== Reutilizando certificado de prueba: $($cert.Thumbprint) =="
}

if ($TrustLocal) {
    Write-Warning "Instalando el certificado como de confianza SOLO para el usuario actual."
    Write-Warning "Cualquier archivo firmado con esta clave privada será aceptado por tu usuario."
    $cer = Join-Path $env:TEMP ("mybot_local_" + $cert.Thumbprint + ".cer")
    Export-Certificate -Cert $cert -FilePath $cer | Out-Null
    Import-Certificate -FilePath $cer -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null
    Import-Certificate -FilePath $cer -CertStoreLocation "Cert:\CurrentUser\TrustedPublisher" | Out-Null
    Remove-Item -LiteralPath $cer -Force
    Write-Host "   Certificado añadido a Root y TrustedPublisher." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 2) Compilación (opcional)
# ---------------------------------------------------------------------------
if (-not $SkipBuild) {
    Write-Host "== Compilando ejecutable =="
    python -m PyInstaller --noconfirm MyBot.spec
    if ($LASTEXITCODE -ne 0) { throw "Fallo PyInstaller." }
}

# ---------------------------------------------------------------------------
# 3) Firmar ejecutable
# ---------------------------------------------------------------------------
Invoke-FirmaLocal -Ruta $ExePath -Certificado $cert

# ---------------------------------------------------------------------------
# 4) Recompilar y firmar el instalador
# ---------------------------------------------------------------------------
if (-not $SkipBuild) {
    $iscc = Get-Iscc
    if ($iscc) {
        Write-Host "== Compilando instalador (contiene el .exe ya firmado) =="
        & $iscc installer.iss
        if ($LASTEXITCODE -ne 0) { throw "Fallo Inno Setup." }
    } else {
        Write-Warning "Inno Setup no encontrado: se omite el instalador."
    }
}

if (-not $InstallerPath -and -not $SkipBuild) {
    $ultimo = Get-ChildItem "dist_installer\MyBot_v*_Instalador.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($ultimo) { $InstallerPath = $ultimo.FullName }
}

if ($InstallerPath) {
    if (Test-Path -LiteralPath $InstallerPath) {
        Invoke-FirmaLocal -Ruta $InstallerPath -Certificado $cert
    } else {
        Write-Warning "No existe el instalador indicado: $InstallerPath"
    }
} elseif (-not $SkipBuild) {
    Write-Warning "No se encontró el instalador para firmar."
}

Write-Host ""
Write-Host "Firma local completada." -ForegroundColor Green
Write-Host "Recuerda: esto NO elimina SmartScreen en otros equipos." -ForegroundColor Yellow
Write-Host "Para quitar la confianza local: tools\self_sign_local.ps1 -Remove" -ForegroundColor Yellow
