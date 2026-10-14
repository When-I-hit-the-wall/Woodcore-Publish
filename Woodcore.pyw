"""Woodcore from its sources, double-clicked (v0.117): Windows runs a .pyw with pythonw, so no console window opens, not even for the instant a .bat takes -- what Woodcore.bat cannot avoid (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-008; docs/architecture/performance.md).

    Woodcore.pyw                              the start page
    Woodcore.pyw "D:\\...\\Musterprojekt.woodcore"   that project -- a .woodcore dropped on this file
    Woodcore.pyw --home                       the start page, whatever WOODCORE_PROJECT names

The start screen comes first (calc/tools/woodcore_start.py), as from Woodcore.exe and Woodcore.bat.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[0:0] = [os.path.join(HERE, "calc", "tools"), os.path.join(HERE, "calc")]

args = sys.argv[1:]
if not args:
    args = ["--home"]
elif not args[0].startswith("-"):
    args = ["--project", args[0], *args[1:]]   # a file dropped on this one, as Woodcore.bat passes it

import woodcore_start  # noqa: E402

woodcore_start.main([sys.argv[0], *args])
