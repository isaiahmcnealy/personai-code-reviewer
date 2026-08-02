"""Offline tests for the scoring logic — no model, no network."""

from personai.contracts import Category, Finding, PRContext, Severity
from personai.eval.dataset import EvalCase, ExpectedIssue
from personai.eval.scoring import aggregate, score_case


def _case(expected):
    return EvalCase(
        name="c", pr=PRContext(owner="o", repo="r", number=1, title="t"), expected=expected
    )


def _finding(file="a.py", line=10, category=Category.correctness, confidence=0.9):
    return Finding(
        file=file,
        line=line,
        severity=Severity.medium,
        category=category,
        title="x",
        body="y",
        confidence=confidence,
    )


def test_exact_match_is_tp():
    s = score_case(_case([ExpectedIssue(file="a.py", line=10)]), [_finding(line=10)])
    assert (s.tp, s.fp, s.fn) == (1, 0, 0)


def test_within_tolerance_matches():
    s = score_case(
        _case([ExpectedIssue(file="a.py", line=10)]), [_finding(line=12)], line_tolerance=3
    )
    assert s.tp == 1


def test_outside_tolerance_is_fn_and_fp():
    s = score_case(
        _case([ExpectedIssue(file="a.py", line=10)]), [_finding(line=20)], line_tolerance=3
    )
    assert (s.tp, s.fn, s.fp) == (0, 1, 1)


def test_file_level_expected_matches_any_finding_on_file():
    assert score_case(_case([ExpectedIssue(file="a.py", line=None)]), [_finding(line=None)]).tp == 1
    assert score_case(_case([ExpectedIssue(file="a.py", line=None)]), [_finding(line=99)]).tp == 1


def test_wrong_file_does_not_match():
    s = score_case(_case([ExpectedIssue(file="a.py", line=10)]), [_finding(file="b.py", line=10)])
    assert (s.tp, s.fn, s.fp) == (0, 1, 1)


def test_two_findings_one_expected_leaves_one_fp_and_nearest_wins():
    s = score_case(
        _case([ExpectedIssue(file="a.py", line=10)]), [_finding(line=10), _finding(line=11)]
    )
    assert (s.tp, s.fp) == (1, 1)
    assert s.matched[0][1].line == 10


def test_clean_case_finding_is_fp():
    s = score_case(_case([]), [_finding(line=3)])
    assert (s.tp, s.fn, s.fp) == (0, 0, 1)


def test_min_confidence_filters_low_confidence_findings():
    s = score_case(
        _case([ExpectedIssue(file="a.py", line=10)]),
        [_finding(line=10, confidence=0.4)],
        min_confidence=0.5,
    )
    assert (s.tp, s.fn, s.fp) == (0, 1, 0)


def test_two_expected_two_findings_full_recall():
    case = _case(
        [
            ExpectedIssue(file="a.py", line=3, category=Category.correctness),
            ExpectedIssue(file="a.py", line=4, category=Category.maintainability),
        ]
    )
    findings = [
        _finding(line=3, category=Category.correctness),
        _finding(line=4, category=Category.maintainability),
    ]
    s = score_case(case, findings)
    assert (s.tp, s.fp, s.fn) == (2, 0, 0)


def test_aggregate_math():
    c1 = score_case(_case([ExpectedIssue(file="a.py", line=10)]), [_finding(line=10)])  # TP
    c2 = score_case(_case([ExpectedIssue(file="b.py", line=5)]), [])  # FN
    c3 = score_case(_case([]), [_finding(file="c.py", line=3)])  # FP
    m = aggregate([c1, c2, c3])
    assert (m.tp, m.fp, m.fn, m.n_cases) == (1, 1, 1, 3)
    assert m.precision == 0.5
    assert m.recall == 0.5
    assert round(m.fp_per_case, 3) == round(1 / 3, 3)


def test_aggregate_empty_uses_1_0_conventions():
    m = aggregate([score_case(_case([]), [])])
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.category_accuracy is None


def test_category_accuracy_over_labeled_pairs():
    case = _case(
        [
            ExpectedIssue(file="a.py", line=10, category=Category.security),
            ExpectedIssue(file="a.py", line=20, category=Category.performance),
        ]
    )
    findings = [
        _finding(line=10, category=Category.security),  # right category
        _finding(line=20, category=Category.correctness),  # wrong category
    ]
    m = aggregate([score_case(case, findings)])
    assert m.category_accuracy == 0.5
