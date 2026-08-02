"""Scoring — match findings to expected issues and compute metrics.

Pure and deterministic: no model, no network. This is the part unit tests pin
down hard, because it defines what "good" means.

Match rule (greedy, nearest-first): after dropping findings below the confidence
floor, each expected issue claims the closest still-unmatched finding on the same
file within `line_tolerance`. Matched pairs are true positives; expected issues
left over are false negatives (missed); findings left over are false positives
(spurious) — valid because fixtures are closed-world (all real issues labeled).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts import Finding
from .dataset import EvalCase, ExpectedIssue


@dataclass
class CaseScore:
    name: str
    matched: list[tuple[ExpectedIssue, Finding]]  # true positives
    missed: list[ExpectedIssue]  # false negatives
    spurious: list[Finding]  # false positives

    @property
    def tp(self) -> int:
        return len(self.matched)

    @property
    def fp(self) -> int:
        return len(self.spurious)

    @property
    def fn(self) -> int:
        return len(self.missed)


@dataclass
class Metrics:
    tp: int
    fp: int
    fn: int
    n_cases: int
    precision: float
    recall: float
    fp_per_case: float
    # None when no matched pair carried a labeled category.
    category_accuracy: float | None


def score_case(
    case: EvalCase,
    findings: list[Finding],
    *,
    line_tolerance: int = 3,
    min_confidence: float = 0.0,
) -> CaseScore:
    candidates = [f for f in findings if f.confidence >= min_confidence]
    used: set[int] = set()
    matched: list[tuple[ExpectedIssue, Finding]] = []
    missed: list[ExpectedIssue] = []

    for exp in case.expected:
        best_idx: int | None = None
        best_dist: int | None = None
        for i, f in enumerate(candidates):
            if i in used or f.file != exp.file:
                continue
            if exp.line is None:
                dist = 0  # a file-level expectation is met by any finding on the file
            elif f.line is None:
                continue  # a line-specific expectation needs a located finding
            else:
                dist = abs(f.line - exp.line)
                if dist > line_tolerance:
                    continue
            if best_dist is None or dist < best_dist:
                best_dist, best_idx = dist, i
        if best_idx is not None:
            used.add(best_idx)
            matched.append((exp, candidates[best_idx]))
        else:
            missed.append(exp)

    spurious = [f for i, f in enumerate(candidates) if i not in used]
    return CaseScore(name=case.name, matched=matched, missed=missed, spurious=spurious)


def aggregate(scores: list[CaseScore]) -> Metrics:
    tp = sum(s.tp for s in scores)
    fp = sum(s.fp for s in scores)
    fn = sum(s.fn for s in scores)
    n = len(scores)

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    fp_per_case = fp / n if n else 0.0

    labeled = [(e, f) for s in scores for (e, f) in s.matched if e.category is not None]
    if labeled:
        category_accuracy = sum(1 for e, f in labeled if f.category == e.category) / len(labeled)
    else:
        category_accuracy = None

    return Metrics(
        tp=tp,
        fp=fp,
        fn=fn,
        n_cases=n,
        precision=precision,
        recall=recall,
        fp_per_case=fp_per_case,
        category_accuracy=category_accuracy,
    )
