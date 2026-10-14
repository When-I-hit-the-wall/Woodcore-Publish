"""The window's old file name, kept so that it still starts the window: woodcore_gui.py since v0.96, catalog_gui.py until then (docs/ui/window.md §10quater).

The launcher installed with Woodcore 0.83 to 0.90 starts the engineer's own sources by this path, `calc/tools/catalog_gui.py`, where *Fichier → Ouvrir les fichiers .woodcore avec ces sources* chose them (packaging/launcher.py, `launcher.dev_checkout`) -- and a launcher is replaced only by a newer one's installer, so a machine that installed nothing since goes on asking for this file. It runs woodcore_gui.py as the program, exactly as `python calc/tools/woodcore_gui.py` would: the same arguments, and woodcore_gui's own `__main__` block, which says in a window of its own where PySide6 is missing.

Nothing may import it: the window is `woodcore_gui`, and this file holds none of its names (tests/test_packaging.py).
"""

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().with_name("woodcore_gui.py")), run_name="__main__")
