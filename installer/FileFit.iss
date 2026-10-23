; Inno Setup script: turns dist\FileFit\ into dist\FileFit-Setup.exe
; Build:  iscc /DAppVersion=1.0.0 installer\FileFit.iss
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppName "FileFit"
#define AppExe "FileFit.exe"

[Setup]
AppId={{6F3B2C1E-9A7D-4E58-B0C4-5D2A8F1E7C93}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Dipanjan Banerjee
AppContact=dipanjanbanerjee20@gmail.com
AppPublisherURL=https://dipanjanbanerjee.github.io/filefit/
AppSupportURL=https://github.com/dipanjanbanerjee/filefit/issues
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Installs for the current user without asking for admin; the user can choose "all users".
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=FileFit-Setup
SetupIconFile=..\filefit\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\LICENSE

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "openwith"; Description: "Show FileFit in the right-click ""Open with"" menu for pictures, PDF and DOCX"; GroupDescription: "Extras:"

[Files]
Source: "..\dist\FileFit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".jpg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".jpeg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".png"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".webp"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".heic"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".pdf"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".docx"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.jpg\OpenWithList\{#AppExe}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.jpeg\OpenWithList\{#AppExe}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.png\OpenWithList\{#AppExe}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.pdf\OpenWithList\{#AppExe}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.docx\OpenWithList\{#AppExe}"; Flags: uninsdeletekey; Tasks: openwith

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; FileFit's own "Update now" runs this installer silently with /UPDATE=1; start FileFit again afterwards.
Filename: "{app}\{#AppExe}"; Flags: nowait runasoriginaluser; Check: IsSelfUpdate

[Code]
function IsSelfUpdate: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:UPDATE|0}') = '1');
end;
