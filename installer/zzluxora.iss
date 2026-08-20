; ============================================================
;  zzluxora v7 — Inno Setup installer script
;  Build: compile with Inno Setup Compiler (ISCC.exe zzluxora.iss)
;  Prereq: run `python build.py` first so dist\zzluxora\ exists.
; ============================================================

#define AppName "zzluxora"
#define AppVersion "7.0.0"
#define AppPublisher "UNNES"
#define AppExeName "zzluxora.exe"
; Fixed GUID so Windows treats every build as the same product (upgrade/uninstall).
#define AppId "{{9F3C1A77-2B4E-4D6A-9C21-7AE5C0B30007}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
; Install to Program Files (64-bit on x64 Windows, x86 on 32-bit).
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Output setup .exe
OutputDir=Output
OutputBaseFilename=zzluxora-setup-v{#AppVersion}
SetupIconFile=..\assets\zzluxora.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; 64-bit install mode when on x64
ArchitecturesInstallIn64BitMode=x64compatible
; Need admin to write Program Files
PrivilegesRequired=admin

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
; Clean install: wipe user data in AppData before copying. Unchecked by default
; (default = keep settings/fixtures across reinstalls).
Name: "cleandata"; Description: "Clean install — remove existing settings & data in AppData"; GroupDescription: "Data:"; Flags: unchecked

[Files]
; Copy the entire PyInstaller onedir output.
Source: "..\dist\zzluxora\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[InstallDelete]
; Wipe the install folder BEFORE copying so it's always fresh (anti-tumpuk).
Type: filesandordirs; Name: "{app}\*"

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
{ Clean install: if the user ticked "cleandata", remove %APPDATA%\zzluxora before install. }
procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: string;
begin
  if CurStep = ssInstall then
  begin
    if WizardIsTaskSelected('cleandata') then
    begin
      DataDir := ExpandConstant('{userappdata}\zzluxora');
      if DirExists(DataDir) then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;

{ Uninstall: ask whether to also delete settings & data in AppData. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: string;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\zzluxora');
    if DirExists(DataDir) then
    begin
      if MsgBox('Also delete your zzluxora settings and data (fixtures, scenes, chases, pages)?'
                + #13#10 + 'Choose No to keep them for a future reinstall.',
                mbConfirmation, MB_YESNO) = IDYES then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;
