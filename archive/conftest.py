"""The archive is not part of the program: a `pytest` run from the repository's root must not collect the retired features' tests, whose imports no longer resolve (archive/README.md). tests/run_tests.py never reaches this folder; this file is for a bare `pytest`."""

collect_ignore_glob = ["*"]
