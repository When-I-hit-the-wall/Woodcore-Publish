"""The installed program: the launcher that picks a version, and what the installer and the build must agree on with the program (packaging/, v0.83, docs/conventions/build-and-release.md §12).

Several versions of Woodcore stand side by side, and a double-click on a `.woodcore` starts Woodcore-Launcher.exe, which picks one: the engineer's own sources where the settings say so, else the version the project asks for, else the newest -- unless the project was exported by a newer one than any installed. The launcher is standard library only and restates three things the program says elsewhere; these hold them equal, and hold its choice on a profile of the test's own. The build itself -- PyInstaller, the Typst inside it, the program run -- is checked by packaging/build.py, which takes minutes and is run when a version is built, not by this suite.

A new version's installer is built by itself (packaging/auto_build.py, v0.87): the post-commit hook starts a build of a commit that changed VERSION, detached, on a clean checkout of that commit. What is held here needs no build -- a scratch repository whose packaging/build.py is a stand-in: which commits start one, that the commit does not wait for it, that it builds the commit and not the working tree, never in the main working tree nor into the commit's index, and one build at a time.
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import conftest
from conftest import ROOT

import project

PACKAGING = ROOT / "packaging"
if str(PACKAGING) not in sys.path:
    sys.path.insert(0, str(PACKAGING))
if str(ROOT / "calc" / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "calc" / "tools"))

import launcher  # noqa: E402
import auto_build  # noqa: E402


def _install(root, *versions):
    for version in versions:
        (root / version).mkdir(parents=True)
        (root / version / "Woodcore.exe").write_bytes(b"")
    return root


def test_the_launcher_says_what_the_program_says():
    import home_page
    assert launcher.DEFAULT_GENERATED == project.DEFAULT_LAYOUT["generated"]
    assert launcher.PIN_KEY == project.PIN_KEY
    assert launcher.INSTALL_ROOT == home_page.INSTALL_ROOT
    assert launcher.version_tuple("0.83.10") > launcher.version_tuple("0.83.9") == project._version_tuple("0.83.9")


def test_the_versions_installed_are_read_newest_first():
    root = _install(conftest.tmpdir("launch_installed"), "0.83.0", "0.9.0", "0.83.2")
    (root / "launcher").mkdir()
    (root / "0.84.0").mkdir()   # a folder without its Woodcore.exe: an installation that failed, or was removed by hand
    assert list(launcher.installed(root)) == ["0.83.2", "0.83.0", "0.9.0"]


def test_the_version_is_the_one_asked_for_else_the_newest_unless_the_project_is_newer():
    versions = ["0.85.0", "0.83.2", "0.83.0"]
    assert launcher.choose(versions) == ("0.85.0", None)
    assert launcher.choose(versions, pin="0.83") == ("0.83.2", None), "a prefix takes its newest"
    assert launcher.choose(versions, pin="0.83.0") == ("0.83.0", None)
    assert launcher.choose(versions, pin="0.8")[0] is None, "0.8 is not a prefix of 0.83: the number is compared by parts"
    assert launcher.choose(versions, written="0.84.1") == ("0.85.0", None)
    version, problem = launcher.choose(versions, written="0.90.0")
    assert version is None and problem[0] == "newer" and problem[1]["version"] == "0.90.0"
    assert launcher.choose([])[1][0] == "none"


def test_the_launcher_reads_the_project_it_is_given():
    folder = conftest.tmpdir("launch_project")
    here = project.write(folder / "P.woodcore", "P")
    assert launcher.pinned(here.file) == "" and launcher.written_by(here.file) == ""
    project.sync_engine(here)
    project.update(here.file, woodcore_version="0.83")
    assert launcher.pinned(here.file) == "0.83" and launcher.written_by(here.file) == project.VERSION


def test_the_launcher_starts_the_version_or_the_sources_the_settings_choose():
    root = _install(conftest.tmpdir("launch_command") / "Woodcore", "0.83.0")
    folder = conftest.tmpdir("launch_command_project")
    here = project.write(folder / "P.woodcore", "P")
    cmd, problem = launcher.command(here.file, root=root, settings={})
    assert problem is None and cmd == [str(root / "0.83.0" / "Woodcore.exe"), "--project", str(here.file)]
    cmd, problem = launcher.command(None, root=root, settings={})
    assert cmd[-1] == "--home", "the Start menu's Woodcore opens the start page"
    cmd, problem = launcher.command(here.file, root=root, settings={"launcher": {"dev_checkout": str(ROOT)}})
    if problem is None:
        assert cmd[1:] == [str(ROOT / "calc" / "tools" / "woodcore_gui.py"), "--project", str(here.file)], cmd
    else:
        assert problem[0] == "dev", "pythonw is on no PATH here"
    cmd, problem = launcher.command(here.file, root=root, settings={"launcher": {"dev_checkout": str(folder / "nowhere")}})
    assert cmd is None and problem[0] == "dev", "sources that are gone were started"


def test_the_launcher_starts_a_checkout_by_the_window_s_file_of_its_time():
    """The window is calc/tools/woodcore_gui.py since v0.96 and was catalog_gui.py until then: a checkout of either age is started by the file it has, the newer name first (launcher.GUI_SCRIPTS) -- and where it has neither, the launcher says the sources are not to be found rather than starting nothing."""
    assert launcher.GUI_SCRIPTS == ("woodcore_gui.py", "catalog_gui.py")
    assert all((ROOT / "calc" / "tools" / name).is_file() for name in launcher.GUI_SCRIPTS), "this checkout lacks the window's file or its shim"
    old = conftest.tmpdir("launch_old_checkout")
    (old / "calc" / "tools").mkdir(parents=True)
    (old / "calc" / "tools" / "catalog_gui.py").write_text("", encoding="utf-8")
    assert launcher.dev_checkout({"launcher": {"dev_checkout": str(old)}}) == old / "calc" / "tools" / "catalog_gui.py", "a checkout older than v0.96 is started by its own file"
    (old / "calc" / "tools" / "woodcore_gui.py").write_text("", encoding="utf-8")
    assert launcher.dev_checkout({"launcher": {"dev_checkout": str(old)}}) == old / "calc" / "tools" / "woodcore_gui.py", "the shim was started over the window"
    gone = launcher.dev_checkout({"launcher": {"dev_checkout": str(old / "nowhere")}})
    assert gone.name == "woodcore_gui.py" and not gone.is_file()
    assert launcher.dev_checkout({}) is None


def test_the_window_s_old_file_name_is_a_shim_that_nothing_imports():
    """calc/tools/catalog_gui.py was the window until v0.96. It stays for one caller -- the launcher installed with Woodcore 0.83 to 0.90, which starts the engineer's sources by that path -- and does one thing: it runs woodcore_gui.py as the program. It holds none of the window's names, so a module importing it would get no window at all: the window is imported as woodcore_gui, from the sources as from Woodcore.exe."""
    import ast
    tools = ROOT / "calc" / "tools"
    shim = (tools / "catalog_gui.py").read_text(encoding="utf-8")
    assert not [n for n in ast.walk(ast.parse(shim)) if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign))], "the shim holds names of its own"
    assert 'with_name("woodcore_gui.py")' in shim and 'run_name="__main__"' in shim and 'if __name__ == "__main__":' in shim
    old = re.compile(r"^\s*(?:import|from)\s+" + "catalog" + r"_gui\b|__import__\(\s*[\"']" + "catalog" + "_gui", re.M)
    offenders = []
    for folder in ("calc", "packaging", "tests"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
                continue
            offenders += [f"{path.relative_to(ROOT).as_posix()}:{text.count(chr(10), 0, found.start()) + 1}"
                          for text in [path.read_text(encoding="utf-8")] for found in old.finditer(text)]
    assert not offenders, "the window's old name imported where woodcore_gui is meant:\n  " + "\n  ".join(offenders)
    # since v0.117 Woodcore.exe starts the start screen, which imports the window itself and hands over to its main()
    assert "import woodcore_start" in (PACKAGING / "entry_gui.py").read_text(encoding="utf-8"), "Woodcore.exe does not start the window"
    assert '"woodcore_gui")' in (tools / "woodcore_start.py").read_text(encoding="utf-8"), "the start screen does not import the window"
    assert r"calc\tools\woodcore_gui.py" in (ROOT / "Woodcore.bat").read_text(encoding="utf-8"), "Woodcore.bat does not start the window"


def test_the_launcher_runs_dry_on_a_profile_of_its_own():
    local = conftest.tmpdir("launch_dry")
    _install(local / "Programs" / "Woodcore", "0.83.0", "0.82.0")
    here = project.write(local / "P" / "P.woodcore", "P") if (local / "P").mkdir() is None else None
    settings = local / "settings.json"
    settings.write_text('{"lang": "en"}', encoding="utf-8")
    env = dict(os.environ, LOCALAPPDATA=str(local), WOODCORE_SETTINGS=str(settings))
    run = subprocess.run([sys.executable, str(PACKAGING / "launcher.py"), "--dry-run", str(here.file)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    assert json.loads(run.stdout)[0].endswith(os.path.join("0.83.0", "Woodcore.exe")), run.stdout
    project.update(here.file, woodcore_version="0.84")
    run = subprocess.run([sys.executable, str(PACKAGING / "launcher.py"), "--dry-run", str(here.file)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert run.returncode == 1 and "0.84" in run.stderr, run.stdout + run.stderr


def test_the_installer_installs_where_the_launcher_looks_per_user_and_side_by_side():
    iss = (PACKAGING / "woodcore.iss").read_text(encoding="utf-8")
    assert re.search(r"^PrivilegesRequired=lowest$", iss, re.M), "an installation that needs an administrator"
    assert re.search(r"^AppId=Woodcore-\{#AppVersion\}$", iss, re.M), "one AppId for every version: a second version would replace the first"
    assert r"DefaultDirName={localappdata}\Programs\Woodcore\{#AppVersion}" in iss
    assert r'{localappdata}\Programs\Woodcore\launcher\Woodcore-Launcher.exe"" ""%1"""' in iss, "the association does not start the launcher"
    assert "HKCU" in iss and "HKLM" not in iss and "HKCR" not in iss, "the association is the user's, never the machine's"
    assert launcher.INSTALL_ROOT.name == "Woodcore" and launcher.INSTALL_ROOT.parent.name == "Programs"


