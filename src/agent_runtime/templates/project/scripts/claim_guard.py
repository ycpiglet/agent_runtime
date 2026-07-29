"""Commit claim artifacts the instant they are written, so a sibling session's
``git reset --hard`` / ``git clean -fd`` cannot erase an *untracked* claim.

Incident 2026-06-12: a freshly created claim JSON was left untracked; a concurrent
session's destructive cleanup wiped it and the claim had to be recreated by hand.
The fix is simple and the opposite of clever: once a claim file exists, commit it.
A committed file is part of HEAD and survives both ``reset --hard`` and ``clean``.

Everything here is **best-effort and non-fatal** — claim creation must never fail
because a commit could not be made. When the commit cannot happen (not a git repo,
git missing, hook failure) the caller is told via the returned dict and can warn.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

CLAIMS_REL = "agents/runtime/task_claims"
CLAIM_COMMIT_TRANSACTION_ENV = "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION"
CLAIM_COMMIT_TRANSACTION_SCHEMA = "agent-runtime-claim-commit-transaction/v1"


def _git(
    root: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=str(root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
            env=env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"code": 127, "out": "", "err": repr(exc)}
    return {"code": proc.returncode, "out": proc.stdout or "", "err": proc.stderr or ""}


def is_git_repo(root: Path) -> bool:
    result = _git(Path(root), ["rev-parse", "--is-inside-work-tree"])
    return result["code"] == 0 and result["out"].strip() == "true"


def _rel(root: Path, path: Path) -> str:
    path = Path(path)
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _claim_json_paths(rels: Iterable[str]) -> list[str]:
    prefix = f"{CLAIMS_REL}/"
    return sorted(
        {
            rel
            for rel in rels
            if rel.startswith(prefix)
            and Path(rel).suffix == ".json"
            and len(Path(rel).parts) == 4
            and ".." not in Path(rel).parts
        }
    )


def _start_commit_transaction(
    root: Path,
    claim_paths: list[str],
) -> tuple[str, Path] | None:
    if not claim_paths:
        return None
    head = _git(root, ["rev-parse", "HEAD"])
    if head["code"] != 0 or not head["out"].strip():
        return None
    nonce = secrets.token_hex(16)
    payload = {
        "schema": CLAIM_COMMIT_TRANSACTION_SCHEMA,
        "root": str(root.resolve()),
        "claim_paths": claim_paths,
        "nonce": nonce,
        "owner_pid": os.getpid(),
        "head": head["out"].strip(),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    resolved = _git(
        root,
        [
            "rev-parse",
            "--git-path",
            f"agent-runtime/claim-commit/{nonce}.json",
        ],
    )
    if resolved["code"] != 0 or not resolved["out"].strip():
        return None
    record_path = Path(resolved["out"].strip())
    if not record_path.is_absolute():
        record_path = root / record_path
    try:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            record_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(raw + "\n")
    except OSError:
        try:
            record_path.unlink()
        except OSError:
            pass
        return None
    return raw, record_path


def commit_paths(root: Path, paths: Iterable[Path], *, message: str, apply: bool = True) -> dict[str, Any]:
    """Commit ONLY the given paths (other staged/untracked work is left untouched)."""
    root = Path(root)
    rels = [_rel(root, Path(p)) for p in paths if Path(p).exists()]
    if not rels:
        return {"ok": True, "committed": False, "reason": "no-paths", "paths": []}
    if not is_git_repo(root):
        return {"ok": False, "committed": False, "reason": "not-a-git-repo", "paths": rels}
    if not apply:
        return {"ok": True, "committed": False, "reason": "dry-run", "paths": rels}

    add = _git(root, ["add", "--", *rels])
    if add["code"] != 0:
        return {"ok": False, "committed": False, "reason": f"git-add-failed: {add['err'][:200]}", "paths": rels}

    claim_paths = _claim_json_paths(rels)
    transaction = _start_commit_transaction(root, claim_paths)
    if claim_paths and transaction is None:
        return {
            "ok": False,
            "committed": False,
            "reason": "claim-commit-transaction-failed",
            "paths": rels,
        }
    commit_env = dict(os.environ)
    commit_env.pop(CLAIM_COMMIT_TRANSACTION_ENV, None)
    transaction_path: Path | None = None
    if transaction is not None:
        raw, transaction_path = transaction
        commit_env[CLAIM_COMMIT_TRANSACTION_ENV] = raw
    try:
        commit = _git(
            root,
            ["commit", "-m", message, "--", *rels],
            env=commit_env,
        )
    finally:
        if transaction_path is not None:
            try:
                transaction_path.unlink()
            except OSError:
                pass
    if commit["code"] == 0:
        return {"ok": True, "committed": True, "paths": rels}
    blob = (commit["out"] + commit["err"]).lower()
    if any(s in blob for s in ("nothing to commit", "no changes added", "nothing added", "working tree clean")):
        return {"ok": True, "committed": False, "reason": "nothing-to-commit", "paths": rels}
    return {"ok": False, "committed": False, "reason": f"git-commit-failed: {(commit['err'] or commit['out'])[:200]}", "paths": rels}


def commit_claim_artifacts(
    root: Path,
    claim_path: Path,
    *,
    extra_paths: Iterable[Path] = (),
    apply: bool = True,
    claim_id: str = "",
) -> dict[str, Any]:
    """Commit a claim JSON (plus its handoff/log sidecars) immediately after creation."""
    paths = [claim_path, *extra_paths]
    label = claim_id or Path(claim_path).name
    message = f"chore(claim): persist {label} (crash-safety guard)"
    return commit_paths(root, paths, message=message, apply=apply)


def untracked_claim_files(root: Path) -> list[str]:
    """Return repo-relative paths of claim-dir files that are untracked or modified."""
    root = Path(root)
    if not is_git_repo(root):
        return []
    # --untracked-files=all so an entirely-untracked claims dir is expanded into
    # individual files instead of collapsing to a single directory entry.
    status = _git(root, ["status", "--porcelain", "--untracked-files=all", "--", CLAIMS_REL])
    if status["code"] != 0:
        return []
    found: list[str] = []
    for line in status["out"].splitlines():
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:].strip()
        if " -> " in path:  # rename
            path = path.split(" -> ", 1)[1].strip()
        if code.strip() in {"D", "!!"} or code == "!!":
            continue
        if path.startswith(CLAIMS_REL):
            found.append(path)
    return found


def sweep(root: Path, *, apply: bool = True) -> dict[str, Any]:
    """Commit any orphaned (untracked/modified) claim files in one shot."""
    root = Path(root)
    paths = untracked_claim_files(root)
    if not paths:
        return {"ok": True, "committed": False, "reason": "clean", "paths": []}
    return commit_paths(
        root, [root / p for p in paths],
        message="chore(claim): persist untracked claim artifacts (crash-safety guard)",
        apply=apply,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Commit untracked claim artifacts (crash-safety)")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true", help="actually commit (default: dry-run)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = sweep(args.root.resolve(), apply=args.apply)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result.get("paths"):
            verb = "committed" if result.get("committed") else "would commit"
            print(f"{verb} {len(result['paths'])} untracked claim file(s): {', '.join(result['paths'])}")
        else:
            print("no untracked claim files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
