"""Rendering an eval run — human text and machine JSON."""

from __future__ import annotations

from dataclasses import dataclass

from .scoring import CaseScore, Metrics


@dataclass
class EvalReport:
    scores: list[CaseScore]
    metrics: Metrics
    persona: str
    line_tolerance: int
    min_confidence: float

    def to_dict(self) -> dict:
        m = self.metrics
        return {
            "persona": self.persona,
            "line_tolerance": self.line_tolerance,
            "min_confidence": self.min_confidence,
            "metrics": {
                "precision": m.precision,
                "recall": m.recall,
                "fp_per_case": m.fp_per_case,
                "category_accuracy": m.category_accuracy,
                "tp": m.tp,
                "fp": m.fp,
                "fn": m.fn,
                "n_cases": m.n_cases,
            },
            "cases": [
                {
                    "name": s.name,
                    "tp": s.tp,
                    "fp": s.fp,
                    "fn": s.fn,
                    "matched": [
                        {
                            "expected": e.model_dump(mode="json"),
                            "finding": f.model_dump(mode="json"),
                        }
                        for e, f in s.matched
                    ],
                    "missed": [e.model_dump(mode="json") for e in s.missed],
                    "spurious": [f.model_dump(mode="json") for f in s.spurious],
                }
                for s in self.scores
            ],
        }


def format_text(report: EvalReport) -> str:
    m = report.metrics
    lines: list[str] = []
    lines.append(
        f"personai eval — persona: {report.persona} | "
        f"tolerance: ±{report.line_tolerance} | min-confidence: {report.min_confidence:.2f}"
    )
    lines.append("")
    lines.append("Per case:")
    width = max((len(s.name) for s in report.scores), default=4)
    for s in report.scores:
        clean = "  (clean)" if (s.tp == 0 and s.fn == 0 and not _was_labeled(s)) else ""
        lines.append(f"  {s.name:<{width}}  TP {s.tp}  FP {s.fp}  FN {s.fn}{clean}")
        for e in s.missed:
            loc = f"{e.file}:{e.line}" if e.line else e.file
            lines.append(f"      MISS  {loc}  {e.note}")
        for f in s.spurious:
            loc = f"{f.file}:{f.line}" if f.line else f.file
            lines.append(f"      FP    [{f.severity}] {f.category} — {loc}  {f.title}")

    cat = "n/a" if m.category_accuracy is None else f"{m.category_accuracy:.2f}"
    lines.append("")
    lines.append(f"Aggregate ({m.n_cases} cases):")
    lines.append(f"  Precision          {m.precision:.2f}   (TP {m.tp} / TP+FP {m.tp + m.fp})")
    lines.append(f"  Recall             {m.recall:.2f}   (TP {m.tp} / TP+FN {m.tp + m.fn})")
    lines.append(f"  False positives    {m.fp}      ({m.fp_per_case:.2f} per case)")
    lines.append(f"  Category accuracy  {cat}")
    lines.append("")
    lines.append("Note: model output is nondeterministic; expect run-to-run variance.")
    return "\n".join(lines)


def _was_labeled(score: CaseScore) -> bool:
    """True if the case had any expected issue (so it isn't a 'clean' fixture)."""
    return bool(score.matched or score.missed)