def test_what_the_build_writes_stays_out_of_the_repository():
    ignored = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "dist/Woodcore-0.83.0-setup.exe", "build/x", "packaging/build/x"],
                             capture_output=True, text=True)
    if ignored.returncode not in (0, 1):
        raise conftest.Skip("git is not available here")
    assert ignored.stdout.split() == ["dist/Woodcore-0.83.0-setup.exe", "build/x", "packaging/build/x"], ignored.stdout
    spec = (PACKAGING / "woodcore.spec").read_text(encoding="utf-8")
    assert "typst.exe" in spec and "build-info.json" in spec and 'tree("templates")' in spec


# Inno Setup 6, "Registry section": the whole set, and there is no `uninsneveruninstall` in it -- a registry
# entry is kept at uninstall unless an uninsdelete* flag says otherwise, which is what the shared association wants.
REGISTRY_FLAGS = {
    "createvalueifdoesntexist", "deletekey", "deletevalue", "dontcreatekey", "noerror",
    "preservestringtype", "uninsclearvalue", "uninsdeletekey", "uninsdeletekeyifempty", "uninsdeletevalue",
}


def iss_flags(text, section):
    """The flags of every entry of one section of an .iss, as [(line number, [flag, ...]), ...]."""
    out, inside = [], False
    for n, line in enumerate(text.splitlines(), 1):
        bare = line.strip()
        if bare.startswith("[") and bare.endswith("]"):
            inside = bare[1:-1].lower() == section.lower()
            continue
        if not inside or not bare or bare.startswith(";"):
            continue
        found = re.search(r"(?:^|;)\s*Flags:\s*([^;]*)", bare, re.I)
        if found:
            out.append((n, found.group(1).split()))
    return out


