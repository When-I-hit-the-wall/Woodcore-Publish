"""tests/bootstrap.py, the one command that prepares a machine for the whole suite (docs/conventions/testing.md §11ter; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-26-01, REQ-26-02; issue #26).

What it must never do is install a Typst whose archive is not the one recorded: the SHA-256 lives in typst-sha256.json, beside the version in typst-version.txt, and an archive that does not hash to it is refused before anything is written. And what it must do on a machine already prepared is nothing.
"""

import contextlib
import hashlib
import io
import json
import os
import tarfile
import zipfile

import conftest
from conftest import ROOT

import bootstrap


@contextlib.contextmanager
def _patched(**names):
    saved = {name: getattr(bootstrap, name) for name in names}
    for name, value in names.items():
        setattr(bootstrap, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(bootstrap, name, value)


def _tar_xz(folder, payload):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:xz") as archive:
        info = tarfile.TarInfo(f"{folder}/typst")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
        notice = b"licence"
        info = tarfile.TarInfo(f"{folder}/LICENSE")
        info.size = len(notice)
        archive.addfile(info, io.BytesIO(notice))
    return buffer.getvalue()


def _zip(folder, payload):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"{folder}/typst.exe", payload)
    return buffer.getvalue()


def test_the_pinned_version_has_a_recorded_hash_for_every_archive_the_bootstrap_may_fetch():
    version = bootstrap.pinned()
    assert version == (ROOT / "typst-version.txt").read_text(encoding="utf-8").strip()
    recorded = json.loads((ROOT / "typst-sha256.json").read_text(encoding="utf-8"))["versions"]
    assert version in recorded, f"typst-sha256.json records no hash for Typst {version}: run `python tests/bootstrap.py --record-hashes {version}`"
    for asset in sorted(set(bootstrap.ASSETS.values())):
        digest = recorded[version].get(asset)
        assert digest and len(digest) == 64 and int(digest, 16) >= 0, (asset, digest)


def test_the_archive_is_the_one_typst_publishes_for_the_platform():
    assert bootstrap.asset_name("Linux", "x86_64") == "typst-x86_64-unknown-linux-musl.tar.xz"
    assert bootstrap.asset_name("Linux", "aarch64") == "typst-aarch64-unknown-linux-musl.tar.xz"
    assert bootstrap.asset_name("Windows", "AMD64") == "typst-x86_64-pc-windows-msvc.zip"
    assert bootstrap.asset_name("Darwin", "arm64") == "typst-aarch64-apple-darwin.tar.xz"
    try:
        bootstrap.asset_name("Plan9", "mips")
    except bootstrap.BootstrapError as exc:
        assert "plan9" in str(exc)
    else:
        raise AssertionError("an archive was named for a platform Typst does not build")


def test_typst_is_installed_only_when_its_archive_hashes_to_the_recorded_sha256():
    folder = conftest.tmpdir("bootstrap-typst")
    payload = b"#!/bin/sh\necho 'typst 9.9.9 (test)'\n"
    asset = "typst-x86_64-unknown-linux-musl.tar.xz"
    data = _tar_xz("typst-x86_64-unknown-linux-musl", payload)
    hashes = folder / "typst-sha256.json"
    hashes.write_text(json.dumps({"versions": {"9.9.9": {asset: hashlib.sha256(data).hexdigest()}}}), encoding="utf-8")
    asked = []

    def download(url):
        asked.append(url)
        return data

    target = bootstrap.install_typst("9.9.9", folder / "bin", asset=asset, hash_file=hashes, download=download)
    assert asked == ["https://github.com/typst/typst/releases/download/v9.9.9/" + asset], asked
    assert target == folder / "bin" / "typst" and target.read_bytes() == payload
    if os.name != "nt":
        assert os.access(target, os.X_OK), "the executable is not executable"

    # an archive that is not the one recorded: refused, nothing written
    other = folder / "other"
    try:
        bootstrap.install_typst("9.9.9", other, asset=asset, hash_file=hashes, download=lambda url: data + b"x")
    except bootstrap.BootstrapError as exc:
        assert "SHA-256" in str(exc) and "refused" in str(exc)
    else:
        raise AssertionError("an archive whose hash is not the recorded one was installed")
    assert not (other / "typst").exists()

    # a version with no recorded hash: refused before anything is downloaded
    asked.clear()
    try:
        bootstrap.install_typst("9.9.8", other, asset=asset, hash_file=hashes, download=download)
    except bootstrap.BootstrapError as exc:
        assert "--record-hashes 9.9.8" in str(exc)
    else:
        raise AssertionError("a Typst with no recorded hash was installed")
    assert asked == [], "an archive was downloaded with no hash to check it against"

    # Windows' archive is a zip holding typst.exe
    zipped = _zip("typst-x86_64-pc-windows-msvc", payload)
    assert bootstrap.extract(zipped, "typst-x86_64-pc-windows-msvc.zip") == payload


