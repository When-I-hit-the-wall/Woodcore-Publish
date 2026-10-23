"""The norms shipped with Woodcore: the PDF of an edition, found in `norm-library/` beside the program (spec 2026-10-22-onglet-neige-type, ARCH-013, ARCH-014, D-22, D-24; docs/architecture/reference-library.md §11bis).

The engineer, 22.10.2026: «il est tout à fait acceptable d'avoir des extraits de norme ou des normes complètes livrées avec woodcore». Every norm of his `norms` repository -- its root, not its `Litteratur/` -- is copied into `norm-library/` at the top of the program's sources and frozen into the installer beside `calc/` (packaging/woodcore.spec), so the same path serves the sources and the installed program: `project.APP_ROOT`. It is not under `calc/norms/`, part of which every project copies (`project.ENGINE_FILES`): no PDF ever goes into a project.

Which file an edition is is said by the norm file that cites its pages (`editions.<lang>.file`, calc/norms/excerpts.py), never here. `WOODCORE_NORMS_LIBRARY` names another folder, for a test or a machine that keeps its own copy. No Qt here: the window renders a page (calc/tools/excerpt_image.py), this module only says where it is.
"""

import os
from pathlib import Path

FOLDER = "norm-library"
ENV = "WOODCORE_NORMS_LIBRARY"


def folder():
    """The folder of the shipped norms: `WOODCORE_NORMS_LIBRARY` where it is set, else `norm-library/` beside the program."""
    named = os.environ.get(ENV)
    if named:
        return Path(named)
    import project
    return project.APP_ROOT / FOLDER


def pdf(file):
    """The path of the norm's PDF `file` (`SIA261-2020-FR.pdf`), or None where it is not there -- a partial clone, an edition not shipped: the caller shows what it has without it (REQ-004)."""
    if not file:
        return None
    path = folder() / file
    return path if path.is_file() else None
