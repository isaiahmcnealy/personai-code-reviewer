# personai

**An open-source AI code reviewer for GitHub pull requests, with customizable
reviewer personas.** Point it at a PR and a persona — a security engineer, a
staff engineer, a readability reviewer — and it reads the diff through that lens
and reports structured findings.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Status: early development](https://img.shields.io/badge/status-early%20development-orange.svg)

<!-- After pushing to GitHub, add a CI badge:
![CI](https://github.com/<owner>/personai-code-reviewer/actions/workflows/ci.yml/badge.svg) -->

> ⚠️ Early development — the interface may change. Feedback and contributions are
> very welcome.

## What it does

- 🎭 **Customizable reviewer personas** — review through a specific lens
  (security, staff engineer, performance, readability), and add your own.
- 🧩 **Structured findings** — every finding has a file, line, severity,
  category, and confidence, so results are consistent and machine-readable, not
  a wall of prose.
- 🔌 **Integration-agnostic core** — the reviewer doesn't know GitHub exists. A
  thin adapter feeds it a pull request; today that's a CLI, next a GitHub Action.
- 📊 **Metrics (planned)** — aggregate findings into per-review metrics: bugs
  found, vulnerabilities detected, potential lines reduced, and more.

## Quickstart

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# 1. Install
uv sync

# 2. Add your credentials — copy the example and fill in both values
cp .env.example .env
```

Edit `.env`:

```ini
GITHUB_TOKEN=github_pat_...     # fine-grained PAT: Contents + Pull requests (read)
ANTHROPIC_API_KEY=sk-ant-...    # your Claude API key
```

`.env` is gitignored, so your keys never get committed. (Prefer the shell?
`export` those two variables instead.) Then review any pull request:

```bash
uv run personai review https://github.com/owner/repo/pull/123 --persona security
```

Available personas: `senior` (default), `security`, `performance`, `readability`.

## Example

```text
$ uv run personai review https://github.com/cli/cli/pull/14035 --persona senior

Reviewing cli/cli#14035 as Staff Engineer (9 files)...

3 finding(s):

[MEDIUM] correctness — api/queries_projects_v2.go:330
  Dropping the substring fallback narrows read:project detection and can
  break graceful degradation  (confidence 0.60)
  The old check matched any error whose text contained the scope message;
  the new path only fires when the error unwraps to api.GraphQLError with
  Type == "INSUFFICIENT_SCOPES". Responses that carry the message without
  that exact type would now hard-fail instead of degrading gracefully...

[LOW] maintainability — api/queries_repo.go:1619
  Duplicated dedupe/sort logic for missing scopes  (confidence 0.70)
  ...
```

Each finding carries a file, line, severity, category, confidence, and a
concrete suggestion — the same structured data an integration (e.g. a GitHub
Action) can post as inline review comments.

## Evaluation

Review quality is measured, not eyeballed. `make eval` runs the reviewer over a
set of labeled fixtures (diffs with known planted issues, plus a clean one) and
scores it on **precision**, **recall**, and **false-positive rate** — so any
prompt, model, or persona change can be compared against a baseline.

```text
$ make eval

Aggregate (6 cases):
  Precision          0.60   (TP 6 / TP+FP 10)
  Recall             1.00   (TP 6 / TP+FN 6)
  False positives    4      (0.67 per case)
  Category accuracy  0.83
```

Matching is deterministic (same file, line within a tolerance window); the fixtures
are *closed-world* (all real issues labeled), so precision is a lower bound —
genuine issues the model finds beyond the labels count against it until labeled.
The scoring logic is fully unit-tested offline; `make eval` itself makes real
model calls and needs `ANTHROPIC_API_KEY`. See [ROADMAP.md](ROADMAP.md) for what
this unlocks (context retrieval, a persona panel).

## How it works

personai is built around one stable interface:

```
PRContext  ──►  review(pr, persona)  ──►  list[Finding]
```

The AI core (`reviewer.py`) turns a pull request into findings using Claude and
imports no integration code. An adapter produces the `PRContext` and consumes
the `Finding`s — so the same core runs behind a CLI today and a GitHub Action
tomorrow without changing the review logic. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the full map.

## Roadmap

Stages 0–2 are done (contracts, CLI slice, **eval harness**); **context
retrieval** is next. Build order puts intelligence and measurement ahead of
integration polish.

See **[ROADMAP.md](ROADMAP.md)** for the full plan, per-stage acceptance
criteria, and the backlog.

## Project layout

```
src/personai/
  contracts.py      # the seam — PRContext / Finding (no GitHub, no Claude)
  reviewer.py       # the AI core: PRContext -> Findings
  personas.py       # reviewer lenses (data, not code)
  github_client.py  # GitHub adapter (the only GitHub-aware module)
  cli.py            # CLI adapter
tests/              # offline tests — no network, no model
```

## Contributing

Contributions are welcome — bug reports, new personas, docs, code. See
[CONTRIBUTING.md](CONTRIBUTING.md) to get set up, and
[good first contributions](CONTRIBUTING.md#good-first-contributions) for where to
start. Adding a reviewer persona is a one-entry change in
[`personas.py`](src/personai/personas.py). By participating you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE) © Isaiah McNealy
