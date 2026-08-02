"""Runner — drive the reviewer over cases and score the results.

`review_fn` is injectable: it defaults to the real `review`, but tests pass a
deterministic stub so the whole runner -> scoring -> report pipeline runs offline
with no model calls.
"""

from __future__ import annotations

from collections.abc import Callable

from ..contracts import Finding
from ..personas import DEFAULT, Persona
from ..reviewer import review
from .dataset import EvalCase
from .report import EvalReport
from .scoring import aggregate, score_case


def run_eval(
    cases: list[EvalCase],
    review_fn: Callable[..., list[Finding]] = review,
    persona: Persona = DEFAULT,
    *,
    line_tolerance: int = 3,
    min_confidence: float = 0.0,
) -> EvalReport:
    scores = []
    for case in cases:
        findings = review_fn(case.pr, persona)
        scores.append(
            score_case(
                case,
                findings,
                line_tolerance=line_tolerance,
                min_confidence=min_confidence,
            )
        )
    return EvalReport(
        scores=scores,
        metrics=aggregate(scores),
        persona=persona.name,
        line_tolerance=line_tolerance,
        min_confidence=min_confidence,
    )