def test_no_entry_of_the_installer_carries_a_flag_its_own_section_does_not_have():
    """Inno refuses the WHOLE script over one unknown flag, and says so only when it compiles -- eight minutes into a build, on its last step.

    v0.83 wrote `Flags: uninsneveruninstall` on the four [Registry] lines of the association, reasoning from the [Files] and [Icons] entries beside them, which do have it. ISCC answered `Error on line 63 ... Parameter "Flags" includes an unknown flag.` and wrote no installer. Planted back, this fails.
    """
    iss = (PACKAGING / "woodcore.iss").read_text(encoding="utf-8")
    entries = iss_flags(iss, "Registry")
    for line, flags in entries:
        unknown = [f for f in flags if f.lower() not in REGISTRY_FLAGS]
        assert not unknown, "woodcore.iss line %d: [Registry] has no flag %s -- Inno refuses the whole script" % (line, unknown)
    assert "uninsneveruninstall" not in iss.split("[Registry]")[1], "uninsneveruninstall is not a [Registry] flag"


# --- A new version's installer, built by itself (packaging/auto_build.py, packaging/hooks/post-commit, v0.87) ---

# The stand-in for packaging/build.py in a scratch repository: the version its own checkout carries, where it ran and whether it saw the main working tree's uncommitted file, written where the real one writes its installer -- after long enough for a commit that waited for it to be caught.
FAKE_BUILD = '''"""A stand-in for packaging/build.py (tests/test_packaging.py)."""
import json, re, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
version = re.search(r'VERSION = "([^"]+)"', (ROOT / "calc" / "project.py").read_text(encoding="utf-8")).group(1)
print("stand-in build of", version, "in", ROOT, flush=True)
began = time.time()
time.sleep(4)
(ROOT / "dist").mkdir(exist_ok=True)
record = {"version": version, "root": str(ROOT), "uncommitted": (ROOT / "uncommitted.txt").exists(), "began": began, "ended": time.time()}
(ROOT / "dist" / ("Woodcore-%s-setup.exe" % version)).write_text(json.dumps(record), encoding="utf-8")
'''


