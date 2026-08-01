"""Core data contracts — the seam between integration and intelligence.

Everything downstream (the reviewer, personas, eval harness) depends only on
these types, never on GitHub. That decoupling is what lets the same AI core run
behind a CLI today and a GitHub Action tomorrow without changing a line of the
review logic: an adapter's only job is to produce a `PRContext` and consume a
list of `Finding`s.

`Finding` is also the schema Claude is constrained to emit (structured output),
so keep it to types the structured-output JSON-schema subset supports: basic
scalars, enums, and optional fields. No numeric/length constraints — validate
those in code if you need them.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Category(StrEnum):
    correctness = "correctness"
    security = "security"
    performance = "performance"
    maintainability = "maintainability"
    testing = "testing"
    style = "style"


# ---------------------------------------------------------------------------
# Input: what a reviewer receives. Produced by an integration adapter.
# ---------------------------------------------------------------------------


class ChangedFile(BaseModel):
    filename: str
    status: str  # "added" | "modified" | "removed" | "renamed"
    additions: int = 0
    deletions: int = 0
    # Unified diff for this file. None for binary files or when GitHub omits it.
    patch: str | None = None


class PRContext(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    description: str = ""
    base_sha: str = ""
    head_sha: str = ""
    files: list[ChangedFile] = Field(default_factory=list)

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}#{self.number}"


# ---------------------------------------------------------------------------
# Output: what a reviewer produces. Consumed by an integration adapter.
# ---------------------------------------------------------------------------


class Finding(BaseModel):
    file: str = Field(description="Repo-relative path the finding refers to.")
    line: int | None = Field(
        default=None,
        description="1-indexed line in the new version of the file, or null "
        "for a file-level finding.",
    )
    severity: Severity
    category: Category
    title: str = Field(description="One-line summary of the issue.")
    body: str = Field(description="Explanation and, where useful, a suggested fix.")
    confidence: float = Field(description="How sure the reviewer is this is a real issue, 0.0-1.0.")


class ReviewResult(BaseModel):
    """Wrapper Claude fills in. A top-level object is required for structured
    output (the schema root cannot be a bare array)."""

    findings: list[Finding] = Field(default_factory=list)
