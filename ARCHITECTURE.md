# Architecture

This document is the map for anyone reading the repo mid-development. It
explains the one design idea everything hangs off, the data flow, where each
piece lives, and where to plug in new work.

## The one idea: the AI core is decoupled from GitHub

personai has a single, stable interface:

```
PRContext  ──►  review(pr, persona)  ──►  list[Finding]
```

- The **core** (`reviewer.py`) turns a pull request into findings using Claude.
  It imports no integration code — not GitHub, not the CLI.
- An **adapter** produces a `PRContext` and consumes the `Finding`s. Today that
  adapter is a CLI reading the GitHub REST API; next it will be a GitHub Action.
  Swapping adapters never touches the core.

Why it matters: the integration surface (CLI, Action, webhook service) never
limits how deep the AI work can go, because the AI doesn't live in the
integration layer. This is the property to preserve in any change.

## Data flow

```
 GitHub PR URL
      │
      ▼
┌──────────────────┐   PRContext    ┌───────────────┐   list[Finding]   ┌──────────────┐
│ github_client.py │ ─────────────► │  reviewer.py  │ ────────────────► │   cli.py     │
│  (adapter in)    │                │  (AI core)    │                   │ (adapter out)│
└──────────────────┘                └───────┬───────┘                   └──────────────┘
                                            │ uses
                                            ▼
                                     ┌───────────────┐
                                     │  personas.py  │  (reviewer lenses, as data)
                                     └───────────────┘

 contracts.py defines PRContext and Finding — the types on every arrow above.
```

## Module responsibilities

| Module | Knows about | Responsibility |
|---|---|---|
| `contracts.py` | nothing | `PRContext`, `Finding`, enums — the seam. No GitHub, no Claude. |
| `reviewer.py` | Claude, contracts | The AI core: render a PR, call the model with a constrained output schema, return validated findings. |
| `personas.py` | nothing | Reviewer lenses (staff engineer, security, performance, readability) as data. |
| `github_client.py` | GitHub, contracts | The only GitHub-aware module. PR URL → `PRContext`. |
| `cli.py` | all of the above | The CLI adapter. Fetch, review, print. |

## Extension points

**Add a reviewer persona** — add one `Persona` entry in `personas.py`. Describe
the *lens* (what it cares about), not the output format (that's shared in
`reviewer.py`). It's immediately selectable via `--persona`.

**Add an integration** (GitHub Action, webhook service) — write a new adapter
that builds a `PRContext` and does something with the returned `Finding`s. Do
not add integration logic to `reviewer.py`.

**Change the finding shape** — edit `Finding` in `contracts.py`. It doubles as
the model's structured-output schema, so stay within the supported JSON-schema
subset (basic scalars, enums, optional fields; no numeric/length constraints).

## Structured output

`review()` constrains Claude to emit a `ReviewResult` (a list of `Finding`s) via
the Anthropic SDK's structured-output support, so responses are always valid and
parseable — no brittle text scraping. The model is `claude-opus-5`, which
reasons before answering by default.

## Planned layers

The eval harness, context retrieval, persona panel, metrics reporting, and the
GitHub Action all slot around the core **without changing its interface** — each
is a new consumer of `PRContext`/`Finding`, not a change to `review()`. See
[ROADMAP.md](ROADMAP.md) for the staged plan and acceptance criteria.
