"""woodcore-cli.exe's first lines: the command line, run from the sources the build laid out beside the executable -- as Woodcore.exe's window is (entry_gui.py, v0.83). The window's «Importer Excel» runs this very program, `woodcore-cli.exe export --data-only`."""

import os
import sys

ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.path[0:0] = [os.path.join(ROOT, "calc", "tools"), os.path.join(ROOT, "calc")]

import cli  # noqa: E402

sys.exit(cli.main())
