"""The lock a window holds on its project (calc/project_lock.py, v0.83, docs/ui/window.md §10quater).

Two windows saving one project lose the first one's work without a word, and a project lives in NextCloud and is opened from more than one machine. A window opening a project writes `<name>.woodcore.lock` beside it; a second window finding one asks. These hold who counts as someone else, when a lock is stale, and that a window never removes a lock that is not its own.
"""

TIER = "fast"  # tests/run_tests.py --fast

import fnmatch
import json

import conftest

import project
import project_lock


def _project(name):
    folder = conftest.tmpdir(name)
    return project.write(folder / "L.woodcore", "L")


def _plant(here, **lock):
    project_lock.lock_path(here).write_text(json.dumps(lock), encoding="utf-8")


def test_a_free_project_is_taken_and_the_lock_names_this_window():
    here = _project("lock_free")
    assert project_lock.acquire(here) is None
    lock = project_lock.read(here)
    me = project_lock.whoami()
    assert (lock["host"], lock["pid"], lock["user"]) == (me["host"], me["pid"], me["user"])
    assert project_lock.holder(here) is None, "a window is not someone else to itself"
    project_lock.release(here)
    assert not project_lock.lock_path(here).exists()


def test_another_machine_s_lock_is_asked_about_and_taken_only_when_forced():
    here = _project("lock_other")
    _plant(here, user="kollege", host="ANDERER-PC", pid=4242, since="2026-09-19T08:00:00")
    held = project_lock.acquire(here)
    assert held is not None and held["host"] == "ANDERER-PC", held
    assert project_lock.read(here)["host"] == "ANDERER-PC", "a lock someone else holds was overwritten without being asked"
    project_lock.release(here)
    assert project_lock.read(here)["host"] == "ANDERER-PC", "a window removed a lock that was not its own"
    assert project_lock.acquire(here, force=True) is None
    assert project_lock.read(here)["host"] == project_lock.whoami()["host"]


def test_a_lock_this_machine_left_for_a_process_gone_is_stale():
    here = _project("lock_stale")
    me = project_lock.whoami()
    _plant(here, user=me["user"], host=me["host"], pid=2**31 - 7, since="2026-09-19T08:00:00")
    assert project_lock.holder(here) is None, "a crashed window's lock kept its project locked"
    assert project_lock.acquire(here) is None
    # a window of this machine still running -- this very test process, seen from a lock that is not its own pid -- is someone else
    import os
    parent = os.getppid()
    _plant(here, user=me["user"], host=me["host"], pid=parent, since="2026-09-19T08:00:00")
    assert project_lock.holder(here) is not None, "another window of this machine was taken for a stale lock"


def test_the_lock_is_synced_and_is_no_project_file():
    """`~$Musterprojekt.woodcore` is what Word would call it, and NextCloud's default exclusion list carries `~$*`: the other machine would never see it. And it must not be taken for a second project by the search beside the checkout."""
    here = _project("lock_name")
    name = project_lock.lock_path(here).name
    assert name == "L.woodcore.lock"
    excluded = ("*~", "~$*", ".~lock.*", "~*.tmp", "*.part", "*.filepart", "._*", ".*.sw?")
    assert not any(fnmatch.fnmatch(name, pattern) for pattern in excluded), name
    assert not fnmatch.fnmatch(name, "*" + project.EXTENSION)
