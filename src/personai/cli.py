"""CLI adapter (Stage 1): `personai review <PR-url>`.

Fetch a real PR, run one persona, print findings. This is the thin integration
that proves the pipe end to end. The GitHub Action wrapper (Stage 1b) is a
different adapter around the same `review()` core.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from . import personas
from .contracts import Finding
from .github_client import fetch_pr
from .reviewer import review

_SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def main(argv: list[str] | None = None) -> int:
    # Load a local .env (if present) so GITHUB_TOKEN / ANTHROPIC_API_KEY can live
    # in a gitignored file instead of the shell. Real env vars still win.
    load_dotenv()

    parser = argparse.ArgumentParser(prog="personai", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    rev = sub.add_parser("review", help="Review a GitHub pull request.")
    rev.add_argument("pr_url", help="GitHub PR URL, e.g. .../owner/repo/pull/123")
    rev.add_argument(
        "--persona",
        default=personas.DEFAULT.key,
        choices=list(personas.REGISTRY),
        help=f"Reviewer persona (default: {personas.DEFAULT.key}).",
    )

    args = parser.parse_args(argv)
    if args.command == "review":
        return _run_review(args.pr_url, args.persona)
    parser.error(f"unknown command {args.command!r}")
    return 2


def _run_review(pr_url: str, persona_key: str) -> int:
    persona = personas.get(persona_key)

    try:
        pr = fetch_pr(pr_url, token=os.getenv("GITHUB_TOKEN"))
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"Reviewing {pr.slug} as {persona.name} ({len(pr.files)} files)...\n")
    findings = review(pr, persona)
    _print_findings(findings)
    return 0


def _print_findings(findings: list[Finding]) -> None:
    if not findings:
        print("No findings. LGTM.")
        return

    findings = sorted(
        findings,
        key=lambda f: (_SEVERITY_ORDER.index(f.severity.value), -f.confidence),
    )
    print(f"{len(findings)} finding(s):\n")
    for f in findings:
        loc = f"{f.file}:{f.line}" if f.line else f.file
        print(f"[{f.severity.value.upper()}] {f.category.value} — {loc}")
        print(f"  {f.title}  (confidence {f.confidence:.2f})")
        for line in f.body.splitlines():
            print(f"  {line}")
        print()


if __name__ == "__main__":
    raise SystemExit(main())
