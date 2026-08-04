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
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

CLAIMS_REL = "agents/runtime/task_claims"
CLAIM_COMMIT_TRANSACTION_ENV = "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION"
CLAIM_COMMIT_TRANSACTION_SCHEMA = "agent-runtime-claim-commit-transaction/v2"
CLAIM_REF_ENV_PREFIX = "AGENT_RUNTIME_CLAIM_REF_"
CLAIM_REF_ROOT_ENV = f"{CLAIM_REF_ENV_PREFIX}ROOT"
CLAIM_REF_EXPECTED_ENV = f"{CLAIM_REF_ENV_PREFIX}EXPECTED"
CLAIM_REF_OLD_ENV = f"{CLAIM_REF_ENV_PREFIX}OLD"
CLAIM_REF_NEW_ENV = f"{CLAIM_REF_ENV_PREFIX}NEW"
CLAIM_REF_HEAD_LOCK_ENV = f"{CLAIM_REF_ENV_PREFIX}HEAD_LOCK"
CLAIM_REF_HEAD_PATH_ENV = f"{CLAIM_REF_ENV_PREFIX}HEAD_PATH"
CLAIM_REF_HEAD_DEVICE_ENV = f"{CLAIM_REF_ENV_PREFIX}HEAD_DEVICE"
CLAIM_REF_HEAD_INODE_ENV = f"{CLAIM_REF_ENV_PREFIX}HEAD_INODE"
CLAIM_REF_ORIGINAL_HOOK_ENV = f"{CLAIM_REF_ENV_PREFIX}ORIGINAL_HOOK"
OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
REPOSITORY_LOCAL_GIT_ENV = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_DIR",
        "GIT_GRAFT_FILE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_INTERNAL_SUPER_PREFIX",
        "GIT_NAMESPACE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_QUARANTINE_PATH",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    }
)

REFERENCE_TRANSACTION_HOOK = r"""#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path

PREFIX = "AGENT_RUNTIME_CLAIM_REF_"


def _run(command, *, root, env, stdin=b""):
    try:
        return subprocess.run(
            command,
            cwd=root,
            env=env,
            input=stdin,
            capture_output=True,
            timeout=30,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(command, 127, b"", repr(exc).encode())


def _forward(proc):
    if proc.stdout:
        sys.stdout.buffer.write(proc.stdout)
    if proc.stderr:
        sys.stderr.buffer.write(proc.stderr)
    return proc.returncode


def _prepared_error(raw, *, env, root, expected_ref, old_oid, new_oid, expected_lock):
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        return "symbolic HEAD identity seal unsupported"
    head_path_text = env.get(f"{PREFIX}HEAD_PATH", "")
    expected_device = env.get(f"{PREFIX}HEAD_DEVICE", "")
    expected_inode = env.get(f"{PREFIX}HEAD_INODE", "")
    if not head_path_text or not expected_device or not expected_inode:
        return "missing sealed HEAD identity"
    try:
        expected_token = (int(expected_device), int(expected_inode))
    except ValueError:
        return "invalid sealed HEAD identity"

    symbolic = _run(
        ["git", "symbolic-ref", "-q", "HEAD"],
        root=root,
        env=env,
    )
    head = _run(["git", "rev-parse", "HEAD"], root=root, env=env)
    lock = _run(
        ["git", "rev-parse", "--git-path", "HEAD.lock"],
        root=root,
        env=env,
    )
    lock_text = lock.stdout.decode("utf-8", "replace").strip()
    lock_path = Path(lock_text)
    if not lock_path.is_absolute():
        lock_path = Path(root) / lock_path
    expected_lock_path = Path(expected_lock)
    head_path = Path(head_path_text)
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(head_path, flags)
        try:
            head_stat = os.fstat(descriptor)
            head_content = os.read(descriptor, 4096)
        finally:
            os.close(descriptor)
        lock_stat = os.lstat(lock_path)
    except OSError:
        return "sealed HEAD or Git-owned lock unavailable"

    lines = raw.decode("utf-8", "replace").splitlines()
    # Git changed what it reports for the symbolic HEAD in a
    # reference-transaction payload. Measured directly:
    #   git 2.34.1 -> "<old> <new> HEAD"
    #   git 2.47.3 -> "<zeros> <new> HEAD"
    # while the branch ref keeps the real old oid in both. Pinning the 2.34
    # shape made every claim-commit transaction fail on any modern git, which
    # is why this passed locally and failed in CI.
    #
    # Only HEAD's old field is relaxed. The branch-ref line still requires the
    # exact old oid, and that line is what carries the compare-and-swap
    # guarantee, so the sealing property is unchanged.
    zero_oid = "0" * len(old_oid)
    expected_ref_line = f"{old_oid} {new_oid} {expected_ref}"
    accepted_head_lines = {
        f"{old_oid} {new_oid} HEAD",
        f"{zero_oid} {new_oid} HEAD",
    }
    head_lines = [line for line in lines if line.endswith(" HEAD")]
    ref_lines = [line for line in lines if line == expected_ref_line]
    payload_ok = (
        len(lines) == 2
        and len(head_lines) == 1
        and len(ref_lines) == 1
        and head_lines[0] in accepted_head_lines
    )
    if (
        symbolic.returncode != 0
        or symbolic.stdout.decode("utf-8", "replace").strip() != expected_ref
        or head.returncode != 0
        or head.stdout.decode("utf-8", "replace").strip() != old_oid
        or lock.returncode != 0
        or os.path.normcase(os.path.abspath(lock_path))
        != os.path.normcase(os.path.abspath(expected_lock_path))
        or not stat.S_ISREG(lock_stat.st_mode)
        or not stat.S_ISREG(head_stat.st_mode)
        or head_stat.st_nlink != 1
        or (head_stat.st_dev, head_stat.st_ino) != expected_token
        or head_content != f"ref: {expected_ref}\n".encode()
        or not payload_ok
    ):
        return "sealed HEAD/ref mismatch"
    return ""


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepared", "committed", "aborted"}:
        print("claim-guard reference transaction: invalid state", file=sys.stderr)
        return 2
    state = sys.argv[1]
    raw = sys.stdin.buffer.read()
    env = dict(os.environ)
    root = env.get(f"{PREFIX}ROOT", "")
    expected_ref = env.get(f"{PREFIX}EXPECTED", "")
    old_oid = env.get(f"{PREFIX}OLD", "")
    new_oid = env.get(f"{PREFIX}NEW", "")
    expected_lock = env.get(f"{PREFIX}HEAD_LOCK", "")
    if not root or not expected_ref or not old_oid or not new_oid or not expected_lock:
        print("claim-guard reference transaction: missing sealed environment", file=sys.stderr)
        return 1

    if state == "prepared":
        error = _prepared_error(
            raw,
            env=env,
            root=root,
            expected_ref=expected_ref,
            old_oid=old_oid,
            new_oid=new_oid,
            expected_lock=expected_lock,
        )
        if error:
            print(f"claim-guard reference transaction: {error}", file=sys.stderr)
            return 1

    original = env.get(f"{PREFIX}ORIGINAL_HOOK", "")
    hook = Path(original) if original else None
    if hook is not None and hook.is_file():
        try:
            if hook.resolve() == Path(__file__).resolve():
                print(
                    "claim-guard reference transaction: recursive hook alias",
                    file=sys.stderr,
                )
                return 1
        except OSError:
            print(
                "claim-guard reference transaction: hook identity unavailable",
                file=sys.stderr,
            )
            return 1

        delegated_env = dict(env)
        for key in list(delegated_env):
            if key.startswith("GIT_CONFIG_") or key.startswith(PREFIX):
                delegated_env.pop(key, None)
        discovered = _run(
            ["git", "rev-parse", "--git-path", "hooks/reference-transaction"],
            root=root,
            env=delegated_env,
        )
        discovered_path = Path(
            discovered.stdout.decode("utf-8", "replace").strip()
        )
        if not discovered_path.is_absolute():
            discovered_path = Path(root) / discovered_path
        try:
            same_hook = (
                discovered.returncode == 0
                and discovered_path.resolve() == hook.resolve()
            )
        except OSError:
            same_hook = False
        if not same_hook:
            print(
                "claim-guard reference transaction: configured hook changed",
                file=sys.stderr,
            )
            return 1

        version = _run(["git", "version"], root=root, env=delegated_env)
        match = re.search(rb"(\d+)\.(\d+)", version.stdout)
        hook_run = bool(
            version.returncode == 0
            and match
            and (int(match.group(1)), int(match.group(2))) >= (2, 36)
        )
        if hook_run:
            proc = _run(
                [
                    "git",
                    "hook",
                    "run",
                    "--ignore-missing",
                    "reference-transaction",
                    "--",
                    state,
                ],
                root=root,
                env=delegated_env,
                stdin=raw,
            )
        elif os.name == "nt":
            print(
                "claim-guard reference transaction: Git >=2.36 required "
                "for configured hooks on Windows",
                file=sys.stderr,
            )
            return 127
        elif not os.access(hook, os.X_OK):
            proc = subprocess.CompletedProcess([], 0, b"", b"")
        else:
            proc = _run(
                [str(hook), state],
                root=root,
                env=delegated_env,
                stdin=raw,
            )
        if _forward(proc) != 0:
            return proc.returncode

    if state == "prepared":
        error = _prepared_error(
            raw,
            env=env,
            root=root,
            expected_ref=expected_ref,
            old_oid=old_oid,
            new_oid=new_oid,
            expected_lock=expected_lock,
        )
        if error:
            print(
                f"claim-guard reference transaction: post-delegation {error}",
                file=sys.stderr,
            )
            return 1
    return 0


raise SystemExit(main())
"""


