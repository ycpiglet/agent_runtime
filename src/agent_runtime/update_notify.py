"""Non-blocking upstream release notice for host projects (TASK-AR-509).

Host projects pin the Agent Runtime upstream in ``agent_runtime.yml``.
``update-notify`` compares the latest upstream semver release tag (via
``git ls-remote --tags``) against the pinned ``upstream.ref`` and prints a
one-line ASCII notice when a newer release exists.

Guarantees:
- never blocks a session: every failure path (missing config, offline remote,
  timeout, parse error) exits 0 and stays silent unless ``--verbose``;
- cheap at session start: the ls-remote result is cached for 24 hours in
  ``<root>/.tmp/update-notify-cache.json`` (``--no-cache`` bypasses it).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from . import allimbot
from .config import load_config

CACHE_RELATIVE_PATH = Path(".tmp") / "update-notify-cache.json"
CACHE_TTL_SECONDS = 24 * 60 * 60
LS_REMOTE_TIMEOUT_SECONDS = 10

HINT_LINE = (
    "hint: bump upstream.ref in agent_runtime.yml, then run "
    "agent_runtime update-plan --check and agent_runtime update --apply"
)

_SEMVER_TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)")


def cache_path(root: Path) -> Path:
    return root / CACHE_RELATIVE_PATH


def _parse_semver(ref: str) -> tuple[int, int, int] | None:
    match = _SEMVER_TAG.fullmatch(ref.strip())
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def parse_ls_remote_tags(output: str) -> list[str]:
    """Extract sorted vX.Y.Z release tags from ``git ls-remote --tags`` output."""
    tags: set[str] = set()
    for line in output.splitlines():
        _, _, ref = line.partition("\t")
        ref = ref.strip()
        if not ref.startswith("refs/tags/"):
            continue
        tag = ref.removeprefix("refs/tags/").removesuffix("^{}")
        if _parse_semver(tag) is not None:
            tags.add(tag)
    return sorted(tags, key=_parse_semver)


def latest_remote_tag(remote_url: str, *, timeout: float = LS_REMOTE_TIMEOUT_SECONDS) -> str | None:
    """Return the latest upstream vX.Y.Z tag, or None when unavailable."""
    env = dict(os.environ)
    # Force (not setdefault): an inherited GIT_TERMINAL_PROMPT=1 must never
    # let `git ls-remote` block a session start on a credential prompt.
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        ["git", "ls-remote", "--tags", remote_url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )
    if result.returncode != 0:
        return None
    tags = parse_ls_remote_tags(result.stdout or "")
    return tags[-1] if tags else None


def _load_cached_tag(path: Path, remote_url: str, now: float) -> tuple[bool, str | None]:
    """Return (cache_hit, latest_tag). A cached failure (None tag) is a valid hit."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False, None
    if not isinstance(data, dict) or data.get("remote_url") != remote_url:
        return False, None
    checked_at = data.get("checked_at")
    if not isinstance(checked_at, (int, float)) or not 0 <= now - checked_at < CACHE_TTL_SECONDS:
        return False, None
    latest_tag = data.get("latest_tag")
    if latest_tag is not None and not isinstance(latest_tag, str):
        return False, None
    return True, latest_tag


def _store_cached_tag(path: Path, remote_url: str, latest_tag: str | None, now: float) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"checked_at": now, "remote_url": remote_url, "latest_tag": latest_tag}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def _notice_lines(pinned_ref: str, latest_tag: str) -> list[str]:
    pinned = _parse_semver(pinned_ref)
    latest = _parse_semver(latest_tag)
    if pinned is not None:
        if latest is None or latest <= pinned:
            return []
        return [
            f"agent-runtime update available: {pinned_ref} -> {latest_tag} (run: update-plan, then update)",
            HINT_LINE,
        ]
    # Branch or SHA pin: the comparison is undefined, so report the latest tag
    # as informational instead of claiming an update is pending.
    return [
        f"agent-runtime latest release: {latest_tag} (pinned ref: {pinned_ref}; run: update-plan, then update)",
        HINT_LINE,
    ]


def _note(verbose: bool, message: str) -> None:
    if verbose:
        print(f"update-notify: {message}", file=sys.stderr)


def run_update_notify(root: Path, *, no_cache: bool = False, verbose: bool = False) -> int:
    try:
        resolved_root = root.resolve()
        config = load_config(resolved_root)
        remote_url = config.upstream_remote_url
        pinned_ref = config.upstream_ref
        if not remote_url or not pinned_ref:
            _note(verbose, "skip: agent_runtime.yml has no upstream.remote_url/upstream.ref")
            return 0

        now = time.time()
        cache_file = cache_path(resolved_root)
        cache_hit = False
        latest_tag: str | None = None
        if not no_cache:
            cache_hit, latest_tag = _load_cached_tag(cache_file, remote_url, now)
        if not cache_hit:
            latest_tag = latest_remote_tag(remote_url)
            _store_cached_tag(cache_file, remote_url, latest_tag, now)
            _note(verbose, f"queried {remote_url} -> latest_tag={latest_tag}")
        else:
            _note(verbose, f"cache hit ({cache_file}) -> latest_tag={latest_tag}")

        if latest_tag is None:
            _note(verbose, "skip: upstream unavailable or no vX.Y.Z release tags found")
            return 0

        lines = _notice_lines(pinned_ref, latest_tag)
        for line in lines:
            print(line)
        if lines:
            allimbot.notify("\n".join(lines), title="agent_runtime update available")
        if not lines and verbose:
            print(f"agent-runtime up to date: {pinned_ref} (latest release tag: {latest_tag})")
        return 0
    except Exception as exc:  # non-blocking guarantee: never fail a session start
        _note(verbose, f"skipped on error: {exc.__class__.__name__}: {exc}")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a non-blocking notice when a newer Agent Runtime release tag exists upstream"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Host project root")
    parser.add_argument("--no-cache", action="store_true", help="Bypass the 24h cache and query the upstream remote")
    parser.add_argument("--verbose", action="store_true", help="Explain skipped or failed checks on stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_update_notify(args.root, no_cache=args.no_cache, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
