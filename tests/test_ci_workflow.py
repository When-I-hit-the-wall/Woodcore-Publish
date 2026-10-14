""".github/workflows/tests.yml, the suite at every push (docs/conventions/build-and-release.md §12; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-27-01 to REQ-27-04; issue #27).

Read as text, the standard library having no YAML reader -- the way tests/test_site.py reads site.yml.
"""

import re

from conftest import ROOT

CI = ROOT / ".github" / "workflows" / "tests.yml"


def _text():
    return CI.read_text(encoding="utf-8")


def _jobs(ci):
    """{job name: its text}, the jobs being the two-space keys under `jobs:`."""
    body = ci.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([a-z_-]+):\n", body, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


def test_the_suite_runs_at_every_push_and_pull_request_and_windows_on_the_default_branch():
    ci = _text()
    triggers = re.search(r"^on:\n((?:[ \t]+.*\n|\n)+?)(?=^\S)", ci, re.M).group(1)
    assert re.findall(r"^  ([a-z_]+):", triggers, re.M) == ["push", "pull_request"], triggers
    assert "pull_request_target" not in ci, "pull_request_target would hand a branch nobody reviewed the repository's token"
    jobs = _jobs(ci)
    assert set(jobs) == {"linux", "windows"}, jobs.keys()
    assert "runs-on: ubuntu-" in jobs["linux"] and "if:" not in jobs["linux"].split("steps:")[0], "Linux runs at every push and pull request"
    assert "runs-on: windows-" in jobs["windows"]
    assert "github.ref == 'refs/heads/master'" in jobs["windows"] and "github.event_name == 'push'" in jobs["windows"], "Windows on the default branch only (master, as site.yml's)"


def test_each_job_prepares_the_machine_with_the_bootstrap_alone_and_runs_the_runner():
    for name, job in _jobs(_text()).items():
        assert "python tests/bootstrap.py" in job, f"{name}: the machine is prepared by tests/bootstrap.py, the one list of what it needs"
        assert "pip install" not in job and "apt-get" not in job and "releases/download" not in job, f"{name}: an installation written here would be a second list"
        assert "python tests/run_tests.py --times" in job, f"{name}: every file in a process of its own, as the runner always runs them (issue #22)"
        assert "--perf" not in job, f"{name}: the tests of time do not run on a shared runner"
        assert 'exit "${PIPESTATUS[0]}"' in job and "shell: bash" in job, f"{name}: the job must fail with the runner, not with tee"
        assert re.search(r"actions/upload-artifact@[0-9a-f]{40}", job) and "if: always()" in job and "test-times.txt" in job, f"{name}: the times kept as an artifact, red run or green"
        assert "cache: pip" in job, f"{name}: pip's downloads cached"
        assert "hashFiles('typst-version.txt', 'typst-sha256.json')" in job, f"{name}: Typst cached by the files that pin it"
        assert re.search(r'--prefix "\$\{\{ runner\.temp \}\}/typst-bin"', job) and "path: ${{ runner.temp }}/typst-bin" in job, f"{name}: the cached folder is the one Typst is installed into"


def test_it_trusts_only_github_s_own_actions_pinned_by_commit_and_may_only_read():
    ci = _text()
    assert re.search(r"^permissions:\n  contents: read\n", ci, re.M), "the token of the workflow may only read"
    assert not re.search(r":\s*write\b", ci), "nothing written with the token"
    assert "secrets." not in ci, "the suite needs no secret"
    for action in re.findall(r"^\s+(?:- )?uses: (\S+)", ci, re.M):
        assert action.startswith("actions/") and re.search(r"@[0-9a-f]{40}$", action), f"{action}: only GitHub's own actions, pinned by the commit"
    assert re.search(r'python-version: "3\.13"', ci), "the Python the build and the site use (packaging/notices.PYTHON)"
