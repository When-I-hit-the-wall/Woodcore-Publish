"""Builds the installer of a new version by itself: a commit that changes VERSION in calc/project.py starts packaging/build.py on a clean checkout of that commit, in the background, and the installer lands in dist/ beside the log of its build (docs/conventions/build-and-release.md §12).

    python packaging/auto_build.py install          activate it on this clone: git config core.hooksPath packaging/hooks
    python packaging/auto_build.py uninstall        deactivate it
    python packaging/auto_build.py start [REV]      the same build by hand, of REV (HEAD by default) whether or not REV changed VERSION -- in the background, like the hook
    python packaging/auto_build.py build REV        the build itself, in the foreground: what `start` and the hook run detached
    python packaging/auto_build.py status           the hook, the build running, what dist/ holds
    python packaging/auto_build.py hook             what packaging/hooks/post-commit runs after every commit

**What fires it.** packaging/hooks/post-commit, which git runs after every commit once `core.hooksPath` names that folder (`install`). It does nothing unless the commit changed VERSION against its first parent -- a first commit carrying one counts as a change, and a merge is compared with the branch it was merged into -- and nothing where dist/ already holds `Woodcore-<version>-setup.exe`. `WOODCORE_NO_AUTOBUILD=1` silences it for one commit.

**Never in the way of the commit.** post-commit runs once the commit is made, and git ignores what it returns. The hook asks git three questions and starts the build as a process of its own and returns: a new process group with a hidden console of its own (`CREATE_NO_WINDOW`, so neither PyInstaller, Typst nor Inno Setup flashes a window), its standard handles on nothing -- so neither git, nor a terminal or a tool capturing the commit's output, waits the eight minutes for it. Measured (22.09.2026): a process started so outlives the Claude tool call that started it, whose job refuses `CREATE_BREAKAWAY_FROM_JOB` (Access is denied) -- which is tried first all the same, for a parent whose job would kill its children on closing and allows them to leave.

**The commit, not the working tree.** Several sessions edit the working tree at once, and a build of it would freeze whatever they had half written. The build runs in a `git worktree add --detach` of the commit, under `%LOCALAPPDATA%\\Woodcore\\build\\checkout\\` -- outside NextCloud, and never the main working tree, which is refused by name -- where that commit's own packaging/build.py builds it. The installer is copied into the real dist/ only once the build succeeded, so a half-written one never stands there to stop the next build, and the worktree is removed, succeeded or not. The log is `dist/build-<version>.log`, written as the build runs and ending on what became of it.

⚠️ **Git's own variables are dropped.** A hook runs with `GIT_DIR`, `GIT_INDEX_FILE` and others set -- a commit of named paths sets `GIT_INDEX_FILE` to a temporary index -- and a `git worktree add` inheriting them would write its checkout into that index. Every git command here, and the build, run without any `GIT_*` variable.

**One build at a time, and none lost.** Its working folders under `%LOCALAPPDATA%\\Woodcore\\build\\` are shared by every build, so packaging/build.py holds a lock there, `build.lock`, for as long as it runs; a build started here while another runs -- two versions committed within eight minutes -- waits for it (`queue()`, up to four hours), saying so on its log without truncating the running one's, and then looks again whether its installer is needed. So an amend of a version's commit made while that version builds rebuilds nothing, the installer of the first being there by then -- unless its build failed, and then the amended commit is built. `start --force` replaces an installer already there.

Standard library only, and nothing imported from calc/: it runs from the working tree after every commit, while another session may be half-way through a module of calc/.
"""

import argparse
import contextlib
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOKS = "packaging/hooks"                  # core.hooksPath, relative: git reads it from the top of the working tree the hook runs in
VERSION_FILE = "calc/project.py"
VERSION_LINE = re.compile(r"""^VERSION\s*=\s*["']([^"']+)["']""", re.M)
LOCK_NAME = "build.lock"                   # packaging/build.py's LOCK, in the folder local_root() names -- held equal by tests/test_packaging.py
QUEUE_NAME = "auto-build.lock"             # the builds started here, one after the other (queue())
WAIT = 4 * 3600                            # seconds a build waits for those before it: a build is some eight minutes
POLL = 2                                   # seconds between two looks while it waits
NO_AUTOBUILD = "WOODCORE_NO_AUTOBUILD"

