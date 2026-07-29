"""Persist explicitly authorized claim artifacts without committing user work.

Incident 2026-06-12: a freshly created claim JSON was left untracked; a concurrent
session's destructive cleanup wiped it and the claim had to be recreated by hand.
The explicit SCM mode therefore stages the artifacts visibly in the real index,
then commits an immutable tree built from a short-lived private index.

The caller receives a structured failure instead of an exception when Git, a
hook, tree validation, or the compare-and-swap ref update fails. Failed artifacts
remain staged in the real index so the ordinary claim gate continues to block.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

CLAIMS_REL = "agents/runtime/task_claims"
CLAIM_COMMIT_TRANSACTION_ENV = "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION"
CLAIM_COMMIT_TRANSACTION_SCHEMA = "agent-runtime-claim-commit-transaction/v2"
OID_RE = re.compile(r"^[0-9a-f]{40,64}$")


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


def _transaction_artifact_path(rel: str) -> bool:
    path = Path(rel)
    name = path.name
    return (
        len(rel) <= 300
        and len(path.parts) == 4
        and path.parts[:3] == ("agents", "runtime", "task_claims")
        and ".." not in path.parts
        and bool(name)
        and all(character.isalnum() or character in "._-" for character in name)
        and (
            path.suffix == ".json"
            or name.endswith(".handoff.md")
            or name.endswith(".log.md")
        )
    )


def _git_path(root: Path, relative: str) -> Path | None:
    resolved = _git(root, ["rev-parse", "--git-path", relative])
    if resolved["code"] != 0 or not resolved["out"].strip():
        return None
    path = Path(resolved["out"].strip())
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _private_index_artifacts(
    root: Path,
    rels: list[str],
    *,
    env: dict[str, str],
) -> list[dict[str, str]] | None:
    artifacts: list[dict[str, str]] = []
    for rel in rels:
        staged = _git(root, ["ls-files", "--stage", "--", rel], env=env)
        lines = [line for line in staged["out"].splitlines() if line.strip()]
        if staged["code"] != 0 or len(lines) != 1:
            return None
        fields = lines[0].split(None, 3)
        if len(fields) != 4 or fields[2] != "0":
            return None
        mode, oid, _stage, indexed_path = fields
        if indexed_path != rel or mode != "100644" or OID_RE.fullmatch(oid) is None:
            return None
        artifacts.append({"path": rel, "mode": mode, "oid": oid})
    return artifacts


def _working_blob(root: Path, rel: str) -> str:
    result = _git(root, ["hash-object", f"--path={rel}", rel])
    if result["code"] != 0:
        return ""
    return result["out"].strip()


def _run_hook(
    root: Path,
    name: str,
    *,
    env: dict[str, str],
    args: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Run one Git commit hook without letting Git construct a mutable tree.

    Git 2.36+ exposes ``git hook run``.  Older POSIX Git installations can
    execute the traditional hook path directly; older Windows installations
    fail closed because Python cannot faithfully reproduce Git-for-Windows'
    shell dispatch.
    """

    version = _git(root, ["version"])
    match = re.search(r"(\d+)\.(\d+)", version["out"])
    supports_hook_run = bool(
        version["code"] == 0
        and match
        and (int(match.group(1)), int(match.group(2))) >= (2, 36)
    )
    if supports_hook_run:
        command = ["hook", "run", "--ignore-missing", name]
        if args:
            command.extend(["--", *args])
        return _git(root, command, env=env)

    hook_path = _git_path(root, f"hooks/{name}")
    if hook_path is None or not hook_path.exists():
        return {"code": 0, "out": "", "err": ""}
    if os.name == "nt":
        return {
            "code": 127,
            "out": "",
            "err": "git-hook-run requires Git >= 2.36 on Windows",
        }
    if not hook_path.is_file() or not os.access(hook_path, os.X_OK):
        return {"code": 0, "out": "", "err": ""}
    try:
        proc = subprocess.run(
            [str(hook_path), *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=env,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return {"code": 127, "out": "", "err": repr(exc)}
    return {"code": proc.returncode, "out": proc.stdout or "", "err": proc.stderr or ""}


def _start_commit_transaction(
    root: Path,
    claim_paths: list[str],
    *,
    artifacts: list[dict[str, str]],
    head: str,
    ref: str,
    index_path: Path,
    tree_oid: str,
    nonce: str,
) -> tuple[str, Path] | None:
    if not claim_paths:
        return None
    payload = {
        "schema": CLAIM_COMMIT_TRANSACTION_SCHEMA,
        "root": str(root.resolve()),
        "claim_paths": claim_paths,
        "artifacts": artifacts,
        "nonce": nonce,
        "owner_pid": os.getpid(),
        "head": head,
        "ref": ref,
        "index": str(index_path.resolve()),
        "tree": tree_oid,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    record_path = _git_path(
        root,
        f"agent-runtime/claim-commit/{nonce}.json",
    )
    if record_path is None:
        return None
    try:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(record_path.parent, 0o700)
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


def _cleanup_private_path(path: Path | None) -> None:
    if path is None:
        return
    for candidate in (path, Path(f"{path}.lock")):
        try:
            candidate.unlink()
        except OSError:
            pass


def _claim_transaction_commit(
    root: Path,
    rels: list[str],
    claim_paths: list[str],
    *,
    message: str,
) -> dict[str, Any]:
    head = _git(root, ["rev-parse", "HEAD"])
    ref = _git(root, ["symbolic-ref", "-q", "HEAD"])
    if (
        head["code"] != 0
        or not head["out"].strip()
        or ref["code"] != 0
        or not ref["out"].strip().startswith("refs/heads/")
    ):
        return {
            "ok": False,
            "committed": False,
            "reason": "claim-commit-detached-head",
            "paths": rels,
        }
    start_head = head["out"].strip()
    symbolic_ref = ref["out"].strip()
    nonce = secrets.token_hex(16)
    index_path = _git_path(root, f"agent-runtime/claim-commit/{nonce}.index")
    message_path = _git_path(root, f"agent-runtime/claim-commit/{nonce}.message")
    if index_path is None or message_path is None:
        return {
            "ok": False,
            "committed": False,
            "reason": "claim-commit-private-path-failed",
            "paths": rels,
        }

    index_env = dict(os.environ)
    index_env.pop(CLAIM_COMMIT_TRANSACTION_ENV, None)
    index_env["GIT_INDEX_FILE"] = str(index_path)
    transaction_path: Path | None = None
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(index_path.parent, 0o700)
        read_tree = _git(root, ["read-tree", start_head], env=index_env)
        if read_tree["code"] != 0:
            return {
                "ok": False,
                "committed": False,
                "reason": f"claim-commit-read-tree-failed: {read_tree['err'][:200]}",
                "paths": rels,
            }
        try:
            os.chmod(index_path, 0o600)
        except OSError:
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-private-index-permission-failed",
                "paths": rels,
            }
        private_add = _git(root, ["add", "--", *rels], env=index_env)
        if private_add["code"] != 0:
            return {
                "ok": False,
                "committed": False,
                "reason": f"claim-commit-private-add-failed: {private_add['err'][:200]}",
                "paths": rels,
            }
        artifacts = _private_index_artifacts(root, rels, env=index_env)
        if artifacts is None:
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-artifact-index-invalid",
                "paths": rels,
            }
        sealed = _git(root, ["write-tree"], env=index_env)
        tree_oid = sealed["out"].strip()
        if sealed["code"] != 0 or OID_RE.fullmatch(tree_oid) is None:
            return {
                "ok": False,
                "committed": False,
                "reason": f"claim-commit-write-tree-failed: {sealed['err'][:200]}",
                "paths": rels,
            }
        head_tree = _git(root, ["rev-parse", f"{start_head}^{{tree}}"])
        if head_tree["code"] == 0 and head_tree["out"].strip() == tree_oid:
            return {
                "ok": True,
                "committed": False,
                "reason": "nothing-to-commit",
                "paths": rels,
            }

        transaction = _start_commit_transaction(
            root,
            claim_paths,
            artifacts=artifacts,
            head=start_head,
            ref=symbolic_ref,
            index_path=index_path,
            tree_oid=tree_oid,
            nonce=nonce,
        )
        if transaction is None:
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-transaction-failed",
                "paths": rels,
            }
        raw, transaction_path = transaction
        hook_env = dict(index_env)
        hook_env[CLAIM_COMMIT_TRANSACTION_ENV] = raw

        descriptor = os.open(
            message_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(message.rstrip("\n") + "\n")

        hook_plan = (
            ("pre-commit", ()),
            ("prepare-commit-msg", (str(message_path), "message")),
            ("commit-msg", (str(message_path),)),
        )
        for hook_name, hook_args in hook_plan:
            hook = _run_hook(root, hook_name, env=hook_env, args=hook_args)
            if hook["code"] != 0:
                detail = hook["err"] or hook["out"]
                return {
                    "ok": False,
                    "committed": False,
                    "reason": f"git-{hook_name}-failed: {detail[:200]}",
                    "paths": rels,
                }

        current_tree = _git(root, ["write-tree"], env=index_env)
        if current_tree["code"] != 0 or current_tree["out"].strip() != tree_oid:
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-transaction-tree-changed",
                "paths": rels,
            }
        for artifact in artifacts:
            if _working_blob(root, artifact["path"]) != artifact["oid"]:
                return {
                    "ok": False,
                    "committed": False,
                    "reason": "claim-commit-transaction-working-blob-changed",
                    "paths": rels,
                }
        current_head = _git(root, ["rev-parse", "HEAD"])
        current_ref = _git(root, ["symbolic-ref", "-q", "HEAD"])
        if (
            current_head["code"] != 0
            or current_head["out"].strip() != start_head
            or current_ref["code"] != 0
            or current_ref["out"].strip() != symbolic_ref
        ):
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-ref-moved",
                "paths": rels,
            }
        try:
            persisted = transaction_path.read_text(encoding="utf-8")
        except OSError:
            persisted = ""
        if persisted != raw + "\n":
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-transaction-record-changed",
                "paths": rels,
            }
        try:
            commit_message = message_path.read_text(encoding="utf-8")
        except OSError:
            commit_message = ""
        if not commit_message.strip():
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-message-empty",
                "paths": rels,
            }

        commit_env = dict(os.environ)
        commit_env.pop(CLAIM_COMMIT_TRANSACTION_ENV, None)
        commit_env.pop("GIT_INDEX_FILE", None)
        commit_args = ["commit-tree", tree_oid, "-p", start_head, "-F", str(message_path)]
        signing = _git(root, ["config", "--bool", "commit.gpgSign"])
        if signing["code"] == 0 and signing["out"].strip().lower() == "true":
            commit_args.insert(1, "-S")
        committed = _git(root, commit_args, env=commit_env)
        commit_oid = committed["out"].strip()
        if committed["code"] != 0 or OID_RE.fullmatch(commit_oid) is None:
            return {
                "ok": False,
                "committed": False,
                "reason": f"claim-commit-tree-failed: {(committed['err'] or committed['out'])[:200]}",
                "paths": rels,
            }
        update = _git(
            root,
            [
                "update-ref",
                "-m",
                f"claim-guard: {message}",
                symbolic_ref,
                commit_oid,
                start_head,
            ],
            env=commit_env,
        )
        if update["code"] != 0:
            return {
                "ok": False,
                "committed": False,
                "reason": f"claim-commit-ref-update-failed: {update['err'][:200]}",
                "paths": rels,
            }

        post = _run_hook(root, "post-commit", env=commit_env)
        result: dict[str, Any] = {
            "ok": True,
            "committed": True,
            "paths": rels,
            "commit": commit_oid,
            "tree": tree_oid,
        }
        if post["code"] != 0:
            result["post_commit_warning"] = (post["err"] or post["out"])[:200]
        return result
    finally:
        _cleanup_private_path(transaction_path)
        _cleanup_private_path(index_path)
        _cleanup_private_path(message_path)


