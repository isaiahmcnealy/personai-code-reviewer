"""Contract-level tests that don't touch the network or the model."""

import pytest

from quorum.contracts import Category, Finding, Severity
from quorum.github_client import parse_pr_url
from quorum.reviewer import _render
from quorum.contracts import ChangedFile, PRContext


def test_parse_pr_url():
    assert parse_pr_url("https://github.com/psf/requests/pull/6432") == (
        "psf",
        "requests",
        6432,
    )


def test_parse_pr_url_rejects_non_pr():
    with pytest.raises(ValueError):
        parse_pr_url("https://github.com/psf/requests")


def test_finding_roundtrips():
    f = Finding(
        file="app.py",
        line=12,
        severity=Severity.high,
        category=Category.security,
        title="SQL injection",
        body="User input is interpolated into the query.",
        confidence=0.9,
    )
    assert Finding.model_validate(f.model_dump()) == f


def test_render_includes_diff_and_title():
    pr = PRContext(
        owner="o",
        repo="r",
        number=1,
        title="Add feature",
        files=[ChangedFile(filename="a.py", status="modified", patch="+ x = 1")],
    )
    rendered = _render(pr)
    assert "Add feature" in rendered
    assert "a.py" in rendered
    assert "+ x = 1" in rendered
