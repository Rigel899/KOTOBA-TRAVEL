#define AppName "Kotoba Travel"
#define AppVersion "1.0.0"
#define AppExeName "Kotoba Travel.exe"
#define ExeDir "dist"

[Setup]
AppId={{8F6A7C5E-3B2D-4F9A-8E1C-7D0B5A2F4C8D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Rigel899
AppPublisherURL=https://github.com/Rigel899/KOTOBA-TRAVEL
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename=KotobaTravel-Setup-v{#AppVersion}
OutputDir=dist
SetupIconFile=src\asset\image\icons\icona.ico
UninstallDisplayIcon={app}\{#AppExeName}
LicenseFile=LICENSE
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#ExeDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Disinstalla {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Avvia {#AppName}"; Flags: nowait postinstall skipifsilent