def commit_paths(root: Path, paths: Iterable[Path], *, message: str, apply: bool = True) -> dict[str, Any]:
    """Commit ONLY the given paths (other staged/untracked work is left untouched)."""
    root = Path(root)
    rels = list(
        dict.fromkeys(_rel(root, Path(path)) for path in paths if Path(path).exists())
    )
    if not rels:
        return {"ok": True, "committed": False, "reason": "no-paths", "paths": []}
    if not is_git_repo(root):
        return {"ok": False, "committed": False, "reason": "not-a-git-repo", "paths": rels}
    if not apply:
        return {"ok": True, "committed": False, "reason": "dry-run", "paths": rels}

    claim_paths = _claim_json_paths(rels)
    if claim_paths and not all(_transaction_artifact_path(rel) for rel in rels):
        return {
            "ok": False,
            "committed": False,
            "reason": "claim-commit-non-artifact-path",
            "paths": rels,
        }
    add = _git(root, ["add", "--", *rels])
    if add["code"] != 0:
        return {"ok": False, "committed": False, "reason": f"git-add-failed: {add['err'][:200]}", "paths": rels}

    if claim_paths:
        return _claim_transaction_commit(
            root,
            rels,
            claim_paths,
            message=message,
        )

    commit_env = dict(os.environ)
    commit_env.pop(CLAIM_COMMIT_TRANSACTION_ENV, None)
    commit = _git(
        root,
        ["commit", "-m", message, "--", *rels],
        env=commit_env,
    )
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