# Windows' process creation flags (winbase.h), named here for the one place they are used.
NEW_PROCESS_GROUP = 0x00000200
NO_WINDOW = 0x08000000
BREAKAWAY_FROM_JOB = 0x01000000


def local_root():
    """packaging/build.py's LOCAL: where every build keeps its environment, its working folders, its lock -- and where the checkouts go."""
    return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Woodcore" / "build"


def say(text):
    print(f"auto-build: {text}", file=sys.stderr, flush=True)


def now():
    return datetime.datetime.now().isoformat(sep=" ", timespec="seconds")


def clean_env(env=None):
    """The environment without git's own variables (the header's warning): a hook inherits GIT_DIR and GIT_INDEX_FILE from the commit that ran it."""
    env = dict(os.environ if env is None else env)
    for key in list(env):
        if key.upper().startswith("GIT_"):
            del env[key]
    return env


def git(repo, *args, check=True):
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=clean_env())
    if check and run.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {run.stderr.strip()}")
    return run


def toplevel(where="."):
    return Path(git(where, "rev-parse", "--show-toplevel").stdout.strip())


def main_root(repo):
    """The main working tree of the repository `repo` belongs to -- where dist/ is -- whichever of its worktrees `repo` is: the first `git worktree list` names."""
    for line in git(repo, "worktree", "list", "--porcelain").stdout.splitlines():
        if line.startswith("worktree "):
            return Path(line[len("worktree "):])
    raise RuntimeError(f"git names no working tree for {repo}")


def version_at(repo, rev):
    """VERSION as calc/project.py states it at commit `rev`, or None where the file or the line is not there."""
    run = git(repo, "show", f"{rev}:{VERSION_FILE}", check=False)
    if run.returncode != 0:
        return None
    found = VERSION_LINE.search(run.stdout)
    return found.group(1) if found else None


def version_change(repo, rev="HEAD"):
    """(old, new) where commit `rev` changed VERSION against its first parent, else None. A first commit carrying a VERSION changed it from None; a merge is compared with the branch it was merged into, its first parent."""
    new = version_at(repo, rev)
    if new is None:
        return None
    parents = git(repo, "rev-list", "--parents", "-n", "1", rev).stdout.split()[1:]
    old = version_at(repo, parents[0]) if parents else None
    return (old, new) if old != new else None


def installer(main, version):
    return Path(main) / "dist" / f"Woodcore-{version}-setup.exe"


def log_path(main, version):
    return Path(main) / "dist" / f"build-{version}.log"


