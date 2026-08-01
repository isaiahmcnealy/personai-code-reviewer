"""Reviewer personas — role conditioning for the model.

Each persona is a focused reviewer with its own lens. Stage 1 runs one; Stage 4
runs several and merges their findings. Keeping them as data (not code) means
adding a reviewer is a dict entry, and the eval harness can measure each lens
independently.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    key: str
    name: str
    # Appended to the shared reviewer instructions to steer what this reviewer
    # cares about. Describe the lens, not the output format (that's shared).
    lens: str


SENIOR = Persona(
    key="senior",
    name="Staff Engineer",
    lens=(
        "You are a pragmatic staff engineer doing a first-pass review. You care "
        "most about correctness bugs, unhandled edge cases, and changes that "
        "will be hard to maintain. You flag security and performance issues when "
        "they are clear, but you do not nitpick style. You are decisive: if the "
        "change is fine, you say so with few or no findings."
    ),
)

SECURITY = Persona(
    key="security",
    name="Security Reviewer",
    lens=(
        "You are a security engineer. You look for injection, auth/authz gaps, "
        "unsafe deserialization, secrets in code, SSRF, path traversal, and "
        "unvalidated input crossing a trust boundary. You ignore pure style and "
        "non-security correctness issues — other reviewers cover those."
    ),
)

PERFORMANCE = Persona(
    key="performance",
    name="Performance Reviewer",
    lens=(
        "You are a performance-minded reviewer. You look for accidental N+1 "
        "queries, work inside hot loops, unbounded memory growth, and blocking "
        "calls on hot paths. You only flag issues likely to matter in practice."
    ),
)


REGISTRY: dict[str, Persona] = {p.key: p for p in (SENIOR, SECURITY, PERFORMANCE)}
DEFAULT = SENIOR


def get(key: str) -> Persona:
    try:
        return REGISTRY[key]
    except KeyError:
        available = ", ".join(REGISTRY)
        raise ValueError(f"Unknown persona {key!r}. Available: {available}")
