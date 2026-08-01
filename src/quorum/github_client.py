"""GitHub adapter — turns a PR URL into a `PRContext`.

This is the *only* module that knows GitHub exists. Swapping the CLI for a
GitHub Action later means writing a different adapter that produces the same
`PRContext`; the reviewer core never changes.
"""

from __future__ import annotations

import re

import httpx

from .contracts import ChangedFile, PRContext

_PR_URL = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)
_API = "https://api.github.com"


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract (owner, repo, number) from a GitHub PR URL."""
    m = _PR_URL.match(url.strip())
    if not m:
        raise ValueError(
            f"Not a GitHub PR URL: {url!r}\n"
            "Expected e.g. https://github.com/owner/repo/pull/123"
        )
    return m["owner"], m["repo"], int(m["number"])


def fetch_pr(url: str, token: str | None) -> PRContext:
    """Fetch a PR and its changed files from the GitHub REST API."""
    owner, repo, number = parse_pr_url(url)

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with httpx.Client(base_url=_API, headers=headers, timeout=30.0) as client:
        pr = _get(client, f"/repos/{owner}/{repo}/pulls/{number}")
        files = _get_paginated(client, f"/repos/{owner}/{repo}/pulls/{number}/files")

    return PRContext(
        owner=owner,
        repo=repo,
        number=number,
        title=pr.get("title") or "",
        description=pr.get("body") or "",
        base_sha=(pr.get("base") or {}).get("sha", ""),
        head_sha=(pr.get("head") or {}).get("sha", ""),
        files=[
            ChangedFile(
                filename=f["filename"],
                status=f.get("status", "modified"),
                additions=f.get("additions", 0),
                deletions=f.get("deletions", 0),
                patch=f.get("patch"),
            )
            for f in files
        ],
    )


def _get(client: httpx.Client, path: str) -> dict:
    resp = client.get(path)
    _raise_for_status(resp)
    return resp.json()


def _get_paginated(client: httpx.Client, path: str) -> list[dict]:
    """Follow GitHub's Link-header pagination (PRs can touch many files)."""
    out: list[dict] = []
    url: str | None = path
    params = {"per_page": 100}
    while url:
        resp = client.get(url, params=params)
        _raise_for_status(resp)
        out.extend(resp.json())
        url = resp.links.get("next", {}).get("url")
        params = None  # the "next" URL already carries its query string
    return out


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    detail = ""
    try:
        detail = resp.json().get("message", "")
    except Exception:
        detail = resp.text[:200]
    raise RuntimeError(f"GitHub API {resp.status_code} on {resp.url}: {detail}")
