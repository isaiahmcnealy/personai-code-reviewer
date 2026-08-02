.PHONY: install test lint fmt check eval

install:
	uv sync --extra dev

test:
	uv run pytest -q

# Live evaluation — real model calls, needs ANTHROPIC_API_KEY, costs a few cents.
# Not part of `check` (nondeterministic and not free).
eval:
	uv run personai eval

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

check: lint test