def alive(pid):
    """Whether process `pid` runs on this machine -- calc/project_lock.py's _alive, restated so that this file imports nothing from calc/."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5   # ERROR_ACCESS_DENIED: it runs, under someone else
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == 259   # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def running(local=None):
    """The build holding packaging/build.py's lock, as the record it wrote there, or None where none runs."""
    try:
        record = json.loads(((local or local_root()) / LOCK_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) and alive(record.get("pid")) else None


def launch_detached(cmd, cwd=None, env=None):
    """Starts `cmd` as a process of its own and returns its Popen at once (the header's «Never in the way of the commit»): its own process group and a hidden console of its own, nothing inherited on its standard handles, and out of its parent's job where that job lets it go."""
    kwargs = dict(cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    if sys.platform != "win32":
        return subprocess.Popen(cmd, start_new_session=True, **kwargs)
    try:
        return subprocess.Popen(cmd, creationflags=NEW_PROCESS_GROUP | NO_WINDOW | BREAKAWAY_FROM_JOB, **kwargs)
    except OSError:   # a job that lets no process leave it -- Claude's: the process is started inside it, and outlives the call all the same
        return subprocess.Popen(cmd, creationflags=NEW_PROCESS_GROUP | NO_WINDOW, **kwargs)


def start(main, rev, force=False):
    """The build of commit `rev` started in the background; returns the Popen, or None where nothing needs starting."""
    main = Path(main)
    sha = git(main, "rev-parse", "--verify", f"{rev}^{{commit}}").stdout.strip()
    version = version_at(main, sha)
    if version is None:
        say(f"{sha[:8]} carries no VERSION in {VERSION_FILE}: nothing to build")
        return None
    if installer(main, version).is_file() and not force:
        say(f"Woodcore {version}: {installer(main, version)} is there already -- no build (start --force replaces it)")
        return None
    held = running()
    after = f", once the build of Woodcore {held.get('version', '?')} that runs has ended" if held else ""
    cmd = [sys.executable, str(Path(__file__).resolve()), "build", sha, "--repo", str(main)] + (["--force"] if force else [])
    process = launch_detached(cmd, cwd=str(main), env=clean_env())
    say(f"Woodcore {version}: building the installer of {sha[:8]} in the background{after} (pid {process.pid}) -- log: {log_path(main, version)}")
    return process


@contextlib.contextmanager
def queue(local, seconds, on_wait):
    """The builds started here, one after the other: a lock the operating system holds on an open file, `auto-build.lock`, which a process that ends -- however it ends -- lets go of, so none is ever left behind. Waits up to `seconds` for it, calling `on_wait` once if it has to, and yields whether it was taken."""
    path = Path(local) / QUEUE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
    deadline, waited, taken = time.monotonic() + seconds, False, False
    try:
        while True:
            try:
                _lock(fd)
                taken = True
                break
            except OSError:
                if not waited:
                    on_wait()
                    waited = True
                if time.monotonic() > deadline:
                    break
                time.sleep(POLL)
        yield taken
    finally:
        if taken:
            try:
                _lock(fd, release=True)
            except OSError:
                pass
        os.close(fd)


def _lock(fd, release=False):
    """One byte of `fd` locked, or let go of; OSError where another process holds it."""
    if sys.platform == "win32":
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN if release else fcntl.LOCK_EX | fcntl.LOCK_NB)


def hook(where="."):
    """What packaging/hooks/post-commit runs: a build of HEAD where HEAD changed VERSION, else nothing. Returns 0 whatever happens."""
    if os.environ.get(NO_AUTOBUILD):
        return 0
    try:
        repo = toplevel(where)
        if version_change(repo, "HEAD") is None:
            return 0
        start(main_root(repo), git(repo, "rev-parse", "HEAD").stdout.strip())   # this worktree's HEAD, which a commit made in another worktree is not the main one's
    except Exception as error:   # a commit is never failed for its installer: say why, and let it be
        say(f"no build started: {error}")
    return 0


def checkout_dir(main, version, sha, local=None):
    """Where commit `sha` is checked out to be built: under local_root(), and never the main working tree nor anything holding it or held in it."""
    target = (local or local_root()) / "checkout" / f"{version}-{sha[:8]}"
    refuse_main(target, main)
    return target


def refuse_main(target, main):
    target, main = Path(target).resolve(), Path(main).resolve()
    if target == main or target in main.parents or main in target.parents:
        raise RuntimeError(f"the build's checkout {target} would be the main working tree {main}, hold it, or lie in it")


def remove_worktree(main, target):
    refuse_main(target, main)
    if git(main, "worktree", "remove", "--force", str(target), check=False).returncode != 0 and Path(target).exists():
        for path in sorted(Path(target).rglob("*"), reverse=True):   # a file left read-only stops rmtree on Windows
            try:
                os.chmod(path, 0o666)
            except OSError:
                pass
        shutil.rmtree(target, ignore_errors=True)
    git(main, "worktree", "prune", check=False)


def build(main, rev, force=False, local=None, wait=WAIT):
    """The build itself, in the foreground: once the builds before it have ended (queue()), commit `rev` checked out beside the main working tree, its packaging/build.py run there, what it wrote into its dist/ copied into the main one, the checkout removed. Returns build.py's exit code, 0 where nothing needed building."""
    main, local = Path(main), Path(local or local_root())
    sha = git(main, "rev-parse", "--verify", f"{rev}^{{commit}}").stdout.strip()
    version = version_at(main, sha)
    if version is None:
        raise RuntimeError(f"{sha[:8]} carries no VERSION in {VERSION_FILE}")
    (main / "dist").mkdir(exist_ok=True)
    log = log_path(main, version)

    def aside(text):   # appended: the log of a build that runs is never truncated by one that waits for it
        with log.open("a", encoding="utf-8") as out:
            out.write(f"{now()}  {text}\n")

    with queue(local, wait, lambda: aside(f"commit {sha[:8]} waits for the build before it")) as taken:
        deadline = time.monotonic() + wait
        while taken and running(local) and time.monotonic() < deadline:   # a packaging/build.py started by hand holds build.lock and not the queue
            time.sleep(POLL)
        if not taken or running(local):
            aside(f"not started for {sha[:8]}: the build before it did not end within {wait / 3600:g} h")
            return 1
        if installer(main, version).is_file() and not force:
            aside(f"not started for {sha[:8]}: {installer(main, version).name} is there already")
            return 0
        return _build_logged(main, sha, version, log, checkout_dir(main, version, sha, local))


def _build_logged(main, sha, version, log, target):
    """build()'s turn, once it has come: the checkout, the build and its removal, on a log of its own."""
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as out:
        def note(text):
            out.write(f"{now()}  {text}\n")
            out.flush()
        note(f"Woodcore {version}: the installer of commit {sha} ({main})")
        git(main, "worktree", "prune", check=False)
        if target.exists():
            remove_worktree(main, target)
        added = git(main, "worktree", "add", "--detach", str(target), sha, check=False)
        if added.returncode != 0:
            note(f"FAILED: git worktree add: {added.stderr.strip()}")
            return 1
        note(f"checked out into {target}")
        try:
            return _build_in(target, main, version, out, note, started)
        except Exception:
            note("FAILED:\n" + traceback.format_exc())
            return 1
        finally:
            remove_worktree(main, target)
            note(f"removed {target}" if not target.exists() else f"could not remove {target}: remove it by hand once nothing holds a file in it")


def _build_in(target, main, version, out, note, started):
    """build()'s middle: packaging/build.py of the checkout `target` run there, its output on the log `out`, and what it wrote into its dist/ copied into the main one."""
    env = clean_env()
    env.update(PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    env.pop(NO_AUTOBUILD, None)
    run = subprocess.run([sys.executable, str(target / "packaging" / "build.py")], cwd=str(target), env=env,
                         stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT)
    out.flush()
    if run.returncode != 0:
        note(f"FAILED: packaging/build.py ended with {run.returncode}, after {(time.monotonic() - started) / 60:.1f} min -- dist/ is left as it was")
        return run.returncode
    dist, copied = Path(main) / "dist", []
    for name in (f"Woodcore-{version}-setup.exe", f"Woodcore-{version}-win64.zip"):
        made = target / "dist" / name
        if made.is_file():
            part = dist / (name + ".part")
            shutil.copyfile(made, part)
            os.replace(part, dist / name)   # never a half-copied installer under the name the next build looks for
            copied.append(dist / name)
    if not copied:
        note("FAILED: packaging/build.py ended well and left nothing in its dist/")
        return 1
    for made in copied:
        note(f"wrote {made} ({made.stat().st_size / 2**20:.0f} MB)")
    note(f"done in {(time.monotonic() - started) / 60:.1f} min")
    return 0


def status(where="."):
    repo = toplevel(where)
    main = main_root(repo)
    hooks = git(main, "config", "--get", "core.hooksPath", check=False).stdout.strip()
    print(f"hook: {'active' if hooks == HOOKS else 'not active (python packaging/auto_build.py install)' if not hooks else 'core.hooksPath is ' + hooks}")
    held = running()
    print(f"build: {'Woodcore %s runs, pid %s, since %s' % (held.get('version', '?'), held.get('pid'), held.get('since', '?')) if held else 'none runs'}")
    with queue(local_root(), 0, lambda: None) as free:
        if not free:
            print("a build started by a commit or by `start` holds the queue: it runs, or checks out its commit")
    version = version_at(main, "HEAD")
    if version:
        print(f"HEAD is Woodcore {version}: installer {'there' if installer(main, version).is_file() else 'not built'} -- {installer(main, version)}")
        if log_path(main, version).is_file():
            print(f"  log: {log_path(main, version)}")
    return 0


def install(where=".", force=False):
    """core.hooksPath set to packaging/hooks on this clone -- refused where it would silence hooks of the clone's own, which are named."""
    main = main_root(toplevel(where))
    current = git(main, "config", "--get", "core.hooksPath", check=False).stdout.strip()
    if current == HOOKS:
        say(f"already active: core.hooksPath is {HOOKS}")
        return 0
    common = Path(git(main, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    hooks_dir = Path(current) if current else common / "hooks"
    if not hooks_dir.is_absolute():
        hooks_dir = main / hooks_dir
    active = sorted(p.name for p in hooks_dir.glob("*") if p.is_file() and not p.name.endswith(".sample")) if hooks_dir.is_dir() else []
    if active and not force:
        say(f"not activated: core.hooksPath would silence the hooks of {hooks_dir}: {', '.join(active)} -- copy what they do into {HOOKS}/, or run again with --force")
        return 1
    git(main, "config", "core.hooksPath", HOOKS)
    say(f"activated: git config core.hooksPath {HOOKS}" + (f" (was {current})" if current else ""))
    return 0


def uninstall(where="."):
    main = main_root(toplevel(where))
    if git(main, "config", "--get", "core.hooksPath", check=False).stdout.strip() != HOOKS:
        say(f"core.hooksPath is not {HOOKS}: nothing to deactivate")
        return 0
    git(main, "config", "--unset", "core.hooksPath")
    say("deactivated: core.hooksPath unset")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="packaging/auto_build.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("hook", help="what packaging/hooks/post-commit runs")
    one = sub.add_parser("start", help="build the installer of REV in the background")
    one.add_argument("rev", nargs="?", default="HEAD")
    one.add_argument("--force", action="store_true", help="replace an installer already in dist/")
    one = sub.add_parser("build", help="build the installer of REV in the foreground")
    one.add_argument("rev")
    one.add_argument("--repo", default=None, help="the repository's main working tree (the one this file is in by default)")
    one.add_argument("--force", action="store_true", help="replace an installer already in dist/")
    sub.add_parser("status", help="the hook, the build running, what dist/ holds")
    one = sub.add_parser("install", help="git config core.hooksPath packaging/hooks")
    one.add_argument("--force", action="store_true", help="even where the clone has hooks of its own, which it then silences")
    sub.add_parser("uninstall", help="unset core.hooksPath")
    args = parser.parse_args(argv)
    if args.command == "hook":
        return hook()
    if args.command == "start":
        repo = toplevel()
        start(main_root(repo), git(repo, "rev-parse", "--verify", f"{args.rev}^{{commit}}").stdout.strip(), args.force)
        return 0
    if args.command == "build":
        repo = Path(args.repo) if args.repo else main_root(toplevel(HERE))
        try:
            return build(repo, args.rev, args.force)
        except Exception:   # run detached, nobody reads its stderr: the reason goes where the build's log would have been
            fallback = local_root() / "auto-build-error.log"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            with fallback.open("a", encoding="utf-8") as out:
                out.write(f"{now()}  build {args.rev} in {repo}:\n{traceback.format_exc()}\n")
            raise
    if args.command == "status":
        return status()
    if args.command == "install":
        return install(force=args.force)
    return uninstall()


if __name__ == "__main__":
    sys.exit(main())
