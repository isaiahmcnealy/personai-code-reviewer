# Quorum

An AI persona code reviewer for GitHub pull requests. A panel of focused
reviewers (a staff engineer, a security reviewer, a performance reviewer) each
reads a PR through its own lens and emits structured findings.

> Codename — rename freely. The one design commitment worth keeping is the
> decoupling below.

## The one architectural idea

The AI core is independent of GitHub. It has a single interface:

```
PRContext  ->  review()  ->  list[Finding]
```

- **`PRContext`** and **`Finding`** ([contracts.py](src/quorum/contracts.py)) are the seam.
- **`review()`** ([reviewer.py](src/quorum/reviewer.py)) is the intelligence. It never imports GitHub.
- An **adapter** produces a `PRContext` and consumes `Finding`s. Today that's a
  CLI ([cli.py](src/quorum/cli.py)) reading the GitHub REST API
  ([github_client.py](src/quorum/github_client.py)). Next it's a GitHub Action —
  a different adapter around the *same* core.

This is why the integration surface never caps how deep the AI can go: the AI
doesn't live in the integration layer.

## Usage

```bash
uv sync
export GITHUB_TOKEN=...        # fine-grained PAT, Contents+PRs read
uv run quorum review https://github.com/owner/repo/pull/123 --persona security
```

Anthropic credentials resolve from the environment (`ANTHROPIC_API_KEY`) or an
`ant auth login` profile.

## Roadmap

The build order puts intelligence and measurement ahead of integration polish.

- [x] **Stage 0 — Contracts.** `PRContext` / `Finding`, the decoupling seam.
- [x] **Stage 1 — Vertical slice.** Fetch a real PR, one persona, structured
      findings, printed. Proves the pipe end to end.
- [ ] **Stage 1b — GitHub Action.** Wrap the same core; post findings as review
      comments automatically on every PR.
- [ ] **Stage 2 — Eval harness.** Labeled PRs with known issues; precision /
      recall on real findings and a false-positive rate. The primary quality
      lever and the main thing to talk through in an interview.
- [ ] **Stage 3 — Context retrieval.** Feed the model callers/callees, related
      tests, and the PR description — not just the raw diff. Token budgeting.
- [ ] **Stage 4 — Persona panel + orchestration.** Run reviewers concurrently;
      merge and deduplicate their findings.
- [ ] **Stage 5 — Production concerns.** Cheap-model triage, caching,
      hallucinated-line handling, cost/latency.

## Layout

```
src/quorum/
  contracts.py      # Stage 0 — the seam (no GitHub, no Claude)
  reviewer.py       # the AI core: PRContext -> Findings
  personas.py       # reviewer lenses (data, not code)
  github_client.py  # GitHub adapter (the only GitHub-aware module)
  cli.py            # CLI adapter
tests/
  test_contracts.py # offline tests — no network, no model
```
