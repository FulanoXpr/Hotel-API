; Inno Setup Script for Hotel Price Checker
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php
;
; Build steps:
;   1. Run: python build_exe.py
;   2. Run: iscc installer.iss
;
; Output: dist/HotelPriceChecker-Setup.exe

#define MyAppName "Hotel Price Checker"
#define MyAppVersion "1.2.2"
#define MyAppPublisher "Foundation for Puerto Rico"
#define MyAppURL "https://github.com/FulanoXpr/Hotel-API"
#define MyAppExeName "HotelPriceChecker.exe"

[Setup]
; Unique identifier for this application (generate new GUID for different apps)
AppId={{8F4E9A7B-3C2D-4E5F-A1B2-C3D4E5F6A7B8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output configuration
OutputDir=dist
OutputBaseFilename=HotelPriceChecker-Setup
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Installer appearance
WizardStyle=modern
; Privileges (per-user install doesn't require admin)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Application icon
SetupIconFile=ui\assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files from PyInstaller output
Source: "dist\HotelPriceChecker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Note: Don't include source files, only the built distribution

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Custom code to handle .env file preservation during upgrades
procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFile: string;
  EnvBackup: string;
begin
  EnvFile := ExpandConstant('{app}\.env');
  EnvBackup := ExpandConstant('{app}\.env.backup');

  if CurStep = ssInstall then
  begin
    // Backup existing .env before install
    if FileExists(EnvFile) then
      CopyFile(EnvFile, EnvBackup, False);
  end
  else if CurStep = ssPostInstall then
  begin
    // Restore .env after install
    if FileExists(EnvBackup) then
    begin
      CopyFile(EnvBackup, EnvFile, False);
      DeleteFile(EnvBackup);
    end;
  end;
end;
