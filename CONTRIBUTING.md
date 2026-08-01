# Contributing to personai

Thanks for your interest — contributions of all kinds are welcome: bug reports,
new reviewer personas, docs, and code. This project is under active early
development, so the architecture may still move; [ARCHITECTURE.md](ARCHITECTURE.md)
is the current map.

## Development setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/<you>/personai-code-reviewer
cd personai-code-reviewer
uv sync --extra dev
```

Common tasks (see the [Makefile](Makefile)):

```bash
make test    # run the test suite
make lint    # ruff check + format check
make fmt     # auto-format and auto-fix
make check   # lint + test (what CI runs)
```

Or directly: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`.

The unit tests run fully offline — no GitHub token or Anthropic key needed. To
exercise a real review end to end:

```bash
export GITHUB_TOKEN=...     # fine-grained PAT: Contents + Pull requests, read
uv run personai review https://github.com/owner/repo/pull/123 --persona security
```

## Good first contributions

- **Add a reviewer persona.** Add one `Persona` entry to
  [`src/personai/personas.py`](src/personai/personas.py) describing the lens it
  reviews through (e.g. accessibility, API design, test coverage). Keep it to
  the *lens* — the output format is shared. It becomes selectable via
  `--persona` automatically.
- **Improve the prompt** in `reviewer.py` to cut false positives or sharpen line
  anchoring.
- **Docs and examples.**

## Pull request guidelines

- Branch off `main`; keep PRs focused on a single change.
- Run `make check` before pushing — CI runs the same commands.
- Add or update tests when you change behavior. Prefer offline tests that don't
  call the network or the model.
- Write a clear description: what changed and why.

## Reporting bugs / requesting features

Open an issue using the templates. For bugs, include the command you ran, what
you expected, and what happened. Please don't paste API keys or tokens.

## Code of Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