def test_recording_hashes_writes_one_per_archive_and_keeps_the_others():
    folder = conftest.tmpdir("bootstrap-record")
    hashes = folder / "typst-sha256.json"
    hashes.write_text(json.dumps({"about": "kept", "versions": {"1.0.0": {"a": "b"}}}), encoding="utf-8")
    recorded = bootstrap.record_hashes("2.0.0", hash_file=hashes, download=lambda url: url.encode())
    data = json.loads(hashes.read_text(encoding="utf-8"))
    assert data["about"] == "kept" and data["versions"]["1.0.0"] == {"a": "b"}
    assert set(data["versions"]["2.0.0"]) == set(bootstrap.ASSETS.values()) == set(recorded)
    url = bootstrap.DOWNLOAD.format(version="2.0.0", asset="typst-x86_64-pc-windows-msvc.zip")
    assert data["versions"]["2.0.0"]["typst-x86_64-pc-windows-msvc.zip"] == hashlib.sha256(url.encode()).hexdigest()


def test_the_packages_and_qt_s_libraries_are_compared_with_what_is_pinned():
    pins = dict(bootstrap.pins())
    assert "PySide6" in pins and "openpyxl" in pins, pins
    installed = dict(pins, openpyxl="0.0.1")
    installed.pop("ezdxf")
    wrong = bootstrap.package_mismatches(version_of=installed.get)
    assert sorted(wrong) == sorted([("openpyxl", pins["openpyxl"], "0.0.1"), ("ezdxf", pins["ezdxf"], None)]), wrong
    assert bootstrap.package_mismatches(version_of=pins.get) == []
    assert bootstrap.missing_qt_packages(find=lambda name: None, system="Windows") == [], "apt is a Linux question"
    assert bootstrap.missing_qt_packages(find=lambda name: None if name == "EGL" else f"lib{name}.so", system="Linux") == ["libegl1"]


def test_a_machine_already_prepared_installs_nothing_on_a_second_call():
    version = bootstrap.pinned()

    def refuse(*_args, **_kwargs):
        raise AssertionError("installed something on a prepared machine")

    out = io.StringIO()
    with _patched(package_mismatches=lambda *a, **k: [], missing_qt_packages=lambda *a, **k: [], found_typst=lambda prefix: ("/x/typst", version),
                  install_packages=refuse, install_qt_packages=refuse, install_typst=refuse,
                  examples_engine_stale=lambda *a, **k: False, refresh_examples_engine=refuse), contextlib.redirect_stdout(out):
        assert bootstrap.main([]) == 0
        assert bootstrap.main(["--check"]) == 0
    assert "already up to date: nothing installed" in out.getvalue(), out.getvalue()

    # --check on a machine that lacks Typst: says so, installs nothing, exit 1
    out = io.StringIO()
    with _patched(package_mismatches=lambda *a, **k: [], missing_qt_packages=lambda *a, **k: [], found_typst=lambda prefix: (None, None),
                  install_typst=refuse, examples_engine_stale=lambda *a, **k: False), contextlib.redirect_stdout(out):
        assert bootstrap.main(["--check"]) == 1
    assert f"missing -- Typst {version}" in out.getvalue(), out.getvalue()


def test_the_engine_s_copy_beside_the_examples_is_written_where_a_clone_has_none_or_an_old_one():
    """`examples/lib/` is generated and not versioned: a clone has none, and test_commands compiles the frozen examples against it. The bootstrap writes it by build_examples.refresh_engine where it is missing or not today's lib/."""
    root = conftest.tmpdir("bootstrap-examples")
    (root / "lib").mkdir()
    (root / "lib" / "calc-engine.typ").write_text("// today\n", encoding="utf-8")
    assert bootstrap.examples_engine_stale(root), "a clone has no copy"
    (root / "examples" / "lib").mkdir(parents=True)
    (root / "examples" / "lib" / "calc-engine.typ").write_text("// yesterday\n", encoding="utf-8")
    (root / "examples" / "commands.typ").write_text("", encoding="utf-8")
    assert bootstrap.examples_engine_stale(root), "a copy of another lib/"
    (root / "examples" / "lib" / "calc-engine.typ").write_text("// today\n", encoding="utf-8")
    assert not bootstrap.examples_engine_stale(root)
    called = []
    bootstrap.refresh_examples_engine(ROOT, run=lambda command, **kw: called.append(command) or type("Done", (), {"returncode": 0})())
    assert "build_examples.refresh_engine()" in called[0][2], "the one function that writes it, not a second copy of it"


def test_claude_code_s_cloud_sessions_call_the_same_command_and_the_engineer_s_machine_does_not():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    commands = [hook["command"] for entry in settings["hooks"]["SessionStart"] for hook in entry["hooks"]]
    assert len(commands) == 1 and "tests/bootstrap.py" in commands[0], commands
    assert '"$CLAUDE_CODE_REMOTE" = "true"' in commands[0], "the hook must stand down outside a cloud session"
