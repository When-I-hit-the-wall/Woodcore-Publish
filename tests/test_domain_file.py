"""One `.typ` per domain of a specialised tab (calc/domains/domain_file.py, issue #64, spec 2026-10-15-structure-projet-dossiers REQ-004, REQ-010, REQ-015, ARCH-004; spec 2026-10-21-commandes-typst-refonte, ARCH-011).

In a project laid out by folders every domain a specialised tab makes has a file of its own in its kind's folder, the domain written out by calc/domains/unfold.py; the file is the engineer's once written. Woodcore writes no stub any more, and knows the stubs an earlier version wrote, to write over them or archive them. These hold the folders, the one reconciliation that archives and says (`sync`) -- idempotent, nothing in a project laid out before --, and that a domain's file compiles once its domain is exported.
"""

import json
import subprocess

import conftest

import documents
import project
import project_template
from domains import domain_file, member_check, snow_source


def _project(name):
    here = project_template.create(conftest.tmpdir(name) / "Halle", "Halle")
    assert here.has_folders
    return here


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_a_domain_file_lies_in_its_kind_s_folder_and_a_stub_of_an_earlier_woodcore_is_known_byte_for_byte():
    """A domain's file is in its kind's folder; Woodcore writes no stub any more (spec 2026-10-21-commandes-typst-refonte, ARCH-011) and knows the ones an earlier version wrote, to write over them (calc/domains/unfold.py LEGACY_STUBS)."""
    from domains import unfold
    here = _project("domain_file_text")
    head = documents.root_import_line(here)
    assert head == '#import "/000-Typst-Config/commands.typ": *'
    assert domain_file.path_of(here, "snow-load", "neige") == here.root / "Variable-loads" / "Snow" / "neige.typ"
    assert domain_file.path_of(here, "check", "ZT-01", "tension") == here.root / "Timber-checks" / "Tension" / "ZT-01.typ"
    assert domain_file.include_call(here, "snow-load", "neige") == '#include "/Variable-loads/Snow/neige.typ"'
    assert set(unfold.LEGACY_STUBS) == set(project.DOMAIN_FOLDERS) - {"live-load"}, "every kind an earlier Woodcore gave a stub is known, and the live loads, never stubbed"
    path = domain_file.path_of(here, "snow-load", "neige")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + '\n\n#show-calc("snow-load", "neige")\n', encoding="utf-8", newline="\n")
    assert unfold.is_legacy_stub(here, "snow-load", "neige", path)
    assert not unfold.is_legacy_stub(here, "snow-load", "neu", path), "a stub is its own domain's"
    path.write_text(head + '\n\n#show-calc("snow-load", "neige")\nMon texte.\n', encoding="utf-8", newline="\n")
    assert not unfold.is_legacy_stub(here, "snow-load", "neige", path), "a stub written in is the engineer's"


def test_sync_writes_nothing_archives_an_untouched_stub_whose_domain_is_gone_and_leaves_an_edited_file():
    here = _project("domain_file_sync")
    head = documents.root_import_line(here)
    _write_json(snow_source.folder(here) / "neige.json", snow_source.new_source("neige"))
    assert domain_file.sync(here) == ([], []), "a domain's file is written out by calc/domains/unfold.py, never by the reconciliation"
    snow = here.root / "Variable-loads" / "Snow" / "alt.typ"
    snow.parent.mkdir(parents=True, exist_ok=True)
    snow.write_text(head + '\n\n#show-calc("snow-load", "alt")\n', encoding="utf-8", newline="\n")
    # a stub an earlier Woodcore wrote, of a domain that is gone: it follows it into archives/
    archived, notes = domain_file.sync(here)
    assert archived == [snow.parent / "archives" / "alt.typ"] and not snow.exists() and notes == []
    assert domain_file.sync(here) == ([], []), "a second reconciliation does nothing"
    # a file of the engineer's: never archived, said
    tension = here.root / "Timber-checks" / "Tension" / "ZT-01.typ"
    tension.parent.mkdir(parents=True, exist_ok=True)
    tension.write_text(head + "\n\nMon texte.\n", encoding="utf-8")
    archived, notes = domain_file.sync(here)
    assert archived == [] and tension.is_file()
    assert [note.code for note in notes] == ["domain_file_orphan"] and "Timber-checks/Tension/ZT-01.typ" in str(notes[0])


def test_a_project_laid_out_before_has_no_domain_files():
    here = project.write(conftest.tmpdir("domain_file_legacy") / "Alt.woodcore", "Alt", conftest.legacy_modes_layout("de"))
    _write_json(snow_source.folder(here) / "neige.json", snow_source.new_source("neige"))
    assert domain_file.sync(here) == ([], [])
    assert domain_file.path_of(here, "snow-load", "neige") is None and domain_file.include_call(here, "snow-load", "neige") is None


