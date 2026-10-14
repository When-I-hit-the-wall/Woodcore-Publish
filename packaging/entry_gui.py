"""Woodcore.exe's first lines: the window, run from the sources the build laid out beside the executable (packaging/woodcore.spec, v0.83).

The program's modules are not frozen into PyInstaller's archive: they are shipped as they are in the checkout, under `_internal/calc/`, and imported from there -- so every path a module derives from its own file, a norm's JSON beside its reader, the glossary beside strings.py, the schemas beside calc/, is the path it has in the checkout, and nothing in calc/ needs to know it is frozen but project.py, which asks `sys.frozen` once.
"""

import os
import sys

ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.path[0:0] = [os.path.join(ROOT, "calc", "tools"), os.path.join(ROOT, "calc")]

# The start screen first, before the window's modules are imported (calc/tools/woodcore_start.py, v0.117): it imports woodcore_gui itself and calls its main().
import woodcore_start  # noqa: E402

woodcore_start.main()
