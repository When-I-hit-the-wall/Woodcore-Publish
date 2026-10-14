# -*- mode: python ; coding: utf-8 -*-
# Woodcore-Launcher.exe (packaging/launcher.py, v0.83): one file, standard library only -- what the .woodcore association and the Start menu start. One file rather than a folder, so that an older installer run after a newer one keeps the newer launcher whole: Inno Setup compares the version resource of one executable, and a folder of them could end up half of each. Run by packaging/build.py, which sets WOODCORE_BUILD_WORK.

import os
from pathlib import Path

WORK = Path(os.environ["WOODCORE_BUILD_WORK"])

launcher = Analysis(
    [str(Path(SPECPATH) / "launcher.py")],
    excludes=["tkinter", "PySide6", "openpyxl", "pypdf", "unittest", "pydoc", "xml", "email", "http", "multiprocessing", "sqlite3"],
    noarchive=False,
)
EXE(
    PYZ(launcher.pure), launcher.scripts, launcher.binaries, launcher.datas, [],
    name="Woodcore-Launcher", console=False,
    icon=str(WORK / "woodcore.ico"), version=str(WORK / "version-launcher.txt"), upx=False,
)