def test_a_domain_file_compiles_once_its_domain_is_exported():
    """The criterion of REQ-004: the snow load `neige` made in the «Neige» tab is printed by what includes its file -- the export writes the domain out, Typst prints it."""
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    here = _project("domain_file_compile")
    _write_json(snow_source.folder(here) / "neige.json", snow_source.new_source("neige"))
    import export_all
    with project.using(here):
        export_all.run()
    path = here.root / "Variable-loads" / "Snow" / "neige.typ"
    assert path.is_file(), "the export writes the domain of a load that has no file"
    probe = here.typst_root / "probe-neige.typ"
    probe.write_text(documents.root_import_line(here) + '\n#include domain-file("snow-load", "neige")\n', encoding="utf-8")
    run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(probe.with_suffix(".pdf"))],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr


def test_a_check_s_stub_is_unfolded_over_and_an_edited_one_is_kept_and_said():
    """REQ-015, D-16: a tension's stub, as an earlier Woodcore wrote it, is written over by its unfolded domain, which the export then names (`file`); a file the engineer wrote in is left as it is and said (`unfold_stub_edited`)."""
    import shutil
    from domains import unfold
    here = conftest.project_copy("domain_file_unfold")
    shutil.copytree(conftest.PROJECT.config_dir, here.config_dir, dirs_exist_ok=True)
    project.sync_engine(here)
    first, second = unfold.domain_path(here, "ZT-01"), unfold.domain_path(here, "ZT-02")
    head = documents.root_import_line(here)
    first.parent.mkdir(parents=True, exist_ok=True)
    first.write_text(head + '\n\n#show-check-member("ZT-01")\n', encoding="utf-8", newline="\n")
    second.write_text(head + '\n\n#show-check-member("ZT-02")\nMon texte.\n', encoding="utf-8", newline="\n")
    assert first == here.root / "Timber-checks" / "Tension" / "ZT-01.typ" and unfold.is_legacy_stub(here, "check", "ZT-01", first)
    checks = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))
    notes = []
    written = unfold.unfold_checks(here, checks, "de", notes=notes)
    assert "ZT-01" in written and "ZT-02" not in written and unfold.is_domain_file(first), "the untouched stub is written over"
    assert "Mon texte." in second.read_text(encoding="utf-8") and not unfold.is_domain_file(second), "the edited stub is kept"
    assert [note.code for note in notes] == ["unfold_stub_edited"] and "ZT-02" in str(notes[0])
    files = unfold.unfolded_files(here, checks)
    assert files["ZT-01"] == "/Timber-checks/Tension/ZT-01.typ" and "ZT-02" not in files, files


def test_the_domains_tab_groups_an_unfolded_check_by_its_kind():
    """REQ-016: the «Domaines» tab lists the engineer's domains and, in a group of their own named by their kind in the window's language, the checks unfolded -- no stub among them."""
    import types
    from domains import formula_domain as fd
    import sys
    tools = str(conftest.CALC / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import formula_tab_domains
    here = conftest.PROJECT
    listed = {d.id: d for d in fd.list_domains(here)}
    # every domain Woodcore writes out is one since the spec 2026-10-21-commandes-typst-refonte (REQ-017): a compression, a connector, a load
    assert {"poutre-p1", "ZT-01", "DR-01", "SD-10", "SL"} <= set(listed), sorted(listed)
    assert fd.group_of(here, listed["poutre-p1"]) is None and fd.group_of(here, listed["ZT-01"]) == ("check", "tension")
    for lang, word in (("fr", "Traction"), ("de", "Zug"), ("en", "Tension")):
        tab = types.SimpleNamespace(app=types.SimpleNamespace(lang=lang), t=lambda key, **values: key)
        assert formula_tab_domains.FormulaDomainsMixin.group_label(tab, ("check", "tension")) == word, lang


def test_a_script_lies_in_scripts_beside_its_domain_and_runs_from_there():
    """REQ-010: laid out by folders a script is `Scripts/<id>.py`, beside the `.typ` that prints it -- its domain written out (spec 2026-10-21-commandes-typst-refonte, REQ-017) --, and it is that file the export runs."""
    from domains import script, unfold
    here = conftest.PROJECT
    paths = script.source_paths(here)
    assert paths and all(path.parent == here.root / "Scripts" for path in paths), paths
    for path in paths:
        typ = path.with_suffix(".typ")
        assert typ.is_file() and unfold.is_domain_file(typ), typ
    report = script.run(paths[0], results_only=True)
    assert report is not None
