#define MyAppName "MyBot"
#define MyAppVersion "1.3.1"
#define MyAppPublisher "i.am.lex"
#define MyAppURL "https://mybot-79861.web.app"
#define MyAppExeName "MyBot.exe"

[Setup]
AppId={{5E4A7D91-8C32-4F1E-9C8E-2B1A6D7E8F90}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Carpeta de destino predeterminada (con selector para cambiarla con "Examinar")
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Configuración del instalador
OutputDir=dist_installer
OutputBaseFilename=MyBot_v1.3.1_Instalador
SetupIconFile=assets\icono.ico
WizardImageFile=assets\wizard_left.bmp
WizardSmallImageFile=assets\wizard_small.bmp
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Permisos e iconos
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=1.3.1.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=MyBot v1.3.1 - Lector de Comentarios y Donaciones TikTok Live
VersionInfoProductName=MyBot
VersionInfoProductVersion=1.3.1.0

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; La aplicacion se empaqueta en modo "carpeta" (PyInstaller onedir): el modo
; "un solo .exe" descomprimia todo en cada arranque y tardaba ~25 s en abrir.
Source: "dist\MyBot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; La interfaz se sirve desde disco: asi se puede actualizar sin recompilar el .exe.
Source: "web\*"; DestDir: "{app}\web"; Flags: ignoreversion recursesubdirs createallsubdirs
; Las voces neuronales (.onnx, ~270 MB) NO se empaquetan: la app las descarga
; bajo demanda desde «Voz & Presets», lo que reduce el instalador drasticamente.
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "voices\*"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icono.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icono.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
{ MyBot renderiza la interfaz con el motor WebView2 de Windows (el mismo que usa
  Microsoft Edge). Si no estuviera disponible, la aplicacion no podria mostrar
  su ventana, asi que se avisa al usuario al terminar la instalacion. }
function WebView2Instalado(): Boolean;
var
  Version: String;
begin
  Result :=
    RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
    RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and (not WebView2Instalado()) then
    MsgBox('MyBot necesita el componente "Microsoft Edge WebView2 Runtime" para mostrar su ventana.' + #13#10 + #13#10 +
           'En Windows 10 y 11 suele venir instalado con Microsoft Edge. Si no es tu caso, descargalo gratis en:' + #13#10 +
           'https://developer.microsoft.com/microsoft-edge/webview2/',
           mbInformation, MB_OK);
end;
