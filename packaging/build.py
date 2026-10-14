"""Builds Woodcore's installed program (docs/conventions/build-and-release.md §12, v0.83): Woodcore.exe and woodcore-cli.exe in one folder, the launcher, and the installer.

    python packaging/build.py                          the folder, the launcher, checked, then the installer (or a zip without Inno Setup)
    python packaging/build.py --compare <p.woodcore>   and a copy of that project exported by the sources and by the built program, compared
    python packaging/build.py --no-installer           stop after the checks

Made on demand, never on every change: the engineer works from the sources (Woodcore.bat), and a build is a version handed to someone -- a colleague, a machine without Python -- or kept. **A new version is built by itself** (v0.87): the commit that changes VERSION in calc/project.py starts this very script on a clean checkout of that commit, in the background, and its installer lands in dist/ beside `build-<version>.log` (packaging/auto_build.py, packaging/hooks/post-commit). What it does, in order:

0. **One build at a time.** `%LOCALAPPDATA%\\Woodcore\\build\\build.lock` names the build that runs: its working folders and the program's folder are every build's, and a second build would remove the first one's work under it. A lock left by a build that no longer runs is taken over.

1. **Its own interpreter.** PyInstaller is not one of the report's dependencies (requirements.txt); it lives in a virtual environment of its own, `%LOCALAPPDATA%\\Woodcore\\build\\venv`, holding requirements.txt and `packaging/requirements-build.txt` and nothing else. The first run creates it -- PySide6 is a download of some 250 MB -- and every run starts again inside it.
2. **What is frozen is what the report was verified with.** The packages installed must be the versions requirements.txt pins, and `typst --version` the one it names -- else nothing is built.
3. **What produced the build**, `build-info.json`: the version, `git describe --always --dirty` of the sources, the date, Python's and Typst's versions -- what an installed program writes into data/project.json where a checkout writes its git revision (calc/project.py source_revision).
4. **PyInstaller**, twice -- after putting the engine's copy beside the frozen examples where the checkout has none, as a clean checkout never has (`examples/lib/` is generated and not versioned, docs/typst/command-docs.md §10sexies), so that the commands tab of the installed program can compile an example whose page is missing: `woodcore.spec` (the two executables, the program's sources beside them, typst.exe) and `launcher.spec` (one file). Their working folders and the program's folder are under `%LOCALAPPDATA%\\Woodcore\\build\\`, outside NextCloud; only what is handed over lands in `Woodcore\\dist\\`, which git ignores.
5. **Checked**: woodcore-cli.exe exports and compiles a copy of the example project with the Typst inside it; Woodcore.exe opens it (`--self-test`); the launcher picks a version (`--dry-run`); with `--compare`, a copy of a real project is exported by the sources and by woodcore-cli.exe and the two data/ folders must be identical to the byte.
6. **The installer**, with Inno Setup 6 where it is installed (`ISCC.exe`): `dist\\Woodcore-<version>-setup.exe`. Without it, `dist\\Woodcore-<version>-win64.zip` -- the folder as it is, to unpack and run -- and the line that installs Inno Setup.
"""

import argparse
import atexit
import datetime
import json
import os
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CALC = ROOT / "calc"
sys.path[0:0] = [str(CALC / "tools"), str(CALC)]

import project  # noqa: E402
import project_lock  # noqa: E402
import dependencies  # noqa: E402
sys.path.insert(0, str(HERE))
import notices  # noqa: E402

LOCAL = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Woodcore" / "build"
VENV = LOCAL / "venv"
WORK = LOCAL / "work"
DIST = ROOT / "dist"
LOCK = LOCAL / "build.lock"          # the build that runs (step 0); packaging/auto_build.py reads it before starting one
LOCK_HELD = "WOODCORE_BUILD_LOCK"    # the pid holding it, handed to the build started again inside its own environment (ensure_interpreter)
EXAMPLES = ROOT / "examples"
TYPST_VERSION = (ROOT / "typst-version.txt").read_text(encoding="utf-8").strip()   # the Typst the report was verified with, read off its one file (v0.117)


