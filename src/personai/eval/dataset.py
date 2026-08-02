"""Labeled evaluation cases and how to load them.

A case is a `PRContext` (reusing the core contract) plus the list of issues we
know are in it. Cases live as JSON in `fixtures/` so the dataset is versioned,
offline, and deterministic. A case with an empty `expected` list is a *clean*
case — any finding it draws is a false positive.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from ..contracts import Category, PRContext

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class ExpectedIssue(BaseModel):
    """A known issue planted in a case's diff (the gold label)."""

    file: str
    # 1-indexed line in the new version of the file, or None for a file-level
    # expectation (any finding on the file satisfies it).
    line: int | None = None
    # Optional: matching is location-first, so category is used only as a
    # secondary "did it categorize correctly" metric, never to make/break a match.
    category: Category | None = None
    note: str = ""


class EvalCase(BaseModel):
    name: str
    pr: PRContext
    expected: list[ExpectedIssue] = Field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.expected


def load_cases(directory: str | Path | None = None) -> list[EvalCase]:
    """Load every `*.json` case from a directory (built-in fixtures by default)."""
    directory = Path(directory) if directory is not None else FIXTURES_DIR
    cases: list[EvalCase] = []
    for path in sorted(directory.glob("*.json")):
        cases.append(EvalCase.model_validate(json.loads(path.read_text())))
    return cases
