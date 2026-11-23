; Script optimizado para preservar estructura de directorios
#define MyAppName "StockSync"
#define MyAppVersion "2025.4.0"
#define MyAppPublisher "LECE systems"
#define MyAppURL "https://www.GrupoLECE.com/"
#define MyAppExeName "LECECOM.exe"

[Setup]
AppId={{B4A06D25-87AB-46ED-BA69-81E0160E326B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest
DisableDirPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=D:\One Drive\OneDrive\Escritorio\instaler
OutputBaseFilename=StockSync
SetupIconFile=C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\assets\icons\icono_app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; ========== ARCHIVOS PRINCIPALES ========== ;
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\.env"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\update_config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\modules\actualizando.ui"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\modules\*"; DestDir: "{app}\modules"; Flags: ignoreversion recursesubdirs createallsubdirs

; ========== ESTRUCTURA DE DIRECTORIOS ========== ;
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\modules\*"; DestDir: "{app}\modules"; Flags: recursesubdirs createallsubdirs
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\model\*"; DestDir: "{app}\model"; Flags: recursesubdirs createallsubdirs
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\Documents\*"; DestDir: "{app}\Documents"; Flags: recursesubdirs createallsubdirs
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\data\*"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs
Source: "C:\Users\Eleazar Leyte Zarate\Documents\Work_Space\Nueva_APP\assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent