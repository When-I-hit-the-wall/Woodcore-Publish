"""The examples' index of the domains names no file the examples do not hold (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-017, defect 11): `examples/data/formulas.json` announced `poutre-p1` while `examples/` had no `Domains/` -- calc/tools/build_examples.py `freeze` now copies every file the index names.
"""

TIER = "fast"

import json

from conftest import ROOT

EXAMPLES = ROOT / "examples"


def test_every_domain_the_index_names_is_a_file_of_the_examples():
    data = json.loads((EXAMPLES / "data" / "formulas.json").read_text(encoding="utf-8"))
    missing = sorted(f"{fid}: {entry['file']}" for fid, entry in data["domains"].items() if not (EXAMPLES / entry["file"]).is_file())
    assert not missing, "examples/data/formulas.json names files examples/ does not hold:\n  " + "\n  ".join(missing)
    assert "poutre-p1" in data["domains"]