def say(text):
    print(f"build: {text}", flush=True)


def fail(text):
    print(f"build: {text}", file=sys.stderr, flush=True)
    sys.exit(1)


def venv_python():
    return VENV / "Scripts" / "python.exe"


def read_lock():
    try:
        record = json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def take_lock():
    """Step 0: this build named in LOCK for as long as it runs, or the build stops naming the one that runs. The process started again inside the build's environment finds its parent's pid in LOCK_HELD and takes nothing."""
    held = read_lock()
    if held and str(held.get("pid")) == os.environ.get(LOCK_HELD):
        return
    if held and project_lock._alive(held.get("pid")):
        fail(f"another build runs -- Woodcore {held.get('version', '?')} from {held.get('root', '?')}, pid {held.get('pid')}, since {held.get('since', '?')}: "
             f"wait for it to end, or end it ({LOCK})")
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.unlink(missing_ok=True)   # none, or left by a build that no longer runs
    record = {"pid": os.getpid(), "version": project.VERSION, "root": str(ROOT), "since": datetime.datetime.now().isoformat(timespec="seconds")}
    try:
        with LOCK.open("x", encoding="utf-8") as out:
            json.dump(record, out)
    except FileExistsError:
        fail(f"another build took {LOCK} at the same moment")
    os.environ[LOCK_HELD] = str(os.getpid())
    atexit.register(release_lock)


def release_lock():
    held = read_lock()
    if held and held.get("pid") == os.getpid():
        LOCK.unlink(missing_ok=True)


def ensure_examples_engine():
    """The engine's copy beside the frozen examples, where the checkout has none (step 4): a working tree keeps the one build_examples.py last wrote, as a manual build always shipped it; a clean checkout gets one from its own lib/."""
    if (EXAMPLES / "lib").is_dir() and (EXAMPLES / "commands.typ").is_file():
        return
    import build_examples
    build_examples.refresh_engine(ROOT)
    say(f"put the engine's copy beside the frozen examples, which this checkout had not: {EXAMPLES / 'lib'}")


def ensure_interpreter():
    """Runs inside the build's own environment: created the first time, and brought to requirements.txt and requirements-build.txt at every build -- pip does nothing where they are met.

    ⚠️ Isolated from the Python the report runs on, and not merely layered over it (`--system-site-packages`, the first try): what is frozen is then exactly what the two files pin, and nothing else a machine happens to carry -- the first build here met an obsolete `pathlib` backport in the base interpreter's site-packages, which PyInstaller refuses to build beside.
    """
    inside = Path(sys.prefix).resolve() == VENV.resolve()
    if not inside:
        config = VENV / "pyvenv.cfg"
        if config.is_file() and "include-system-site-packages = true" in config.read_text(encoding="utf-8"):
            say(f"replacing {VENV}, which saw the base interpreter's packages")
            remove(VENV)
        if not venv_python().is_file():
            say(f"creating the build environment {VENV}")
            subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        say("bringing it to requirements.txt and packaging/requirements-build.txt")
        subprocess.run([str(venv_python()), "-m", "pip", "install", "--disable-pip-version-check", "-q",
                        "-r", str(ROOT / "requirements.txt"), "-r", str(HERE / "requirements-build.txt")], check=True)
        sys.exit(subprocess.run([str(venv_python()), str(Path(__file__).resolve()), *sys.argv[1:]]).returncode)
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        fail("PyInstaller is missing from the build environment -- " + str(VENV))


