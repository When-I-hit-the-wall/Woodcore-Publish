@echo off
rem woodcore-cli: the report built from a terminal (docs/conventions/build-and-release.md §12) -- in place of the build.ps1 and the Makefile the project folder carried until v0.82; woodcore-cli.exe beside an installed Woodcore is the same program.
rem   woodcore-cli export --project "..\Musterprojekt\Musterprojekt.woodcore" [--level N | --uniform N] [--lang fr] [--all-levels] [--skip-data | --data-only]
rem   woodcore-cli check  --project ...
rem   woodcore-cli sync-engine --project ... [--update]
rem   woodcore-cli new "D:\...\Halle Nord" [--name ...] [--number ...] [--client ...] [--company ...] [--author ...]
python "%~dp0calc\cli.py" %*
