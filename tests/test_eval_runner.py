"""Offline test for the runner via a stub reviewer — no model, no network."""

from personai.contracts import Category, Finding, PRContext, Severity
from personai.eval.dataset import EvalCase, ExpectedIssue
from personai.eval.runner import run_eval


def _case(name, number, expected):
    return EvalCase(
        name=name,
        pr=PRContext(owner="o", repo="r", number=number, title=name),
        expected=expected,
    )


def _f(file, line, category=Category.correctness):
    return Finding(
        file=file,
        line=line,
        severity=Severity.medium,
        category=category,
        title="x",
        body="y",
        confidence=0.9,
    )


def test_run_eval_with_stub_reviewer():
    cases = [
        _case("hit", 1, [ExpectedIssue(file="a.py", line=10)]),
        _case("miss", 2, [ExpectedIssue(file="b.py", line=5)]),
        _case("clean", 3, []),
    ]
    canned = {1: [_f("a.py", 11)], 2: [], 3: [_f("c.py", 3)]}

    def stub(pr, persona):
        return canned[pr.number]

    report = run_eval(cases, review_fn=stub)
    m = report.metrics
    assert (m.tp, m.fp, m.fn, m.n_cases) == (1, 1, 1, 3)
    assert m.precision == 0.5
    assert m.recall == 0.5
    assert report.persona  # persona name recorded for the report header

    d = report.to_dict()
    assert d["metrics"]["tp"] == 1
    assert len(d["cases"]) == 3


def test_run_eval_perfect_scores():
    cases = [_case("hit", 1, [ExpectedIssue(file="a.py", line=10, category=Category.security)])]

    def stub(pr, persona):
        return [_f("a.py", 10, category=Category.security)]

    m = run_eval(cases, review_fn=stub).metrics
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.category_accuracy == 1.0
