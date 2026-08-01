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
uv sync
export GITHUB_TOKEN=...     # fine-grained PAT: Contents + Pull requests, read
uv run personai review https://github.com/owner/repo/pull/123 --persona security
```

Available personas: `senior`, `security`, `performance`, `readability`.

Anthropic credentials resolve from the environment (`ANTHROPIC_API_KEY`) or an
`ant auth login` profile.

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

Build order puts intelligence and measurement ahead of integration polish.

- [x] **Contracts** — `PRContext` / `Finding`, the decoupling seam.
- [x] **Vertical slice** — fetch a real PR, one persona, structured findings, CLI.
- [ ] **Eval harness** — labeled PRs; precision / recall / false-positive rate.
- [ ] **Context retrieval** — feed the model callers/callees and related tests,
      not just the raw diff.
- [ ] **Persona panel** — run reviewers concurrently, merge and dedup findings.
- [ ] **Metrics reporting** — bugs found, vulnerabilities detected, lines reduced.
- [ ] **GitHub Action** — post findings as PR review comments automatically.

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
