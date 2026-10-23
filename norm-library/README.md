# norm-library — the norms shipped with Woodcore

The PDFs of the norms Woodcore is calculated against, copied from the root of the engineer's `When-I-hit-the-wall/norms` repository on 22.10.2026 (spec `docs/requirements/completed/2026-10-22-onglet-neige-type.md`, D-22, D-24) and frozen into the installer beside `calc/` (`packaging/woodcore.spec`). The engineer, 22.10.2026: «il est tout à fait acceptable d'avoir des extraits de norme ou des normes complètes livrées avec woodcore».

- **What is here**: every PDF of that repository's root, as it stands there, under the same name. Not its `Litteratur/` (handbooks, not norms), and not `SZS-C4-2021.pdf` (353 MB) and `SZS-C5-2018.pdf` (245 MB), which GitHub refuses outside Git LFS (the engineer's choice, 22.10.2026).
- **Who reads it**: `calc/norms/library.py` finds a file here through `project.APP_ROOT`, the same from the sources and installed; the norm file that cites an edition's pages names its file (`editions.<lang>.file`, read by `calc/norms/excerpts.py`). The window cuts an excerpt out of a page and opens a chapter (`calc/tools/excerpt_image.py`, `calc/tools/norm_reader.py`). Nothing here is ever copied into a project.
- **A new edition** is copied here under its library name and named by the norm file that reads it; an edition replaced stays until no norm file names it. `WOODCORE_NORMS_LIBRARY` names another folder for a test or a machine that keeps its own copy.

The rules this folder follows are `docs/architecture/reference-library.md` §11bis.