def check_versions():
    mismatch = dependencies.check()
    if mismatch:
        fail("the packages installed are not the ones requirements.txt pins: "
             + "; ".join(f"{name} {found or 'missing'} (pinned {wanted})" for name, wanted, found in mismatch))
    if ".".join(map(str, sys.version_info[:2])) != notices.PYTHON:
        fail(f"the build runs on Python {sys.version_info[0]}.{sys.version_info[1]}, and legal/THIRD-PARTY-NOTICES.txt names Python {notices.PYTHON}: build with it, or bring notices.PYTHON and Python-PSF.txt to the new one")
    problem = notices.stale()
    if problem:
        fail(problem)
    typst = shutil.which("typst")
    if typst is None:
        fail("typst is not on the PATH: the program ships the Typst it compiles with")
    version = project.typst_version()
    if version != TYPST_VERSION:
        fail(f"typst {version} is on the PATH, and the report is verified with {TYPST_VERSION}")
    return Path(typst)


def revision():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "describe", "--always", "--dirty", "--abbrev=8"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def write_build_info(typst):
    info = {
        "version": project.VERSION,
        "revision": revision(),
        "built": datetime.datetime.now().isoformat(timespec="seconds"),
        "python": ".".join(map(str, sys.version_info[:3])),
        "typst": project.typst_version(),
    }
    (WORK / "build-info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(typst, WORK / "typst.exe")
    if info["revision"].endswith("-dirty"):
        say(f"the sources carry changes nobody committed: the build records {info['revision']}")
    return info


def write_icon(target, sizes=(16, 20, 24, 32, 40, 48, 64, 128, 256)):
    """woodcore.ico from calc/tools/woodcore.svg, drawn by Qt at every size Windows asks for, each a PNG inside the icon file."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(CALC / "tools" / "woodcore.svg"))
    images = []
    for size in sizes:
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        images.append((size, bytes(data)))
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, blobs = b"", b""
    for size, png in images:
        side = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset + len(blobs))
        blobs += png
    target.write_bytes(header + entries + blobs)


def write_version_resource(target, name, description):
    numbers = tuple((list(project._version_tuple(project.VERSION)) + [0, 0, 0, 0])[:4])
    target.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers}, prodvers={numbers}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Florian Lamprecht'),
      StringStruct('LegalCopyright', '© 2026 Florian Lamprecht'),
      StringStruct('FileDescription', {description!r}),
      StringStruct('FileVersion', {project.VERSION!r}),
      StringStruct('InternalName', {name!r}),
      StringStruct('OriginalFilename', {name + '.exe'!r}),
      StringStruct('ProductName', 'Woodcore'),
      StringStruct('ProductVersion', {project.VERSION!r})])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding="utf-8")


def pyinstaller(spec, distpath):
    env = dict(os.environ, WOODCORE_BUILD_WORK=str(WORK))
    say(f"PyInstaller {spec.name}")
    run = subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
                          "--distpath", str(distpath), "--workpath", str(WORK / "pyi" / spec.stem), str(spec)], env=env)
    if run.returncode != 0:
        fail(f"PyInstaller {spec.name} failed")


def compile_sources(app):
    """The program's sources compiled once here, so the first start of an installed Woodcore does not compile them in its own folder."""
    subprocess.run([sys.executable, "-m", "compileall", "-q", "-j", "0", str(app / "_internal" / "calc")], check=True)


def run_checked(cmd, what, env=None, timeout=600):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout)
    if result.returncode != 0:
        fail(f"{what} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result


def copy_project(source_file, target):
    """A copy of the project `source_file` names, its engine's read-only files made writable so the copy can be removed."""
    source = Path(source_file).resolve().parent
    if target.exists():
        remove(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("_Archiv", "*.lock", "~$*"))
    return target / Path(source_file).name


def remove(path):
    for p in sorted(Path(path).rglob("*"), reverse=True):
        try:
            os.chmod(p, 0o666)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


def smoke(app, launcher):
    """The built program, run: the command line exports and compiles the example project with its own Typst, the window opens it, the launcher picks a version."""
    env = dict(os.environ, PYTHONUTF8="1", QT_QPA_PLATFORM="offscreen", QT_QPA_FONTDIR=r"C:\Windows\Fonts",
               WOODCORE_SETTINGS=str(WORK / "smoke-settings.json"))
    env.pop(project.ENV, None)
    (WORK / "smoke-settings.json").write_text('{"lang": "en"}', encoding="utf-8")
    cli = app / "woodcore-cli.exe"
    run_checked([str(cli), "--help"], "woodcore-cli.exe --help", env)
    example = copy_project(ROOT / "tests" / "projet-exemple" / "Exemple.woodcore", WORK / "smoke" / "Exemple")
    run_checked([str(cli), "sync-engine", "--project", str(example)], "woodcore-cli.exe sync-engine", env)
    out = run_checked([str(cli), "export", "--skip-data", "--project", str(example)], "woodcore-cli.exe export --skip-data", env)
    if not project.Project.load(example).report_pdf.is_file():   # where the project's layout.pdf says, never a literal: beside the .typ by default since v0.87
        fail("woodcore-cli.exe compiled no PDF:\n" + out.stdout + out.stderr)
    say("woodcore-cli.exe: engine copied, report compiled with the Typst inside it, archived")
    run_checked([str(app / "Woodcore.exe"), "--project", str(example), "--self-test"], "Woodcore.exe --self-test", env, timeout=300)
    say("Woodcore.exe: the window opened the example project and closed")
    record = json.loads((project.Project.load(example).generated_dir / "VERSION").read_text(encoding="utf-8"))   # where the project's layout.generated says, never a literal: at the top of a project in three documents
    if record["version"] != project.VERSION:
        fail(f"the engine copied by the built program says {record['version']}")
    # an installation as the installer lays it out, in a profile of the check's own: one version, its Woodcore.exe
    local = WORK / "smoke" / "Local"
    installed = local / "Programs" / "Woodcore" / project.VERSION
    installed.mkdir(parents=True)
    shutil.copy2(app / "Woodcore.exe", installed / "Woodcore.exe")
    dry = run_checked([str(launcher), "--dry-run", str(example)], "Woodcore-Launcher.exe --dry-run", dict(env, LOCALAPPDATA=str(local)))
    if project.VERSION not in dry.stdout:
        fail("the launcher did not pick the version installed: " + dry.stdout + dry.stderr)
    say("Woodcore-Launcher.exe: picks the version installed")


def compare(app, named):
    """A copy of project `named` exported by the sources and by woodcore-cli.exe: the two data/ folders must be identical to the byte."""
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", WOODCORE_SETTINGS=str(WORK / "smoke-settings.json"))
    env.pop(project.ENV, None)
    results = {}
    for route, cmd in (("sources", [sys.executable, str(CALC / "cli.py")]), ("built", [str(app / "woodcore-cli.exe")])):
        copied = copy_project(named, WORK / "compare" / route / Path(named).resolve().parent.name)
        data = project.Project.load(copied).data_dir
        if data.exists():
            remove(data)   # written afresh by each route, so nothing the copy brought along is compared
        run_checked([*cmd, "export", "--data-only", "--update-engine", "--project", str(copied)], f"export by the {route}", env)
        results[route] = {p.relative_to(data).as_posix(): p.read_bytes() for p in sorted(data.rglob("*")) if p.is_file()}
    sources, built = results["sources"], results["built"]
    differ = sorted(name for name in set(sources) | set(built) if sources.get(name) != built.get(name))
    if differ:
        detail = ""
        if "project.json" in differ:
            detail = "\n  sources: " + sources.get("project.json", b"").decode("utf-8", "replace") + "\n  built:   " + built.get("project.json", b"").decode("utf-8", "replace")
        fail(f"data/ differs between the sources and the built program in {len(differ)} file(s): {', '.join(differ[:12])}{detail}")
    say(f"--compare: data/ identical to the byte, {len(sources)} files, sources and built program")


def iscc():
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs")):
        if base:
            candidate = Path(base) / "Inno Setup 6" / "ISCC.exe"
            if candidate.is_file():
                return candidate
    found = shutil.which("ISCC")
    return Path(found) if found else None


def package(app, launcher):
    DIST.mkdir(exist_ok=True)
    compiler = iscc()
    if compiler is not None:
        run_checked([str(compiler), "/Q", f"/DAppVersion={project.VERSION}", f"/DSourceDir={app}", f"/DLauncherExe={launcher}",
                     f"/DIconFile={WORK / 'woodcore.ico'}", f"/DOutputDir={DIST}", str(HERE / "woodcore.iss")], "Inno Setup", timeout=1800)
        target = DIST / f"Woodcore-{project.VERSION}-setup.exe"
        say(f"wrote {target} ({target.stat().st_size / 2**20:.0f} MB)")
        return target
    target = DIST / f"Woodcore-{project.VERSION}-win64.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                archive.write(path, Path("Woodcore", project.VERSION, path.relative_to(app)).as_posix())
        archive.write(launcher, "Woodcore/launcher/Woodcore-Launcher.exe")
        archive.write(WORK / "woodcore.ico", "Woodcore/launcher/woodcore.ico")
    say(f"Inno Setup 6 is not installed: wrote {target} ({target.stat().st_size / 2**20:.0f} MB) instead of an installer.")
    say("  for the installer: winget install --id JRSoftware.InnoSetup -e --scope user, then run this again")
    return target


def main():
    parser = argparse.ArgumentParser(prog="packaging/build.py", description=__doc__.splitlines()[0])
    parser.add_argument("--compare", metavar="PROJECT", help="a .woodcore whose export by the sources and by the built program must match")
    parser.add_argument("--no-installer", action="store_true", help="stop after the checks")
    parser.add_argument("--installer-only", action="store_true", help="the installer again from the program already built -- what an edit to woodcore.iss needs, where a whole build is eight minutes")
    args = parser.parse_args()
    take_lock()
    ensure_interpreter()
    if args.installer_only:
        app, launcher = LOCAL / "program" / "Woodcore", LOCAL / "launcher" / "Woodcore-Launcher.exe"
        missing = [p for p in (app / "Woodcore.exe", app / "woodcore-cli.exe", launcher, WORK / "woodcore.ico") if not p.is_file()]
        if missing:
            fail("nothing built to make an installer from -- run the build without --installer-only first:\n  " + "\n  ".join(map(str, missing)))
        say(f"the program as the last build left it: {app}")
        package(app, launcher)
        return
    typst = check_versions()
    if WORK.exists():
        remove(WORK)
    WORK.mkdir(parents=True)
    info = write_build_info(typst)
    say(f"Woodcore {info['version']} ({info['revision'] or 'no git'}), Python {info['python']}, Typst {info['typst']}")
    write_icon(WORK / "woodcore.ico")
    write_version_resource(WORK / "version-gui.txt", "Woodcore", "Woodcore")
    write_version_resource(WORK / "version-cli.txt", "woodcore-cli", "Woodcore command line")
    write_version_resource(WORK / "version-launcher.txt", "Woodcore-Launcher", "Woodcore launcher")
    ensure_examples_engine()
    programs = LOCAL / "program"
    pyinstaller(HERE / "woodcore.spec", programs)
    pyinstaller(HERE / "launcher.spec", LOCAL / "launcher")
    app, launcher = programs / "Woodcore", LOCAL / "launcher" / "Woodcore-Launcher.exe"
    compile_sources(app)
    size = sum(p.stat().st_size for p in app.rglob("*") if p.is_file())
    say(f"the program: {app} ({size / 2**20:.0f} MB)")
    smoke(app, launcher)
    if args.compare:
        compare(app, args.compare)
    if not args.no_installer:
        package(app, launcher)


if __name__ == "__main__":
    main()
