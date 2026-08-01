# Roadmap

Single source of truth for milestones and planned features. The README shows a
short status line; this file is canonical. Everything is built to preserve the
one architectural rule — the AI core stays decoupled from any integration (see
[ARCHITECTURE.md](ARCHITECTURE.md)).

**Status:** ✅ done · 🚧 in progress · ⬜ planned

| Stage | Milestone | Status |
|------:|-----------|:------:|
| 0 | Contracts | ✅ |
| 1 | Vertical slice (CLI) | ✅ |
| 2 | Eval harness | ⬜ |
| 3 | Context retrieval | ⬜ |
| 4 | Persona panel + orchestration | ⬜ |
| 5 | Metrics reporting | ⬜ |
| 6 | GitHub Action | ⬜ |

---

## Core milestones

### ✅ Stage 0 — Contracts
The seam between integration and intelligence.
- [x] `PRContext` and `Finding` types (`contracts.py`), independent of GitHub.
- [x] `Finding` doubles as the model's structured-output schema.

### ✅ Stage 1 — Vertical slice (CLI)
Prove the pipe end to end.
- [x] GitHub adapter: PR URL → `PRContext` (`github_client.py`).
- [x] AI core: `review(pr, persona)` → `list[Finding]` via `claude-opus-5`.
- [x] Personas: senior, security, performance, readability.
- [x] `personai review <url>` CLI; validated on a live public PR.

### ⬜ Stage 2 — Eval harness  ← next
Measure review quality instead of guessing. The primary quality lever.
- [ ] A labeled set of PRs with known issues (planted or curated).
- [ ] A runner that scores `review()` output against the labels.
- [ ] Metrics: precision, recall on real issues, and false-positive rate.
- [ ] Reproducible report so any prompt/model change can be compared.
- **Done when:** `make eval` prints precision/recall/FP over the labeled set.

### ⬜ Stage 3 — Context retrieval
Give the model more than the raw diff.
- [ ] Pull in callers/callees of changed symbols and related tests.
- [ ] Rank and budget context to a token limit.
- **Done when:** eval metrics improve measurably vs. the diff-only baseline.

### ⬜ Stage 4 — Persona panel + orchestration
Run several reviewers, combine their output.
- [ ] Run personas concurrently over one PR.
- [ ] Merge and deduplicate overlapping findings.
- **Done when:** one command returns a single deduped, multi-lens review.

### ⬜ Stage 5 — Metrics reporting
Aggregate findings into a per-review scorecard.
- [ ] Counts by category/severity: bugs found, vulnerabilities detected,
      syntax errors caught, potential lines reduced, etc.
- [ ] Machine-readable (JSON) plus a human summary.
- **Done when:** a review emits a metrics block alongside the findings.

### ⬜ Stage 6 — GitHub Action
Make it run automatically on PRs.
- [ ] Action wrapper around the same `review()` core (a new adapter).
- [ ] Post findings as inline PR review comments.
- [ ] `ANTHROPIC_API_KEY` via repo Actions secrets, not the workflow file.
- **Done when:** opening a PR in a repo with the Action installed posts a review.

---

## Backlog (not yet scheduled)

Ideas worth doing once the core stages land. Not commitments.

- **Cost / latency controls** — cheap-model triage pass, response caching.
- **Config file** — per-repo persona selection, severity thresholds, path ignores.
- **Multi-provider support** — a model abstraction behind `review()`.
- **Inline fix suggestions** — emit suggested patches, not just descriptions.
- **Custom personas from config** — let users define a lens without code.
- **Web dashboard** — browse reviews and metrics over time.

Have an idea? Open an issue or see [CONTRIBUTING.md](CONTRIBUTING.md).
