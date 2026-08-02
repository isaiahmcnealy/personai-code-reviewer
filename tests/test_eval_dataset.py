"""Offline tests for loading the built-in fixtures."""

from personai.contracts import Category
from personai.eval.dataset import load_cases


def _by_name():
    return {c.name: c for c in load_cases()}


def test_builtin_fixtures_load():
    cases = load_cases()
    assert len(cases) >= 6
    names = {c.name for c in cases}
    assert {"sql_injection", "clean_rename", "multi_issue"} <= names


def test_clean_case_has_no_expected():
    clean = _by_name()["clean_rename"]
    assert clean.expected == []
    assert clean.is_clean


def test_case_parses_pr_and_labels():
    sql = _by_name()["sql_injection"]
    assert sql.pr.files[0].filename == "app/db.py"
    assert sql.pr.files[0].patch  # non-empty diff
    assert sql.expected[0].category == Category.security
    assert sql.expected[0].line == 14


def test_multi_issue_has_two_labels():
    assert len(_by_name()["multi_issue"].expected) == 2
