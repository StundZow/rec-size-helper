; Rec Size Helper — Inno Setup script.
; Built via release.py, which passes /DMyAppVersion=<version>.
#ifndef MyAppVersion
  #define MyAppVersion "1.0"
#endif

#define MyAppName "Rec Size Helper"
#define MyAppPublisher "StundZow"
#define MyAppExeName "RecSizeHelper.exe"
#define MyAppURL "https://github.com/StundZow/rec-size-helper"

[Setup]
AppId={{B6C1B6B0-6C1E-4B7B-9C2A-6C6F2A7E4A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
; Per-user install (no admin/UAC prompt needed) so the app's own
; auto-updater can keep replacing its own exe without elevation.
DefaultDirName={localappdata}\Programs\RecSizeHelper
DefaultGroupName=Rec Size Helper
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=RecSizeHelperSetup
SetupIconFile=rechelper\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le Bureau"; GroupDescription: "Icônes supplémentaires :"; Flags: checkedonce

[Files]
Source: "dist\RecSizeHelper.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Rec Size Helper"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Désinstaller Rec Size Helper"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Rec Size Helper"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer Rec Size Helper"; Flags: nowait postinstall skipifsilent
