#define MyAppName "MyBot"
#define MyAppVersion "1.2"
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
OutputBaseFilename=MyBot_v1.2_Instalador
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
VersionInfoVersion=1.2.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=MyBot v1.2 - Lector de Comentarios y Donaciones TikTok Live
VersionInfoProductName=MyBot
VersionInfoProductVersion=1.2.0.0

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\MyBot.exe"; DestDir: "{app}"; Flags: ignoreversion
; Las voces neuronales (.onnx, ~270 MB) NO se empaquetan: la app las descarga
; bajo demanda desde «Voz & Presets», lo que reduce el instalador a ~1/5.
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "voices\*"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icono.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icono.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