def _repository_env(source: dict[str, str] | None = None) -> dict[str, str]:
    """Return an environment that cannot redirect this transaction to another repo."""

    env = dict(os.environ if source is None else source)
    for key in list(env):
        if (
            key in REPOSITORY_LOCAL_GIT_ENV
            or key.startswith("GIT_CONFIG_")
            or key.startswith(CLAIM_REF_ENV_PREFIX)
        ):
            env.pop(key, None)
    env.pop(CLAIM_COMMIT_TRANSACTION_ENV, None)
    return env


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
    result = _git(
        Path(root),
        ["rev-parse", "--is-inside-work-tree"],
        env=_repository_env(),
    )
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
            not name.casefold().startswith(".claim-store")
            or rel == f"{CLAIMS_REL}/.claim-store"
        )
        and (
            rel == f"{CLAIMS_REL}/.claim-store"
            or path.suffix == ".json"
            or name.endswith(".handoff.md")
            or name.endswith(".log.md")
        )
    )


def _git_path(
    root: Path,
    relative: str,
    *,
    env: dict[str, str] | None = None,
) -> Path | None:
    resolved = _git(root, ["rev-parse", "--git-path", relative], env=env)
    if resolved["code"] != 0 or not resolved["out"].strip():
        return None
    path = Path(resolved["out"].strip())
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _git_admin_dirs(
    root: Path,
    *,
    env: dict[str, str],
) -> tuple[Path, Path] | None:
    git_dir = _git(root, ["rev-parse", "--absolute-git-dir"], env=env)
    common_dir = _git(root, ["rev-parse", "--git-common-dir"], env=env)
    if git_dir["code"] != 0 or common_dir["code"] != 0:
        return None
    git_path = Path(git_dir["out"].strip())
    common_path = Path(common_dir["out"].strip())
    if not git_path.is_absolute():
        git_path = root / git_path
    if not common_path.is_absolute():
        common_path = root / common_path
    git_path = git_path.resolve()
    common_path = common_path.resolve()
    if not git_path.is_dir() or not common_path.is_dir():
        return None
    return git_path, common_path


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


def _working_blob(root: Path, rel: str, *, env: dict[str, str]) -> str:
    result = _git(root, ["hash-object", f"--path={rel}", rel], env=env)
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

    version = _git(root, ["version"], env=env)
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

    hook_path = _git_path(root, f"hooks/{name}", env=env)
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
    env: dict[str, str],
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
        env=env,
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


def _write_private_file(path: Path, content: str) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    os.chmod(path, 0o600)


def _cleanup_ref_context(path: Path | None) -> None:
    """Remove only the files this transaction owns; never recurse into Git state."""

    if path is None:
        return
    for name in ("reference-transaction",):
        _cleanup_private_path(path / name)
    try:
        path.rmdir()
    except OSError:
        pass


def _create_ref_context(
    git_dir: Path,
    *,
    nonce: str,
) -> Path | None:
    """Create a private hook context for Git's actual-HEAD ref transaction."""

    parent = git_dir / "agent-runtime" / "claim-commit"
    context = parent / f"{nonce}.hooks"
    interpreter = str(Path(sys.executable).resolve())
    if (
        not interpreter
        or len(interpreter.encode("utf-8")) > 120
        or any(character.isspace() for character in interpreter)
    ):
        return None
    hook_source = REFERENCE_TRANSACTION_HOOK.replace(
        "#!/usr/bin/env python3",
        f"#!{interpreter}",
        1,
    )
    try:
        parent.mkdir(parents=True, exist_ok=True)
        os.chmod(parent, 0o700)
        os.mkdir(context, 0o700)
        os.chmod(context, 0o700)
        hook_path = context / "reference-transaction"
        _write_private_file(hook_path, hook_source)
        os.chmod(hook_path, 0o700)
    except OSError:
        _cleanup_ref_context(context)
        return None
    return context


def _read_descriptor(descriptor: int, *, limit: int = 4096) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    return os.read(descriptor, limit)


def _open_sealed_head(
    path: Path,
    *,
    symbolic_ref: str,
) -> tuple[int, tuple[int, int]] | None:
    """Hold the authorized symbolic-HEAD inode across Git's lock handoff."""

    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        return None
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or _read_descriptor(descriptor)
            != f"ref: {symbolic_ref}\n".encode("utf-8")
        ):
            os.close(descriptor)
            return None
        return descriptor, (metadata.st_dev, metadata.st_ino)
    except OSError:
        os.close(descriptor)
        return None


def _sealed_head_identity_error(
    path: Path,
    descriptor: int,
    *,
    symbolic_ref: str,
) -> str:
    """Verify that no Git lockfile rewrite replaced symbolic HEAD."""

    try:
        held = os.fstat(descriptor)
        current = os.lstat(path)
        content = _read_descriptor(descriptor)
    except OSError:
        return "claim-commit-sealed-head-unavailable"
    if (
        not stat.S_ISREG(held.st_mode)
        or not stat.S_ISREG(current.st_mode)
        or held.st_nlink != 1
        or current.st_nlink != 1
        or (held.st_dev, held.st_ino) != (current.st_dev, current.st_ino)
        or content != f"ref: {symbolic_ref}\n".encode("utf-8")
    ):
        return "claim-commit-sealed-head-identity-changed"
    return ""


def _path_entry_exists(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _acquire_owned_lock(path: Path) -> tuple[int, int] | None:
    """Create a cooperative Git lock and return its device/inode ownership token."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError:
        return None
    try:
        try:
            os.fchmod(descriptor, 0o600)
        except (AttributeError, OSError):
            pass
        stat = os.fstat(descriptor)
        return stat.st_dev, stat.st_ino
    finally:
        os.close(descriptor)


def _release_owned_lock(path: Path | None, token: tuple[int, int] | None) -> None:
    if path is None or token is None:
        return
    try:
        stat = path.lstat()
        if (stat.st_dev, stat.st_ino) == token:
            path.unlink()
    except OSError:
        pass


def _transaction_state_error(
    root: Path,
    *,
    artifacts: list[dict[str, str]],
    index_env: dict[str, str],
    real_env: dict[str, str],
    start_head: str,
    symbolic_ref: str,
    tree_oid: str,
    transaction_path: Path,
    transaction_raw: str,
    message_path: Path,
) -> str:
    current_tree = _git(root, ["write-tree"], env=index_env)
    if current_tree["code"] != 0 or current_tree["out"].strip() != tree_oid:
        return "claim-commit-transaction-tree-changed"
    for artifact in artifacts:
        if (
            _working_blob(root, artifact["path"], env=real_env)
            != artifact["oid"]
        ):
            return "claim-commit-transaction-working-blob-changed"
    current_head = _git(root, ["rev-parse", "HEAD"], env=real_env)
    current_ref = _git(root, ["symbolic-ref", "-q", "HEAD"], env=real_env)
    if (
        current_head["code"] != 0
        or current_head["out"].strip() != start_head
        or current_ref["code"] != 0
        or current_ref["out"].strip() != symbolic_ref
    ):
        return "claim-commit-ref-moved"
    try:
        persisted = transaction_path.read_text(encoding="utf-8")
    except OSError:
        persisted = ""
    if persisted != transaction_raw + "\n":
        return "claim-commit-transaction-record-changed"
    try:
        commit_message = message_path.read_text(encoding="utf-8")
    except OSError:
        commit_message = ""
    if not commit_message.strip():
        return "claim-commit-message-empty"
    return ""


def _reflog_transition_error(
    root: Path,
    ref: str,
    *,
    old_oid: str,
    new_oid: str,
    action: str,
    env: dict[str, str],
) -> str:
    path = _git_path(root, f"logs/{ref}", env=env)
    if path is None:
        return "claim-commit-reflog-missing"
    try:
        lines = path.read_bytes().splitlines()
    except OSError:
        return "claim-commit-reflog-unreadable"
    if not lines:
        return "claim-commit-reflog-empty"
    line = lines[-1].decode("utf-8", "replace")
    prefix, separator, recorded_action = line.partition("\t")
    fields = prefix.split()
    if (
        not separator
        or len(fields) < 2
        or fields[0] != old_oid
        or fields[1] != new_oid
        or recorded_action != action
    ):
        return "claim-commit-reflog-transition-mismatch"
    return ""


def _publication_state_error(
    root: Path,
    *,
    real_env: dict[str, str],
    symbolic_ref: str,
    start_head: str,
    commit_oid: str,
    reflog_action: str,
) -> str:
    published_ref = _git(root, ["symbolic-ref", "-q", "HEAD"], env=real_env)
    published_head = _git(root, ["rev-parse", "HEAD"], env=real_env)
    if (
        published_ref["code"] != 0
        or published_ref["out"].strip() != symbolic_ref
        or published_head["code"] != 0
        or published_head["out"].strip() != commit_oid
    ):
        return "claim-commit-publication-verification-failed"
    for ref in ("HEAD", symbolic_ref):
        error = _reflog_transition_error(
            root,
            ref,
            old_oid=start_head,
            new_oid=commit_oid,
            action=reflog_action,
            env=real_env,
        )
        if error:
            return error
    return ""


def _claim_transaction_commit(
    root: Path,
    rels: list[str],
    claim_paths: list[str],
    *,
    message: str,
) -> dict[str, Any]:
    real_env = _repository_env()
    head = _git(root, ["rev-parse", "HEAD"], env=real_env)
    ref = _git(root, ["symbolic-ref", "-q", "HEAD"], env=real_env)
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
    admin_dirs = _git_admin_dirs(root, env=real_env)
    if admin_dirs is None:
        return {
            "ok": False,
            "committed": False,
            "reason": "claim-commit-git-admin-path-failed",
            "paths": rels,
        }
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        return {
            "ok": False,
            "committed": False,
            "reason": "claim-commit-symbolic-head-seal-unsupported",
            "paths": rels,
        }
    git_dir, _common_dir = admin_dirs
    nonce = secrets.token_hex(16)
    index_path = _git_path(
        root,
        f"agent-runtime/claim-commit/{nonce}.index",
        env=real_env,
    )
    message_path = _git_path(
        root,
        f"agent-runtime/claim-commit/{nonce}.message",
        env=real_env,
    )
    if index_path is None or message_path is None:
        return {
            "ok": False,
            "committed": False,
            "reason": "claim-commit-private-path-failed",
            "paths": rels,
        }

    index_env = dict(real_env)
    index_env["GIT_INDEX_FILE"] = str(index_path)
    transaction_path: Path | None = None
    ref_context: Path | None = None
    sealed_head_descriptor: int | None = None
    head_lock_path: Path | None = None
    head_lock_token: tuple[int, int] | None = None
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
        # `git add` writes a lock file and renames it over the index, so the
        # inode changes and the chmod above was applied to a file object git
        # then discarded. The mode comes back as 0666 & ~umask, and
        # parallel_worktree_gate rejects any private index with group or other
        # bits set - so under any umask looser than 0077 the gate refuses to
        # recognise this very transaction and reports the claim as
        # authorized-but-not-persisted. Re-apply and verify after every git
        # invocation that can replace the index.
        if not _harden_private_index(index_path):
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-private-index-permission-failed",
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
        if not _harden_private_index(index_path):
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-private-index-permission-failed",
                "paths": rels,
            }
        tree_oid = sealed["out"].strip()
        if sealed["code"] != 0 or OID_RE.fullmatch(tree_oid) is None:
            return {
                "ok": False,
                "committed": False,
                "reason": f"claim-commit-write-tree-failed: {sealed['err'][:200]}",
                "paths": rels,
            }
        head_tree = _git(
            root,
            ["rev-parse", f"{start_head}^{{tree}}"],
            env=real_env,
        )
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
            env=real_env,
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

        state_error = _transaction_state_error(
            root,
            artifacts=artifacts,
            index_env=index_env,
            real_env=real_env,
            start_head=start_head,
            symbolic_ref=symbolic_ref,
            tree_oid=tree_oid,
            transaction_path=transaction_path,
            transaction_raw=raw,
            message_path=message_path,
        )
        if state_error:
            return {
                "ok": False,
                "committed": False,
                "reason": state_error,
                "paths": rels,
            }

        commit_env = dict(real_env)
        commit_args = ["commit-tree", tree_oid, "-p", start_head, "-F", str(message_path)]
        signing = _git(
            root,
            ["config", "--bool", "commit.gpgSign"],
            env=commit_env,
        )
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
        head_path = git_dir / "HEAD"
        sealed_head = _open_sealed_head(
            head_path,
            symbolic_ref=symbolic_ref,
        )
        if sealed_head is None:
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-symbolic-head-seal-failed",
                "paths": rels,
            }
        sealed_head_descriptor, sealed_head_token = sealed_head
        ref_context = _create_ref_context(git_dir, nonce=nonce)
        if ref_context is None:
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-ref-context-failed",
                "paths": rels,
            }
        original_reference_hook = _git_path(
            root,
            "hooks/reference-transaction",
            env=real_env,
        )
        ref_env = dict(real_env)
        ref_env["GIT_CONFIG_COUNT"] = "1"
        ref_env["GIT_CONFIG_KEY_0"] = "core.hooksPath"
        ref_env["GIT_CONFIG_VALUE_0"] = str(ref_context)
        ref_env[CLAIM_REF_ROOT_ENV] = str(root.resolve())
        ref_env[CLAIM_REF_EXPECTED_ENV] = symbolic_ref
        ref_env[CLAIM_REF_OLD_ENV] = start_head
        ref_env[CLAIM_REF_NEW_ENV] = commit_oid
        head_lock_path = git_dir / "HEAD.lock"
        ref_env[CLAIM_REF_HEAD_LOCK_ENV] = str(head_lock_path.resolve())
        ref_env[CLAIM_REF_HEAD_PATH_ENV] = str(head_path.absolute())
        ref_env[CLAIM_REF_HEAD_DEVICE_ENV] = str(sealed_head_token[0])
        ref_env[CLAIM_REF_HEAD_INODE_ENV] = str(sealed_head_token[1])
        ref_env[CLAIM_REF_ORIGINAL_HOOK_ENV] = (
            str(original_reference_hook)
            if original_reference_hook is not None
            else ""
        )
        if _path_entry_exists(head_lock_path):
            return {
                "ok": False,
                "committed": False,
                "reason": "claim-commit-head-lock-unavailable",
                "paths": rels,
            }
        reflog_action = f"claim-guard: {' '.join(message.splitlines()).strip()}"
        post: dict[str, Any] = {"code": 0, "out": "", "err": ""}
        state_error = _transaction_state_error(
            root,
            artifacts=artifacts,
            index_env=index_env,
            real_env=real_env,
            start_head=start_head,
            symbolic_ref=symbolic_ref,
            tree_oid=tree_oid,
            transaction_path=transaction_path,
            transaction_raw=raw,
            message_path=message_path,
        )
        if state_error:
            return {
                "ok": False,
                "committed": False,
                "reason": state_error,
                "paths": rels,
            }
        update = _git(
            root,
            [
                "update-ref",
                "--create-reflog",
                "-m",
                reflog_action,
                "HEAD",
                commit_oid,
                start_head,
            ],
            env=ref_env,
        )
        if update["code"] != 0:
            return {
                "ok": False,
                "committed": False,
                "reason": (
                    "claim-commit-ref-update-failed: "
                    f"{update['err'][:200]}"
                ),
                "paths": rels,
            }
        head_lock_token = _acquire_owned_lock(head_lock_path)
        if head_lock_token is None:
            return {
                "ok": False,
                "committed": True,
                "reason": "claim-commit-post-publication-head-lock-unavailable",
                "publication_state": "published_unverified",
                "paths": rels,
                "commit": commit_oid,
                "tree": tree_oid,
            }
        try:
            state_error = _sealed_head_identity_error(
                head_path,
                sealed_head_descriptor,
                symbolic_ref=symbolic_ref,
            )
            if not state_error:
                state_error = _publication_state_error(
                    root,
                    real_env=real_env,
                    symbolic_ref=symbolic_ref,
                    start_head=start_head,
                    commit_oid=commit_oid,
                    reflog_action=reflog_action,
                )
            if state_error:
                return {
                    "ok": False,
                    "committed": True,
                    "reason": state_error,
                    "publication_state": "published_unverified",
                    "paths": rels,
                    "commit": commit_oid,
                    "tree": tree_oid,
                }
            post = _run_hook(root, "post-commit", env=commit_env)
            state_error = _sealed_head_identity_error(
                head_path,
                sealed_head_descriptor,
                symbolic_ref=symbolic_ref,
            )
            if not state_error:
                state_error = _publication_state_error(
                    root,
                    real_env=real_env,
                    symbolic_ref=symbolic_ref,
                    start_head=start_head,
                    commit_oid=commit_oid,
                    reflog_action=reflog_action,
                )
            if state_error:
                return {
                    "ok": False,
                    "committed": True,
                    "reason": state_error,
                    "publication_state": "published_unverified",
                    "paths": rels,
                    "commit": commit_oid,
                    "tree": tree_oid,
                }
        finally:
            _release_owned_lock(head_lock_path, head_lock_token)
            head_lock_token = None

        result: dict[str, Any] = {
            "ok": True,
            "committed": True,
            "publication_state": "verified",
            "paths": rels,
            "commit": commit_oid,
            "tree": tree_oid,
        }
        if post["code"] != 0:
            result["post_commit_warning"] = (post["err"] or post["out"])[:200]
        return result
    finally:
        _release_owned_lock(head_lock_path, head_lock_token)
        if sealed_head_descriptor is not None:
            try:
                os.close(sealed_head_descriptor)
            except OSError:
                pass
        _cleanup_ref_context(ref_context)
        _cleanup_private_path(transaction_path)
        _cleanup_private_path(index_path)
        _cleanup_private_path(message_path)


def commit_paths(root: Path, paths: Iterable[Path], *, message: str, apply: bool = True) -> dict[str, Any]:
    """Commit ONLY the given paths (other staged/untracked work is left untouched)."""
    root = Path(root)
    real_env = _repository_env()
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
    add = _git(root, ["add", "--", *rels], env=real_env)
    if add["code"] != 0:
        return {"ok": False, "committed": False, "reason": f"git-add-failed: {add['err'][:200]}", "paths": rels}

    if claim_paths:
        return _claim_transaction_commit(
            root,
            rels,
            claim_paths,
            message=message,
        )

    commit_env = dict(real_env)
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


def _harden_private_index(index_path: Path) -> bool:
    """Force 0600 on the private index and confirm it stuck.

    Called after every git invocation that can replace the index file, because
    git writes a lock and renames it into place rather than editing in situ.
    Verifying rather than assuming is deliberate: the failure this guards is
    silent, and it disables the claim-commit transaction wholesale.
    """

    try:
        os.chmod(index_path, 0o600)
        return not (index_path.stat().st_mode & 0o077)
    except OSError:
        return False


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
    status = _git(
        root,
        ["status", "--porcelain", "--untracked-files=all", "--", CLAIMS_REL],
        env=_repository_env(),
    )
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
            if not result.get("ok") and result.get("committed"):
                verb = "published but unverified; DO NOT RETRY"
            elif not result.get("ok"):
                verb = "failed to commit"
            else:
                verb = "committed" if result.get("committed") else "would commit"
            print(f"{verb} {len(result['paths'])} untracked claim file(s): {', '.join(result['paths'])}")
        else:
            print("no untracked claim files")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
