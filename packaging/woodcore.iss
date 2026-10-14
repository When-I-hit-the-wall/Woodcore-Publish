; Woodcore's installer (docs/conventions/build-and-release.md §12, v0.83), compiled by packaging/build.py with Inno Setup 6:
;   ISCC.exe /DAppVersion=0.83.0 /DSourceDir=<the folder PyInstaller built> /DLauncherExe=<Woodcore-Launcher.exe> /DIconFile=<woodcore.ico> /DOutputDir=<Woodcore\dist> woodcore.iss
;
; Per user and without administrator rights, into %LOCALAPPDATA%\Programs\Woodcore\<version>\. Each version is an installation of its own -- its own AppId, its own entry in the list of installed programs, its own uninstaller -- so several stand side by side, and a project exported years ago opens again with the program that exported it. Beside them, in launcher\, Woodcore-Launcher.exe: what the .woodcore association and the Start menu start, and which picks the version (packaging/launcher.py). A version's installer puts the launcher there only when it is newer than the one there (its version resource); the last version uninstalled takes the launcher, the shortcut and the association with it ([Code]).

#ifndef AppVersion
  #error Compile through packaging/build.py, which names AppVersion, SourceDir, LauncherExe, IconFile and OutputDir
#endif

[Setup]
AppId=Woodcore-{#AppVersion}
AppName=Woodcore {#AppVersion}
AppVersion={#AppVersion}
AppVerName=Woodcore {#AppVersion}
AppPublisher=Florian Lamprecht
AppCopyright=© 2026 Florian Lamprecht
AppContact=woodcore@pineo.ch
AppPublisherURL=https://woodcore.pages.dev/
AppSupportURL=https://woodcore.pages.dev/
DefaultDirName={localappdata}\Programs\Woodcore\{#AppVersion}
DisableDirPage=yes
DisableProgramGroupPage=yes
UsePreviousAppDir=no
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=Woodcore-{#AppVersion}-setup
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\Woodcore.exe
UninstallDisplayName=Woodcore {#AppVersion}
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
WizardStyle=modern

[Languages]
; the licence each language's wizard shows, to be accepted before anything is installed (legal/, docs/conventions/build-and-release.md §12); the program carries the three and THIRD-PARTY-NOTICES.txt in its _internal\legal folder
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"; LicenseFile: "..\legal\LICENSE-fr.txt"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"; LicenseFile: "..\legal\LICENSE-de.txt"
Name: "en"; MessagesFile: "compiler:Default.isl"; LicenseFile: "..\legal\LICENSE-en.txt"

[CustomMessages]
fr.Associate=Ouvrir les fichiers .woodcore avec Woodcore (double-clic)
de.Associate=.woodcore-Dateien mit Woodcore öffnen (Doppelklick)
en.Associate=Open .woodcore files with Woodcore (double-click)
fr.ProjectType=Projet Woodcore
de.ProjectType=Woodcore-Projekt
en.ProjectType=Woodcore project
fr.Launch=Lancer Woodcore
de.Launch=Woodcore starten
en.Launch=Start Woodcore

[Tasks]
Name: "associate"; Description: "{cm:Associate}"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; the launcher and its icon are shared by every version installed: kept by an uninstaller, removed with the last version ([Code])
Source: "{#LauncherExe}"; DestDir: "{localappdata}\Programs\Woodcore\launcher"; Flags: uninsneveruninstall
Source: "{#IconFile}"; DestDir: "{localappdata}\Programs\Woodcore\launcher"; Flags: uninsneveruninstall

[Icons]
Name: "{userprograms}\Woodcore"; Filename: "{localappdata}\Programs\Woodcore\launcher\Woodcore-Launcher.exe"; IconFilename: "{localappdata}\Programs\Woodcore\launcher\woodcore.ico"; Flags: uninsneveruninstall
Name: "{userprograms}\Woodcore\Woodcore {#AppVersion}"; Filename: "{app}\Woodcore.exe"; Parameters: "--home"

; ⚠️ No `uninsneveruninstall` here: [Registry] has no such flag (Inno refuses the whole script), and a registry entry is kept at uninstall unless a uninsdelete* flag says otherwise -- which is what the shared association wants. The last version uninstalled removes it in [Code].
[Registry]
Root: HKCU; Subkey: "Software\Classes\.woodcore"; ValueType: string; ValueName: ""; ValueData: "Woodcore.Project"; Tasks: associate
Root: HKCU; Subkey: "Software\Classes\Woodcore.Project"; ValueType: string; ValueName: ""; ValueData: "{cm:ProjectType}"; Tasks: associate
Root: HKCU; Subkey: "Software\Classes\Woodcore.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{localappdata}\Programs\Woodcore\launcher\woodcore.ico"""; Tasks: associate
Root: HKCU; Subkey: "Software\Classes\Woodcore.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{localappdata}\Programs\Woodcore\launcher\Woodcore-Launcher.exe"" ""%1"""; Tasks: associate

[Run]
Filename: "{app}\Woodcore.exe"; Parameters: "--home"; Description: "{cm:Launch}"; Flags: nowait postinstall skipifsilent

[Code]
{ The last version uninstalled takes what every version shares: the launcher, its shortcut and the association. A version is still installed where its folder holds Woodcore.exe. }
function AnotherVersionInstalled(): Boolean;
var
  Found: TFindRec;
  Root: String;
begin
  Result := False;
  Root := ExpandConstant('{localappdata}\Programs\Woodcore\');
  if FindFirst(Root + '*', Found) then
  begin
    try
      repeat
        if (Found.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and (Found.Name <> '.') and (Found.Name <> '..')
           and (CompareText(Found.Name, 'launcher') <> 0)
           and (CompareText(Root + Found.Name, ExpandConstant('{app}')) <> 0)
           and FileExists(Root + Found.Name + '\Woodcore.exe') then
          Result := True;
      until Result or not FindNext(Found);
    finally
      FindClose(Found);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Kind: String;
begin
  if (CurUninstallStep = usPostUninstall) and not AnotherVersionInstalled() then
  begin
    DelTree(ExpandConstant('{localappdata}\Programs\Woodcore\launcher'), True, True, True);
    DeleteFile(ExpandConstant('{userprograms}\Woodcore.lnk'));
    RemoveDir(ExpandConstant('{userprograms}\Woodcore'));
    if RegQueryStringValue(HKCU, 'Software\Classes\.woodcore', '', Kind) and (Kind = 'Woodcore.Project') then
      RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\.woodcore');
    RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\Woodcore.Project');
    RemoveDir(ExpandConstant('{localappdata}\Programs\Woodcore'));
  end;
end;
