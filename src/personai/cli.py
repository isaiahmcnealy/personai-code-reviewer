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

    ev = sub.add_parser("eval", help="Score the reviewer against labeled fixtures.")
    ev.add_argument(
        "--persona",
        default=personas.DEFAULT.key,
        choices=list(personas.REGISTRY),
        help=f"Reviewer persona (default: {personas.DEFAULT.key}).",
    )
    ev.add_argument(
        "--fixtures", default=None, help="Directory of *.json cases (default: built-in)."
    )
    ev.add_argument(
        "--json", action="store_true", dest="as_json", help="Emit machine-readable JSON."
    )
    ev.add_argument("--line-tolerance", type=int, default=3, help="Line-match window (default: 3).")
    ev.add_argument("--min-confidence", type=float, default=0.0, help="Ignore findings below this.")

    args = parser.parse_args(argv)
    if args.command == "review":
        return _run_review(args.pr_url, args.persona)
    if args.command == "eval":
        return _run_eval(args)
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


def _run_eval(args: argparse.Namespace) -> int:
    import json

    from .eval.dataset import load_cases
    from .eval.report import format_text
    from .eval.runner import run_eval

    persona = personas.get(args.persona)
    cases = load_cases(args.fixtures)
    if not cases:
        where = args.fixtures or "built-in fixtures"
        print(f"error: no eval cases found in {where}", file=sys.stderr)
        return 1

    report = run_eval(
        cases,
        persona=persona,
        line_tolerance=args.line_tolerance,
        min_confidence=args.min_confidence,
    )
    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_text(report))
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