def _git(repo, *args, env=None):
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                         env=env or auto_build.clean_env())
    assert run.returncode == 0, "git %s: %s%s" % (" ".join(args), run.stdout, run.stderr)
    return run


def _repo(name):
    """A scratch repository of its own, with no hook until a test sets one."""
    if shutil.which("git") is None:
        raise conftest.Skip("git is not available here")
    repo = conftest.tmpdir(name)
    _git(repo, "init", "-q", "-b", "main")
    for key, value in (("user.name", "test"), ("user.email", "test@example.invalid"), ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
        _git(repo, "config", key, value)
    return repo


def _version(repo, version, note=""):
    (repo / "calc").mkdir(exist_ok=True)
    (repo / "calc" / "project.py").write_text('"""%s"""\n\nVERSION = "%s"\n' % (note, version), encoding="utf-8")


def _commit_all(repo, message):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _wait(condition, seconds=90):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.2)
    return condition()


def test_a_commit_starts_a_build_only_where_it_changed_the_version():
    repo = _repo("auto_versions")
    _version(repo, "0.1.0")
    _commit_all(repo, "v0.1")
    assert auto_build.version_change(repo) == (None, "0.1.0"), "a first commit carrying a VERSION is a new version"
    (repo / "notes.txt").write_text("a", encoding="utf-8")
    _commit_all(repo, "notes")
    assert auto_build.version_change(repo) is None
    _version(repo, "0.1.0", note="its docstring edited")
    _commit_all(repo, "calc/project.py, the same version")
    assert auto_build.version_change(repo) is None, "calc/project.py changed and its VERSION did not"
    _version(repo, "0.2.0")
    _commit_all(repo, "v0.2")
    assert auto_build.version_change(repo) == ("0.1.0", "0.2.0")
    _git(repo, "switch", "-q", "-c", "side")
    _version(repo, "0.3.0")
    _commit_all(repo, "v0.3 on a branch")
    _git(repo, "switch", "-q", "main")
    (repo / "other.txt").write_text("b", encoding="utf-8")
    _commit_all(repo, "meanwhile")
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    assert auto_build.version_change(repo) == ("0.2.0", "0.3.0"), "a merge bringing a new version into the branch is a new version"
    _git(repo, "switch", "-q", "side")
    (repo / "more.txt").write_text("c", encoding="utf-8")
    _commit_all(repo, "more on the branch")
    _git(repo, "switch", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge side again", "side")
    assert auto_build.version_change(repo) is None, "a merge into a branch that had the version already"
    (repo / "calc" / "project.py").unlink()
    _commit_all(repo, "no calc/project.py")
    assert auto_build.version_change(repo) is None


def test_the_hook_builds_the_commit_in_a_checkout_of_its_own_and_the_commit_does_not_wait_for_it():
    """End to end on a scratch repository: packaging/auto_build.py and packaging/hooks/ as they are, packaging/build.py a stand-in that takes four seconds.

    It also holds the header's warning: the commit is made of named paths while another file is staged, so git runs the hook with GIT_INDEX_FILE naming a temporary index -- a `git worktree add` inheriting it would write its checkout into the index, and the file staged would be lost from it.
    """
    repo = _repo("auto_hook")
    local = conftest.tmpdir("auto_hook_local")
    (repo / "packaging").mkdir()
    shutil.copy2(PACKAGING / "auto_build.py", repo / "packaging" / "auto_build.py")
    shutil.copytree(PACKAGING / "hooks", repo / "packaging" / "hooks")
    (repo / "packaging" / "build.py").write_text(FAKE_BUILD, encoding="utf-8")
    (repo / ".gitignore").write_text("dist/\n", encoding="utf-8")
    _version(repo, "0.1.0")
    _commit_all(repo, "v0.1, before the hook")
    _git(repo, "config", "core.hooksPath", auto_build.HOOKS)
    env = auto_build.clean_env()
    env["LOCALAPPDATA"] = str(local)
    env.pop(auto_build.NO_AUTOBUILD, None)

    def commit(*args, extra=None):
        started = time.monotonic()
        run = subprocess.run(["git", "-C", str(repo), "commit", "-q", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                             env=dict(env, **(extra or {})), timeout=60)
        assert run.returncode == 0, run.stdout + run.stderr
        return run, time.monotonic() - started

    (repo / "uncommitted.txt").write_text("in the working tree, never committed", encoding="utf-8")
    (repo / "staged.txt").write_text("staged, and not in the commit", encoding="utf-8")
    _git(repo, "add", "staged.txt")
    pids = {}
    for version in ("0.2.0", "0.3.0"):   # the second committed while the first builds: it waits its turn, and is built
        _version(repo, version)
        run, took = commit("-m", "v" + version, "--", "calc/project.py")
        assert not (repo / "dist" / ("Woodcore-%s-setup.exe" % version)).exists(), "the commit waited for the build (%.1f s)" % took
        assert took < 10, "the commit took %.1f s" % took
        assert "building the installer" in run.stderr, run.stderr
        pids[version] = int(re.search(r"\(pid (\d+)\)", run.stderr).group(1))
    records = {}
    for version, pid in pids.items():
        assert _wait(lambda: not auto_build.alive(pid)), "the build of %s never ended" % version
        log = (repo / "dist" / ("build-%s.log" % version)).read_text(encoding="utf-8")
        target = repo / "dist" / ("Woodcore-%s-setup.exe" % version)
        assert target.is_file(), log
        record = records[version] = json.loads(target.read_text(encoding="utf-8"))
        built = Path(record["root"]).resolve()
        assert record["version"] == version and not record["uncommitted"], record
        assert built != repo.resolve() and local.resolve() in built.parents, "not a checkout of its own under %LOCALAPPDATA%: " + str(built)
        assert not built.exists(), "the checkout was left behind"
        assert "stand-in build of %s" % version in log and "wrote " in log and log.rstrip().splitlines()[-1].endswith("removed %s" % built), log
    assert records["0.3.0"]["began"] >= records["0.2.0"]["ended"], "two builds ran at once"
    assert _git(repo, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1, "a worktree left registered"
    assert _git(repo, "diff", "--cached", "--name-only").stdout.split() == ["staged.txt"], "the build's checkout wrote into the commit's index"
    assert (repo / "uncommitted.txt").is_file()

    (repo / "notes.txt").write_text("a commit with no new version", encoding="utf-8")
    _git(repo, "add", "notes.txt")
    run, took = commit("-m", "notes")
    assert "auto-build" not in run.stderr, run.stderr
    (repo / "dist" / "Woodcore-0.4.0-setup.exe").write_text("built already", encoding="utf-8")
    _version(repo, "0.4.0")
    run, took = commit("-am", "v0.4, its installer there already")
    assert "there already" in run.stderr and "building" not in run.stderr, run.stderr
    _version(repo, "0.5.0")
    run, took = commit("-am", "v0.5, silenced", extra={auto_build.NO_AUTOBUILD: "1"})
    assert run.stderr == "" and not (repo / "dist" / "build-0.5.0.log").exists(), run.stderr


def test_a_detached_launch_returns_at_once_and_outlives_what_started_it():
    """What makes the hook return at once: the process it starts inherits none of its standard handles, so a caller reading the commit's output to its end -- a terminal, a tool -- does not wait for the build either. Planted, stdout inherited: this run took the sleeper's three seconds."""
    folder = conftest.tmpdir("auto_detach")
    marker = folder / "marker.txt"
    sleeper = "import time, pathlib; time.sleep(3); pathlib.Path(%r).write_text('done')" % str(marker)
    starter = folder / "starter.py"
    starter.write_text("import sys\nsys.path.insert(0, %r)\nimport auto_build\nprocess = auto_build.launch_detached([sys.executable, '-c', %r])\nprint(process.pid)\n"
                       % (str(PACKAGING), sleeper), encoding="utf-8")
    started = time.monotonic()
    run = subprocess.run([sys.executable, str(starter)], capture_output=True, text=True, timeout=60)
    took = time.monotonic() - started
    assert run.returncode == 0, run.stdout + run.stderr
    assert took < 2.5 and not marker.exists(), "the caller waited for the detached process (%.1f s)" % took
    assert _wait(marker.is_file, 30) and marker.read_text() == "done", "the detached process ended with what started it"


def test_the_build_checkout_is_never_the_main_working_tree():
    main = conftest.tmpdir("auto_main")
    local = conftest.tmpdir("auto_main_local")
    assert auto_build.checkout_dir(main, "0.87.0", "0123456789abcdef", local) == local / "checkout" / "0.87.0-01234567"
    for wrong in (main, main.parent, main / "sub" / "folder"):
        for refuse in (lambda: auto_build.refuse_main(wrong, main), lambda: auto_build.remove_worktree(main, wrong)):
            try:
                refuse()
            except RuntimeError:
                continue
            raise AssertionError("taken for the build's checkout: %s, the main working tree being %s" % (wrong, main))
    try:
        auto_build.checkout_dir(main, "0.87.0", "0123456789abcdef", main / "local")
    except RuntimeError:
        pass
    else:
        raise AssertionError("a checkout inside the main working tree")
    assert main.is_dir(), "a refusal removed something"


def _load_build():
    spec = importlib.util.spec_from_file_location("woodcore_packaging_build", PACKAGING / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_one_build_at_a_time_and_the_hook_reads_the_lock_the_build_holds():
    build = _load_build()
    assert build.LOCAL == auto_build.local_root() and build.LOCK == auto_build.local_root() / auto_build.LOCK_NAME
    local = conftest.tmpdir("auto_lock")
    lock = local / "Woodcore" / "build" / auto_build.LOCK_NAME
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"pid": os.getpid(), "version": "0.87.0", "root": "elsewhere", "since": "now"}), encoding="utf-8")
    assert auto_build.running(lock.parent)["version"] == "0.87.0"
    env = dict(auto_build.clean_env(), LOCALAPPDATA=str(local))
    env.pop(build.LOCK_HELD, None)
    run = subprocess.run([sys.executable, str(PACKAGING / "build.py"), "--installer-only"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env, timeout=120)
    assert run.returncode == 1 and "another build runs" in run.stderr, run.stdout + run.stderr
    assert [p.name for p in lock.parent.iterdir()] == [auto_build.LOCK_NAME], "a build refused went on to make its environment"
    ended = int(subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True).stdout)
    lock.write_text(json.dumps({"pid": ended, "version": "0.86.0"}), encoding="utf-8")
    assert auto_build.running(lock.parent) is None, "a lock left by a build that ended stops the next"

    # the builds started by commits queue behind one another; one that waited too long gives up, saying so, and checks nothing out
    repo = _repo("auto_queue")
    _version(repo, "0.9.0")
    _commit_all(repo, "v0.9")
    queued = conftest.tmpdir("auto_queue_local")
    with auto_build.queue(queued, 0, lambda: None) as taken:
        assert taken
        with auto_build.queue(queued, 0, lambda: None) as again:
            assert not again, "two builds hold the queue at once"
        assert auto_build.build(repo, "HEAD", local=queued, wait=1) == 1
    log = (repo / "dist" / "build-0.9.0.log").read_text(encoding="utf-8")
    assert "waits for the build before it" in log and "did not end within" in log, log
    assert not (queued / "checkout").exists() and not (repo / "dist" / "Woodcore-0.9.0-setup.exe").exists()
    with auto_build.queue(queued, 0, lambda: None) as taken:
        assert taken, "the queue was not let go of"


def test_activating_the_hook_never_silences_hooks_of_the_clone():
    repo = _repo("auto_install")
    own = repo / ".git" / "hooks" / "pre-commit"
    own.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    def run(*args):
        return subprocess.run([sys.executable, str(PACKAGING / "auto_build.py"), *args], cwd=str(repo), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=auto_build.clean_env(), timeout=60)

    def hooks_path():
        return subprocess.run(["git", "-C", str(repo), "config", "--get", "core.hooksPath"], capture_output=True, text=True).stdout.strip()

    refused = run("install")
    assert refused.returncode == 1 and "pre-commit" in refused.stderr and hooks_path() == "", refused.stderr
    own.unlink()
    assert run("install").returncode == 0 and hooks_path() == auto_build.HOOKS
    assert "already active" in run("install").stderr
    assert run("uninstall").returncode == 0 and hooks_path() == ""


def test_the_hook_is_a_shell_script_git_can_run_wherever_it_is_checked_out():
    hook = (PACKAGING / "hooks" / "post-commit").read_bytes()
    assert hook.startswith(b"#!/bin/sh\n") and b"\r" not in hook, "Git for Windows runs a hook that starts with #!, and sh reads a carriage return as part of the line"
    assert b"auto_build.py hook" in hook and b"exit 0" in hook
    attributes = (PACKAGING / "hooks" / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(r"^\*\s+text\s+eol=lf$", attributes, re.M), "checked out with CRLF where core.autocrlf is set"
