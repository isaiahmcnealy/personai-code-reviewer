"""The AI core: `PRContext` in -> structured `Finding`s out.

This module knows nothing about GitHub or the CLI. It takes a `PRContext`, runs
one persona through Claude with a constrained output schema, and returns
validated `Finding`s. Everything the project builds later — retrieval, a
persona panel, the eval harness, the metrics report — is layered around this
interface without changing it.
"""

from __future__ import annotations

import anthropic

from .contracts import Finding, PRContext, ReviewResult
from .personas import DEFAULT, Persona

# claude-opus-5 thinks by default at high effort — good for review reasoning —
# and supports structured outputs. See the claude-api reference for the current
# model table.
MODEL = "claude-opus-5"

# Rough guard so the first slice doesn't send a novel to the API. Real context
# management (retrieve callers/callees, rank, budget tokens) is a later stage;
# for now we just cap and note truncation.
MAX_DIFF_CHARS = 60_000

_SHARED_INSTRUCTIONS = """\
You are one reviewer on a pull request. You are given the PR title, description, \
and the unified diff of each changed file.

Report concrete, actionable issues in the CHANGED lines. Rules:
- Anchor each finding to a real file and, where possible, a line in the new \
version of the file.
- Only report issues you can justify from the diff. Do not speculate about code \
you cannot see, and do not invent line numbers.
- Prefer a few high-signal findings over many low-value ones. A clean change \
should return an empty list — a noisy reviewer gets muted.
- Set `confidence` honestly: 0.9+ for issues you are sure about, lower when the \
surrounding code you can't see might change the conclusion.
"""


def review(
    pr: PRContext,
    persona: Persona = DEFAULT,
    *,
    client: anthropic.Anthropic | None = None,
    model: str = MODEL,
) -> list[Finding]:
    """Run a single persona over a PR and return its findings."""
    client = client or anthropic.Anthropic()

    system = f"{persona.lens}\n\n{_SHARED_INSTRUCTIONS}"
    resp = client.messages.parse(
        model=model,
        max_tokens=16_000,
        system=system,
        messages=[{"role": "user", "content": _render(pr)}],
        output_format=ReviewResult,
    )
    return resp.parsed_output.findings


def _render(pr: PRContext) -> str:
    parts = [
        f"# Pull request: {pr.slug}",
        f"## Title\n{pr.title}",
        f"## Description\n{pr.description or '(none)'}",
        "## Changed files",
    ]

    budget = MAX_DIFF_CHARS
    for f in pr.files:
        header = f"\n### {f.filename} ({f.status}, +{f.additions}/-{f.deletions})"
        if f.patch is None:
            parts.append(f"{header}\n(no textual diff available — binary or too large)")
            continue
        patch = f.patch
        if len(patch) > budget:
            patch = patch[:budget] + "\n... [diff truncated]"
            budget = 0
        else:
            budget -= len(patch)
        parts.append(f"{header}\n```diff\n{patch}\n```")
        if budget == 0:
            parts.append("\n... [remaining files omitted from this pass]")
            break

    return "\n".join(parts)
