@echo off
rem Woodcore run from its sources (docs/ui/window.md §10quater) -- what the installed Woodcore.exe does, without being installed.
rem   Woodcore.bat                               the start page: the recent projects, Open, New project, Convert an old folder
rem   Woodcore.bat "D:\...\Musterprojekt.woodcore"    that project -- a .woodcore dropped on this file, or double-clicked once the launcher is told to use these sources (File menu)
rem   Woodcore.bat --home                        the start page, whatever WOODCORE_PROJECT names
rem pythonw opens the window without a console; python is the fallback where only it is on PATH.
set "TOOL=%~dp0calc\tools\woodcore_gui.py"
if "%~1"=="" (
  where pythonw >nul 2>nul && (start "" pythonw "%TOOL%" --home) || (start "" python "%TOOL%" --home)
) else if "%~1"=="--home" (
  where pythonw >nul 2>nul && (start "" pythonw "%TOOL%" --home) || (start "" python "%TOOL%" --home)
) else (
  where pythonw >nul 2>nul && (start "" pythonw "%TOOL%" --project "%~1") || (start "" python "%TOOL%" --project "%~1")
)
