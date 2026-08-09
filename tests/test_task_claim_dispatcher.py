from __future__ import annotations

import base64
import importlib.util
import hashlib
import json
import os
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from agent_runtime import claim_store, knowledge_records


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "task_claim_dispatcher.py"
GATE = REPO_ROOT / "scripts" / "parallel_worktree_gate.py"
CONCURRENCY_GATE = REPO_ROOT / "scripts" / "collaboration_concurrency_gate.py"
IDENTITY_GATE = REPO_ROOT / "scripts" / "agent_identity_gate.py"
ATTRIBUTION_GATE = REPO_ROOT / "scripts" / "attribution_gate.py"


def _fixture_work_uid(kind: str, display_id: str) -> str:
    digest = bytearray(
        hashlib.sha256(
            f"agent-runtime-test:{kind}:{display_id}".encode("utf-8")
        ).digest()[:16]
    )
    # Keep fixtures deterministic while honoring the production v4/v7
    # contract: set the RFC version and variant bits exactly as UUIDv4.
    digest[6] = (digest[6] & 0x0F) | 0x40
    digest[8] = (digest[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(digest)))


def _fixture_task_set_id(task_id: str) -> str:
    return "TASKSET-AR-FIXTURE-" + hashlib.sha256(
        task_id.encode("utf-8")
    ).hexdigest()[:16].upper()


def _write_canonical_task_identity(
    root: Path,
    task_id: str,
    *,
    task_set_id: str = "",
) -> Path:
    """Provision the canonical identity authority legacy fixtures omitted."""

    task_uid = _fixture_work_uid("task", task_id)
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "schema_version: agent-runtime-work-item/v1",
        f"id: {task_id}",
        f"display_id: {task_id}",
        f"task_uid: {task_uid}",
        f"work_id: {task_id}",
        f"work_uid: {task_uid}",
        "kind: task",
    ]
    lines.append(f"task_set_id: {task_set_id or _fixture_task_set_id(task_id)}")
    lines.extend(
        [
            "---",
            "",
            "# Canonical task identity fixture",
            "",
        ]
    )
    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    return path


def _load_dispatcher_module():
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "task_claim_dispatcher_transaction_test",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _routing_off_env() -> dict[str, str]:
    """Pin the dormant-role routing flags OFF so these baseline claim-lifecycle
    tests assert the unchanged behavior deterministically, regardless of an
    ambient flag in the developer's shell (the live review-routing seam is
    exercised in tests/test_role_routing_wiring.py).

    The dispatcher runs the installed security gate from the fixture host as a
    nested subprocess. Pin the package under test with an absolute path so a
    relative ambient ``PYTHONPATH=src`` cannot resolve against that temporary
    host or an editable install from a different Git worktree.
    """
    env = dict(os.environ)
    source_root = str((REPO_ROOT / "src").resolve())
    ambient_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        os.pathsep.join((source_root, ambient_pythonpath))
        if ambient_pythonpath
        else source_root
    )
    for flag in ("AR_ROLE_ROUTING", "AR_SCOUT_COUNCIL", "AR_BETA_ACTIVATION"):
        env.pop(flag, None)
    # Claim SCM policy must be explicit in each regression. An ambient setting
    # must never turn a nominal host test into a committing test.
    env.pop("AGENT_RUNTIME_CLAIM_AUTOCOMMIT", None)
    return env


def _run_dispatcher(
    root: Path,
    *args: str,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = _routing_off_env()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _run_gate(
    root: Path,
    *,
    now: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(GATE), "--root", str(root), "--check"]
    if now is not None:
        command.extend(("--now", now))
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_concurrency_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONCURRENCY_GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_identity_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(IDENTITY_GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_attribution_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ATTRIBUTION_GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_worktree(
    root: Path,
    task_id: str,
    *,
    task_set_id: str = "",
) -> None:
    _write_canonical_task_identity(root, task_id, task_set_id=task_set_id)
    worktree = root / ".worktrees" / task_id
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")


def _run_git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _git_stdout(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def _claim_store_outer_anchor(root: Path) -> Path:
    git_dir = Path(_git_stdout(root, "rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    return git_dir.resolve() / "agent-runtime" / "task-claim-store"


def _init_git_worktree(tmp_path: Path, name: str) -> tuple[Path, Path]:
    primary = tmp_path / name
    primary.mkdir()
    _run_git(primary, "init")
    _run_git(primary, "config", "user.email", "dispatcher-test@example.invalid")
    _run_git(primary, "config", "user.name", "Dispatcher Test")
    (primary / "README.md").write_text("fixture\n", encoding="utf-8")
    _run_git(primary, "add", "README.md")
    _run_git(primary, "commit", "-m", "fixture")
    linked = tmp_path / f"{name}-linked"
    _run_git(primary, "worktree", "add", "-b", f"{name}-worker", str(linked))
    return primary, linked


def _create_linked_claim(
    linked: Path,
    *,
    suffix: str,
    extra_args: tuple[str, ...] = (),
    env_overrides: dict[str, str] | None = None,
    provision_identity: bool = True,
) -> subprocess.CompletedProcess[str]:
    task_id = f"TASK-AR-{suffix}"
    identity_args: tuple[str, ...] = ()
    if provision_identity:
        task_set_id = _fixture_task_set_id(task_id)
        _write_canonical_task_identity(
            linked,
            task_id,
            task_set_id=task_set_id,
        )
        identity_args = ("--task-set-id", task_set_id)
    return _run_dispatcher(
        linked,
        "create",
        "--task-id",
        task_id,
        "--worktree-path",
        ".",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T08:00:00+09:00",
        "--suffix",
        suffix,
        "--json",
        *identity_args,
        *extra_args,
        env_overrides=env_overrides,
    )


def _tree_entry_snapshot(root: Path) -> dict[str, bytes]:
    """Capture files *and* directories so rejected creates leave no residue."""

    if not root.exists():
        return {}
    snapshot: dict[str, bytes] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        if path.is_symlink():
            snapshot[relative] = ("symlink:" + os.readlink(path)).encode("utf-8")
        elif path.is_dir():
            snapshot[relative] = b"directory"
        elif path.is_file():
            snapshot[relative] = path.read_bytes()
    return snapshot


def _claim_create_mutation_snapshot(root: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Capture checkout and checkout-admin claim authority surfaces."""

    outer_runtime_dir = _claim_store_outer_anchor(root).parent
    return _tree_entry_snapshot(root), _tree_entry_snapshot(outer_runtime_dir)


@pytest.mark.parametrize("lease_minutes", ("-1", "0"))
def test_create_cli_refuses_nonpositive_lease_before_any_mutation(
    tmp_path: Path,
    lease_minutes: str,
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        f"create-invalid-lease-{lease_minutes.replace('-', 'negative')}",
    )
    before = _claim_create_mutation_snapshot(linked)

    result = _create_linked_claim(
        linked,
        suffix=f"655-invalid-{lease_minutes.replace('-', 'negative')}",
        extra_args=("--lease-minutes", lease_minutes),
        provision_identity=False,
    )

    assert result.returncode != 0
    assert "Traceback" not in result.stdout + result.stderr
    assert _claim_create_mutation_snapshot(linked) == before


def test_create_cli_refuses_overflowing_lease_without_traceback_or_residue(
    tmp_path: Path,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "create-overflowing-lease")
    before = _claim_create_mutation_snapshot(linked)

    result = _create_linked_claim(
        linked,
        suffix="655-overflow",
        extra_args=("--lease-minutes", "100000000000000000000"),
        provision_identity=False,
    )

    assert result.returncode != 0
    assert "Traceback" not in result.stdout + result.stderr
    assert _claim_create_mutation_snapshot(linked) == before


@pytest.mark.parametrize("lease_minutes", (True, False))
def test_create_api_refuses_boolean_lease_before_any_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lease_minutes: bool,
) -> None:
    module = _load_dispatcher_module()
    _primary, linked = _init_git_worktree(
        tmp_path,
        f"create-boolean-lease-{str(lease_minutes).lower()}",
    )
    for flag in (
        "AR_ROLE_ROUTING",
        "AR_SCOUT_COUNCIL",
        "AR_BETA_ACTIVATION",
        "AGENT_RUNTIME_CLAIM_AUTOCOMMIT",
    ):
        monkeypatch.delenv(flag, raising=False)
    args = module.build_parser().parse_args(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            f"TASK-AR-655-bool-{str(lease_minutes).lower()}",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:00:00+09:00",
            "--suffix",
            f"655-bool-{str(lease_minutes).lower()}",
            "--json",
        ]
    )
    args.lease_minutes = lease_minutes
    before = _claim_create_mutation_snapshot(linked)

    result = args.func(args)

    assert result != 0
    assert _claim_create_mutation_snapshot(linked) == before


def test_create_one_minute_lease_preserves_exact_boundary(tmp_path: Path) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "create-one-minute-lease")

    result = _create_linked_claim(
        linked,
        suffix="655-one-minute",
        extra_args=("--lease-minutes", "1"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    claim = json.loads(result.stdout)["claim"]
    claimed_at = datetime.fromisoformat(claim["claimed_at"])
    expires_at = datetime.fromisoformat(claim["expires_at"])
    assert (expires_at - claimed_at).total_seconds() == 60
    assert claim["lease"]["expires_at"] == claim["expires_at"]


# One level past the declared bound. Derived, never hardcoded: the old fixtures
# used 1100/1200 to overflow CPython's recursion limit, so the refusal was a
# parser side effect that silently disappeared on 3.12+.
_OVER_DEPTH = claim_store.CLAIM_MAX_JSON_DEPTH + 1


def _adversarial_claim_bytes(
    payload_kind: str,
    *,
    claim_id: str,
    task_id: str,
) -> bytes:
    base: dict[str, object] = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "agent_role": "lead-engineer",
        "status": "claimed",
    }
    if payload_kind == "oversized-malformed":
        return json.dumps(base).encode("utf-8") + b"x" * (256 * 1024 + 1)
    if payload_kind == "deep":
        return (
            json.dumps(base)[:-1]
            + ',"nested":'
            + "[" * _OVER_DEPTH
            + "0"
            + "]" * _OVER_DEPTH
            + "}"
        ).encode("utf-8")
    if payload_kind == "invalid-utf8":
        return json.dumps(base).encode("utf-8") + b"\xff"
    if payload_kind == "unknown-status":
        base["status"] = "mystery"
        return json.dumps(base).encode("utf-8")
    if payload_kind == "nonstring-status":
        base["status"] = ["claimed"]
        return json.dumps(base).encode("utf-8")
    return (
        json.dumps(base)[:-1]
        + ',"integer":'
        + "9" * 1000
        + "}"
    ).encode("utf-8")


def test_default_claim_creation_persists_files_without_changing_host_head(
    tmp_path: Path,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "default-files-only")
    before = _git_stdout(linked, "rev-parse", "HEAD")

    result = _create_linked_claim(linked, suffix="648-default")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert (linked / payload["path"]).is_file()
    assert payload["claim"]["persistence"] == {
        "mode": "working_tree",
        "scm_commit_authorized": False,
    }
    assert _git_stdout(linked, "rev-parse", "HEAD") == before


def test_first_claim_initializes_identical_inner_and_checkout_outer_witnesses(
    tmp_path: Path,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-store-first-claim")

    result = _create_linked_claim(linked, suffix="654-witness")

    assert result.returncode == 0, result.stderr or result.stdout
    claim_id = json.loads(result.stdout)["claim"]["claim_id"]
    inner = linked / "agents/runtime/task_claims/.claim-store"
    outer = _claim_store_outer_anchor(linked)
    assert inner.read_bytes() == outer.read_bytes()
    witness = json.loads(inner.read_text(encoding="utf-8"))
    assert witness == {
        "schema": "agent-runtime-task-claim-store/v1",
        "generation_id": witness["generation_id"],
        "witness_claim_id": claim_id,
    }


def test_claim_creation_refuses_outer_only_store_before_any_claim_side_effect(
    tmp_path: Path,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-store-outer-only")
    outer = _claim_store_outer_anchor(linked)
    outer.parent.mkdir(parents=True, exist_ok=True)
    outer.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim-store/v1",
                "generation_id": "12345678-1234-4234-9234-123456789abc",
                "witness_claim_id": "CLAIM-hidden",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _create_linked_claim(linked, suffix="654-outer-only")

    assert result.returncode == 1
    assert "claim-store" in result.stderr
    assert not (linked / "agents/runtime/task_claims").exists()


@pytest.mark.parametrize(
    "claim_id",
    ("../../ESCAPE", "CLAIM-valid/../../ESCAPE", "CLAIM-"),
)
def test_claim_creation_refuses_noncanonical_claim_id_without_mutation(
    tmp_path: Path,
    claim_id: str,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-id-boundary")
    seeded = _create_linked_claim(linked, suffix="654-claim-id-witness")
    assert seeded.returncode == 0, seeded.stderr or seeded.stdout
    before = {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    }

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        "TASK-AR-claim-id-boundary",
        "--worktree-path",
        ".",
        "--agent-role",
        "lead-engineer",
        "--claim-id",
        claim_id,
        "--now",
        "2026-07-29T08:05:00+09:00",
        "--suffix",
        "654-claim-id-boundary",
        "--json",
    )

    assert result.returncode == 1
    assert "claim_id" in result.stderr
    assert {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize(
    ("path_flag", "outside_name"),
    (
        ("--handoff-path", "escaped-claim-handoff.md"),
        ("--log-path", "escaped-claim-log.md"),
    ),
)
def test_claim_creation_refuses_artifact_path_escape_without_mutation(
    tmp_path: Path,
    path_flag: str,
    outside_name: str,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, f"artifact-{outside_name}")
    seeded = _create_linked_claim(linked, suffix=f"654-{outside_name}-witness")
    assert seeded.returncode == 0, seeded.stderr or seeded.stdout
    outside = linked.parent / outside_name
    before = {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    }

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        f"TASK-AR-{outside_name}",
        "--worktree-path",
        ".",
        "--agent-role",
        "lead-engineer",
        "--claim-id",
        f"CLAIM-{outside_name}",
        path_flag,
        f"../{outside_name}",
        "--now",
        "2026-07-29T08:05:00+09:00",
        "--suffix",
        f"654-{outside_name}",
        "--json",
    )

    assert result.returncode == 1
    assert path_flag.removeprefix("--").replace("-", "_") in result.stderr
    assert not outside.exists()
    assert {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize(
    ("path_flag", "artifact_name"),
    (
        ("--handoff-path", "retained.handoff.md"),
        ("--log-path", "retained.log.md"),
    ),
)
def test_claim_creation_refuses_existing_artifact_without_mutation(
    tmp_path: Path,
    path_flag: str,
    artifact_name: str,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, f"artifact-collision-{artifact_name}")
    seeded = _create_linked_claim(linked, suffix=f"654-{artifact_name}-witness")
    assert seeded.returncode == 0, seeded.stderr or seeded.stdout
    artifact = linked / "agents/runtime/task_claims" / artifact_name
    artifact.write_text("retained artifact\n", encoding="utf-8")
    collision_task_id = f"TASK-AR-654-{artifact_name}-collision"
    _write_canonical_task_identity(linked, collision_task_id)
    before = {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    }

    result = _create_linked_claim(
        linked,
        suffix=f"654-{artifact_name}-collision",
        extra_args=(
            path_flag,
            f"agents/runtime/task_claims/{artifact_name}",
        ),
        provision_identity=False,
    )

    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize(
    "payload_kind",
    (
        "oversized-malformed",
        "deep",
        "invalid-utf8",
        "huge-integer",
        "unknown-status",
        "nonstring-status",
    ),
)
def test_claim_creation_refuses_unbounded_existing_claim_before_side_effects(
    tmp_path: Path,
    payload_kind: str,
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        f"claim-store-bounded-{payload_kind}",
    )
    first = _create_linked_claim(linked, suffix="654-retained-witness")
    assert first.returncode == 0, first.stderr or first.stdout
    claims = linked / "agents" / "runtime" / "task_claims"
    path = claims / f"CLAIM-adversarial-{payload_kind}.json"
    raw = _adversarial_claim_bytes(
        payload_kind,
        claim_id=f"CLAIM-adversarial-{payload_kind}",
        task_id="TASK-AR-adversarial",
    )
    path.write_bytes(raw)
    before = {
        item.name: item.read_bytes()
        for item in claims.iterdir()
        if item.is_file()
    }

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        "TASK-AR-adversarial",
        "--worktree-path",
        ".",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T08:05:00+09:00",
        "--suffix",
        "654-bounded-refusal",
        "--json",
    )

    assert result.returncode == 1
    assert "claim-store create refused" in result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert path.read_bytes() == raw
    assert {
        item.name: item.read_bytes()
        for item in claims.iterdir()
        if item.is_file()
    } == before


def test_claim_creation_rejects_container_valued_active_authority_without_mutation(
    tmp_path: Path,
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        "claim-container-valued-active-authority",
    )
    first = _create_linked_claim(linked, suffix="654-retained-witness")
    assert first.returncode == 0, first.stderr or first.stdout
    claims = linked / "agents" / "runtime" / "task_claims"
    malformed_id = "CLAIM-malformed-active-shape"
    malformed_path = claims / f"{malformed_id}.json"
    malformed_path.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": malformed_id,
                "status": "claimed",
                "task_id": ["TASK-AR-target"],
                "task_set_id": {"bad": "shape"},
                "agent_instance_id": ["bad"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    before = {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    }
    outer = _claim_store_outer_anchor(linked)
    outer_before = outer.read_bytes()

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        "TASK-AR-target",
        "--agent-role",
        "orchestrator",
        "--mode",
        "orchestrator",
        "--now",
        "2026-08-02T11:00:00+09:00",
        "--suffix",
        "second-authority",
        "--json",
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "claim-store create refused" in result.stderr
    assert "task_id" in result.stderr
    assert {
        path.relative_to(linked).as_posix(): path.read_bytes()
        for path in linked.rglob("*")
        if path.is_file()
    } == before
    assert outer.read_bytes() == outer_before
    assert len(list(claims.glob("CLAIM-*.json"))) == 2


@pytest.mark.parametrize(
    "payload_kind",
    (
        "oversized-malformed",
        "deep",
        "invalid-utf8",
        "huge-integer",
        "unknown-status",
        "nonstring-status",
    ),
)
def test_claim_release_refuses_unbounded_existing_claim_before_side_effects(
    tmp_path: Path,
    payload_kind: str,
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        f"claim-release-bounded-{payload_kind}",
    )
    created = _create_linked_claim(
        linked,
        suffix=f"654-release-retained-{payload_kind}",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    created_payload = json.loads(created.stdout)
    claim = created_payload["claim"]
    claims = linked / "agents" / "runtime" / "task_claims"
    adversarial_id = f"CLAIM-release-adversarial-{payload_kind}"
    adversarial_path = claims / f"{adversarial_id}.json"
    raw = _adversarial_claim_bytes(
        payload_kind,
        claim_id=adversarial_id,
        task_id="TASK-AR-release-adversarial",
    )
    adversarial_path.write_bytes(raw)
    before = {
        item.name: item.read_bytes()
        for item in claims.iterdir()
        if item.is_file()
    }

    result = _run_dispatcher(
        linked,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260729-080600-kst-bounded-release",
        "--verifier-role",
        "qa-reviewer",
        "--allow-missing-evidence",
        "--now",
        "2026-07-29T08:06:00+09:00",
        "--json",
    )

    assert result.returncode == 1
    assert "claim-store release refused" in result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert adversarial_path.read_bytes() == raw
    assert {
        item.name: item.read_bytes()
        for item in claims.iterdir()
        if item.is_file()
    } == before
    persisted = json.loads((linked / created_payload["path"]).read_text(encoding="utf-8"))
    assert persisted["status"] == "claimed"


@pytest.mark.parametrize(
    ("failure_stage", "warning_stage"),
    (
        ("registry", "agent-instance-registry"),
        ("event", "claim-created-event"),
    ),
)
def test_claim_creation_reports_truthful_success_after_post_commit_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure_stage: str,
    warning_stage: str,
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        f"claim-post-commit-{failure_stage}",
    )
    _write_canonical_task_identity(
        linked,
        f"TASK-AR-post-commit-{failure_stage}",
    )
    dispatcher = _load_dispatcher_module()
    lock_depth = {"value": 0}
    original_store_lock = dispatcher.claim_store.store_lock

    @contextmanager
    def observed_store_lock(*args, **kwargs):
        with original_store_lock(*args, **kwargs):
            lock_depth["value"] += 1
            try:
                yield
            finally:
                lock_depth["value"] -= 1

    monkeypatch.setattr(
        dispatcher.claim_store,
        "store_lock",
        observed_store_lock,
    )

    def fail_post_commit(*_args, **_kwargs):
        assert lock_depth["value"] == 0
        raise OSError(f"injected {failure_stage} failure")

    if failure_stage == "registry":
        monkeypatch.setattr(dispatcher, "record_claim_instance", fail_post_commit)
    else:
        monkeypatch.setattr(dispatcher, "append_event", fail_post_commit)

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            f"TASK-AR-post-commit-{failure_stage}",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            f"654-post-commit-{failure_stage}",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "claim-store create refused" not in captured.err
    payload = json.loads(captured.out)
    assert payload["status"] == "created"
    assert payload["post_commit_warnings"] == [
        {
            "stage": warning_stage,
            "reason": f"injected {failure_stage} failure",
        }
    ]
    claim_path = linked / payload["path"]
    assert claim_path.is_file()
    assert json.loads(claim_path.read_text(encoding="utf-8"))["status"] == "claimed"
    assert (
        linked / "agents" / "runtime" / "task_claims" / ".claim-store"
    ).is_file()
    assert _claim_store_outer_anchor(linked).is_file()


def test_claim_creation_has_no_fallible_post_publish_ownership_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-owned-publication")
    _write_canonical_task_identity(linked, "TASK-AR-owned-publication")
    dispatcher = _load_dispatcher_module()
    capture_calls: list[Path] = []

    def fail_legacy_capture(path: Path, _expected: bytes) -> None:
        capture_calls.append(Path(path))
        raise OSError("injected post-publication ownership capture failure")

    monkeypatch.setattr(
        dispatcher,
        "_capture_created_publication",
        fail_legacy_capture,
        raising=False,
    )

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            "TASK-AR-owned-publication",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            "654-owned-publication",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0, captured.err
    assert capture_calls == []
    response = json.loads(captured.out)
    claim = response["claim"]
    assert (linked / response["path"]).is_file()
    assert (linked / claim["handoff_path"]).is_file()
    assert (linked / claim["log_path"]).is_file()
    assert (linked / "agents/runtime/task_claims/.claim-store").is_file()
    assert _claim_store_outer_anchor(linked).is_file()


@pytest.mark.parametrize(
    "failure_stage",
    ("second-artifact", "claim-publication", "outer-marker"),
)
def test_first_claim_creation_rolls_back_authority_on_publication_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure_stage: str,
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        f"claim-create-rollback-{failure_stage}",
    )
    dispatcher = _load_dispatcher_module()
    suffix = f"654-rollback-{failure_stage}"
    _write_canonical_task_identity(linked, f"TASK-AR-{suffix}")

    if failure_stage == "second-artifact":
        original = dispatcher._ensure_text_file
        calls = {"count": 0}

        def fail_second_artifact(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("injected second artifact publication failure")
            return original(*args, **kwargs)

        monkeypatch.setattr(dispatcher, "_ensure_text_file", fail_second_artifact)
    elif failure_stage == "claim-publication":
        original = dispatcher.atomic_io.publish_json_owned_atomic

        def fail_claim_publication(path, payload, **kwargs):
            if Path(path).name.startswith("CLAIM-"):
                raise OSError("injected claim publication failure")
            return original(path, payload, **kwargs)

        monkeypatch.setattr(
            dispatcher.atomic_io,
            "publish_json_owned_atomic",
            fail_claim_publication,
        )
    else:
        original = dispatcher.claim_store._write_immutable
        calls = {"count": 0}

        def fail_outer_marker(path, payload):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("injected outer marker publication failure")
            return original(path, payload)

        monkeypatch.setattr(
            dispatcher.claim_store,
            "_write_immutable",
            fail_outer_marker,
        )

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            f"TASK-AR-{suffix}",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            suffix,
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert "claim-store create refused" in captured.err
    claim_dir = linked / "agents/runtime/task_claims"
    assert not list(claim_dir.glob("CLAIM-*"))
    assert not (claim_dir / ".claim-store").exists()
    assert not _claim_store_outer_anchor(linked).exists()
    assert not claim_dir.exists()
    assert (
        linked / "agents/lead_engineer/tasks" / f"TASK-AR-{suffix}.md"
    ).is_file()

    retried = _create_linked_claim(linked, suffix=suffix)
    assert retried.returncode == 0, retried.stderr or retried.stdout


def test_failed_claim_creation_preserves_initialized_marker_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-create-marker-preservation")
    seeded = _create_linked_claim(linked, suffix="654-marker-seed")
    assert seeded.returncode == 0, seeded.stderr or seeded.stdout
    inner = linked / "agents/runtime/task_claims/.claim-store"
    outer = _claim_store_outer_anchor(linked)
    marker_bytes = (inner.read_bytes(), outer.read_bytes())
    dispatcher = _load_dispatcher_module()
    original = dispatcher._ensure_text_file
    calls = {"count": 0}

    def fail_second_artifact(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("injected initialized-store artifact failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(dispatcher, "_ensure_text_file", fail_second_artifact)
    suffix = "654-marker-preserved-retry"
    _write_canonical_task_identity(linked, f"TASK-AR-{suffix}")
    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            f"TASK-AR-{suffix}",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            suffix,
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert "claim-store create refused" in captured.err
    assert (inner.read_bytes(), outer.read_bytes()) == marker_bytes
    assert not list((linked / "agents/runtime/task_claims").glob(f"*{suffix}*"))

    retried = _create_linked_claim(linked, suffix=suffix)
    assert retried.returncode == 0, retried.stderr or retried.stdout


def test_first_claim_preserves_witness_when_inner_marker_cleanup_is_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        "claim-create-incomplete-marker-recovery",
    )
    dispatcher = _load_dispatcher_module()
    _write_canonical_task_identity(
        linked,
        "TASK-AR-incomplete-marker-recovery",
    )
    outer = _claim_store_outer_anchor(linked)
    original_write = dispatcher.claim_store._write_immutable
    original_remove_marker = dispatcher.claim_store._remove_created_marker
    original_remove_publication = dispatcher._remove_owned_publication

    def fail_outer_marker(path, payload):
        if Path(path) == outer:
            raise OSError("injected outer marker publication failure")
        return original_write(path, payload)

    def fail_inner_marker_cleanup(path, identity, payload):
        if Path(path).name == ".claim-store":
            return False
        return original_remove_marker(path, identity, payload)

    def keep_inner_marker(path, *, expected, identity=None):
        if Path(path).name == ".claim-store":
            return "injected inner marker cleanup remained unavailable"
        return original_remove_publication(
            path,
            expected=expected,
            identity=identity,
        )

    monkeypatch.setattr(
        dispatcher.claim_store,
        "_write_immutable",
        fail_outer_marker,
    )
    monkeypatch.setattr(
        dispatcher.claim_store,
        "_remove_created_marker",
        fail_inner_marker_cleanup,
    )
    monkeypatch.setattr(
        dispatcher,
        "_remove_owned_publication",
        keep_inner_marker,
    )

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            "TASK-AR-incomplete-marker-recovery",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            "654-incomplete-marker-recovery",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert "recovery-required" in captured.err
    claim_dir = linked / "agents/runtime/task_claims"
    claims = sorted(claim_dir.glob("CLAIM-*.json"))
    assert len(claims) == 1
    claim = json.loads(claims[0].read_text(encoding="utf-8"))
    claim_id = claim["claim_id"]
    assert (claim_dir / f"{claim_id}.handoff.md").is_file()
    assert (claim_dir / f"{claim_id}.log.md").is_file()
    assert (claim_dir / ".claim-store").is_file()
    assert not outer.exists()
    inspection = dispatcher.claim_store.inspect_store(linked)
    assert inspection.state == "migration-required"
    assert inspection.witness_claim_id == claim_id


def test_claim_creation_uses_exclusive_publication_for_new_authority_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-exclusive-publication")
    _write_canonical_task_identity(linked, "TASK-AR-exclusive-publication")
    dispatcher = _load_dispatcher_module()
    published_text: list[Path] = []
    published_json: list[Path] = []
    original_publish_text = dispatcher.atomic_io.publish_text_owned_atomic
    original_publish_json = dispatcher.atomic_io.publish_json_owned_atomic
    original_write_text = dispatcher.atomic_io.write_text_atomic
    original_write_json = dispatcher.atomic_io.write_json_atomic

    def observe_publish_text(path, text, **kwargs):
        published_text.append(Path(path))
        return original_publish_text(path, text, **kwargs)

    def observe_publish_json(path, payload, **kwargs):
        published_json.append(Path(path))
        return original_publish_json(path, payload, **kwargs)

    def refuse_claim_overwrite_text(path, text, **kwargs):
        if Path(path).name.endswith((".handoff.md", ".log.md")):
            raise AssertionError("claim artifacts must use exclusive publication")
        return original_write_text(path, text, **kwargs)

    def refuse_claim_overwrite_json(path, payload, **kwargs):
        if Path(path).name.startswith("CLAIM-"):
            raise AssertionError("claim authority must use exclusive publication")
        return original_write_json(path, payload, **kwargs)

    monkeypatch.setattr(
        dispatcher.atomic_io,
        "publish_text_owned_atomic",
        observe_publish_text,
    )
    monkeypatch.setattr(
        dispatcher.atomic_io,
        "publish_json_owned_atomic",
        observe_publish_json,
    )
    monkeypatch.setattr(
        dispatcher.atomic_io,
        "write_text_atomic",
        refuse_claim_overwrite_text,
    )
    monkeypatch.setattr(
        dispatcher.atomic_io,
        "write_json_atomic",
        refuse_claim_overwrite_json,
    )

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            "TASK-AR-exclusive-publication",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            "654-exclusive-publication",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0, captured.err
    artifact_publications = [
        path
        for path in published_text
        if path.name.endswith((".handoff.md", ".log.md"))
    ]
    assert sorted(path.suffixes[-2:] for path in artifact_publications) == [
        [".handoff", ".md"],
        [".log", ".md"],
    ]
    assert len(published_json) == 1
    assert published_json[0].name.startswith("CLAIM-")


def test_claim_create_revalidates_preflight_after_lock_acquisition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-preflight-revalidation")
    _write_canonical_task_identity(linked, "TASK-AR-preflight-revalidation")
    dispatcher = _load_dispatcher_module()
    original_prepare = dispatcher._prepare_create
    calls: list[bool] = []

    def mutate_between_preflights(args, *, emit_success=True):
        calls.append(emit_success)
        result = original_prepare(args, emit_success=emit_success)
        if len(calls) == 1 and not isinstance(result, int):
            args.progress_pct = 101
        return result

    monkeypatch.setattr(dispatcher, "_prepare_create", mutate_between_preflights)

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            "TASK-AR-preflight-revalidation",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            "654-preflight-revalidation",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert calls == [False, True]
    assert "progress_pct must be between 0 and 100" in captured.err
    assert not (linked / "agents/runtime/task_claims").exists()


def test_create_preflight_does_not_mutate_inferred_taskset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = _load_dispatcher_module()
    args = dispatcher.build_parser().parse_args(
        [
            "--root",
            str(tmp_path),
            "create",
            "--task-id",
            "TASK-AR-inferred-taskset",
            "--agent-role",
            "lead-engineer",
        ]
    )
    monkeypatch.setattr(
        dispatcher,
        "_effective_taskset_id",
        lambda *_args, **_kwargs: ("TASKSET-INFERRED", []),
    )

    preparation = dispatcher._prepare_create(args, emit_success=False)

    assert not isinstance(preparation, int)
    assert preparation.task_set_id == "TASKSET-INFERRED"
    assert args.task_set_id == ""


def test_claim_create_refuses_preflight_authority_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-preflight-authority")
    _write_canonical_task_identity(linked, "TASK-AR-preflight-authority")
    dispatcher = _load_dispatcher_module()
    original_prepare = dispatcher._prepare_create
    calls = {"count": 0}

    def change_first_authority(args, *, emit_success=True):
        calls["count"] += 1
        result = original_prepare(args, emit_success=emit_success)
        if calls["count"] == 1 and not isinstance(result, int):
            return result._replace(
                task_set_id="TASKSET-REMOVED-WHILE-LOCKING",
                strict_claim_preflight=True,
            )
        return result

    monkeypatch.setattr(dispatcher, "_prepare_create", change_first_authority)

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            "TASK-AR-preflight-authority",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            "654-preflight-authority",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert calls["count"] == 2
    assert "authority-changed-while-locking" in captured.err
    assert not (linked / "agents/runtime/task_claims").exists()


def test_explicit_cli_opt_in_commits_only_claim_artifacts(tmp_path: Path) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "explicit-claim-commit")
    unrelated = linked / "unrelated.txt"
    unrelated.write_text("must stay uncommitted\n", encoding="utf-8")
    before = _git_stdout(linked, "rev-parse", "HEAD")

    result = _create_linked_claim(
        linked,
        suffix="648-cli-opt-in",
        extra_args=("--commit-claim-artifacts",),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["claim"]["persistence"] == {
        "mode": "scm_commit",
        "scm_commit_authorized": True,
    }
    after = _git_stdout(linked, "rev-parse", "HEAD")
    assert after != before
    changed = set(_git_stdout(linked, "diff-tree", "--no-commit-id", "--name-only", "-r", after).splitlines())
    claim_id = json.loads(result.stdout)["claim"]["claim_id"]
    assert changed == {
        "agents/runtime/task_claims/.claim-store",
        f"agents/runtime/task_claims/{claim_id}.json",
        f"agents/runtime/task_claims/{claim_id}.handoff.md",
        f"agents/runtime/task_claims/{claim_id}.log.md",
    }
    assert "?? unrelated.txt" in _git_stdout(linked, "status", "--porcelain")


def test_opt_in_scm_helper_exception_reports_committed_claim_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-commit-helper-exception")
    _write_canonical_task_identity(linked, "TASK-AR-scm-helper-exception")
    dispatcher = _load_dispatcher_module()
    before = _git_stdout(linked, "rev-parse", "HEAD")
    calls = {"count": 0}

    def fail_commit_helper(*_args, **_kwargs):
        calls["count"] += 1
        raise RuntimeError(
            "injected opt-in SCM helper failure\n" + "x" * 400
        )

    monkeypatch.setattr(
        dispatcher.claim_guard,
        "commit_claim_artifacts",
        fail_commit_helper,
    )

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "create",
            "--task-id",
            "TASK-AR-scm-helper-exception",
            "--worktree-path",
            ".",
            "--agent-role",
            "lead-engineer",
            "--now",
            "2026-07-29T08:05:00+09:00",
            "--suffix",
            "654-scm-helper-exception",
            "--commit-claim-artifacts",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert calls["count"] == 1
    response = json.loads(captured.out)
    assert response["status"] == "created"
    assert response["claim"]["persistence"] == {
        "mode": "scm_commit",
        "scm_commit_authorized": True,
    }
    assert len(response["post_commit_warnings"]) == 1
    warning = response["post_commit_warnings"][0]
    assert warning["stage"] == "claim-artifact-scm-persistence"
    reason = warning["reason"]
    assert reason.startswith("injected opt-in SCM helper failure")
    assert 0 < len(reason) <= 256
    assert "\n" not in reason and "\r" not in reason
    assert "claim-store create refused" not in captured.err
    assert "claim authority persisted" in captured.err
    assert _git_stdout(linked, "rev-parse", "HEAD") == before
    claim_path = linked / response["path"]
    assert claim_path.is_file()
    assert json.loads(claim_path.read_text(encoding="utf-8"))["status"] == "claimed"
    assert (linked / "agents/runtime/task_claims/.claim-store").is_file()
    assert _claim_store_outer_anchor(linked).is_file()


def test_explicit_cli_opt_in_failed_commit_is_blocked_as_not_persisted(
    tmp_path: Path,
) -> None:
    primary, linked = _init_git_worktree(tmp_path, "explicit-claim-commit-hook-failure")
    before = _git_stdout(linked, "rev-parse", "HEAD")
    hook = primary / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)

    result = _create_linked_claim(
        linked,
        suffix="648-cli-hook-failure",
        extra_args=("--commit-claim-artifacts",),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["claim"]["persistence"] == {
        "mode": "scm_commit",
        "scm_commit_authorized": True,
    }
    assert _git_stdout(linked, "rev-parse", "HEAD") == before
    claim_id = payload["claim"]["claim_id"]
    assert set(_git_stdout(linked, "diff", "--cached", "--name-only").splitlines()) == {
        "agents/runtime/task_claims/.claim-store",
        f"agents/runtime/task_claims/{claim_id}.json",
        f"agents/runtime/task_claims/{claim_id}.handoff.md",
        f"agents/runtime/task_claims/{claim_id}.log.md",
    }

    gate = _run_gate(linked)

    assert gate.returncode == 1
    assert "task-claim:authorized-commit-not-persisted" in gate.stdout
    assert "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION" not in os.environ
    transaction_dir = Path(
        _git_stdout(linked, "rev-parse", "--git-path", "agent-runtime/claim-commit")
    )
    if not transaction_dir.is_absolute():
        transaction_dir = linked / transaction_dir
    assert not list(transaction_dir.glob("*.json"))


def test_published_unverified_claim_is_terminal_and_never_reported_as_success(
    tmp_path: Path,
) -> None:
    primary, linked = _init_git_worktree(tmp_path, "published-unverified")
    original_ref = _git_stdout(linked, "symbolic-ref", "-q", "HEAD")
    before = _git_stdout(linked, "rev-parse", "HEAD")
    _run_git(linked, "branch", "roundtrip-branch")
    marker = linked / ".reference-roundtrip-active"
    hook = primary / ".git" / "hooks" / "reference-transaction"
    hook.write_text(
        "#!/bin/sh\n"
        "if test \"$1\" = committed && "
        f"! test -e {str(marker)!r}; then\n"
        f"  : > {str(marker)!r}\n"
        "  git symbolic-ref HEAD refs/heads/roundtrip-branch || exit 1\n"
        f"  git symbolic-ref HEAD {original_ref!r} || exit 1\n"
        f"  rm -f {str(marker)!r}\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)

    result = _create_linked_claim(
        linked,
        suffix="648-published-unverified",
        extra_args=("--commit-claim-artifacts",),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "created_published_unverified"
    persistence = payload["persistence_result"]
    assert persistence["ok"] is False
    assert persistence["committed"] is True
    assert persistence["publication_state"] == "published_unverified"
    assert persistence["reason"] == "claim-commit-sealed-head-identity-changed"
    assert "DO NOT RETRY" in result.stderr
    assert _git_stdout(linked, "symbolic-ref", "-q", "HEAD") == original_ref
    after = _git_stdout(linked, "rev-parse", "HEAD")
    assert after == persistence["commit"]
    assert _git_stdout(linked, "rev-list", "--count", f"{before}..{after}") == "1"
    claim_id = payload["claim"]["claim_id"]
    changed = set(
        _git_stdout(
            linked,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            after,
        ).splitlines()
    )
    assert changed == {
        "agents/runtime/task_claims/.claim-store",
        f"agents/runtime/task_claims/{claim_id}.json",
        f"agents/runtime/task_claims/{claim_id}.handoff.md",
        f"agents/runtime/task_claims/{claim_id}.log.md",
    }
    assert not marker.exists()


@pytest.mark.parametrize("setting", ["0", "false", "off", "not-a-policy"])
def test_false_or_malformed_compatibility_setting_never_commits(
    tmp_path: Path,
    setting: str,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, f"claim-policy-{setting}")
    before = _git_stdout(linked, "rev-parse", "HEAD")

    result = _create_linked_claim(
        linked,
        suffix=f"648-{setting}",
        env_overrides={"AGENT_RUNTIME_CLAIM_AUTOCOMMIT": setting},
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["claim"]["persistence"]["mode"] == "working_tree"
    assert _git_stdout(linked, "rev-parse", "HEAD") == before


def test_true_compatibility_setting_retains_authorized_crash_safety(
    tmp_path: Path,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "claim-policy-true")
    before = _git_stdout(linked, "rev-parse", "HEAD")

    result = _create_linked_claim(
        linked,
        suffix="648-env-opt-in",
        env_overrides={"AGENT_RUNTIME_CLAIM_AUTOCOMMIT": "1"},
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["claim"]["persistence"]["mode"] == "scm_commit"
    assert _git_stdout(linked, "rev-parse", "HEAD") != before


def test_create_claim_allows_registered_linked_worktree_as_runtime_root(tmp_path: Path) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "runtime")
    _write_canonical_task_identity(linked, "TASK-AR-648")
    (linked / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        "TASK-AR-648",
        "--worktree-path",
        ".",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T08:00:00+09:00",
        "--suffix",
        "linked-root",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["claim"]["worktree_path"] == "."


def test_create_claim_refuses_primary_checkout_even_when_registered(tmp_path: Path) -> None:
    primary, _linked = _init_git_worktree(tmp_path, "runtime")
    _write_canonical_task_identity(primary, "TASK-AR-648")
    (primary / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_dispatcher(
        primary,
        "create",
        "--task-id",
        "TASK-AR-648",
        "--worktree-path",
        ".",
        "--agent-role",
        "lead-engineer",
    )

    assert result.returncode == 1
    assert "primary checkout" in result.stderr


def test_create_claim_refuses_registered_worktree_from_other_repository(tmp_path: Path) -> None:
    primary, _linked = _init_git_worktree(tmp_path, "runtime")
    _other_primary, other_linked = _init_git_worktree(tmp_path, "other")
    _write_canonical_task_identity(primary, "TASK-AR-648")
    (primary / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_dispatcher(
        primary,
        "create",
        "--task-id",
        "TASK-AR-648",
        "--worktree-path",
        str(other_linked),
        "--agent-role",
        "lead-engineer",
    )

    assert result.returncode == 1
    assert "different git repository" in result.stderr


def test_create_claim_refuses_primary_root_targeting_same_repo_linked_worktree(
    tmp_path: Path,
) -> None:
    primary, linked = _init_git_worktree(tmp_path, "runtime")
    _write_canonical_task_identity(primary, "TASK-AR-648")
    (primary / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_dispatcher(
        primary,
        "create",
        "--task-id",
        "TASK-AR-648",
        "--worktree-path",
        str(linked),
        "--agent-role",
        "lead-engineer",
    )

    assert result.returncode == 1
    assert "primary checkout" in result.stderr


def test_create_claim_refuses_linked_root_targeting_sibling_worktree(tmp_path: Path) -> None:
    primary, linked = _init_git_worktree(tmp_path, "runtime")
    sibling = tmp_path / "runtime-sibling"
    _run_git(primary, "worktree", "add", "-b", "runtime-sibling-worker", str(sibling))
    _write_canonical_task_identity(linked, "TASK-AR-648")
    (linked / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        "TASK-AR-648",
        "--worktree-path",
        str(sibling),
        "--agent-role",
        "lead-engineer",
    )

    assert result.returncode == 1
    assert "invoking linked worktree itself" in result.stderr


def _write_routing_work(
    root: Path,
    task_id: str,
    *,
    worker_tier: str = "worker_low",
    triggers: list[str] | None = None,
) -> str:
    task_uid = _fixture_work_uid("task", task_id)
    task_path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                f"id: {task_id}",
                f"display_id: {task_id}",
                f"task_uid: {task_uid}",
                f"work_id: {task_id}",
                f"work_uid: {task_uid}",
                "kind: task",
                f"worker_model_tier: {worker_tier}",
                "---",
                "",
            ]
        ),
        encoding="utf-8",
    )
    unit_id = f"UNIT-{task_id}-001"
    unit_rel = f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md"
    unit_path = root / unit_rel
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "schema_version: agent-runtime-work-item/v1",
        f"work_id: {unit_id}",
        f"work_uid: {_fixture_work_uid('unit', unit_id)}",
        "kind: unit",
        f"parent_id: {task_id}",
        f"unit_id: {unit_id}",
        f"task_id: {task_id}",
        f"model_tier: {worker_tier}",
        # Deliberately NON-degenerate. This helper generates the spec behind
        # nearly every claim test, and while it emitted one target file and no
        # stop_condition, every claim-to-spec comparison was evaluated where
        # both sides were trivially equal. That is why a whole-digest heartbeat
        # anchor which would have refused every production heartbeat passed 219
        # tests, and why renew and adopt shipped the same break undetected.
        "target_files:",
        "  - scripts/routing_target.py",
        "  - scripts/routing_second.py",
        "stop_condition: Stop before anything irreversible",
        "escalation_triggers:",
    ]
    lines.extend(f"  - {trigger}" for trigger in (triggers or []))
    lines.extend(["---", ""])
    unit_path.write_text("\n".join(lines), encoding="utf-8")
    return unit_rel


def _install_real_security_gate(root: Path) -> None:
    policy = root / "agents" / "project" / "SECURITY-SERVICE-POLICY.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text(
        (
            REPO_ROOT
            / "agents"
            / "project"
            / "SECURITY-SERVICE-POLICY.json"
        ).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    gate = root / "scripts" / "security_service_gate.py"
    gate.parent.mkdir(parents=True, exist_ok=True)
    gate.write_bytes(
        (REPO_ROOT / "scripts" / "security_service_gate.py").read_bytes()
    )


def _write_runtime_config(root: Path, *profiles: str) -> None:
    lines = [
        "schema: agent-runtime-config/v2",
        "project: dispatcher-test",
        "profiles:",
    ]
    lines.extend(f"  - {profile}" for profile in profiles)
    lines.extend(
        [
            "sync:",
            "  mode: check-diff-apply",
            "  allow_silent_overwrite: false",
            "",
        ]
    )
    (root / "agent_runtime.yml").write_text("\n".join(lines), encoding="utf-8")


def test_create_claim_separates_system_identity_from_readable_display_name(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--tag",
        "planning",
        "--tag",
        "no-ssot-write",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    claim = payload["claim"]
    assert claim["agent_role"] == "lead-engineer"
    assert claim["team_id"] == "agent-runtime-core"
    assert claim["agent_instance_id"] == "le-20260610-143012-kst-a7f3"
    assert claim["display_name"] == "lead_engineer@design-01"
    assert claim["callsite_id"] == "terminal:wt-task-ar-246:tab-01"
    assert claim["pane_id"] == "terminal:wt-task-ar-246:tab-01"
    assert claim["mode"] == "design"
    assert claim["phase"] == "claim-created"
    assert claim["progress_pct"] == 0
    assert claim["task_set_id"] == _fixture_task_set_id("TASK-AR-246")
    assert claim["step_index"] == 1
    assert claim["step_total"] == 6
    assert claim["status_text"] == "Claim created"
    assert claim["updated_at"] == "2026-06-10T14:30:12+09:00"
    assert claim["tags"] == ["planning", "no-ssot-write"]
    assert claim["worktree_path"] == ".worktrees/TASK-AR-246"
    assert claim["branch"] == "codex/task-ar-246-design-01"

    claim_path = tmp_path / payload["path"]
    assert claim_path.exists()
    instance_path = tmp_path / "agents" / "runtime" / "instances" / "le-20260610-143012-kst-a7f3.json"
    assert instance_path.exists()
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    assert instance["schema"] == "agent-runtime-agent-instance/v1"
    assert instance["role"] == "lead-engineer"
    assert instance["team_id"] == "agent-runtime-core"
    assert instance["agent_instance_id"] == "le-20260610-143012-kst-a7f3"
    assert instance["display_name"] == "lead_engineer@design-01"
    assert instance["callsign"] == "lead_engineer@design-01"
    assert instance["callsite_id"] == "terminal:wt-task-ar-246:tab-01"
    assert instance["pane_id"] == "terminal:wt-task-ar-246:tab-01"
    assert instance["spawned_at"] == "2026-06-10T14:30:12+09:00"
    assert instance["spawned_by"] == "task_claim_dispatcher"
    assert instance["task_id"] == "TASK-AR-246"
    assert instance["worktree_path"] == ".worktrees/TASK-AR-246"
    assert instance["claim_refs"] == [payload["path"]]
    assert (tmp_path / claim["handoff_path"]).exists()
    assert (tmp_path / claim["log_path"]).exists()
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event"] == "claim_created"
    assert events[-1]["actor"] == "le-20260610-143012-kst-a7f3"
    assert events[-1]["actor_role"] == "lead-engineer"
    assert events[-1]["agent_instance_id"] == "le-20260610-143012-kst-a7f3"
    assert events[-1]["display_name"] == "lead_engineer@design-01"
    assert events[-1]["callsite_id"] == "terminal:wt-task-ar-246:tab-01"
    assert events[-1]["claim_id"] == claim["claim_id"]
    assert events[-1]["task_id"] == "TASK-AR-246"

    gate = _run_gate(
        tmp_path,
        now="2026-06-10T14:31:00+09:00",
    )
    assert gate.returncode == 0, gate.stdout
    concurrency_gate = _run_concurrency_gate(tmp_path)
    assert concurrency_gate.returncode == 0, concurrency_gate.stdout
    identity_gate = _run_identity_gate(tmp_path)
    assert identity_gate.returncode == 0, identity_gate.stdout


def test_create_claim_refuses_task_that_is_already_active(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "qa-reviewer",
        "--mode",
        "review",
        "--now",
        "2026-06-10T14:35:12+09:00",
        "--suffix",
        "b8c4",
        "--json",
    )

    assert second.returncode == 1
    assert "task already has an active claim" in (second.stderr or second.stdout)
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 1


def test_projection_emits_full_pointer_agent_record_not_scalar_claim_id(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(
        tmp_path,
        "TASK-AR-246",
        task_set_id="TASKSET-AR-PROJECTION",
    )
    unit_rel = _write_heartbeat_unit(tmp_path, task_id="TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--task-set-id",
        "TASKSET-AR-PROJECTION",
        "--unit-id",
        "UNIT-TASK-AR-246-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "projection",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    claim = json.loads(created.stdout)["claim"]
    pointer = tmp_path / "agents/project/NEXT-SESSION-POINTER.yml"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text("sentinel: serial-projection-owner\n", encoding="utf-8")
    pointer_before = pointer.read_bytes()

    result = _run_dispatcher(
        tmp_path,
        "projection",
        "--claim-id",
        claim["claim_id"],
        "--now",
        "2026-06-10T14:31:12+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert pointer.read_bytes() == pointer_before
    projection = json.loads(result.stdout)
    assert projection["operation"] == "merge"
    assert projection["task_claim_ref"].endswith(f"{claim['claim_id']}.json")
    assert projection["pointer"]["active_task"] == "TASK-AR-246"
    assert projection["pointer"]["current_agents"] == [{
        "claim_id": claim["claim_id"],
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": claim["agent_instance_id"],
        "display_name": claim["display_name"],
        "callsite_id": claim["callsite_id"],
        "pane_id": claim["pane_id"],
        "task_id": "TASK-AR-246",
        "unit_id": "UNIT-TASK-AR-246-001",
        "task_set_id": "TASKSET-AR-PROJECTION",
        "status": "claimed",
        "phase": "claim-created",
        "progress_pct": 0,
        "step_index": 1,
        "step_total": 6,
        "status_text": "Claim created",
        "worktree_path": ".worktrees/TASK-AR-246",
        "branch": claim["branch"],
        "requested_model_tier": "worker_standard",
        "selected_model_tier": "worker_standard",
        "routing_policy_id": "task-unit-tier-policy",
        "routing_escalation_reason": None,
        "task_token_budget": None,
        "claim_token_budget": None,
        "claim_path": projection["task_claim_ref"],
        "handoff_path": claim["handoff_path"],
        "log_path": claim["log_path"],
        "last_heartbeat": "2026-06-10T14:30:12+09:00",
        "mutation_revision": 0,
    }]


def test_projection_reads_release_committed_before_its_canonical_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _create_release_candidate(
        tmp_path,
        task_id="TASK-AR-projection-snapshot",
        suffix="projection-snapshot",
    )
    claim = payload["claim"]
    claim_path = tmp_path / payload["path"]
    dispatcher = _load_dispatcher_module()
    original_snapshot = dispatcher.claim_store.read_claims_snapshot
    calls = {"count": 0}

    def release_then_read_snapshot(root):
        calls["count"] += 1
        with dispatcher.claim_store.store_lock(root):
            current = dispatcher.claim_store.read_claim_payload(claim_path)
            current["status"] = "released"
            dispatcher.atomic_io.write_json_atomic(claim_path, current)
        return original_snapshot(root)

    monkeypatch.setattr(
        dispatcher.claim_store,
        "read_claims_snapshot",
        release_then_read_snapshot,
    )

    rc = dispatcher.main(
        [
            "--root",
            str(tmp_path),
            "projection",
            "--claim-id",
            claim["claim_id"],
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert calls["count"] == 1
    assert rc == 1
    assert "projection requires an active worker claim" in captured.err
    assert json.loads(claim_path.read_text(encoding="utf-8"))["status"] == "released"


def test_projection_reports_bounded_claim_store_failure_without_traceback(
    tmp_path: Path,
) -> None:
    payload = _create_release_candidate(
        tmp_path,
        task_id="TASK-AR-246",
        suffix="projection-invalid-store",
    )
    claim = payload["claim"]
    malformed = tmp_path / "agents/runtime/task_claims/CLAIM-000-invalid.json"
    malformed.write_bytes(b"{\xff")

    result = _run_dispatcher(
        tmp_path,
        "projection",
        "--claim-id",
        claim["claim_id"],
        "--json",
    )

    assert result.returncode == 1
    assert "claim-store projection refused" in result.stderr
    assert "Traceback" not in result.stdout + result.stderr


def test_projection_rejects_released_but_not_self_asserted_overlay_claims(
    tmp_path: Path,
):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id", "TASK-AR-246",
        "--agent-role", "lead-engineer",
        "--now", "2026-06-10T14:30:12+09:00",
        "--suffix", "reject-projection",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    claim = json.loads(created.stdout)["claim"]
    path = tmp_path / "agents/runtime/task_claims" / f"{claim['claim_id']}.json"

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["status"] = "released"
    path.write_text(json.dumps(payload), encoding="utf-8")
    inactive = _run_dispatcher(tmp_path, "projection", "--claim-id", claim["claim_id"], "--json")
    assert inactive.returncode == 1
    assert "requires an active worker claim" in inactive.stderr

    payload["status"] = "claimed"
    payload["overlay"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    direct = _run_dispatcher(
        tmp_path,
        "projection",
        "--claim-id",
        claim["claim_id"],
        "--now",
        "2026-06-10T14:31:00+09:00",
        "--json",
    )
    assert direct.returncode == 0, direct.stderr or direct.stdout
    assert json.loads(direct.stdout)["operation"] == "merge"


def test_release_claim_requires_existing_handoff_and_log_files(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    payload = json.loads(created.stdout)
    claim = payload["claim"]
    (tmp_path / claim["handoff_path"]).unlink()

    failed = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--now",
        "2026-06-10T14:45:12+09:00",
        "--json",
    )

    assert failed.returncode == 1
    assert "handoff/log pointer is missing" in (failed.stderr or failed.stdout)
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"


def test_create_claim_accepts_taskset_progress_fields(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(
        tmp_path,
        "TASK-AR-248",
        task_set_id="TASKSET-AR-PANE-PROGRESS",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-248",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "lead-engineer",
        "--team-id",
        "agent-runtime-core",
        "--mode",
        "implement",
        "--phase",
        "implement",
        "--progress-pct",
        "48",
        "--step-index",
        "3",
        "--step-total",
        "6",
        "--status-text",
        "Rendering task-set progress in UI state",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "p2",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["task_set_id"] == "TASKSET-AR-PANE-PROGRESS"
    assert claim["step_index"] == 3
    assert claim["step_total"] == 6
    assert claim["status_text"] == "Rendering task-set progress in UI state"
    assert claim["updated_at"] == "2026-06-10T19:45:00+09:00"


def test_create_claim_accepts_pm_unit_scope_fields(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(
        tmp_path,
        "TASK-AR-344",
        task_set_id="TASKSET-AR-PM-OPERATING-SYSTEM",
    )
    # The spec must exist and declare this claim's ids: create now runs the
    # same resolution heartbeat does, so a claim pointing at a missing or
    # mismatched spec would be born unusable. Written inline rather than via
    # _write_routing_work because this test supplies its own --stop-condition
    # and must not also inherit one from the spec.
    spec = (
        tmp_path
        / "agents/lead_engineer/tasks/units/TASK-AR-344/UNIT-TASK-AR-344-001.md"
    )
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "work_id: UNIT-TASK-AR-344-001\n"
        f"work_uid: {_fixture_work_uid('unit', 'UNIT-TASK-AR-344-001')}\n"
        "kind: unit\n"
        "parent_id: TASK-AR-344\n"
        "unit_id: UNIT-TASK-AR-344-001\n"
        "task_id: TASK-AR-344\n"
        "target_files:\n"
        "  - scripts/pm_scope.py\n"
        "---\n\n# UNIT-TASK-AR-344-001\n",
        encoding="utf-8",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-344",
        "--task-set-id",
        "TASKSET-AR-PM-OPERATING-SYSTEM",
        "--project-id",
        "PROJECT-AGENT-RUNTIME-PM-OS",
        "--unit-id",
        "UNIT-TASK-AR-344-001",
        "--unit-spec",
        "agents/lead_engineer/tasks/units/TASK-AR-344/UNIT-TASK-AR-344-001.md",
        "--model-tier",
        "worker_standard",
        "--wip-slot",
        "2",
        "--stop-condition",
        "stop_after:UNIT-TASK-AR-344-001:no_adjacent_taskset",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "pm1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["project_id"] == "PROJECT-AGENT-RUNTIME-PM-OS"
    assert claim["unit_id"] == "UNIT-TASK-AR-344-001"
    assert claim["unit_spec"].endswith("UNIT-TASK-AR-344-001.md")
    assert claim["model_tier"] == "worker_standard"
    assert claim["wip_slot"] == 2
    assert claim["stop_condition"] == "stop_after:UNIT-TASK-AR-344-001:no_adjacent_taskset"


def test_create_claim_derives_low_requested_and_selected_tier_from_unit(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-646"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:00:00+09:00",
        "--suffix",
        "route-low",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["requested_model_tier"] == "worker_low"
    assert claim["selected_model_tier"] == "worker_low"
    assert claim["model_tier"] == "worker_low"
    assert claim["provider_tier"] == "haiku"
    assert claim["routing_status"] == "selected"
    assert claim["routing_policy_id"] == "task-unit-tier-policy"
    assert claim["routing_high_tier_authorized"] is True
    assert claim["routing_escalation_reason"] is None
    assert claim["routing_registered_triggers"] == []
    assert claim["routing_signals"] == []
    assert claim["actual_model"] is None
    assert claim["actual_model_status"] == "unverified"


def test_create_claim_visibly_escalates_data_integrity_signal(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-647"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(
        tmp_path, task_id, triggers=["data_integrity"]
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:01:00+09:00",
        "--suffix",
        "route-risk",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["requested_model_tier"] == "worker_low"
    assert claim["selected_model_tier"] == "planner_high"
    assert claim["model_tier"] == "planner_high"
    assert claim["provider_tier"] == "opus"
    assert claim["routing_status"] == "escalated"
    assert claim["routing_high_tier_authorized"] is True
    assert claim["routing_escalation_reason"] == "trigger:data_integrity"
    assert claim["routing_registered_triggers"] == ["data_integrity"]
    assert claim["routing_signals"] == ["data_integrity"]
    assert claim["routing_unknown_triggers"] == []


def test_create_claim_records_durable_task_and_claim_budgets(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-652"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-TASK-AR-652-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--task-token-budget",
        "1200",
        "--claim-token-budget",
        "400",
        "--now",
        "2026-07-30T07:02:00+09:00",
        "--suffix",
        "budget",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["task_token_budget"] == 1200
    assert claim["claim_token_budget"] == 400


def test_create_claim_rejects_invalid_durable_budget(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-652"
    _write_worktree(tmp_path, task_id)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--task-token-budget",
        "-1",
        "--json",
    )

    assert result.returncode == 1
    assert "task_token_budget must be a non-negative integer" in result.stderr


def test_create_claim_runs_installed_security_service_gate_before_persistence(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-647"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    unit = tmp_path / unit_rel
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py",
            "  - .env.production",
        ),
        encoding="utf-8",
    )
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:03:00+09:00",
        "--suffix",
        "security-block",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert ".env.production" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_installed_security_profile_refuses_claim_without_unit_spec(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--target-file",
        ".env.production",
        "--now",
        "2026-07-29T07:04:00+09:00",
        "--suffix",
        "security-no-unit",
        "--json",
    )

    assert result.returncode == 1
    assert "requires registered task and unit identities" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_non_regular_installed_security_gate_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    gate = tmp_path / "scripts" / "security_service_gate.py"
    gate.mkdir(parents=True)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:30+09:00",
        "--suffix",
        "security-gate-dir",
        "--json",
    )

    assert result.returncode == 1
    assert "not a regular managed file" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_symlinked_security_gate_parent_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    external_scripts = tmp_path / "external-scripts"
    external_scripts.mkdir()
    (external_scripts / "security_service_gate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").symlink_to(external_scripts, target_is_directory=True)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:40+09:00",
        "--suffix",
        "security-gate-parent-link",
        "--json",
    )

    assert result.returncode == 1
    assert "not a regular managed file" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_drifted_regular_security_gate_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    gate = tmp_path / "scripts" / "security_service_gate.py"
    gate.parent.mkdir(parents=True)
    gate.write_text("raise SystemExit(0)\n", encoding="utf-8")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:50+09:00",
        "--suffix",
        "security-gate-drift",
        "--json",
    )

    assert result.returncode == 1
    assert "drifted" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


@pytest.mark.parametrize(
    "profile_evidence",
    ["config-only", "full-runtime", "partial-assets", "lock-only"],
)
def test_selected_security_profile_with_missing_gate_refuses_claim(
    tmp_path: Path,
    profile_evidence: str,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    unit = tmp_path / unit_rel
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py",
            "  - .env.production",
        ),
        encoding="utf-8",
    )
    if profile_evidence == "config-only":
        _write_runtime_config(tmp_path, "core", "security-service")
    if profile_evidence == "full-runtime":
        _write_runtime_config(tmp_path, "full-runtime")
    if profile_evidence == "partial-assets":
        _install_real_security_gate(tmp_path)
        (tmp_path / ".allimbot.json").write_bytes(
            (
                REPO_ROOT
                / "src"
                / "agent_runtime"
                / "templates"
                / "project"
                / ".allimbot.json"
            ).read_bytes()
        )
        (tmp_path / "scripts" / "security_service_gate.py").unlink()
    if profile_evidence == "lock-only":
        (tmp_path / "agent_runtime.lock.json").write_text(
            json.dumps(
                {
                    "schema": "agent-runtime-lock/v2",
                    "profiles": ["core", "security-service"],
                }
            ),
            encoding="utf-8",
        )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:55+09:00",
        "--suffix",
        f"security-gate-missing-{profile_evidence}",
        "--json",
    )

    assert result.returncode == 1
    assert "selected or partially installed profile" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_malformed_host_config_blocks_at_claim_dispatch_seam(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-649"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    _install_real_security_gate(tmp_path)
    (tmp_path / "agent_runtime.yml").write_text(
        "schema: agent-runtime-config/v2\n"
        "project: broken\n"
        "host:\n"
        "  risk_paths: nope\n",
        encoding="utf-8",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:05:00+09:00",
        "--suffix",
        "security-bad-config",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_unterminated_required_security_metadata_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-649"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(
        tmp_path,
        task_id,
        triggers=["security"],
    )
    unit = tmp_path / unit_rel
    unit_text = unit.read_text(encoding="utf-8")
    unit_text = unit_text.replace(
        "  - scripts/routing_target.py",
        "  - .env.production",
    ).replace(
        "target_files:",
        'risk_tier: "high\n'
        'security_sensitive: "true\n'
        'approval_required: "true\n'
        "target_files:",
    )
    unit.write_text(
        unit_text + "\n## Security Controls\n\nSynthetic test boundary.\n",
        encoding="utf-8",
    )
    _write_runtime_config(tmp_path, "core", "security-service")
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:05:30+09:00",
        "--suffix",
        "unterminated-security-metadata",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_html_block_heading_cannot_authorize_security_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-652"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(
        tmp_path,
        task_id,
        triggers=["security"],
    )
    unit = tmp_path / unit_rel
    unit_text = unit.read_text(encoding="utf-8")
    unit_text = unit_text.replace(
        "  - scripts/routing_target.py",
        "  - .env.production",
    ).replace(
        "target_files:",
        "risk_tier: high\n"
        "security_sensitive: true\n"
        "approval_required: true\n"
        "target_files:",
    )
    unit.write_text(
        unit_text
        + "\n<!--\n"
        + "hidden comment\n"
        + "-->## Security Controls\n",
        encoding="utf-8",
    )
    _write_runtime_config(tmp_path, "core", "security-service")
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:05:45+09:00",
        "--suffix",
        "html-block-security-heading",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "section:Security Controls" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_safe_review_document_cannot_substitute_for_requested_unit(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-650"
    _write_worktree(tmp_path, task_id)
    canonical_unit = _write_routing_work(tmp_path, task_id)
    canonical_path = tmp_path / canonical_unit
    canonical_path.write_text(
        canonical_path.read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py",
            "  - .env.production",
        ),
        encoding="utf-8",
    )
    review = tmp_path / "reviews" / "safe-unit.md"
    review.parent.mkdir(parents=True)
    review.write_text(
        "---\n"
        f"unit_id: UNIT-{task_id}-001\n"
        f"task_id: {task_id}\n"
        "target_files:\n"
        "  - README.md\n"
        "---\n",
        encoding="utf-8",
    )
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        "reviews/safe-unit.md",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:06:00+09:00",
        "--suffix",
        "security-substitute",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_non_regular_host_config_blocks_at_claim_dispatch_seam(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-651"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    _install_real_security_gate(tmp_path)
    (tmp_path / "agent_runtime.yml").mkdir()

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:07:00+09:00",
        "--suffix",
        "security-config-dir",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_create_claim_has_zero_security_profile_burden_when_gate_absent(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    _write_runtime_config(tmp_path, "core # core-only host")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:00+09:00",
        "--suffix",
        "core-no-gate",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_create_claim_keeps_unknown_routing_signal_visible(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(
        tmp_path, task_id, triggers=["future_unregistered_risk"]
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-TASK-AR-648-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:02:00+09:00",
        "--suffix",
        "route-unknown",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["routing_status"] == "unverified"
    assert claim["routing_unknown_triggers"] == ["future_unregistered_risk"]
    assert claim["actual_model"] is None


def test_create_claim_rejects_missing_worktree(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_canonical_task_identity(tmp_path, "TASK-AR-246")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
    )

    assert result.returncode == 1
    assert "task worktree is not ready" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_create_claim_refuses_duplicate_active_taskset(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(
        tmp_path,
        "TASK-AR-248",
        task_set_id="TASKSET-AR-PANE-PROGRESS",
    )
    _write_worktree(
        tmp_path,
        "TASK-AR-249",
        task_set_id="TASKSET-AR-PANE-PROGRESS",
    )
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-248",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "p2",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "qa-reviewer",
        "--now",
        "2026-06-10T19:46:00+09:00",
        "--suffix",
        "p3",
        "--json",
    )

    assert second.returncode == 1
    assert "task set already has an active claim" in second.stderr


def test_create_claim_rejects_intersecting_footprint_listing_conflicting_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-501")
    _write_worktree(tmp_path, "TASK-AR-502")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-501",
        "--agent-role",
        "lead-engineer",
        "--target-file",
        "scripts/shared.py",
        "--target-file",
        "docs/notes.md",
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--suffix",
        "fp1",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout
    first_claim = json.loads(first.stdout)["claim"]
    assert first_claim["target_files"] == ["scripts/shared.py", "docs/notes.md"]

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-502",
        "--agent-role",
        "qa-reviewer",
        "--target-file",
        "scripts/shared.py",
        "--now",
        "2026-06-13T10:05:00+09:00",
        "--suffix",
        "fp2",
        "--json",
    )

    assert second.returncode == 1
    assert "footprint conflict with active claims" in second.stderr
    assert first_claim["claim_id"] in second.stderr
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 1


def test_create_claims_with_disjoint_footprints_coexist(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    footprints = {
        "TASK-AR-501": "scripts/alpha.py",
        "TASK-AR-502": "scripts/beta.py",
        "TASK-AR-503": "docs/gamma.md",
    }
    for index, (task_id, target) in enumerate(sorted(footprints.items()), start=1):
        _write_worktree(tmp_path, task_id)
        result = _run_dispatcher(
            tmp_path,
            "create",
            "--task-id",
            task_id,
            "--agent-role",
            "lead-engineer",
            "--target-file",
            target,
            "--now",
            f"2026-06-13T10:0{index}:00+09:00",
            "--suffix",
            f"dj{index}",
            "--json",
        )
        assert result.returncode == 0, result.stderr or result.stdout
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == len(footprints)


def test_create_claim_rejects_glob_prefix_footprint_overlap(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-501")
    _write_worktree(tmp_path, "TASK-AR-502")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-501",
        "--agent-role",
        "lead-engineer",
        "--target-file",
        "scripts/**",
        "--now",
        "2026-06-13T11:00:00+09:00",
        "--suffix",
        "gl1",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout
    first_claim = json.loads(first.stdout)["claim"]

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-502",
        "--agent-role",
        "qa-reviewer",
        "--target-file",
        "scripts/sub/module.py",
        "--now",
        "2026-06-13T11:05:00+09:00",
        "--suffix",
        "gl2",
        "--json",
    )

    assert second.returncode == 1
    assert "footprint conflict with active claims" in second.stderr
    assert first_claim["claim_id"] in second.stderr


def test_create_claim_footprint_less_legacy_claim_does_not_block(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-501")
    _write_worktree(tmp_path, "TASK-AR-502")
    legacy = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-501",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-13T12:00:00+09:00",
        "--suffix",
        "lg1",
        "--json",
    )
    assert legacy.returncode == 0, legacy.stderr or legacy.stdout
    assert "footprint-less" in legacy.stderr
    legacy_claim = json.loads(legacy.stdout)["claim"]
    assert legacy_claim["target_files"] == []

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-502",
        "--agent-role",
        "qa-reviewer",
        "--target-file",
        "scripts/shared.py",
        "--now",
        "2026-06-13T12:05:00+09:00",
        "--suffix",
        "lg2",
        "--json",
    )

    assert second.returncode == 0, second.stderr or second.stdout
    assert "footprint-less" in second.stderr
    assert legacy_claim["claim_id"] in second.stderr
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 2


def test_create_claim_derives_target_files_from_unit_spec(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-503")
    unit_rel = "agents/lead_engineer/tasks/units/TASK-AR-503/UNIT-TASK-AR-503-001.md"
    unit_path = tmp_path / unit_rel
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                "work_id: UNIT-TASK-AR-503-001",
                f"work_uid: {_fixture_work_uid('unit', 'UNIT-TASK-AR-503-001')}",
                "kind: unit",
                "parent_id: TASK-AR-503",
                "unit_id: UNIT-TASK-AR-503-001",
                "task_id: TASK-AR-503",
                "status: worker_ready",
                "target_files:",
                "  - scripts/unit_target.py",
                "  - docs/unit_target.md",
                "---",
                "",
                "## Context",
                "",
                "Unit spec for footprint derivation.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-503",
        "--agent-role",
        "lead-engineer",
        "--unit-id",
        f"UNIT-TASK-AR-503-001",
        "--unit-spec",
        unit_rel,
        "--now",
        "2026-06-13T13:00:00+09:00",
        "--suffix",
        "us1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["target_files"] == ["scripts/unit_target.py", "docs/unit_target.md"]


def test_explicit_target_files_outside_the_unit_spec_are_refused(
    tmp_path: Path,
) -> None:
    """The spec is the authority when there is one.

    Unioning an out-of-spec file made the claim's footprint a strict superset
    of the spec's from birth, so every claim-to-spec comparison downstream
    started from a divergence - the single root of the heartbeat, renew, and
    adopt false positives. Explicit entries that ARE in the spec still work and
    still order first; see the companion test below.
    """
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-504"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--target-file",
        "README.md",
        "--now",
        "2026-07-29T07:06:00+09:00",
        "--suffix",
        "union-footprint",
        "--json",
    )

    assert result.returncode != 0
    assert "outside the unit spec" in (result.stdout + result.stderr)


def test_explicit_target_files_inside_the_unit_spec_are_ordered_first(
    tmp_path: Path,
) -> None:
    """The explicit-first ordering contract survives the narrowing."""
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-504b"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)

    result = _run_dispatcher(
        tmp_path, "create",
        "--task-id", task_id,
        "--unit-id", f"UNIT-{task_id}-001",
        "--unit-spec", unit_rel,
        "--agent-role", "lead-engineer",
        "--target-file", "scripts/routing_second.py",
        "--now", "2026-07-29T07:06:00+09:00",
        "--suffix", "orderfirst",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["target_files"] == [
        "scripts/routing_second.py",
        "scripts/routing_target.py",
    ]


def test_create_claim_normalizes_new_targets_and_surfaces_matching_compound(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    _write_worktree(tmp_path, "TASK-AR-645")
    task_path = tmp_path / "agents/lead_engineer/tasks/TASK-AR-645.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_uid = _fixture_work_uid("task", "TASK-AR-645")
    task_path.write_text(
        "---\nid: TASK-AR-645\ndisplay_id: TASK-AR-645\n"
        f"task_uid: {task_uid}\nwork_id: TASK-AR-645\nwork_uid: {task_uid}\n"
        f"task_set_id: {_fixture_task_set_id('TASK-AR-645')}\n"
        "defect_signatures:\n"
        "  - claim lookup omitted\n---\n",
        encoding="utf-8",
    )
    unit_rel = (
        "agents/lead_engineer/tasks/units/TASK-AR-645/"
        "UNIT-TASK-AR-645-001.md"
    )
    unit_path = tmp_path / unit_rel
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(
        "---\nwork_id: UNIT-TASK-AR-645-001\n"
        f"work_uid: {_fixture_work_uid('unit', 'UNIT-TASK-AR-645-001')}\n"
        "parent_id: TASK-AR-645\nunit_id: UNIT-TASK-AR-645-001\n"
        "task_id: TASK-AR-645\n"
        "status: worker_ready\ntarget_files:\n"
        "  - new:src/agent_runtime/knowledge_records.py\n"
        "  - scripts/task_claim_dispatcher.py\n"
        "defect_signatures:\n"
        "  - claim lookup omitted\n---\n",
        encoding="utf-8",
    )
    _path, prior = knowledge_records.create_record(
        tmp_path,
        work_ids=["TASK-AR-500"],
        defect_signatures=["claim lookup omitted"],
        title="Search before claim",
        summary="A worker repeated a known error.",
        cause="The dispatcher did not search.",
        prevention="Search before persistence.",
        source_refs=["reviews/source.md"],
        prevention_refs=["scripts/task_claim_dispatcher.py"],
        verification_refs=["reviews/verify.json"],
        created_at="2026-07-28T12:00:00+09:00",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-645",
        "--agent-role",
        "lead-engineer",
        "--unit-id",
        "UNIT-TASK-AR-645-001",
        "--unit-spec",
        unit_rel,
        "--now",
        "2026-07-29T04:20:00+09:00",
        "--suffix",
        "lookup",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["target_files"] == [
        "src/agent_runtime/knowledge_records.py",
        "scripts/task_claim_dispatcher.py",
    ]
    assert claim["defect_signatures"] == [
        knowledge_records.normalize_signature("claim lookup omitted")
    ]
    assert claim["knowledge_lookup"] == {"status": "matched", "match_count": 1}
    assert claim["knowledge_matches"][0]["id"] == prior["id"]
    assert "before claim persistence" in result.stderr


def test_create_claim_refuses_malformed_canonical_compound_before_persistence(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    _write_worktree(tmp_path, "TASK-AR-646")
    record_dir = knowledge_records.records_dir(tmp_path)
    record_dir.mkdir(parents=True)
    (record_dir / "COMPOUND-20260729-000000-bad-000000000000.json").write_text(
        '{"schema":"wrong"}\n', encoding="utf-8"
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-646",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T04:21:00+09:00",
        "--suffix",
        "bad-record",
        "--json",
    )

    assert result.returncode == 1
    assert "compound knowledge lookup failed before claim persistence" in result.stderr
    claims = tmp_path / "agents/runtime/task_claims"
    assert not claims.exists() or not list(claims.glob("*.json"))


def _create_release_candidate(tmp_path: Path, *, task_id: str = "TASK-AR-507", suffix: str = "cv1") -> dict:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, task_id)
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--mode",
        "implement",
        "--now",
        "2026-06-13T09:00:00+09:00",
        "--suffix",
        suffix,
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    return json.loads(created.stdout)


def _write_evidence(tmp_path: Path, rel: str = "agents/runtime/task_claims/evidence/W4B-VERIFICATION.md") -> str:
    evidence = tmp_path / rel
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("# W4b verification\n\n- result: pass\n", encoding="utf-8")
    return rel


def test_release_without_verifier_is_refused(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "cross-verification required" in refused.stderr
    assert "--verified-by" in refused.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"
    assert "verified_by" not in saved


def test_release_refuses_worker_self_verification_listing_both_ids(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    worker_id = claim["agent_instance_id"]
    evidence_rel = _write_evidence(tmp_path)

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        worker_id,
        "--verifier-role",
        "lead-engineer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "cross-verification violation" in refused.stderr
    assert f"verified_by={worker_id}" in refused.stderr
    assert f"worker agent_instance_id={worker_id}" in refused.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"


def test_release_with_distinct_verifier_records_fields_and_pane_event(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "released"
    assert saved["released_at"] == "2026-06-13T10:15:00+09:00"
    assert saved["verified_by"] == "qa-20260613-101500-kst-w4b1"
    assert saved["verifier_role"] == "qa-reviewer"
    assert saved["verification_evidence"] == evidence_rel
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    release_event = events[-1]
    assert release_event["event"] == "claim_released"
    assert release_event["claim_id"] == claim["claim_id"]
    assert release_event["actor"] == claim["agent_instance_id"]
    assert release_event["verified_by"] == "qa-20260613-101500-kst-w4b1"
    assert release_event["verifier_role"] == "qa-reviewer"


@pytest.mark.parametrize("inactive_status", ("released", "blocked"))
def test_release_refuses_to_rebind_inactive_claim_verification(
    tmp_path: Path,
    inactive_status: str,
) -> None:
    payload = _create_release_candidate(
        tmp_path,
        task_id=f"TASK-AR-inactive-{inactive_status}",
        suffix=f"inactive-{inactive_status}",
    )
    claim_path = tmp_path / payload["path"]
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    original_evidence = _write_evidence(
        tmp_path,
        "agents/runtime/task_claims/evidence/ORIGINAL-W4B.md",
    )
    claim.update(
        {
            "status": inactive_status,
            "released_at": "2026-06-13T09:30:00+09:00",
            "verified_by": "qa-original-verifier",
            "verifier_role": "qa-reviewer",
            "verification_evidence": original_evidence,
        }
    )
    claim_path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    before = claim_path.read_bytes()
    replacement_evidence = _write_evidence(
        tmp_path,
        "agents/runtime/task_claims/evidence/REPLACEMENT-W4B.md",
    )

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-replacement-verifier",
        "--verifier-role",
        "release-manager",
        "--verification-evidence",
        replacement_evidence,
        "--now",
        "2026-06-13T11:00:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "active claim" in refused.stderr
    assert claim_path.read_bytes() == before


def test_release_reports_truthful_success_after_post_commit_event_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _create_release_candidate(tmp_path, suffix="post-release-event")
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)
    dispatcher = _load_dispatcher_module()
    lock_depth = {"value": 0}
    original_store_lock = dispatcher.claim_store.store_lock

    @contextmanager
    def observed_store_lock(*args, **kwargs):
        with original_store_lock(*args, **kwargs):
            lock_depth["value"] += 1
            try:
                yield
            finally:
                lock_depth["value"] -= 1

    monkeypatch.setattr(
        dispatcher.claim_store,
        "store_lock",
        observed_store_lock,
    )

    def fail_event(*_args, **_kwargs):
        assert lock_depth["value"] == 0
        raise OSError("injected release event failure")

    monkeypatch.setattr(dispatcher, "append_event", fail_event)
    rc = dispatcher.main(
        [
            "--root",
            str(tmp_path),
            "release",
            "--claim-id",
            claim["claim_id"],
            "--verified-by",
            "qa-20260613-101500-kst-w4b-post-event",
            "--verifier-role",
            "qa-reviewer",
            "--verification-evidence",
            evidence_rel,
            "--now",
            "2026-06-13T10:15:00+09:00",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "claim-store release refused" not in captured.err
    released = json.loads(captured.out)
    assert released["status"] == "released"
    assert released["post_commit_warnings"] == [
        {
            "stage": "claim-released-event",
            "reason": "injected release event failure",
        }
    ]
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "released"
    assert saved["verified_by"] == "qa-20260613-101500-kst-w4b-post-event"


def test_release_requires_evidence_ref_by_default(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "verification evidence required" in refused.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"


def test_release_refuses_nonexistent_evidence_ref(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        "agents/runtime/task_claims/evidence/does-not-exist.md",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "verification evidence not found" in refused.stderr


@pytest.mark.parametrize(
    "evidence_mode",
    ("absolute-outside", "relative-escape", "directory", "symlink"),
)
def test_release_refuses_noncanonical_evidence_without_mutating_claim(
    tmp_path: Path,
    evidence_mode: str,
) -> None:
    payload = _create_release_candidate(tmp_path, suffix=f"evidence-{evidence_mode}")
    claim = payload["claim"]
    outside = tmp_path.parent / f"outside-{evidence_mode}.md"
    outside.write_text("# Not repository evidence\n", encoding="utf-8")
    if evidence_mode == "absolute-outside":
        evidence_ref = str(outside.resolve())
    elif evidence_mode == "relative-escape":
        evidence_ref = f"../{outside.name}"
    elif evidence_mode == "directory":
        evidence_dir = tmp_path / "reviews/evidence-directory"
        evidence_dir.mkdir(parents=True)
        evidence_ref = evidence_dir.relative_to(tmp_path).as_posix()
    else:
        target = tmp_path / "reviews/direct-evidence.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Direct evidence\n", encoding="utf-8")
        alias = tmp_path / "reviews/evidence-alias.md"
        try:
            alias.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"symlink creation unavailable: {exc}")
        evidence_ref = alias.relative_to(tmp_path).as_posix()

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b-evidence-boundary",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_ref,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "verification evidence" in refused.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"
    assert "verification_evidence" not in saved


@pytest.mark.parametrize("pointer_mode", ("outside", "symlink"))
def test_release_refuses_noncanonical_handoff_pointer_without_mutating_claim(
    tmp_path: Path,
    pointer_mode: str,
) -> None:
    payload = _create_release_candidate(
        tmp_path,
        suffix=f"handoff-pointer-{pointer_mode}",
    )
    claim_path = tmp_path / payload["path"]
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    if pointer_mode == "outside":
        outside = tmp_path.parent / "outside-handoff.md"
        outside.write_text("# Outside handoff\n", encoding="utf-8")
        claim["handoff_path"] = f"../{outside.name}"
    else:
        direct = tmp_path / "agents/runtime/task_claims/direct-handoff.md"
        direct.write_text("# Direct handoff\n", encoding="utf-8")
        alias = tmp_path / "agents/runtime/task_claims/alias.handoff.md"
        try:
            alias.symlink_to(direct)
        except OSError as exc:
            pytest.skip(f"symlink creation unavailable: {exc}")
        claim["handoff_path"] = alias.relative_to(tmp_path).as_posix()
    claim_path.write_text(json.dumps(claim), encoding="utf-8")
    evidence_ref = _write_evidence(tmp_path)

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b-pointer-boundary",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_ref,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "handoff_path" in refused.stderr
    saved = json.loads(claim_path.read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"
    assert "verification_evidence" not in saved


def test_release_allow_missing_evidence_escape_prints_loud_warning(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--allow-missing-evidence",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    assert "WARNING" in released.stderr
    assert "--allow-missing-evidence" in released.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "released"
    assert saved["verified_by"] == "qa-20260613-101500-kst-w4b1"
    assert saved["verification_evidence"] == ""


def test_release_still_refuses_self_verification_with_missing_evidence_escape(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    worker_id = claim["agent_instance_id"]

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        worker_id,
        "--verifier-role",
        "lead-engineer",
        "--allow-missing-evidence",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "cross-verification violation" in refused.stderr


def test_legacy_released_claims_without_verifier_fields_pass_check_gates(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    legacy = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-20260601-090000-task-ar-400-old1",
        "task_id": "TASK-AR-400",
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": "le-20260601-090000-kst-old1",
        "display_name": "lead_engineer@implement-01",
        "callsite_id": "terminal:wt-task-ar-400:tab-01",
        "pane_id": "terminal:wt-task-ar-400:tab-01",
        "mode": "implement",
        "status": "released",
        "task_set_id": "",
        "worktree_path": ".worktrees/TASK-AR-400",
        "branch": "codex/task-ar-400-implement-01",
        "claimed_at": "2026-06-01T09:00:00+09:00",
        "released_at": "2026-06-01T12:00:00+09:00",
        "last_heartbeat": "2026-06-01T12:00:00+09:00",
        "updated_at": "2026-06-01T12:00:00+09:00",
        "expires_at": "2026-06-01T09:30:00+09:00",
        "handoff_path": "agents/runtime/task_claims/CLAIM-20260601-090000-task-ar-400-old1.handoff.md",
        "log_path": "agents/runtime/task_claims/CLAIM-20260601-090000-task-ar-400-old1.log.md",
        "tags": [],
        "target_files": [],
    }
    (claim_dir / f"{legacy['claim_id']}.json").write_text(
        json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    gate = _run_gate(tmp_path)
    assert gate.returncode == 0, gate.stdout
    concurrency_gate = _run_concurrency_gate(tmp_path)
    assert concurrency_gate.returncode == 0, concurrency_gate.stdout
    identity_gate = _run_identity_gate(tmp_path)
    assert identity_gate.returncode == 0, identity_gate.stdout


def test_create_claim_rejects_invalid_progress_and_step_state(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    bad_progress = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--progress-pct",
        "104",
    )
    bad_step = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--step-index",
        "7",
        "--step-total",
        "6",
    )
    bad_done = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--phase",
        "completed",
        "--step-index",
        "2",
        "--step-total",
        "6",
    )

    assert bad_progress.returncode == 1
    assert "progress_pct must be between 0 and 100" in bad_progress.stderr
    assert bad_step.returncode == 1
    assert "step_index must be between 1 and step_total" in bad_step.stderr
    assert bad_done.returncode == 1
    assert "completion phase requires step_index to equal step_total" in bad_done.stderr


def test_create_claim_records_active_scope_boundary(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(
        tmp_path,
        "TASK-AR-328",
        task_set_id="TASKSET-AR-UI-UX-V2",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-328",
        "--task-set-id",
        "TASKSET-AR-UI-UX-V2",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-13T09:00:00+09:00",
        "--suffix",
        "sc1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    # Active scope defaults to the task_set_id so the boundary guard has a
    # recorded scope to enforce against.
    assert claim["active_scope"] == "TASKSET-AR-UI-UX-V2"
    assert claim["scope_transition_approved"] is False


def test_release_with_taskset_completed_phase_emits_completion_event(tmp_path: Path):
    payload = _create_release_candidate(tmp_path, task_id="TASK-AR-329", suffix="tc1")
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    # Mark the claim's scope + completion phase before release so the dispatcher
    # emits the taskset.completed boundary signal.
    claim_path = tmp_path / payload["path"]
    saved = json.loads(claim_path.read_text(encoding="utf-8"))
    saved["active_scope"] = "TASKSET-AR-UI-UX-V2"
    saved["phase"] = "taskset-completed"
    saved["progress_pct"] = 100
    claim_path.write_text(json.dumps(saved), encoding="utf-8")

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    completed = [event for event in events if event["event"] == "taskset.completed"]
    assert completed, "expected a taskset.completed event to be emitted"
    event = completed[-1]
    assert event["task_set_id"] == "TASKSET-AR-UI-UX-V2"
    assert event["claim_id"] == claim["claim_id"]
    assert "stop and report" in event["message"]


def test_release_without_completion_phase_emits_no_completion_event(tmp_path: Path):
    payload = _create_release_candidate(tmp_path, task_id="TASK-AR-330", suffix="nc1")
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    assert not [event for event in events if event["event"] == "taskset.completed"]


# TASK-AR-655: task-claim heartbeat/renewal authority -----------------------

SCOPE_BINDING_SCHEMA = "agent-runtime-claim-scope-binding/v1"


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _expected_scope_binding(claim: dict[str, object], *, bound_at: str) -> dict[str, object]:
    """Independent oracle for the immutable renewal scope contract."""

    components = {
        "task": _canonical_sha256({"task_id": claim.get("task_id") or ""}),
        "unit": _canonical_sha256(
            {
                "unit_id": claim.get("unit_id") or "",
                "unit_spec": claim.get("unit_spec") or "",
            }
        ),
        "target_files": _canonical_sha256(
            sorted({str(item) for item in claim.get("target_files", [])})
        ),
        "stop_condition": _canonical_sha256(claim.get("stop_condition") or ""),
    }
    return {
        "schema": SCOPE_BINDING_SCHEMA,
        "digest": _canonical_sha256(components),
        "components": components,
        "bound_at": bound_at,
    }


def _claim_scope_binding(claim: dict[str, object]) -> dict[str, object]:
    binding = claim.get("scope_binding")
    if isinstance(binding, dict) and isinstance(binding.get("digest"), str):
        return json.loads(json.dumps(binding))
    return _expected_scope_binding(
        claim,
        bound_at=str(claim.get("claimed_at") or ""),
    )


def _claim_scope_digest(claim: dict[str, object]) -> str:
    return str(_claim_scope_binding(claim)["digest"])


def _write_heartbeat_unit(
    root: Path,
    *,
    task_id: str,
    targets: tuple[str, ...] = ("scripts/claim_worker.py",),
    stop_condition: str = "stop_after:UNIT:verification",
) -> str:
    unit_id = f"UNIT-{task_id}-001"
    relative = f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "schema_version: agent-runtime-work-item/v1",
        f"work_id: {unit_id}",
        f"work_uid: {_fixture_work_uid('unit', unit_id)}",
        "kind: unit",
        f"parent_id: {task_id}",
        f"unit_id: {unit_id}",
        f"task_id: {task_id}",
        "status: worker_ready",
        "target_files:",
        *(f"  - {target}" for target in targets),
        f"stop_condition: {stop_condition}",
        "---",
        "",
        "# Heartbeat fixture unit",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return relative


def _create_heartbeat_candidate(
    root: Path,
    *,
    task_id: str = "TASK-AR-655-HEARTBEAT",
    suffix: str = "heartbeat",
    now: str = "2026-08-03T09:00:00+09:00",
    worktree_path: str = "",
) -> dict[str, object]:
    (root / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    if not worktree_path:
        _write_worktree(root, task_id)
    _write_canonical_task_identity(
        root,
        task_id,
        task_set_id="TASKSET-AR-655-HEARTBEAT",
    )
    stop_condition = f"stop_after:UNIT-{task_id}-001:verification"
    unit_rel = _write_heartbeat_unit(
        root,
        task_id=task_id,
        stop_condition=stop_condition,
    )
    create_args = [
        "create",
        "--task-id",
        task_id,
        "--task-set-id",
        "TASKSET-AR-655-HEARTBEAT",
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--stop-condition",
        stop_condition,
        "--agent-role",
        "lead-engineer",
        "--agent-instance-id",
        f"le-20260803-090000-kst-{suffix}",
        "--callsite-id",
        f"terminal:wt-{task_id.lower()}:tab-01",
        "--lease-minutes",
        "30",
        "--now",
        now,
        "--suffix",
        suffix,
        "--json",
    ]
    if worktree_path:
        create_args.extend(("--worktree-path", worktree_path))
    created = _run_dispatcher(root, *create_args)
    assert created.returncode == 0, created.stderr or created.stdout
    return json.loads(created.stdout)


def _heartbeat_args(
    claim: dict[str, object],
    *,
    now: str = "2026-08-03T09:10:00+09:00",
    expected_revision: int = 0,
    agent_instance_id: str | None = None,
    callsite_id: str | None = None,
) -> tuple[str, ...]:
    return (
        "heartbeat",
        "--claim-id",
        str(claim["claim_id"]),
        "--agent-instance-id",
        agent_instance_id or str(claim["agent_instance_id"]),
        "--callsite-id",
        callsite_id or str(claim["callsite_id"]),
        "--expected-revision",
        str(expected_revision),
        "--phase",
        "implementation",
        "--progress-pct",
        "45",
        "--step-index",
        "4",
        "--step-total",
        "10",
        "--status-text",
        "Atomic heartbeat contract under test",
        "--now",
        now,
        "--json",
    )


def _replace_cli_option(args: tuple[str, ...], flag: str, value: str) -> tuple[str, ...]:
    updated = list(args)
    index = updated.index(flag)
    updated[index + 1] = value
    return tuple(updated)


def _without_cli_option(args: tuple[str, ...], flag: str) -> tuple[str, ...]:
    updated = list(args)
    index = updated.index(flag)
    del updated[index : index + 2]
    return tuple(updated)


PROGRESS_OPTIONS = (
    "--phase",
    "--progress-pct",
    "--step-index",
    "--step-total",
    "--status-text",
)


def _heartbeat_without_progress_args(claim: dict[str, object]) -> tuple[str, ...]:
    args = _heartbeat_args(claim)
    for flag in PROGRESS_OPTIONS:
        args = _without_cli_option(args, flag)
    return args


def _claim_path(root: Path, created: dict[str, object]) -> Path:
    return root / str(created["path"])


def _read_created_claim(root: Path, created: dict[str, object]) -> dict[str, object]:
    return json.loads(_claim_path(root, created).read_text(encoding="utf-8"))


def test_create_claim_starts_revision_zero_with_component_scope_binding(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="create-binding")
    claim = created["claim"]

    assert claim["mutation_revision"] == 0
    assert claim["scope_binding"] == _expected_scope_binding(
        claim,
        bound_at="2026-08-03T09:00:00+09:00",
    )
    assert _read_created_claim(tmp_path, created)["scope_binding"] == claim["scope_binding"]


def test_heartbeat_cli_atomically_advances_timestamps_progress_and_revision(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="cli-success")
    claim = created["claim"]

    result = _run_dispatcher(tmp_path, *_heartbeat_args(claim))

    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    persisted = _read_created_claim(tmp_path, created)
    assert persisted["last_heartbeat"] == "2026-08-03T09:10:00+09:00"
    assert persisted["updated_at"] == "2026-08-03T09:10:00+09:00"
    assert persisted["expires_at"] == "2026-08-03T09:40:00+09:00"
    assert persisted["lease"]["heartbeat_at"] == persisted["last_heartbeat"]
    assert persisted["lease"]["expires_at"] == persisted["expires_at"]
    assert persisted["phase"] == "implementation"
    assert persisted["progress_pct"] == 45
    assert persisted["step_index"] == 4
    assert persisted["step_total"] == 10
    assert persisted["status_text"] == "Atomic heartbeat contract under test"
    assert persisted["mutation_revision"] == 1
    assert response["receipt"]["claim_revision"] == 1
    assert response["projection"]["claim_revision"] == 1
    projected_agent = response["projection"]["pointer"]["current_agents"][0]
    for field in (
        "phase",
        "progress_pct",
        "step_index",
        "step_total",
        "status_text",
        "last_heartbeat",
        "mutation_revision",
    ):
        assert projected_agent[field] == persisted[field]


def test_heartbeat_module_api_uses_the_same_atomic_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="api-success")
    claim = created["claim"]
    dispatcher = _load_dispatcher_module()
    parsed = dispatcher.build_parser().parse_args(
        ["--root", str(tmp_path), *_heartbeat_args(claim)]
    )

    rc = parsed.func(parsed)

    captured = capsys.readouterr()
    assert rc == 0, captured.err or captured.out
    response = json.loads(captured.out)
    assert response["receipt"]["claim_revision"] == 1
    assert _read_created_claim(tmp_path, created)["mutation_revision"] == 1


def test_heartbeat_success_reconciles_instance_and_pane_event_receipts(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="receipt-reconcile")
    claim = created["claim"]

    result = _run_dispatcher(tmp_path, *_heartbeat_args(claim))

    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    persisted = _read_created_claim(tmp_path, created)
    instance_path = (
        tmp_path
        / "agents/runtime/instances"
        / f"{claim['agent_instance_id']}.json"
    )
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    assert instance["updated_at"] == persisted["updated_at"]
    assert instance["last_heartbeat"] == persisted["last_heartbeat"]
    assert instance["claim_revision"] == persisted["mutation_revision"]
    instance_receipt = response["receipt"]["instance"]
    assert instance_receipt["path"] == instance_path.relative_to(tmp_path).as_posix()
    assert instance_receipt["updated_at"] == instance["updated_at"]
    assert instance_receipt["claim_revision"] == instance["claim_revision"]

    event_log = tmp_path / "agents/runtime/pane_events/pane-events.jsonl"
    events = [
        json.loads(line)
        for line in event_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    heartbeats = [event for event in events if event.get("event") == "instance_heartbeat"]
    assert len(heartbeats) == 1
    event = heartbeats[0]
    assert event["agent_instance_id"] == claim["agent_instance_id"]
    assert event["claim_id"] == claim["claim_id"]
    assert event["ts"] == persisted["last_heartbeat"]
    event_receipt = response["receipt"]["pane_event"]
    for field in ("seq", "event", "agent_instance_id", "claim_id", "ts"):
        assert event_receipt[field] == event[field]


@pytest.mark.parametrize(
    ("case", "mutate", "now", "revision", "owner_suffix", "callsite_suffix", "message"),
    (
        (
            "wrong-owner",
            lambda claim: None,
            "2026-08-03T09:10:00+09:00",
            0,
            "-other",
            "",
            "owner",
        ),
        (
            "wrong-callsite",
            lambda claim: None,
            "2026-08-03T09:10:00+09:00",
            0,
            "",
            ":other",
            "callsite",
        ),
        (
            "inactive",
            lambda claim: claim.update(status="released"),
            "2026-08-03T09:10:00+09:00",
            0,
            "",
            "",
            "active",
        ),
        (
            "expired",
            lambda claim: (
                claim.update(expires_at="2026-08-03T08:59:59+09:00"),
                claim["lease"].update(expires_at="2026-08-03T08:59:59+09:00"),
            ),
            "2026-08-03T09:10:00+09:00",
            0,
            "",
            "",
            "expired",
        ),
        (
            "timestamp-regression",
            lambda claim: None,
            "2026-08-03T08:59:59+09:00",
            0,
            "",
            "",
            "strictly increasing",
        ),
        (
            "timestamp-equality",
            lambda claim: None,
            "2026-08-03T09:00:00+09:00",
            0,
            "",
            "",
            "strictly increasing",
        ),
        (
            "torn-heartbeat",
            lambda claim: claim["lease"].update(
                heartbeat_at="2026-08-03T08:59:59+09:00"
            ),
            "2026-08-03T09:10:00+09:00",
            0,
            "",
            "",
            "timestamp",
        ),
        (
            "torn-expiry",
            lambda claim: claim["lease"].update(
                expires_at="2026-08-03T09:31:00+09:00"
            ),
            "2026-08-03T09:10:00+09:00",
            0,
            "",
            "",
            "expires",
        ),
        (
            "stale-revision",
            lambda claim: None,
            "2026-08-03T09:10:00+09:00",
            7,
            "",
            "",
            "revision",
        ),
    ),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_heartbeat_refuses_invalid_authority_without_mutation(
    tmp_path: Path,
    case: str,
    mutate,
    now: str,
    revision: int,
    owner_suffix: str,
    callsite_suffix: str,
    message: str,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix=f"reject-{case}")
    path = _claim_path(tmp_path, created)
    claim = json.loads(path.read_text(encoding="utf-8"))
    mutate(claim)
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    before = path.read_bytes()
    before_tree = _tree_entry_snapshot(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        *_heartbeat_args(
            claim,
            now=now,
            expected_revision=revision,
            agent_instance_id=str(claim["agent_instance_id"]) + owner_suffix,
            callsite_id=str(claim["callsite_id"]) + callsite_suffix,
        ),
        env_overrides={"AGENT_RUNTIME_CLAIM_GRACE_SECONDS": "0"},
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert message in result.stderr.lower()
    assert path.read_bytes() == before
    assert _tree_entry_snapshot(tmp_path) == before_tree


def test_heartbeat_accepts_exact_expiry_equality_but_requires_newer_heartbeat(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="expiry-equality")
    path = _claim_path(tmp_path, created)
    claim = json.loads(path.read_text(encoding="utf-8"))
    claim["expires_at"] = "2026-08-03T09:10:00+09:00"
    claim["lease"]["expires_at"] = "2026-08-03T09:10:00+09:00"
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = _run_dispatcher(
        tmp_path,
        *_heartbeat_args(claim, now="2026-08-03T09:10:00+09:00"),
        env_overrides={"AGENT_RUNTIME_CLAIM_GRACE_SECONDS": "0"},
    )

    assert result.returncode == 0, result.stderr or result.stdout
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["mutation_revision"] == 1
    assert persisted["expires_at"] == "2026-08-03T09:20:00+09:00"


@pytest.mark.parametrize("operation", ("heartbeat", "renew"))
def test_claim_mutation_preserves_subsecond_timestamp_monotonicity(
    tmp_path: Path,
    operation: str,
) -> None:
    created = _create_heartbeat_candidate(
        tmp_path,
        suffix=f"subsecond-{operation}",
    )
    claim = created["claim"]
    now = "2026-08-03T09:00:00.000001+09:00"
    args = (
        _heartbeat_args(claim, now=now)
        if operation == "heartbeat"
        else _renew_args(claim, now=now)
    )

    result = _run_dispatcher(tmp_path, *args)

    assert result.returncode == 0, result.stderr or result.stdout
    persisted = _read_created_claim(tmp_path, created)
    assert persisted["last_heartbeat"] == now
    assert persisted["lease"]["heartbeat_at"] == now
    expected_expiry = (
        "2026-08-03T09:30:00.000001+09:00"
        if operation == "heartbeat"
        else "2026-08-03T09:45:00.000001+09:00"
    )
    assert persisted["expires_at"] == expected_expiry
    assert persisted["lease"]["expires_at"] == expected_expiry


def test_heartbeat_without_progress_options_preserves_coherent_progress(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="heartbeat-no-progress")
    claim = created["claim"]

    result = _run_dispatcher(tmp_path, *_heartbeat_without_progress_args(claim))

    assert result.returncode == 0, result.stderr or result.stdout
    persisted = _read_created_claim(tmp_path, created)
    for field in ("phase", "progress_pct", "step_index", "step_total", "status_text"):
        assert persisted[field] == claim[field]
    assert persisted["mutation_revision"] == 1
    assert persisted["last_heartbeat"] == "2026-08-03T09:10:00+09:00"


@pytest.mark.parametrize("missing_flag", PROGRESS_OPTIONS)
def test_heartbeat_refuses_partial_progress_group_without_mutation(
    tmp_path: Path,
    missing_flag: str,
) -> None:
    created = _create_heartbeat_candidate(
        tmp_path,
        suffix=f"partial-{missing_flag.removeprefix('--')}",
    )
    claim = created["claim"]
    path = _claim_path(tmp_path, created)
    before = path.read_bytes()
    before_tree = _tree_entry_snapshot(tmp_path)
    args = _without_cli_option(_heartbeat_args(claim), missing_flag)

    result = _run_dispatcher(tmp_path, *args)

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert "progress" in result.stderr.lower()
    assert path.read_bytes() == before
    assert _tree_entry_snapshot(tmp_path) == before_tree


@pytest.mark.parametrize(
    ("case", "overrides", "message"),
    (
        ("negative-pct", {"--progress-pct": "-1"}, "progress"),
        ("oversized-pct", {"--progress-pct": "101"}, "progress"),
        ("zero-step-index", {"--step-index": "0"}, "step"),
        ("step-past-total", {"--step-index": "11"}, "step"),
        ("zero-step-total", {"--step-total": "0"}, "step"),
        (
            "completion-before-final-step",
            {
                "--phase": "completed",
                "--progress-pct": "100",
                "--step-index": "9",
                "--step-total": "10",
            },
            "completion",
        ),
        (
            "completion-before-full-progress",
            {
                "--phase": "completed",
                "--progress-pct": "99",
                "--step-index": "10",
                "--step-total": "10",
            },
            "completion",
        ),
    ),
)
def test_heartbeat_refuses_incoherent_progress_without_mutation(
    tmp_path: Path,
    case: str,
    overrides: dict[str, str],
    message: str,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix=f"progress-{case}")
    claim = created["claim"]
    path = _claim_path(tmp_path, created)
    before = path.read_bytes()
    before_tree = _tree_entry_snapshot(tmp_path)
    args = _heartbeat_args(claim)
    for flag, value in overrides.items():
        args = _replace_cli_option(args, flag, value)

    result = _run_dispatcher(tmp_path, *args)

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert message in result.stderr.lower()
    assert path.read_bytes() == before
    assert _tree_entry_snapshot(tmp_path) == before_tree


def test_heartbeat_atomic_write_failure_leaves_all_authority_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="atomic-failure")
    claim = created["claim"]
    before = _tree_entry_snapshot(tmp_path)
    dispatcher = _load_dispatcher_module()

    def fail_atomic_write(*_args, **_kwargs):
        raise OSError("forced heartbeat atomic replacement failure")

    monkeypatch.setattr(dispatcher.atomic_io, "write_json_atomic", fail_atomic_write)
    rc = dispatcher.main(["--root", str(tmp_path), *_heartbeat_args(claim)])

    captured = capsys.readouterr()
    assert rc == 1
    assert "forced heartbeat atomic replacement failure" in captured.err
    assert _tree_entry_snapshot(tmp_path) == before


def test_concurrent_heartbeats_with_same_revision_have_exactly_one_winner(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="concurrent-cas")
    claim = created["claim"]

    def invoke() -> subprocess.CompletedProcess[str]:
        return _run_dispatcher(tmp_path, *_heartbeat_args(claim))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: invoke(), range(2)))

    assert sorted(result.returncode for result in results) == [0, 1]
    loser = next(result for result in results if result.returncode == 1)
    assert "revision" in loser.stderr.lower()
    assert _read_created_claim(tmp_path, created)["mutation_revision"] == 1


def _renew_args(
    claim: dict[str, object],
    *,
    expected_revision: int = 0,
    expected_scope_digest: str | None = None,
    now: str = "2026-08-03T09:10:00+09:00",
    replan_ref: str = "",
    agent_instance_id: str | None = None,
    callsite_id: str | None = None,
    lease_minutes: str = "45",
) -> tuple[str, ...]:
    args = [
        "renew",
        "--claim-id",
        str(claim["claim_id"]),
        "--agent-instance-id",
        agent_instance_id or str(claim["agent_instance_id"]),
        "--callsite-id",
        callsite_id or str(claim["callsite_id"]),
        "--expected-revision",
        str(expected_revision),
        "--expected-scope-digest",
        expected_scope_digest or _claim_scope_digest(claim),
        "--lease-minutes",
        lease_minutes,
        "--now",
        now,
        "--json",
    ]
    if replan_ref:
        args.extend(("--replan-ref", replan_ref))
    return tuple(args)


@pytest.mark.parametrize("operation", ("heartbeat", "renew"))
@pytest.mark.parametrize("deadline_case", ("malformed", "partial", "naive"))
def test_claim_mutation_refuses_indeterminate_deadline_without_mutation(
    tmp_path: Path,
    operation: str,
    deadline_case: str,
) -> None:
    created = _create_heartbeat_candidate(
        tmp_path,
        suffix=f"{operation}-deadline-{deadline_case}",
    )
    path = _claim_path(tmp_path, created)
    claim = json.loads(path.read_text(encoding="utf-8"))
    if deadline_case == "malformed":
        claim["expires_at"] = "not-an-iso-deadline"
        claim["lease"]["expires_at"] = "not-an-iso-deadline"
    elif deadline_case == "partial":
        claim["lease"].pop("expires_at")
    else:
        claim["expires_at"] = "2026-08-03T09:30:00"
        claim["lease"]["expires_at"] = "2026-08-03T09:30:00"
    path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    before = _tree_entry_snapshot(tmp_path)
    args = _heartbeat_args(claim) if operation == "heartbeat" else _renew_args(claim)

    result = _run_dispatcher(
        tmp_path,
        *args,
        env_overrides={"AGENT_RUNTIME_CLAIM_GRACE_SECONDS": "0"},
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert _tree_entry_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    ("case", "mutate", "now", "expected_revision"),
    (
        ("inactive", lambda claim: claim.update(status="released"), "2026-08-03T09:10:00+09:00", 0),
        (
            "expired",
            lambda claim: (
                claim.update(expires_at="2026-08-03T08:59:59+09:00"),
                claim["lease"].update(expires_at="2026-08-03T08:59:59+09:00"),
            ),
            "2026-08-03T09:10:00+09:00",
            0,
        ),
        ("heartbeat-regression", lambda claim: None, "2026-08-03T08:59:59+09:00", 0),
        ("heartbeat-equality", lambda claim: None, "2026-08-03T09:00:00+09:00", 0),
        (
            "torn-heartbeat",
            lambda claim: claim["lease"].update(
                heartbeat_at="2026-08-03T08:59:59+09:00"
            ),
            "2026-08-03T09:10:00+09:00",
            0,
        ),
        (
            "torn-expiry",
            lambda claim: claim["lease"].update(
                expires_at="2026-08-03T09:31:00+09:00"
            ),
            "2026-08-03T09:10:00+09:00",
            0,
        ),
        ("stale-revision", lambda claim: None, "2026-08-03T09:10:00+09:00", 9),
    ),
)
def test_renew_refuses_invalid_authority_without_any_mutation(
    tmp_path: Path,
    case: str,
    mutate,
    now: str,
    expected_revision: int,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix=f"renew-reject-{case}")
    path = _claim_path(tmp_path, created)
    claim = json.loads(path.read_text(encoding="utf-8"))
    mutate(claim)
    path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    before = _tree_entry_snapshot(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        *_renew_args(
            claim,
            now=now,
            expected_revision=expected_revision,
        ),
        env_overrides={"AGENT_RUNTIME_CLAIM_GRACE_SECONDS": "0"},
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert _tree_entry_snapshot(tmp_path) == before


def test_renew_atomic_write_failure_leaves_full_snapshot_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="renew-atomic-failure")
    claim = created["claim"]
    before = _tree_entry_snapshot(tmp_path)
    dispatcher = _load_dispatcher_module()

    def fail_atomic_write(*_args, **_kwargs):
        raise OSError("forced renewal atomic replacement failure")

    monkeypatch.setattr(dispatcher.atomic_io, "write_json_atomic", fail_atomic_write)

    rc = dispatcher.main(["--root", str(tmp_path), *_renew_args(claim)])

    capsys.readouterr()
    assert rc == 1
    assert _tree_entry_snapshot(tmp_path) == before


def test_renew_unchanged_scope_extends_lease_and_returns_equal_scope_digests(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="renew-same")
    claim = created["claim"]
    old_digest = _claim_scope_digest(claim)

    result = _run_dispatcher(tmp_path, *_renew_args(claim))

    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    persisted = _read_created_claim(tmp_path, created)
    assert persisted["last_heartbeat"] == "2026-08-03T09:10:00+09:00"
    assert persisted["updated_at"] == "2026-08-03T09:10:00+09:00"
    assert persisted["expires_at"] == "2026-08-03T09:55:00+09:00"
    assert persisted["lease"]["heartbeat_at"] == persisted["last_heartbeat"]
    assert persisted["lease"]["expires_at"] == persisted["expires_at"]
    assert persisted["mutation_revision"] == 1
    assert response["receipt"]["claim_revision"] == 1
    scope_change = response["receipt"]["scope_change"]
    assert scope_change["changed"] is False
    assert scope_change["old_digest"] == old_digest
    assert scope_change["new_digest"] == old_digest
    assert scope_change["replan_ref"] is None


def test_renew_success_reconciles_projection_instance_and_single_pane_event(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="renew-receipt-reconcile")
    claim = created["claim"]

    result = _run_dispatcher(tmp_path, *_renew_args(claim))

    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    persisted = _read_created_claim(tmp_path, created)
    projection = response["projection"]
    assert projection["claim_revision"] == persisted["mutation_revision"]
    projected_agents = projection["pointer"]["current_agents"]
    assert len(projected_agents) == 1
    projected = projected_agents[0]
    assert projected["claim_id"] == claim["claim_id"]
    assert projected["mutation_revision"] == persisted["mutation_revision"]
    assert projected["last_heartbeat"] == persisted["last_heartbeat"]

    instance_path = (
        tmp_path
        / "agents/runtime/instances"
        / f"{claim['agent_instance_id']}.json"
    )
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    assert instance["updated_at"] == persisted["updated_at"]
    assert instance["last_heartbeat"] == persisted["last_heartbeat"]
    assert instance["claim_revision"] == persisted["mutation_revision"]
    instance_receipt = response["receipt"]["instance"]
    assert instance_receipt["updated_at"] == instance["updated_at"]
    assert instance_receipt["claim_revision"] == instance["claim_revision"]

    event_log = tmp_path / "agents/runtime/pane_events/pane-events.jsonl"
    events = [
        json.loads(line)
        for line in event_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    renewal_events = [
        event for event in events if event.get("event") == "instance_heartbeat"
    ]
    assert len(renewal_events) == 1
    event = renewal_events[0]
    assert event["claim_id"] == claim["claim_id"]
    assert event["agent_instance_id"] == claim["agent_instance_id"]
    assert event["ts"] == persisted["last_heartbeat"]
    event_receipt = response["receipt"]["pane_event"]
    for field in ("seq", "event", "claim_id", "agent_instance_id", "ts"):
        assert event_receipt[field] == event[field]


def test_renew_refuses_stale_expected_scope_digest_without_mutation(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="stale-scope-digest")
    claim = created["claim"]
    before = _tree_entry_snapshot(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        *_renew_args(claim, expected_scope_digest="0" * 64),
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert "scope" in result.stderr.lower()
    assert _tree_entry_snapshot(tmp_path) == before


def test_concurrent_renewals_with_same_revision_have_exactly_one_winner(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="renew-concurrent-cas")
    claim = created["claim"]
    args = _renew_args(claim)

    def invoke() -> subprocess.CompletedProcess[str]:
        return _run_dispatcher(tmp_path, *args)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: invoke(), range(2)))

    assert sorted(result.returncode for result in results) == [0, 1]
    loser = next(result for result in results if result.returncode == 1)
    assert "revision" in loser.stderr.lower()
    persisted = _read_created_claim(tmp_path, created)
    assert persisted["mutation_revision"] == 1
    assert persisted["last_heartbeat"] == "2026-08-03T09:10:00+09:00"
    assert persisted["lease"]["heartbeat_at"] == persisted["last_heartbeat"]


@pytest.mark.parametrize(
    ("identity_field", "expected_message"),
    (("agent_instance_id", "owner"), ("callsite_id", "callsite")),
)
def test_renew_refuses_wrong_owner_or_callsite_without_mutation(
    tmp_path: Path,
    identity_field: str,
    expected_message: str,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix=f"renew-{identity_field}")
    claim = created["claim"]
    before = _tree_entry_snapshot(tmp_path)
    kwargs = {
        "agent_instance_id": str(claim["agent_instance_id"]),
        "callsite_id": str(claim["callsite_id"]),
    }
    kwargs[identity_field] += "-wrong"

    result = _run_dispatcher(tmp_path, *_renew_args(claim, **kwargs))

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert expected_message in result.stderr.lower()
    assert _tree_entry_snapshot(tmp_path) == before


@pytest.mark.parametrize("lease_minutes", ("0", "-1", str(10**100)))
def test_renew_refuses_invalid_or_overflowing_lease_without_mutation(
    tmp_path: Path,
    lease_minutes: str,
) -> None:
    suffix = "overflow" if len(lease_minutes) > 20 else lease_minutes.replace("-", "negative")
    created = _create_heartbeat_candidate(tmp_path, suffix=f"renew-lease-{suffix}")
    claim = created["claim"]
    before = _tree_entry_snapshot(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        *_renew_args(claim, lease_minutes=lease_minutes),
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert "lease_minutes" in result.stderr
    assert _tree_entry_snapshot(tmp_path) == before


@pytest.mark.parametrize("drift_component", ("target_files", "stop_condition"))
def test_renew_refuses_single_component_drift_without_replan_or_mutation(
    tmp_path: Path,
    drift_component: str,
) -> None:
    created = _create_heartbeat_candidate(
        tmp_path,
        suffix=f"single-drift-{drift_component}",
    )
    claim = created["claim"]
    targets = tuple(str(item) for item in claim["target_files"])
    stop_condition = str(claim["stop_condition"])
    if drift_component == "target_files":
        targets = (*targets, "scripts/target_only_replan.py")
    else:
        stop_condition = stop_condition + ":stop-only-drift"
    _write_heartbeat_unit(
        tmp_path,
        task_id=str(claim["task_id"]),
        targets=targets,
        stop_condition=stop_condition,
    )
    before = _tree_entry_snapshot(tmp_path)

    result = _run_dispatcher(tmp_path, *_renew_args(claim))

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert _tree_entry_snapshot(tmp_path) == before


@pytest.mark.parametrize("with_unaccepted_replan", (False, True))
def test_renew_refuses_scope_drift_without_matching_accepted_replan(
    tmp_path: Path,
    with_unaccepted_replan: bool,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix=f"drift-{with_unaccepted_replan}")
    claim = created["claim"]
    unit_path = tmp_path / str(claim["unit_spec"])
    _write_heartbeat_unit(
        tmp_path,
        task_id=str(claim["task_id"]),
        targets=("scripts/claim_worker.py", "scripts/silently_broadened.py"),
        stop_condition="stop_after:UNIT:adjacent-scope",
    )
    replan_ref = ""
    if with_unaccepted_replan:
        replan_ref = "reviews/REVIEW-2026-08-03-draft-replan.md"
        review = tmp_path / replan_ref
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text(
            "---\nstatus: draft\ntask_id: "
            + str(claim["task_id"])
            + "\nunit_id: "
            + str(claim["unit_id"])
            + "\n---\n",
            encoding="utf-8",
        )
        _write_plan_design_record(
            tmp_path,
            claim=claim,
            replan_ref=replan_ref,
            anchor=unit_path,
        )
    before = _claim_path(tmp_path, created).read_bytes()

    result = _run_dispatcher(
        tmp_path,
        *_renew_args(claim, replan_ref=replan_ref),
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "replan" in result.stderr.lower()
    assert _claim_path(tmp_path, created).read_bytes() == before


def _write_plan_design_record(
    root: Path,
    *,
    claim: dict[str, object],
    replan_ref: str,
    anchor: Path,
) -> None:
    anchor_rel = anchor.relative_to(root).as_posix()
    registry = {
        "schema": "agent-runtime-plan-assumptions/v1",
        "updated_at": "2026-08-03T09:09:00+09:00",
        "assumption_sets": [
            {
                "taskset_id": claim["task_set_id"],
                "design_record": replan_ref,
                "recorded_at": "2026-08-03T09:09:00+09:00",
                "revalidation_policy": "block_dispatch_on_drift",
                "anchors": [
                    {
                        "path": anchor_rel,
                        "kind": "sha256",
                        "value": hashlib.sha256(anchor.read_bytes()).hexdigest(),
                    }
                ],
            }
        ],
    }
    path = root / "agents/project/work-items/PLAN-ASSUMPTIONS.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_accepted_replan_review(
    root: Path,
    *,
    relative: str,
    task_id: str,
    unit_id: str,
    indirect_ref: str = "",
) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"id: {Path(relative).stem}",
        "status: accepted",
        "signal: pass",
        "tier: T3",
        f"task_id: {task_id}",
        f"unit_id: {unit_id}",
    ]
    if indirect_ref:
        lines.extend(("evidence:", f"  - {indirect_ref}"))
    lines.extend(("---", "", "# Accepted renewal replan", ""))
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize(
    "invalid_replan",
    ("wrong-task", "wrong-unit", "design-record-mismatch", "indirect-design-record"),
)
def test_renew_refuses_nonmatching_or_indirect_accepted_replan_without_mutation(
    tmp_path: Path,
    invalid_replan: str,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix=f"bad-replan-{invalid_replan}")
    claim = created["claim"]
    unit_path = tmp_path / str(claim["unit_spec"])
    _write_heartbeat_unit(
        tmp_path,
        task_id=str(claim["task_id"]),
        targets=(*tuple(str(item) for item in claim["target_files"]), "scripts/replan_drift.py"),
        stop_condition=str(claim["stop_condition"]),
    )
    requested_ref = f"reviews/REVIEW-2026-08-03-{invalid_replan}-requested.md"
    review_task_id = str(claim["task_id"])
    review_unit_id = str(claim["unit_id"])
    if invalid_replan == "wrong-task":
        review_task_id = review_task_id + "-OTHER"
    elif invalid_replan == "wrong-unit":
        review_unit_id = review_unit_id + "-OTHER"
    _write_accepted_replan_review(
        tmp_path,
        relative=requested_ref,
        task_id=review_task_id,
        unit_id=review_unit_id,
    )

    design_ref = requested_ref
    if invalid_replan in {"design-record-mismatch", "indirect-design-record"}:
        design_ref = f"reviews/REVIEW-2026-08-03-{invalid_replan}-design-record.md"
        _write_accepted_replan_review(
            tmp_path,
            relative=design_ref,
            task_id=str(claim["task_id"]),
            unit_id=str(claim["unit_id"]),
            indirect_ref=requested_ref if invalid_replan == "indirect-design-record" else "",
        )
    _write_plan_design_record(
        tmp_path,
        claim=claim,
        replan_ref=design_ref,
        anchor=unit_path,
    )
    before = _tree_entry_snapshot(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        *_renew_args(claim, replan_ref=requested_ref),
    )

    assert result.returncode == 1, result.stdout or result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert _tree_entry_snapshot(tmp_path) == before


def test_renew_accepts_matching_plan_design_replan_and_receipts_old_new_scope(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="accepted-replan")
    claim = created["claim"]
    old_digest = _claim_scope_digest(claim)
    unit_path = tmp_path / str(claim["unit_spec"])
    new_targets = ("scripts/claim_worker.py", "scripts/replanned_helper.py")
    new_stop = "stop_after:UNIT:replanned-verification"
    _write_heartbeat_unit(
        tmp_path,
        task_id=str(claim["task_id"]),
        targets=new_targets,
        stop_condition=new_stop,
    )
    replan_ref = "reviews/REVIEW-2026-08-03-accepted-heartbeat-replan.md"
    review = tmp_path / replan_ref
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(
        "---\n"
        "id: REVIEW-2026-08-03-accepted-heartbeat-replan\n"
        "status: accepted\n"
        "signal: pass\n"
        "tier: T3\n"
        f"task_id: {claim['task_id']}\n"
        f"unit_id: {claim['unit_id']}\n"
        "---\n\n# Accepted replan\n",
        encoding="utf-8",
    )
    _write_plan_design_record(
        tmp_path,
        claim=claim,
        replan_ref=replan_ref,
        anchor=unit_path,
    )

    result = _run_dispatcher(
        tmp_path,
        *_renew_args(claim, replan_ref=replan_ref),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    persisted = _read_created_claim(tmp_path, created)
    new_digest = persisted["scope_binding"]["digest"]
    assert new_digest != old_digest
    assert persisted["target_files"] == list(new_targets)
    assert persisted["stop_condition"] == new_stop
    scope_change = response["receipt"]["scope_change"]
    assert scope_change["changed"] is True
    assert scope_change["old_digest"] == old_digest
    assert scope_change["new_digest"] == new_digest
    assert scope_change["replan_ref"] == replan_ref


def test_accepted_renewal_persists_bounded_full_scope_provenance(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="full-scope-provenance")
    claim = created["claim"]
    old_binding = _claim_scope_binding(claim)
    unit_path = tmp_path / str(claim["unit_spec"])
    new_targets = (*tuple(str(item) for item in claim["target_files"]), "scripts/provenance.py")
    new_stop = str(claim["stop_condition"]) + ":replanned"
    _write_heartbeat_unit(
        tmp_path,
        task_id=str(claim["task_id"]),
        targets=new_targets,
        stop_condition=new_stop,
    )
    replan_ref = "reviews/REVIEW-2026-08-03-full-scope-provenance.md"
    _write_accepted_replan_review(
        tmp_path,
        relative=replan_ref,
        task_id=str(claim["task_id"]),
        unit_id=str(claim["unit_id"]),
    )
    _write_plan_design_record(
        tmp_path,
        claim=claim,
        replan_ref=replan_ref,
        anchor=unit_path,
    )

    result = _run_dispatcher(
        tmp_path,
        *_renew_args(claim, replan_ref=replan_ref),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    persisted = _read_created_claim(tmp_path, created)
    new_binding = persisted["scope_binding"]
    assert new_binding == _expected_scope_binding(
        persisted,
        bound_at="2026-08-03T09:10:00+09:00",
    )
    assert set(old_binding["components"]) == {
        "task",
        "unit",
        "target_files",
        "stop_condition",
    }
    assert set(new_binding["components"]) == set(old_binding["components"])
    last_renewal = persisted["last_renewal"]
    assert last_renewal["replan_ref"] == replan_ref
    assert last_renewal["old_scope_binding"] == old_binding
    assert last_renewal["new_scope_binding"] == new_binding
    assert len(json.dumps(last_renewal, ensure_ascii=False)) <= 4096
    scope_receipt = response["receipt"]["scope_change"]
    assert scope_receipt["replan_ref"] == replan_ref
    assert scope_receipt["old_scope_binding"] == old_binding
    assert scope_receipt["new_scope_binding"] == new_binding


def test_heartbeat_never_changes_git_head_index_or_refs(tmp_path: Path) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "heartbeat-no-git")
    created = _create_heartbeat_candidate(
        linked,
        task_id="TASK-AR-655-NO-GIT",
        suffix="no-git",
        worktree_path=".",
    )
    claim = created["claim"]
    pointer = linked / "agents/project/NEXT-SESSION-POINTER.yml"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text("sentinel: serial projection owner\n", encoding="utf-8")
    pointer_before = pointer.read_bytes()
    before = {
        "head": _git_stdout(linked, "rev-parse", "HEAD"),
        "index": _git_stdout(linked, "write-tree"),
        "refs": _git_stdout(linked, "for-each-ref", "--format=%(refname) %(objectname)"),
    }

    heartbeated = _run_dispatcher(linked, *_heartbeat_args(claim))
    assert heartbeated.returncode == 0, heartbeated.stderr or heartbeated.stdout
    persisted = _read_created_claim(linked, created)
    renewed = _run_dispatcher(
        linked,
        *_renew_args(
            persisted,
            expected_revision=1,
            expected_scope_digest=str(persisted["scope_binding"]["digest"]),
            now="2026-08-03T09:20:00+09:00",
        ),
    )
    assert renewed.returncode == 0, renewed.stderr or renewed.stdout

    assert _git_stdout(linked, "rev-parse", "HEAD") == before["head"]
    assert _git_stdout(linked, "write-tree") == before["index"]
    assert _git_stdout(linked, "for-each-ref", "--format=%(refname) %(objectname)") == before["refs"]
    assert pointer.read_bytes() == pointer_before


def test_committed_heartbeat_reports_auxiliary_failures_without_retry_ambiguity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="aux-warning")
    claim = created["claim"]
    dispatcher = _load_dispatcher_module()

    def fail_instance(*_args, **_kwargs):
        raise OSError("forced instance refresh failure")

    def fail_event(*_args, **_kwargs):
        raise OSError("forced pane event failure")

    monkeypatch.setattr(dispatcher, "record_claim_instance", fail_instance)
    monkeypatch.setattr(dispatcher, "append_event", fail_event)

    rc = dispatcher.main(["--root", str(tmp_path), *_heartbeat_args(claim)])

    captured = capsys.readouterr()
    assert rc == 0, captured.err or captured.out
    response = json.loads(captured.out)
    assert response["status"] == "heartbeat_committed_with_warnings"
    assert response["receipt"]["committed"] is True
    assert response["receipt"]["claim_revision"] == 1
    stages = {item["stage"] for item in response["post_commit_warnings"]}
    assert stages == {"agent-instance-registry", "claim-heartbeat-event"}
    assert _read_created_claim(tmp_path, created)["mutation_revision"] == 1


def test_committed_renew_reports_auxiliary_failures_without_losing_claim_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="renew-aux-warning")
    claim = created["claim"]
    dispatcher = _load_dispatcher_module()

    def fail_instance(*_args, **_kwargs):
        raise OSError("forced renewal instance refresh failure")

    def fail_event(*_args, **_kwargs):
        raise OSError("forced renewal pane event failure")

    monkeypatch.setattr(dispatcher, "record_claim_instance", fail_instance)
    monkeypatch.setattr(dispatcher, "append_event", fail_event)
    monkeypatch.setattr(
        dispatcher,
        "append_census_event",
        fail_event,
        raising=False,
    )

    rc = dispatcher.main(["--root", str(tmp_path), *_renew_args(claim)])

    captured = capsys.readouterr()
    assert rc == 0, captured.err or captured.out
    response = json.loads(captured.out)
    assert response["status"].endswith("committed_with_warnings")
    assert response["receipt"]["committed"] is True
    assert response["receipt"]["claim_revision"] == 1
    assert len(response["post_commit_warnings"]) == 2
    persisted = _read_created_claim(tmp_path, created)
    assert persisted["mutation_revision"] == 1
    assert persisted["updated_at"] == "2026-08-03T09:10:00+09:00"
    assert persisted["lease"]["heartbeat_at"] == persisted["last_heartbeat"]


def test_projection_rejects_expired_claim_and_exposes_live_claim_revision(
    tmp_path: Path,
) -> None:
    created = _create_heartbeat_candidate(tmp_path, suffix="projection-revision")
    claim = created["claim"]
    live = _run_dispatcher(
        tmp_path,
        "projection",
        "--claim-id",
        str(claim["claim_id"]),
        "--now",
        "2026-08-03T09:10:00+09:00",
        "--json",
    )
    assert live.returncode == 0, live.stderr or live.stdout
    projection = json.loads(live.stdout)
    assert projection["claim_revision"] == 0
    assert projection["pointer"]["current_agents"][0]["mutation_revision"] == 0

    path = _claim_path(tmp_path, created)
    expired = json.loads(path.read_text(encoding="utf-8"))
    expired["expires_at"] = "2026-08-03T08:59:59+09:00"
    expired["lease"]["expires_at"] = "2026-08-03T08:59:59+09:00"
    path.write_text(json.dumps(expired, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    refused = _run_dispatcher(
        tmp_path,
        "projection",
        "--claim-id",
        str(claim["claim_id"]),
        "--now",
        "2026-08-03T09:10:00+09:00",
        "--json",
        env_overrides={"AGENT_RUNTIME_CLAIM_GRACE_SECONDS": "0"},
    )
    assert refused.returncode == 1
    assert "expired" in refused.stderr.lower()


@pytest.mark.parametrize("deadline_case", ("expired", "indeterminate"))
def test_projection_without_now_uses_wall_clock_and_refuses_nonlive_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    deadline_case: str,
) -> None:
    created = _create_heartbeat_candidate(
        tmp_path,
        suffix=f"projection-default-{deadline_case}",
    )
    claim = created["claim"]
    path = _claim_path(tmp_path, created)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if deadline_case == "expired":
        payload["expires_at"] = "2026-08-03T08:59:59+09:00"
        payload["lease"]["expires_at"] = "2026-08-03T08:59:59+09:00"
    else:
        payload["lease"].pop("expires_at")
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    dispatcher = _load_dispatcher_module()
    observed: list[str | None] = []

    def fixed_wall_clock(value: str | None) -> datetime:
        observed.append(value)
        return datetime.fromisoformat("2026-08-03T09:10:00+09:00")

    monkeypatch.setattr(dispatcher, "_mutation_now", fixed_wall_clock)
    monkeypatch.setenv("AGENT_RUNTIME_CLAIM_GRACE_SECONDS", "0")

    rc = dispatcher.main(
        [
            "--root",
            str(tmp_path),
            "projection",
            "--claim-id",
            str(claim["claim_id"]),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert observed == [None]
    assert rc == 1
    assert deadline_case in captured.err.lower()
    assert captured.out == ""
    assert "Traceback" not in captured.err


def test_projection_without_now_emits_current_agent_mutation_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created = _create_heartbeat_candidate(
        tmp_path,
        suffix="projection-default-live-revision",
    )
    claim = created["claim"]
    dispatcher = _load_dispatcher_module()
    observed: list[str | None] = []

    def fixed_wall_clock(value: str | None) -> datetime:
        observed.append(value)
        return datetime.fromisoformat("2026-08-03T09:10:00+09:00")

    monkeypatch.setattr(dispatcher, "_mutation_now", fixed_wall_clock)

    rc = dispatcher.main(
        [
            "--root",
            str(tmp_path),
            "projection",
            "--claim-id",
            str(claim["claim_id"]),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert observed == [None]
    assert rc == 0, captured.err or captured.out
    projection = json.loads(captured.out)
    assert projection["claim_revision"] == 0
    assert projection["pointer"]["current_agents"][0]["mutation_revision"] == 0


def _canonical_overlay_heartbeat_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[object, dict[str, object], Path]:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    _write_canonical_task_identity(
        tmp_path,
        "TASK-AR-655-overlay-heartbeat",
        task_set_id="TASKSET-AR-V080-OPERABILITY-HARDENING",
    )
    dispatcher = _load_dispatcher_module()
    routed = dispatcher.role_routing.route_review_pass(
        tmp_path,
        task_id="TASK-AR-655-overlay-heartbeat",
        task_set_id="TASKSET-AR-V080-OPERABILITY-HARDENING",
        event="closeout",
        now="2026-08-03T10:00:00+09:00",
    )
    assert len(routed["created"]) == 1
    claim = dict(routed["created"][0])
    path = (
        tmp_path
        / "agents/runtime/task_claims"
        / f"{claim['claim_id']}.json"
    )
    claim.update(
        {
            "mutation_revision": 0,
            "expires_at": "2026-08-03T10:30:00+09:00",
            "lease": {
                "claimed_at": "2026-08-03T10:00:00+09:00",
                "heartbeat_at": "2026-08-03T10:00:00+09:00",
                "expires_at": "2026-08-03T10:30:00+09:00",
            },
        }
    )
    dispatcher.atomic_io.write_json_atomic(path, claim)
    return dispatcher, claim, path


def test_overlay_owner_heartbeat_renews_without_primary_pointer_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dispatcher, claim, path = _canonical_overlay_heartbeat_fixture(
        tmp_path,
        monkeypatch,
    )
    pointer = tmp_path / "agents/project/NEXT-SESSION-POINTER.yml"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text("sentinel: primary projection owner\n", encoding="utf-8")
    pointer_before = pointer.read_bytes()

    rc = dispatcher.main(
        [
            "--root",
            str(tmp_path),
            "heartbeat",
            "--claim-id",
            str(claim["claim_id"]),
            "--agent-instance-id",
            str(claim["agent_instance_id"]),
            "--callsite-id",
            str(claim["callsite_id"]),
            "--expected-revision",
            "0",
            "--now",
            "2026-08-03T10:10:00+09:00",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0, captured.err or captured.out
    response = json.loads(captured.out)
    assert response["receipt"]["committed"] is True
    assert response["receipt"]["claim_revision"] == 1
    assert response["projection"]["operation"] == "overlay-no-primary-pointer"
    assert response["projection"]["claim_id"] == claim["claim_id"]
    assert response["projection"]["claim_revision"] == 1
    assert "pointer" not in response["projection"]
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["mutation_revision"] == 1
    assert persisted["last_heartbeat"] == "2026-08-03T10:10:00+09:00"
    assert persisted["lease"]["heartbeat_at"] == persisted["last_heartbeat"]
    assert persisted["expires_at"] == "2026-08-03T10:40:00+09:00"
    assert persisted["lease"]["expires_at"] == persisted["expires_at"]
    assert pointer.read_bytes() == pointer_before


def test_overlay_scope_renew_and_standalone_projection_remain_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dispatcher, claim, path = _canonical_overlay_heartbeat_fixture(
        tmp_path,
        monkeypatch,
    )
    before = path.read_bytes()

    renew_rc = dispatcher.main(
        [
            "--root",
            str(tmp_path),
            "renew",
            "--claim-id",
            str(claim["claim_id"]),
            "--agent-instance-id",
            str(claim["agent_instance_id"]),
            "--callsite-id",
            str(claim["callsite_id"]),
            "--expected-revision",
            "0",
            "--expected-scope-digest",
            "overlay-scope-not-applicable",
            "--lease-minutes",
            "30",
            "--now",
            "2026-08-03T10:10:00+09:00",
            "--json",
        ]
    )
    renew_output = capsys.readouterr()
    projection_rc = dispatcher.main(
        [
            "--root",
            str(tmp_path),
            "projection",
            "--claim-id",
            str(claim["claim_id"]),
            "--now",
            "2026-08-03T10:10:00+09:00",
            "--json",
        ]
    )
    projection_output = capsys.readouterr()

    assert renew_rc == 1
    assert "overlay" in renew_output.err.lower()
    assert projection_rc == 1
    assert "overlay" in projection_output.err.lower()
    assert path.read_bytes() == before


# ===========================================================================
# TASK-AR-659 RED — a claim that no automated path can reach must still have a
# registered, owner-bound recovery command.
#
# Regression source: CLAIM-20260803-002651-task-ar-655-5f27 expired and stayed
# `status: claimed` with four paths closed at once — claim_reaper skips
# mode=orchestrator before testing liveness, heartbeat/renew reject a claim that
# predates mutation_revision/scope_binding, task and task-set exclusivity refuse
# a replacement claim, and no expire/terminalize/bootstrap subcommand exists.
# One stale claim blocked both its own task and the task needed to fix it.
# ===========================================================================

_OWNER = "ycpiglet <68498184+ycpiglet@users.noreply.github.com>"


def _recovery_actor_id(root: Path) -> str:
    instance_dir = root / "agents" / "runtime" / "instances"
    for path in sorted(instance_dir.glob("*.json"), key=lambda item: item.name):
        payload = json.loads(path.read_text(encoding="utf-8"))
        actor_id = str(payload.get("agent_instance_id") or "")
        if actor_id and path.stem == actor_id:
            return actor_id
    raise AssertionError(f"fixture has no exact registered actor in {instance_dir}")


def _legacy_claim(linked: Path, suffix: str) -> tuple[Path, dict]:
    """Create a spec-backed claim, then strip the mutation fields.

    Spec-backed on purpose: every real claim carries a unit_spec, and that is
    the scope authority adoption anchors to. A spec-less claim has no authority
    to diff against and is deliberately handled by a separate, stricter path
    (see test_adopt_refuses_a_spec_less_claim_without_a_replan).
    """
    task_id = f"TASK-AR-{suffix}"
    unit_rel = _write_routing_work(linked, task_id)
    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--worktree-path",
        ".",
        "--now",
        "2026-07-29T08:00:00+09:00",
        "--suffix",
        suffix.replace("-", "")[-8:],
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    claim = json.loads(path.read_text(encoding="utf-8"))
    claim.pop("mutation_revision", None)
    claim.pop("scope_binding", None)
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, claim


def _recovery_receipt_dir(root: Path) -> Path:
    return root / "agents" / "runtime" / "recovery_receipts"


def _pane_event_bytes(root: Path) -> bytes | None:
    path = root / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    return path.read_bytes() if path.exists() else None


def _recovery_candidate(
    linked: Path,
    operation: str,
    *,
    suffix: str,
) -> tuple[Path, dict, list[str]]:
    if operation == "adopt":
        path, claim = _legacy_claim(linked, suffix)
        args = [
            "--root",
            str(linked),
            "adopt",
            "--claim-id",
            str(claim["claim_id"]),
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            str(claim["agent_instance_id"]),
            "--reason",
            "receipt-first legacy adoption",
            "--now",
            "2026-07-29T08:30:00+09:00",
            "--json",
        ]
        return path, claim, args

    assert operation == "terminalize"
    created = _create_linked_claim(
        linked,
        suffix=suffix,
        extra_args=("--lease-minutes", "1"),
    )
    assert created.returncode == 0, created.stderr or created.stdout
    payload = json.loads(created.stdout)
    path = linked / payload["path"]
    claim = payload["claim"]
    args = [
        "--root",
        str(linked),
        "terminalize",
        "--claim-id",
        str(claim["claim_id"]),
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        str(claim["agent_instance_id"]),
        "--reason",
        "receipt-first expired claim terminalization",
        "--now",
        "2026-07-29T18:00:00+09:00",
        "--json",
    ]
    return path, claim, args


def _dispatcher_recovery_module(dispatcher, monkeypatch: pytest.MonkeyPatch):
    # The import is deliberately late: _load_dispatcher_module() installs the
    # repository scripts directory on sys.path. `raising=False` keeps this a
    # behavioral RED when dispatcher wiring is still absent instead of failing
    # at test setup merely because no module attribute exists yet.
    import recovery_receipt

    monkeypatch.setattr(dispatcher, "recovery_receipt", recovery_receipt, raising=False)
    return recovery_receipt


def _run_full_dispatcher_args(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_routing_off_env(),
    )


def _registered_instance_record(root: Path, agent_instance_id: str) -> dict:
    path = (
        root
        / "agents"
        / "runtime"
        / "instances"
        / f"{agent_instance_id}.json"
    )
    assert path.is_file(), f"missing fixture agent instance: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _recovery_command_case(
    linked: Path,
    operation: str,
    *,
    suffix: str,
) -> tuple[list[str], Path | None, dict]:
    if operation in {"adopt", "terminalize"}:
        path, claim, args = _recovery_candidate(
            linked,
            operation,
            suffix=suffix,
        )
        return args, path, claim

    assert operation == "activate-store"
    created = _create_linked_claim(linked, suffix=suffix)
    assert created.returncode == 0, created.stderr or created.stdout
    claim = json.loads(created.stdout)["claim"]
    _claim_store_outer_anchor(linked).unlink()
    return (
        [
            "--root",
            str(linked),
            "activate-store",
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            str(claim["agent_instance_id"]),
            "--reason",
            "attributed claim-store recovery",
            "--json",
        ],
        None,
        claim,
    )


@pytest.mark.parametrize("operation", ("adopt", "terminalize", "activate-store"))
def test_recovery_event_separates_owner_from_exact_registered_actor(
    tmp_path: Path,
    operation: str,
) -> None:
    """Owner approves recovery; a registered runtime instance executes it."""

    _primary, linked = _init_git_worktree(
        tmp_path,
        f"ar660-recovery-actor-{operation}",
    )
    args, path, claim = _recovery_command_case(
        linked,
        operation,
        suffix=f"660-actor-{operation}",
    )
    actor_id = str(claim["agent_instance_id"])
    actor_record = _registered_instance_record(linked, actor_id)
    assert args[args.index("--actor-instance-id") + 1] == actor_id

    result = _run_full_dispatcher_args(args)

    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    event_lines = _pane_event_bytes(linked)
    assert event_lines is not None
    event = json.loads(event_lines.decode("utf-8").splitlines()[-1])
    assert event["recovery_operation"] == operation
    assert event["owner_id"] == _OWNER
    assert event["actor"] == actor_id
    assert event["agent_instance_id"] == actor_id
    assert event["actor_role"] == actor_record["role"]
    assert event["callsite_id"] == actor_record["callsite_id"]
    assert event["display_name"] == actor_record["display_name"]

    receipt_ref = response["recovery_receipt"]["receipt_ref"]
    receipt = json.loads((linked / receipt_ref).read_text(encoding="utf-8"))
    assert receipt["owner_id"] == _OWNER
    if path is not None:
        persisted = json.loads(path.read_text(encoding="utf-8"))
        assert persisted["recovered_by"] == _OWNER

    gate = _run_attribution_gate(linked)
    assert gate.returncode == 0, gate.stdout + gate.stderr
    assert "attribution-gate: pass" in gate.stdout


@pytest.mark.parametrize("operation", ("adopt", "terminalize", "activate-store"))
@pytest.mark.parametrize("actor_case", ("missing", "unknown"))
def test_recovery_refuses_missing_or_unknown_actor_before_any_mutation(
    tmp_path: Path,
    operation: str,
    actor_case: str,
) -> None:
    _primary, linked = _init_git_worktree(
        tmp_path,
        f"ar660-recovery-{actor_case}-{operation}",
    )
    args, _path, _claim = _recovery_command_case(
        linked,
        operation,
        suffix=f"660-{actor_case}-{operation}",
    )
    actor_index = args.index("--actor-instance-id")
    if actor_case == "missing":
        del args[actor_index : actor_index + 2]
    else:
        args[actor_index + 1] = "unregistered-recovery-actor"

    checkout_before = _tree_entry_snapshot(linked)
    admin_root = _claim_store_outer_anchor(linked).parent
    admin_before = _tree_entry_snapshot(admin_root)
    events_before = _pane_event_bytes(linked)
    receipts = _recovery_receipt_dir(linked)
    receipts_before = _tree_entry_snapshot(receipts)

    result = _run_full_dispatcher_args(args)

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "actor-instance-id" in combined or "actor instance" in combined
    if actor_case == "unknown":
        assert "registered" in combined and "exact" in combined
    assert _tree_entry_snapshot(linked) == checkout_before
    assert _tree_entry_snapshot(admin_root) == admin_before
    assert _pane_event_bytes(linked) == events_before
    assert _tree_entry_snapshot(receipts) == receipts_before


@pytest.mark.parametrize("operation", ("adopt", "terminalize", "activate-store"))
@pytest.mark.parametrize(
    "registry_race",
    ("unlink", "atomic-replace", "field-change"),
)
def test_recovery_revalidates_actor_registry_inside_the_commit_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
    registry_race: str,
) -> None:
    """An actor that disappears or changes after lookup has no authority.

    The Owner approval and the first registry read are not a capability token.
    Recovery must prove that the exact canonical actor record still exists at
    the mutation boundary, before either the prepared receipt or its subject is
    published.  This pins the TOCTOU seam for all three recovery commands.
    """

    _primary, linked = _init_git_worktree(
        tmp_path,
        f"ar660-actor-race-{operation}-{registry_race}",
    )
    args, claim_path, claim = _recovery_command_case(
        linked,
        operation,
        suffix=f"660-race-{operation}-{registry_race}",
    )
    dispatcher = _load_dispatcher_module()
    real_resolve = dispatcher._registered_recovery_actor
    actor_id = str(claim["agent_instance_id"])
    actor_path = (
        linked
        / "agents"
        / "runtime"
        / "instances"
        / f"{actor_id}.json"
    )
    assert actor_path.is_file()
    resolutions = {"count": 0}

    def race_after_first_resolution(root: Path, requested_id: object):
        resolutions["count"] += 1
        actor = real_resolve(root, requested_id)
        if resolutions["count"] != 1:
            return actor
        if registry_race == "unlink":
            actor_path.unlink()
        else:
            changed = json.loads(actor_path.read_text(encoding="utf-8"))
            changed["callsite_id"] = f"{changed['callsite_id']}:changed"
            encoded = json.dumps(changed, ensure_ascii=False, indent=2) + "\n"
            if registry_race == "atomic-replace":
                replacement = actor_path.with_suffix(".replacement")
                replacement.write_text(encoded, encoding="utf-8")
                os.replace(replacement, actor_path)
            else:
                actor_path.write_text(encoded, encoding="utf-8")
        return actor

    monkeypatch.setattr(
        dispatcher,
        "_registered_recovery_actor",
        race_after_first_resolution,
    )
    claim_before = claim_path.read_bytes() if claim_path is not None else None
    admin_root = _claim_store_outer_anchor(linked).parent
    admin_before = _tree_entry_snapshot(admin_root)
    events_before = _pane_event_bytes(linked)
    receipt_dir = _recovery_receipt_dir(linked)
    receipts_before = _tree_entry_snapshot(receipt_dir)

    rc = dispatcher.main(args)
    output = capsys.readouterr()

    assert rc == 1, output.out + output.err
    assert resolutions["count"] >= 2, (
        "recovery trusted a stale actor snapshot instead of revalidating it "
        "at the commit boundary"
    )
    assert "actor instance" in (output.out + output.err).lower()
    if claim_path is not None:
        assert claim_path.read_bytes() == claim_before
    assert _tree_entry_snapshot(admin_root) == admin_before
    assert _pane_event_bytes(linked) == events_before
    assert _tree_entry_snapshot(receipt_dir) == receipts_before


@pytest.mark.parametrize("operation", ("adopt", "terminalize", "activate-store"))
@pytest.mark.parametrize(
    "registry_race",
    ("disappearance", "replacement", "field-drift"),
)
def test_recovery_binds_actor_authority_to_prepared_receipt_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
    registry_race: str,
) -> None:
    """The receipt publisher, not its caller, owns the final actor proof."""

    _primary, linked = _init_git_worktree(
        tmp_path,
        f"ar660-publish-race-{operation}-{registry_race}",
    )
    args, _claim_path, claim = _recovery_command_case(
        linked,
        operation,
        suffix=f"660-publish-{operation}-{registry_race}",
    )
    dispatcher = _load_dispatcher_module()
    recovery_receipt = _dispatcher_recovery_module(dispatcher, monkeypatch)
    real_prepare = recovery_receipt.prepare_recovery_receipt
    actor_id = str(claim["agent_instance_id"])
    actor_path = (
        linked
        / "agents"
        / "runtime"
        / "instances"
        / f"{actor_id}.json"
    )
    actor_bytes = actor_path.read_bytes()
    actor_inode = actor_path.stat().st_ino
    prepare_calls = 0
    publisher_precommit_seen = False

    def race_after_caller_revalidation(**kwargs):
        nonlocal prepare_calls, publisher_precommit_seen
        prepare_calls += 1
        publisher_precommit_seen = callable(kwargs.get("precommit"))
        if registry_race == "disappearance":
            actor_path.unlink()
        elif registry_race == "replacement":
            replacement = actor_path.with_name(f".{actor_path.name}.replacement")
            replacement.write_bytes(actor_bytes)
            os.replace(replacement, actor_path)
            assert actor_path.stat().st_ino != actor_inode
        else:
            changed = json.loads(actor_bytes.decode("utf-8"))
            changed["callsite_id"] = f"{changed['callsite_id']}:drifted"
            actor_path.write_text(
                json.dumps(changed, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return real_prepare(**kwargs)

    monkeypatch.setattr(
        recovery_receipt,
        "prepare_recovery_receipt",
        race_after_caller_revalidation,
    )
    claims_root = linked / "agents" / "runtime" / "task_claims"
    claims_before = _tree_entry_snapshot(claims_root)
    admin_root = _claim_store_outer_anchor(linked).parent
    admin_before = _tree_entry_snapshot(admin_root)
    events_before = _pane_event_bytes(linked)
    receipt_dir = _recovery_receipt_dir(linked)
    receipts_before = _tree_entry_snapshot(receipt_dir)

    rc = dispatcher.main(args)
    output = capsys.readouterr()

    assert rc == 1, output.out + output.err
    assert prepare_calls == 1
    assert publisher_precommit_seen, (
        "dispatcher did not bind actor authority to the receipt publisher"
    )
    assert "actor instance" in (output.out + output.err).lower()
    assert _tree_entry_snapshot(claims_root) == claims_before
    assert _tree_entry_snapshot(admin_root) == admin_before
    assert _pane_event_bytes(linked) == events_before
    assert _tree_entry_snapshot(receipt_dir) == receipts_before


def test_recovery_refuses_instance_filename_payload_identity_mismatch(
    tmp_path: Path,
) -> None:
    """A plausible filename must not launder a different canonical actor."""

    _primary, linked = _init_git_worktree(tmp_path, "ar660-recovery-actor-mismatch")
    args, path, claim = _recovery_command_case(
        linked,
        "terminalize",
        suffix="660-actor-mismatch",
    )
    assert path is not None
    source = _registered_instance_record(linked, str(claim["agent_instance_id"]))
    requested_id = "fake-recovery-actor"
    mismatch = (
        linked
        / "agents"
        / "runtime"
        / "instances"
        / f"{requested_id}.json"
    )
    mismatch.write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    args[args.index("--actor-instance-id") + 1] = requested_id
    before = path.read_bytes()
    events_before = _pane_event_bytes(linked)

    result = _run_full_dispatcher_args(args)

    assert result.returncode != 0
    assert "exact" in (result.stdout + result.stderr).lower()
    assert path.read_bytes() == before
    assert _pane_event_bytes(linked) == events_before
    assert not _recovery_receipt_dir(linked).exists()


@pytest.mark.parametrize("operation", ("adopt", "terminalize"))
def test_recovery_prepares_before_strict_claim_write_and_events_after_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
) -> None:
    """The pane event is derived from a committed receipt, never its authority."""
    _primary, linked = _init_git_worktree(tmp_path, f"ar660-wal-order-{operation}")
    path, _claim, args = _recovery_candidate(
        linked,
        operation,
        suffix=f"660-wal-{operation}",
    )
    dispatcher = _load_dispatcher_module()
    recovery_receipt = _dispatcher_recovery_module(dispatcher, monkeypatch)
    receipt_dir = _recovery_receipt_dir(linked)
    real_write = dispatcher.atomic_io.write_json_atomic
    real_append = dispatcher.append_event
    observed: list[str] = []

    def _strict_subject_write(candidate, payload, *write_args, **write_kwargs):
        if Path(candidate).resolve() == path.resolve():
            prepared = list(receipt_dir.glob("*.prepared.json"))
            assert len(prepared) == 1, "claim write ran before the prepared WAL record"
            assert not list(receipt_dir.glob("*.committed.json"))
            assert not list(receipt_dir.glob("*.indeterminate.json"))
            assert write_kwargs.get("fsync_policy") == "strict"
            observed.append("subject")
        return real_write(candidate, payload, *write_args, **write_kwargs)

    def _event_after_commit(event_root: Path, event: dict):
        committed_paths = list(receipt_dir.glob("*.committed.json"))
        assert len(committed_paths) == 1, "pane event ran before committed receipt"
        committed = recovery_receipt.validate_receipt(committed_paths[0])
        assert event["recovery_operation"] == operation
        assert event["receipt_id"] == committed["receipt_id"]
        assert str(event["prepared_receipt_ref"]).endswith(
            f"{committed['receipt_id']}.prepared.json"
        )
        assert str(event["outcome_receipt_ref"]).endswith(committed_paths[0].name)
        observed.append("event")
        return real_append(event_root, event)

    monkeypatch.setattr(dispatcher.atomic_io, "write_json_atomic", _strict_subject_write)
    monkeypatch.setattr(dispatcher, "append_event", _event_after_commit)

    rc = dispatcher.main(args)
    captured = capsys.readouterr()

    assert rc == 0, captured.err or captured.out
    assert observed == ["subject", "event"]
    response = json.loads(captured.out)
    assert response["recovery_receipt"]["status"] == "committed"
    assert response["recovery_receipt"]["retry_safe"] is False
    assert len(list(receipt_dir.glob("*.prepared.json"))) == 1
    assert len(list(receipt_dir.glob("*.committed.json"))) == 1


@pytest.mark.parametrize("operation", ("adopt", "terminalize"))
def test_recovery_prepare_failure_preserves_subject_and_event_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, f"ar660-wal-prepare-{operation}")
    path, _claim, args = _recovery_candidate(
        linked,
        operation,
        suffix=f"660-prep-{operation}",
    )
    subject_before = path.read_bytes()
    events_before = _pane_event_bytes(linked)
    dispatcher = _load_dispatcher_module()
    recovery_receipt = _dispatcher_recovery_module(dispatcher, monkeypatch)

    def _fail_prepare(**_kwargs):
        raise OSError("prepared receipt sink is unavailable")

    monkeypatch.setattr(recovery_receipt, "prepare_recovery_receipt", _fail_prepare)

    rc = dispatcher.main(args)
    captured = capsys.readouterr()

    assert rc != 0
    assert "Traceback" not in captured.out + captured.err
    assert path.read_bytes() == subject_before
    assert _pane_event_bytes(linked) == events_before
    receipt_dir = _recovery_receipt_dir(linked)
    assert not receipt_dir.exists() or list(receipt_dir.iterdir()) == []


def test_terminalize_post_commit_atomic_uncertainty_is_indeterminate_nonretry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "ar660-wal-indeterminate")
    path, _claim, args = _recovery_candidate(
        linked,
        "terminalize",
        suffix="660-indet",
    )
    events_before = _pane_event_bytes(linked)
    dispatcher = _load_dispatcher_module()
    _dispatcher_recovery_module(dispatcher, monkeypatch)
    real_write = dispatcher.atomic_io.write_json_atomic

    def _commit_then_lose_durability(candidate, payload, *write_args, **write_kwargs):
        if Path(candidate).resolve() != path.resolve():
            return real_write(candidate, payload, *write_args, **write_kwargs)
        assert write_kwargs.get("fsync_policy") == "strict"
        real_write(
            candidate,
            payload,
            *write_args,
            **{**write_kwargs, "fsync_policy": "best_effort"},
        )
        raise dispatcher.atomic_io.AtomicWriteError(
            "parent fsync failed after subject rename",
            stage="parent-fsync",
            committed=True,
            retry_safe=False,
        )

    monkeypatch.setattr(
        dispatcher.atomic_io,
        "write_json_atomic",
        _commit_then_lose_durability,
    )

    rc = dispatcher.main(args)
    captured = capsys.readouterr()

    assert rc != 0
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "expired"
    assert _pane_event_bytes(linked) == events_before
    receipt_dir = _recovery_receipt_dir(linked)
    assert len(list(receipt_dir.glob("*.prepared.json"))) == 1
    assert not list(receipt_dir.glob("*.committed.json"))
    indeterminate_paths = list(receipt_dir.glob("*.indeterminate.json"))
    assert len(indeterminate_paths) == 1
    indeterminate = json.loads(indeterminate_paths[0].read_text(encoding="utf-8"))
    assert indeterminate["retry_safe"] is False
    response = json.loads(captured.out)
    assert response["status"] == "indeterminate"
    assert response["retry_safe"] is False


@pytest.mark.parametrize(
    ("operation", "receipt_committed"),
    (
        ("adopt", True),
        ("terminalize", False),
        ("activate-store", None),
    ),
)
def test_recovery_receipt_terminal_publication_uncertainty_is_never_generic_refusal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
    receipt_committed: bool | None,
) -> None:
    """A crossed subject commit point must survive the broad RuntimeError seam."""

    _primary, linked = _init_git_worktree(
        tmp_path,
        f"ar660-receipt-error-{operation}",
    )
    dispatcher = _load_dispatcher_module()
    recovery_receipt = _dispatcher_recovery_module(dispatcher, monkeypatch)
    stage = f"{operation}-terminal-receipt-publication"

    if operation in {"adopt", "terminalize"}:
        path, _claim, args = _recovery_candidate(
            linked,
            operation,
            suffix=f"660-receipt-error-{operation}",
        )

        def _commit_subject_then_lose_receipt(**kwargs):
            kwargs["mutate_subject"]()
            raise recovery_receipt.RecoveryReceiptError(
                "terminal receipt durability is uncertain",
                stage=stage,
                committed=True,
                retry_safe=False,
                receipt_committed=receipt_committed,
            )

        monkeypatch.setattr(
            recovery_receipt,
            "execute_recovery",
            _commit_subject_then_lose_receipt,
        )
    else:
        created = _create_linked_claim(
            linked,
            suffix="660-receipt-error-activate",
        )
        assert created.returncode == 0, created.stderr or created.stdout
        inner = linked / "agents/runtime/task_claims/.claim-store"
        outer = _claim_store_outer_anchor(linked)
        inner.unlink()
        outer.unlink()
        path = None
        args = [
            "--root",
            str(linked),
            "activate-store",
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            _recovery_actor_id(linked),
            "--reason",
            "terminal activation receipt durability is uncertain",
            "--json",
        ]

        def _lose_activation_receipt(**_kwargs):
            raise recovery_receipt.RecoveryReceiptError(
                "terminal receipt durability is uncertain",
                stage=stage,
                committed=True,
                retry_safe=False,
                receipt_committed=receipt_committed,
            )

        monkeypatch.setattr(
            recovery_receipt,
            "commit_prepared_recovery",
            _lose_activation_receipt,
        )

    rc = dispatcher.main(args)
    captured = capsys.readouterr()

    assert rc != 0
    response = json.loads(captured.out)
    assert response["status"] == "indeterminate"
    assert response["retry_safe"] is False
    assert response["stage"] == stage
    assert response["receipt_committed"] is receipt_committed
    assert response["recovery_receipt"]["stage"] == stage
    assert (
        response["recovery_receipt"]["receipt_committed"]
        is receipt_committed
    )
    assert "MUST NOT be retried" in captured.err
    assert "refused" not in captured.err.lower()
    if path is not None:
        persisted = json.loads(path.read_text(encoding="utf-8"))
        expected_status = "expired" if operation == "terminalize" else "claimed"
        assert persisted["status"] == expected_status


@pytest.mark.parametrize("operation", ("adopt", "terminalize"))
def test_committed_recovery_digest_never_rereads_subject_after_store_unlock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
) -> None:
    """Report the receipt-bound image, never a later uncooperative mutation."""

    _primary, linked = _init_git_worktree(
        tmp_path,
        f"ar660-after-digest-{operation}",
    )
    path, _claim, args = _recovery_candidate(
        linked,
        operation,
        suffix=f"660-after-digest-{operation}",
    )
    dispatcher = _load_dispatcher_module()
    _dispatcher_recovery_module(dispatcher, monkeypatch)
    real_read_bytes = Path.read_bytes
    intruder_bytes = b'{"post_lock_intruder":true}\n'
    subject_reads = {"count": 0}

    def _show_followup_mutation_on_fifth_subject_read(candidate: Path) -> bytes:
        if candidate.resolve() == path.resolve():
            subject_reads["count"] += 1
            # Four reads belong to the locked transaction: caller before-image,
            # receipt raw CAS, caller raw CAS, and receipt after-image.  The
            # historical fifth read happened after store authority was released.
            if subject_reads["count"] > 4:
                return intruder_bytes
        return real_read_bytes(candidate)

    monkeypatch.setattr(
        Path,
        "read_bytes",
        _show_followup_mutation_on_fifth_subject_read,
    )

    rc = dispatcher.main(args)
    captured = capsys.readouterr()

    assert rc == 0, captured.err or captured.out
    response = json.loads(captured.out)
    expected_after = (
        json.dumps(response["claim"], ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    assert response["after_sha256"] == hashlib.sha256(expected_after).hexdigest()
    assert response["after_sha256"] != hashlib.sha256(intruder_bytes).hexdigest()
    assert subject_reads["count"] == 4
    assert real_read_bytes(path) == expected_after


def test_red_legacy_claim_is_adoptable_by_owner_bound_command(tmp_path: Path) -> None:
    """A pre-mutation-field claim must be adoptable instead of unrecoverable."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-adopt")
    path, claim = _legacy_claim(linked, "659-adopt")
    assert "mutation_revision" not in claim
    assert "scope_binding" not in claim

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "legacy claim predates the mutation fields",
        "--now",
        "2026-07-29T08:30:00+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    adopted = json.loads(path.read_text(encoding="utf-8"))
    assert adopted["mutation_revision"] == 0
    assert isinstance(adopted["scope_binding"], dict)
    assert adopted["status"] == "claimed"          # adoption is not a lifecycle change
    assert adopted["recovered_by"] == _OWNER


def test_red_adopt_refuses_a_caller_without_owner_identity(tmp_path: Path) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "ar659-adopt-anon")
    path, claim = _legacy_claim(linked, "659-adopt-anon")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        "   ",
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "no identity",
        "--now",
        "2026-07-29T08:30:00+09:00",
        "--json",
    )

    assert result.returncode != 0
    assert "Traceback" not in (result.stdout + result.stderr)
    assert path.read_bytes() == before
    # Must be refused for a *stated* reason, not merely because argparse does not
    # know the subcommand — otherwise this passes vacuously pre-implementation.
    combined = (result.stdout + result.stderr).lower()
    assert "owner" in combined
    assert "invalid choice" not in combined


def test_red_expired_claim_is_terminalizable_by_owner_bound_command(
    tmp_path: Path,
) -> None:
    """An expired claim must reach a terminal state without delete/release/complete."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-terminalize")
    result = _create_linked_claim(
        linked, suffix="659-term", extra_args=("--lease-minutes", "1")
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    claim_id = payload["claim"]["claim_id"]

    result = _run_dispatcher(
        linked,
        "terminalize",
        "--claim-id",
        claim_id,
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "lease expired with no reachable command",
        "--now",
        "2026-07-29T18:00:00+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert path.is_file()                          # not deleted
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["status"] == "expired"            # not released, not completed
    assert after["recovered_from_status"] == "claimed"
    assert after["recovered_by"] == _OWNER
    assert after["recovery_reason"]


def test_red_terminalize_refuses_a_live_claim(tmp_path: Path) -> None:
    """A live claim must never be terminalizable, whatever the owner asks."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-live")
    result = _create_linked_claim(
        linked, suffix="659-live", extra_args=("--lease-minutes", "120")
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "terminalize",
        "--claim-id",
        payload["claim"]["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "attempting to kill a live claim",
        "--now",
        "2026-07-29T08:30:00+09:00",
        "--json",
    )

    assert result.returncode != 0
    assert "Traceback" not in (result.stdout + result.stderr)
    assert path.read_bytes() == before
    combined = (result.stdout + result.stderr).lower()
    assert "live" in combined or "not expired" in combined
    assert "invalid choice" not in combined


def test_red_terminalize_reaches_an_orchestrator_claim_the_reaper_skips(
    tmp_path: Path,
) -> None:
    """Mode must not decide reachability: the reaper skips orchestrator claims."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-orch")
    result = _create_linked_claim(
        linked,
        suffix="659-orch",
        extra_args=("--lease-minutes", "1", "--mode", "orchestrator"),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]

    result = _run_dispatcher(
        linked,
        "terminalize",
        "--claim-id",
        payload["claim"]["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "orchestrator claim the reaper will never reach",
        "--now",
        "2026-07-29T18:00:00+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "expired"


def test_red_new_checkout_can_activate_its_claim_store(tmp_path: Path) -> None:
    """A fresh worktree must have a registered claim-store activation command.

    The outer marker lives in the per-worktree git admin dir, so every new
    worktree starts `migration-required`. The only caller of
    adopt_legacy_store() is sync.py, which needs a consumer agent_runtime.yml
    that the runtime repository itself does not have.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar659-activate")
    result = _create_linked_claim(linked, suffix="659-activate")
    assert result.returncode == 0, result.stderr or result.stdout

    outer = _claim_store_outer_anchor(linked)
    assert outer.is_file()
    outer.unlink()                                  # reproduce a fresh checkout

    # Unattributed activation must be refused: this lifts the whole store out
    # of the fail-closed migration-required state.
    anon = _run_dispatcher(
        linked,
        "activate-store",
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--json",
    )
    assert anon.returncode != 0
    assert not outer.is_file()

    result = _run_dispatcher(
        linked,
        "activate-store",
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "fresh checkout needs its claim store",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert outer.is_file()
    assert json.loads(result.stdout)["activated_by"] == _OWNER


def test_red_recovery_refuses_when_claim_store_authority_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The store lock proves exclusion, not that the store is the same store.

    Every other mutating path pairs store_lock with verify_snapshot (create
    2083/2203, projection 2894, release 3128/3223) and claim_reaper does the
    same. Recovery commands run when the system is already degraded, so they
    are the last place that may skip the authority check.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar659-authority")
    result = _create_linked_claim(
        linked, suffix="659-authority", extra_args=("--lease-minutes", "1")
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    before = path.read_bytes()

    dispatcher = _load_dispatcher_module()
    real_verify = dispatcher.claim_store.verify_snapshot
    calls = {"n": 0}

    def _verify_then_fail(*probe_args, **probe_kwargs):
        # Let the read path verify normally, then fail the pre-write check.
        # This isolates the read->write window rather than the read itself.
        calls["n"] += 1
        if calls["n"] == 1:
            return real_verify(*probe_args, **probe_kwargs)
        return False

    monkeypatch.setattr(dispatcher.claim_store, "verify_snapshot", _verify_then_fail)

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "terminalize",
            "--claim-id",
            payload["claim"]["claim_id"],
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            _recovery_actor_id(linked),
            "--reason",
            "authority changed mid-flight",
            "--now",
            "2026-07-29T18:00:00+09:00",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 1
    assert "authority changed" in (captured.out + captured.err)
    assert "Traceback" not in (captured.out + captured.err)
    assert path.read_bytes() == before


# --- TASK-AR-659 W4b P0: a caller-supplied clock must not defeat liveness ---


def test_red_terminalize_cannot_use_a_future_now_to_kill_a_live_claim(
    tmp_path: Path,
) -> None:
    """`--now` is a determinism seam, not an authority seam.

    Judging liveness against a caller-supplied clock makes "a live claim is
    never terminalizable" false: any caller can pass a future timestamp and
    end a healthy claim, then create their own claim on the freed task.
    claim_reaper --apply --now 2099 refuses the same claim, so this would be
    the only path in the runtime that can end a live one.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar659-future-now")
    # The claim must be live against the WALL clock, so this trailing --now
    # overrides the fixture's pinned past timestamp. The property under test is
    # about real time by nature and cannot be pinned to a fixed instant.
    wall_now = datetime.now().astimezone().isoformat(timespec="seconds")
    result = _create_linked_claim(
        linked,
        suffix="659-future",
        extra_args=("--lease-minutes", "600", "--now", wall_now),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "terminalize",
        "--claim-id",
        payload["claim"]["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "future clock must not grant authority",
        "--now",
        "2099-01-01T00:00:00+09:00",
        "--json",
    )

    assert result.returncode != 0, (
        "a future --now terminalized a live claim: "
        + (result.stdout + result.stderr)
    )
    assert path.read_bytes() == before
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "claimed"


def test_red_adopt_cannot_use_a_future_now_to_bypass_liveness(tmp_path: Path) -> None:
    """Adoption must not become reachable on a claim a future clock 'expires'."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-adopt-future")
    path, claim = _legacy_claim(linked, "659-adopt-future")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "adoption under a future clock",
        "--now",
        "2099-01-01T00:00:00+09:00",
        "--json",
    )

    if result.returncode == 0:
        adopted = json.loads(path.read_text(encoding="utf-8"))
        assert adopted["recovered_at"] < "2099", (
            "a future --now was recorded as the recovery timestamp: "
            f"{adopted['recovered_at']}"
        )
    else:
        assert path.read_bytes() == before


def test_deadline_missing_claim_needs_explicit_opt_in_to_terminalize(
    tmp_path: Path,
) -> None:
    """A claim with no deadline needs an exit, but ending it is a judgement.

    It must not ride the expired path silently, and it must not stay
    exit-less the way CLAIM-20260803-002651-task-ar-655-5f27 did.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar659-nodeadline")
    result = _create_linked_claim(linked, suffix="659-nodeadline")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    claim_id = payload["claim"]["claim_id"]

    claim = json.loads(path.read_text(encoding="utf-8"))
    claim.pop("expires_at", None)
    claim.pop("lease", None)
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    args = (
        "terminalize",
        "--claim-id",
        claim_id,
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "claim carries no deadline at all",
    )

    refused = _run_dispatcher(linked, *args, "--json")
    assert refused.returncode != 0
    assert "allow-indeterminate-lease" in (refused.stdout + refused.stderr)
    assert path.read_bytes() == before

    allowed = _run_dispatcher(linked, *args, "--allow-indeterminate-lease", "--json")
    assert allowed.returncode == 0, allowed.stderr or allowed.stdout
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["status"] == "expired"
    assert after["recovered_by"] == _OWNER


def test_adopt_anchors_scope_binding_to_the_unit_spec_not_the_claim(
    tmp_path: Path,
) -> None:
    """Deleting scope_binding must not let a caller choose their own scope.

    renew derives the binding from _current_scope_values (unit-spec anchored).
    If adopt derived it from the claim's own mutable target_files, a caller
    could drop the binding, widen target_files, and have adopt mint a valid
    binding over the widened scope.
    """
    task_id = "TASK-AR-659anchor"
    _primary, linked = _init_git_worktree(tmp_path, "ar659-scope-anchor")
    unit_rel = _write_routing_work(linked, task_id)
    # The unit spec declares exactly one target file; that is the honest scope.
    spec_files = ["scripts/routing_target.py", "scripts/routing_second.py"]

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--worktree-path",
        ".",
        "--now",
        "2026-07-29T08:00:00+09:00",
        "--suffix",
        "anchor",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    claim = json.loads(path.read_text(encoding="utf-8"))
    assert claim["target_files"] == spec_files

    # Tamper: drop the binding and widen scope inside the claim file itself.
    claim.pop("scope_binding", None)
    claim["target_files"] = [
        "src/agent_runtime/claim_store.py",
        "scripts/claim_reaper.py",
    ]
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")

    before = path.read_bytes()
    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "attempting to mint a binding over chosen scope",
        "--json",
    )

    # Widened scope must be refused outright, not quietly re-anchored: adopt
    # holds the same bar as renew, which demands an accepted T2/T3 replan on
    # any scope change.
    assert result.returncode != 0, (
        "adopt accepted caller-widened scope without a replan: " + result.stdout
    )
    assert "replan" in (result.stdout + result.stderr).lower()
    assert path.read_bytes() == before


def test_adopt_leaves_the_claim_renewable(tmp_path: Path) -> None:
    """Adoption exists so heartbeat and renew can reach the claim again.

    _persisted_scope_binding recomputes the expected binding from the claim's
    OWN target_files/stop_condition, so writing a spec-anchored binding without
    also writing those fields leaves the two permanently irreconcilable and
    makes renew refuse forever.
    """
    task_id = "TASK-AR-659renewable"
    _primary, linked = _init_git_worktree(tmp_path, "ar659-renewable")
    unit_rel = _write_routing_work(linked, task_id)

    result = _run_dispatcher(
        linked,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--worktree-path",
        ".",
        "--now",
        "2026-07-29T08:00:00+09:00",
        "--lease-minutes",
        "600",
        "--suffix",
        "renewable",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    claim = json.loads(path.read_text(encoding="utf-8"))

    # Reproduce a legacy claim: drop the mutation fields entirely.
    claim.pop("mutation_revision", None)
    claim.pop("scope_binding", None)
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")

    # The spec must actually drift, otherwise spec-anchored and claim-anchored
    # scope are identical and the regression cannot reproduce. Spec drift after
    # claim creation is the normal case for a legacy claim.
    unit_path = linked / unit_rel
    unit_path.write_text(
        unit_path.read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py",
            "  - scripts/routing_target.py\n  - scripts/routing_extra.py",
        ),
        encoding="utf-8",
    )
    replan_rel = "reviews/REVIEW-adopt-renewable-replan.md"
    replan_path = linked / replan_rel
    replan_path.parent.mkdir(parents=True, exist_ok=True)
    replan_path.write_text(
        "\n".join(
            [
                "---",
                "id: REVIEW-adopt-renewable-replan",
                f"task_id: {task_id}",
                f"unit_id: UNIT-{task_id}-001",
                "review_kind: scope-amendment",
                "tier: T3",
                "status: accepted",
                "signal: pass",
                "---",
                "",
            ]
        ),
        encoding="utf-8",
    )
    # The replan must be the taskset's registered design_record with live
    # anchors, exactly as renew demands.
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "plan_assumption_gate.py"),
            "--root",
            str(linked),
            "record",
            "--taskset",
            str(claim["task_set_id"]),
            "--design-record",
            replan_rel,
            "--anchor",
            unit_rel,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "legacy claim predates the mutation fields",
        "--replan-ref",
        replan_rel,
        "--now",
        "2026-07-29T09:00:00+09:00",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    adopted = json.loads(path.read_text(encoding="utf-8"))
    # The regression: binding written from the spec while target_files kept the
    # old value leaves the two permanently irreconcilable.
    assert "scripts/routing_extra.py" in adopted["target_files"]

    # The whole point: renew must now work against the adopted claim.
    result = _run_dispatcher(
        linked,
        "renew",
        "--claim-id",
        adopted["claim_id"],
        "--agent-instance-id",
        adopted["agent_instance_id"],
        "--callsite-id",
        adopted["callsite_id"],
        "--expected-revision",
        str(adopted["mutation_revision"]),
        "--expected-scope-digest",
        adopted["scope_binding"]["digest"],
        "--lease-minutes",
        "60",
        "--now",
        "2026-07-29T10:00:00+09:00",
        "--json",
    )
    assert result.returncode == 0, (
        "adopt left the claim un-renewable: " + (result.stderr or result.stdout)
    )


def test_adopt_refuses_a_present_but_invalid_mutation_revision(tmp_path: Path) -> None:
    """`type(x) is int` treats "7" as absent; resetting it to 0 loses CAS history."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-bad-rev")
    result = _create_linked_claim(linked, suffix="659-badrev")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    claim = json.loads(path.read_text(encoding="utf-8"))
    claim["mutation_revision"] = "7"
    claim.pop("scope_binding", None)
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "string revision must not be silently reset",
        "--json",
    )

    assert result.returncode != 0
    assert "mutation_revision" in (result.stdout + result.stderr)
    assert path.read_bytes() == before


def test_owner_identity_is_length_bounded(tmp_path: Path) -> None:
    """Every neighbouring provenance field is capped; this one must be too."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-owner-len")
    path, claim = _legacy_claim(linked, "659-ownerlen")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        "x" * 5050,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "unbounded owner identity",
        "--json",
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    # Pin the reason, not just the exit code: otherwise a future refusal for an
    # unrelated cause would keep this green while the cap silently disappears.
    assert "owner identity exceeds" in (result.stdout + result.stderr)


def test_recovery_reason_is_length_bounded(tmp_path: Path) -> None:
    """Owner id and reason land in the same record; capping one is half a fix."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-reason-len")
    path, claim = _legacy_claim(linked, "659-reasonlen")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "y" * 20000,
        "--json",
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "recovery reason exceeds" in (result.stdout + result.stderr)


def test_markerless_activation_receipt_binds_exact_two_subject_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both marker images belong to one prepared WAL record before either exists."""
    _primary, linked = _init_git_worktree(tmp_path, "ar660-activation-two-subject")
    result = _create_linked_claim(linked, suffix="660-act-two")
    assert result.returncode == 0, result.stderr or result.stdout
    inner = linked / "agents" / "runtime" / "task_claims" / ".claim-store"
    outer = _claim_store_outer_anchor(linked)
    assert inner.is_file() and outer.is_file()
    inner.unlink()
    outer.unlink()

    dispatcher = _load_dispatcher_module()
    recovery_receipt = _dispatcher_recovery_module(dispatcher, monkeypatch)
    real_prepare = recovery_receipt.prepare_recovery_receipt
    real_adopt = dispatcher.claim_store.adopt_legacy_store
    captured: dict[str, object] = {}

    def _capture_prepare(**kwargs):
        assert not inner.exists() and not outer.exists()
        captured["prepare"] = kwargs
        prepared_path = real_prepare(**kwargs)
        captured["prepared_path"] = prepared_path
        return prepared_path

    def _observe_precommit(root, *adopt_args, **adopt_kwargs):
        precommit = adopt_kwargs.get("precommit")
        captured["precommit"] = precommit
        if precommit is None:
            return real_adopt(root, *adopt_args, **adopt_kwargs)

        def _wrapped(plan):
            captured["plan"] = plan
            assert not inner.exists() and not outer.exists()
            result = precommit(plan)
            prepared_path = captured.get("prepared_path")
            assert isinstance(prepared_path, Path) and prepared_path.is_file()
            assert not inner.exists() and not outer.exists()
            return result

        adopt_kwargs["precommit"] = _wrapped
        return real_adopt(root, *adopt_args, **adopt_kwargs)

    monkeypatch.setattr(recovery_receipt, "prepare_recovery_receipt", _capture_prepare)
    monkeypatch.setattr(
        dispatcher.claim_store,
        "adopt_legacy_store",
        _observe_precommit,
    )

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "activate-store",
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            _recovery_actor_id(linked),
            "--reason",
            "bind both marker publications to one recovery receipt",
            "--json",
        ]
    )
    output = capsys.readouterr()

    assert rc == 0, output.err or output.out
    assert callable(captured.get("precommit"))
    plan = captured["plan"]
    assert plan.operation == "legacy-store-adoption"
    assert [subject.path for subject in plan.subjects] == [inner, outer]
    assert all(subject.before_bytes is None for subject in plan.subjects)
    assert len({subject.after_bytes for subject in plan.subjects}) == 1

    def _logical_ref(path: Path) -> str:
        if path.resolve() == inner.resolve():
            return "agents/runtime/task_claims/.claim-store"
        if path.resolve() == outer.resolve():
            return "git-admin:agent-runtime/task-claim-store"
        raise AssertionError(f"unexpected activation subject: {path}")

    expected_before = {
        "subjects": [
            {"path": _logical_ref(subject.path), "exists": False, "base64_bytes": None}
            for subject in plan.subjects
        ]
    }
    expected_after = {
        "subjects": [
            {
                "path": _logical_ref(subject.path),
                "exists": True,
                "base64_bytes": base64.b64encode(subject.after_bytes).decode("ascii"),
            }
            for subject in plan.subjects
        ]
    }
    prepare = captured["prepare"]
    assert prepare["operation"] == "activate-store"
    assert prepare["before_bytes"] == recovery_receipt.canonical_json_bytes(
        expected_before
    )
    assert prepare["predicted_after_bytes"] == recovery_receipt.canonical_json_bytes(
        expected_after
    )
    assert inner.read_bytes() == plan.subjects[0].after_bytes
    assert outer.read_bytes() == plan.subjects[1].after_bytes
    receipt_dir = _recovery_receipt_dir(linked)
    assert len(list(receipt_dir.glob("*.prepared.json"))) == 1
    assert len(list(receipt_dir.glob("*.committed.json"))) == 1


def test_initialized_activation_is_receipt_and_event_free_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _primary, linked = _init_git_worktree(tmp_path, "ar660-activation-noop")
    result = _create_linked_claim(linked, suffix="660-act-noop")
    assert result.returncode == 0, result.stderr or result.stdout
    inner = linked / "agents" / "runtime" / "task_claims" / ".claim-store"
    outer = _claim_store_outer_anchor(linked)
    marker_before = (inner.read_bytes(), outer.read_bytes())
    event_before = _pane_event_bytes(linked)
    receipt_dir = _recovery_receipt_dir(linked)
    receipts_before = (
        sorted(path.name for path in receipt_dir.iterdir())
        if receipt_dir.exists()
        else []
    )

    dispatcher = _load_dispatcher_module()
    recovery_receipt = _dispatcher_recovery_module(dispatcher, monkeypatch)

    def _must_not_prepare(**_kwargs):
        raise AssertionError("initialized activation prepared a false recovery receipt")

    def _must_not_event(*_args, **_kwargs):
        raise AssertionError("initialized activation emitted a false recovery event")

    monkeypatch.setattr(recovery_receipt, "prepare_recovery_receipt", _must_not_prepare)
    monkeypatch.setattr(dispatcher, "append_event", _must_not_event)

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "activate-store",
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            _recovery_actor_id(linked),
            "--reason",
            "verify initialized no-op",
            "--json",
        ]
    )
    output = capsys.readouterr()

    assert rc == 0, output.err or output.out
    response = json.loads(output.out)
    assert response["status"] == "not_required"
    assert response["audit"] == "no-op"
    assert (inner.read_bytes(), outer.read_bytes()) == marker_before
    assert _pane_event_bytes(linked) == event_before
    receipts_after = (
        sorted(path.name for path in receipt_dir.iterdir())
        if receipt_dir.exists()
        else []
    )
    assert receipts_after == receipts_before


def test_activation_audit_loss_is_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A derived pane-event failure cannot erase durable receipt authority."""
    _primary, linked = _init_git_worktree(tmp_path, "ar659-audit-loss")
    result = _create_linked_claim(linked, suffix="659-auditloss")
    assert result.returncode == 0, result.stderr or result.stdout
    _claim_store_outer_anchor(linked).unlink()
    events_before = _pane_event_bytes(linked)

    dispatcher = _load_dispatcher_module()
    recovery_receipt = _dispatcher_recovery_module(dispatcher, monkeypatch)

    def _broken_sink(*_a, **_k):
        raise OSError("pane event sink is unavailable")

    monkeypatch.setattr(dispatcher, "append_event", _broken_sink)

    rc = dispatcher.main(
        [
            "--root",
            str(linked),
            "activate-store",
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            _recovery_actor_id(linked),
            "--reason",
            "audit sink is broken",
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0  # activation must not roll back
    assert _claim_store_outer_anchor(linked).is_file()
    assert _pane_event_bytes(linked) == events_before
    response = json.loads(captured.out)
    assert response["audit"] == "receipt-recorded:event-lost"
    assert response["recovery_receipt"]["status"] == "committed"
    receipt_dir = _recovery_receipt_dir(linked)
    prepared = list(receipt_dir.glob("*.prepared.json"))
    committed = list(receipt_dir.glob("*.committed.json"))
    assert len(prepared) == len(committed) == 1
    assert recovery_receipt.validate_receipt(prepared[0])["state"] == "prepared"
    assert recovery_receipt.validate_receipt(committed[0])["state"] == "committed"
    assert "event" in captured.err.lower()
    assert "not recorded" in captured.err.lower()
    assert "attribution" not in captured.err.lower() or "not durable" not in captured.err.lower()


def test_indeterminate_flag_cannot_end_a_claim_with_a_future_deadline(
    tmp_path: Path,
) -> None:
    """Indeterminate does not mean "no evidence".

    The pre-`lease`-nesting legacy shape carries a readable, valid, future
    top-level expires_at. That is positive evidence of liveness, and no flag
    may discard it -- this is the exact shape the flag exists to serve, so an
    owner reasonably believes it only ends provably-dead claims.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar659-indet-live")
    wall_now = datetime.now().astimezone().isoformat(timespec="seconds")
    result = _create_linked_claim(
        linked,
        suffix="659-indetlive",
        extra_args=("--lease-minutes", "600", "--now", wall_now),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]

    claim = json.loads(path.read_text(encoding="utf-8"))
    claim.pop("lease", None)  # legacy shape: top-level deadline only
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "terminalize",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "flag must not override readable liveness",
        "--allow-indeterminate-lease",
        "--json",
    )

    assert result.returncode != 0, (
        "the flag ended a claim whose readable deadline is still in the future: "
        + result.stdout
    )
    assert path.read_bytes() == before
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "claimed"


def test_adopt_refuses_a_spec_less_claim_without_a_replan(tmp_path: Path) -> None:
    """With no unit_spec there is no authority to diff against.

    _current_scope_values echoes the claim's own fields back, so a diff-based
    gate compares the claim to itself and can never fire. Such a claim must
    require an explicit replan instead of having its contents blessed.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar659-specless")
    result = _create_linked_claim(linked, suffix="659-specless")
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    path = linked / payload["path"]
    claim = json.loads(path.read_text(encoding="utf-8"))
    assert not str(claim.get("unit_spec") or "").strip()

    claim.pop("scope_binding", None)
    claim["target_files"] = [
        "src/agent_runtime/claim_store.py",
        "scripts/claim_reaper.py",
    ]
    claim["stop_condition"] = "attacker chosen"
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "spec-less claim must not self-bless its scope",
        "--json",
    )

    assert result.returncode != 0, (
        "adopt blessed caller-chosen scope on a spec-less claim: " + result.stdout
    )
    assert "replan" in (result.stdout + result.stderr).lower()
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "label, offset_seconds, expect_ended",
    [
        ("future-deadline-live", 36000, False),
        ("just-past-expiry-within-grace", -60, False),
        ("at-grace-boundary", -600, True),
        ("well-past-grace-truly-dead", -18000, True),
    ],
)
def test_indeterminate_flag_respects_the_liveness_evidence_boundary(
    tmp_path: Path, label: str, offset_seconds: int, expect_ended: bool
) -> None:
    """The evidence refusal must not make --allow-indeterminate-lease useless.

    A `deadline-partial` claim still carries a readable deadline. Refuse while
    that deadline says the claim may be alive; end it once it is provably dead.
    Without the dead cases pinned, tightening the guard could silently turn the
    flag into a no-op and re-open the exit-less deadlock this unit closes.
    """
    _primary, linked = _init_git_worktree(tmp_path, f"ar659-bound-{label}")
    now = datetime.now().astimezone()
    result = _create_linked_claim(
        linked,
        suffix="659-bound",
        extra_args=("--lease-minutes", "600", "--now", now.isoformat(timespec="seconds")),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    path = linked / json.loads(result.stdout)["path"]

    claim = json.loads(path.read_text(encoding="utf-8"))
    claim.pop("lease", None)  # legacy shape: readable top-level deadline only
    claim["expires_at"] = (
        now + timedelta(seconds=offset_seconds)
    ).isoformat(timespec="seconds")
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")

    result = _run_dispatcher(
        linked,
        "terminalize",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        f"boundary case {label}",
        "--allow-indeterminate-lease",
        "--json",
    )

    final = json.loads(path.read_text(encoding="utf-8"))["status"]
    if expect_ended:
        assert result.returncode == 0, (
            f"{label}: a provably dead legacy claim was not endable — the flag "
            "has become useless: " + (result.stderr or result.stdout)
        )
        assert final == "expired"
    else:
        assert result.returncode != 0, f"{label}: ended a claim that may be alive"
        assert final == "claimed"


# ===========================================================================
# TASK-AR-655 W4b round 2 — the mutation commands must hold the same bar as
# their recovery siblings. Both defects below let a claim outlive or outgrow
# what its own record authorizes, which is exactly what this unit exists to
# prevent.
# ===========================================================================


def _spec_backed_claim(linked: Path, task_id: str, suffix: str, minutes: str = "30"):
    unit_rel = _write_routing_work(linked, task_id)
    result = _run_dispatcher(
        linked, "create",
        "--task-id", task_id,
        "--agent-role", "lead-engineer",
        "--unit-id", f"UNIT-{task_id}-001",
        "--unit-spec", unit_rel,
        "--worktree-path", ".",
        "--lease-minutes", minutes,
        "--now", datetime.now().astimezone().isoformat(timespec="seconds"),
        "--suffix", suffix,
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    return linked / payload["path"], payload["claim"]


def test_heartbeat_refuses_a_claim_whose_scope_binding_no_longer_matches(
    tmp_path: Path,
) -> None:
    """renew validates the persisted binding; heartbeat must too.

    target_files is the enforced footprint: _footprint_conflict_errors reads it
    to refuse sibling creates, and footprint_conflict_gate --enforce-undeclared
    blocks on writes outside it. Editing it out of band and then heartbeating
    launders a scope broadening past the replan bar and keeps re-authorizing it
    on an indefinitely extendable lease.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar655-hb-scope")
    path, claim = _spec_backed_claim(linked, "TASK-AR-655hbscope", "hbscope")

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["target_files"] = list(tampered["target_files"]) + [
        "scripts/anything_i_want.py"
    ]
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "heartbeat",
        "--claim-id",
        claim["claim_id"],
        "--agent-instance-id",
        claim["agent_instance_id"],
        "--callsite-id",
        claim["callsite_id"],
        "--expected-revision",
        "0",
        "--json",
    )

    assert result.returncode != 0, (
        "heartbeat accepted a claim whose target_files no longer match its "
        "scope_binding: " + result.stdout
    )
    assert "scope binding" in (result.stdout + result.stderr).lower()
    assert path.read_bytes() == before


@pytest.mark.parametrize("operation", ["heartbeat", "renew"])
def test_mutation_now_cannot_push_a_lease_past_the_wall_clock(
    tmp_path: Path, operation: str
) -> None:
    """`--now` is a determinism seam, not an authority seam.

    _recovery_now already clamps for adopt/terminalize. _mutation_now does not,
    so passing a `now` just short of the deadline advances the lease by a full
    window per call, unbounded and in constant real time. Every consumer then
    believes the fabricated deadline: the reaper reports the claim live and no
    surface compares a persisted lease field to the wall clock.
    """
    _primary, linked = _init_git_worktree(tmp_path, f"ar655-clock-{operation}")
    path, claim = _spec_backed_claim(
        linked, f"TASK-AR-655clock{operation}", f"clk{operation[:3]}"
    )

    deadline = datetime.fromisoformat(
        json.loads(path.read_text(encoding="utf-8"))["expires_at"]
    )
    forged = (deadline - timedelta(seconds=1)).isoformat(timespec="seconds")

    args = [
        operation,
        "--claim-id",
        claim["claim_id"],
        "--agent-instance-id",
        claim["agent_instance_id"],
        "--callsite-id",
        claim["callsite_id"],
        "--expected-revision",
        "0",
        "--now",
        forged,
    ]
    if operation == "renew":
        args += [
            "--expected-scope-digest",
            claim["scope_binding"]["digest"],
            "--lease-minutes",
            "30",
        ]
    args.append("--json")

    result = _run_dispatcher(linked, *args)

    after = json.loads(path.read_text(encoding="utf-8"))
    wall = datetime.now().astimezone()
    persisted = datetime.fromisoformat(after["expires_at"])
    original = datetime.fromisoformat(claim["expires_at"])

    assert persisted <= max(original, wall) + timedelta(minutes=31), (
        f"{operation} pushed the lease to {persisted.isoformat()} using a forged "
        f"--now while the wall clock is {wall.isoformat()}; rc={result.returncode}"
    )
    assert datetime.fromisoformat(after["last_heartbeat"]) <= wall + timedelta(
        seconds=5
    ), f"{operation} recorded a future last_heartbeat: {after['last_heartbeat']}"


def test_heartbeat_scope_check_cannot_be_skipped_by_self_declared_overlay(
    tmp_path: Path,
) -> None:
    """The exemption must not key on a flag the claim asserts about itself.

    `overlay` lives in the same file whose integrity is being checked and is
    not covered by the scope digest, so keying the skip on it lets one extra
    key launder a widened footprint. A genuine overlay is recognisable by
    carrying no scope_binding at all, which is not forgeable in the same way.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar655-overlay-bypass")
    path, claim = _spec_backed_claim(linked, "TASK-AR-655ovl", "ovlbyp")

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["target_files"] = list(tampered["target_files"]) + ["src/agent_runtime/**"]
    tampered["overlay"] = True
    tampered["allow_parallel_task_set"] = True
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked, "heartbeat",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--json",
    )

    assert result.returncode != 0, (
        "a self-declared overlay flag skipped the scope-binding check: "
        + result.stdout
    )
    assert path.read_bytes() == before


def test_heartbeat_refuses_a_non_overlay_claim_with_no_scope_binding(
    tmp_path: Path,
) -> None:
    """Deleting the binding must not be an easier bypass than forging it."""
    _primary, linked = _init_git_worktree(tmp_path, "ar655-binding-deleted")
    path, claim = _spec_backed_claim(linked, "TASK-AR-655nobind", "nobind")

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered.pop("scope_binding", None)
    tampered["target_files"] = list(tampered["target_files"]) + ["src/agent_runtime/**"]
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked, "heartbeat",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--json",
    )

    assert result.returncode != 0, (
        "a non-overlay claim heartbeat with its scope_binding deleted: "
        + result.stdout
    )
    assert path.read_bytes() == before


def test_heartbeat_is_anchored_to_the_unit_spec_like_renew(tmp_path: Path) -> None:
    """A self-consistent claim is not an authorized claim.

    The binding is an unkeyed digest over the claim's own fields, so widening
    target_files AND recomputing the binding yields a claim that passes an
    internal-consistency check. renew re-derives scope from unit_spec via
    _current_scope_values and refuses; heartbeat did not, and heartbeat is the
    command that keeps a claim alive indefinitely.
    """
    _primary, linked = _init_git_worktree(tmp_path, "ar655-hb-anchor")
    path, claim = _spec_backed_claim(linked, "TASK-AR-655hbanchor", "hbanch")

    dispatcher = _load_dispatcher_module()
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["target_files"] = ["src/agent_runtime/**"]
    tampered["scope_binding"] = dispatcher.claim_store.scope_binding(
        task_id=tampered["task_id"],
        unit_id=tampered["unit_id"],
        unit_spec=tampered["unit_spec"],
        target_files=tampered["target_files"],
        stop_condition=tampered.get("stop_condition"),
        bound_at=tampered["scope_binding"]["bound_at"],
    )
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked, "heartbeat",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--json",
    )

    assert result.returncode != 0, (
        "heartbeat accepted a self-consistent but unauthorized scope widening: "
        + result.stdout
    )
    assert path.read_bytes() == before


def test_scope_binding_digest_layout_is_frozen(tmp_path: Path) -> None:
    """A silent reorder of `components` would invalidate every stored binding.

    Pinned against a fixed input so relocating or refactoring the minter cannot
    change the wire format unnoticed.
    """
    dispatcher = _load_dispatcher_module()
    binding = dispatcher.claim_store.scope_binding(
        task_id="TASK-AR-000",
        unit_id="UNIT-TASK-AR-000-001",
        unit_spec="agents/lead_engineer/tasks/units/TASK-AR-000/UNIT-TASK-AR-000-001.md",
        target_files=["b.py", "a.py", "b.py"],
        stop_condition="stop before anything irreversible",
        bound_at="2026-01-01T00:00:00+09:00",
    )
    assert binding["schema"] == "agent-runtime-claim-scope-binding/v1"
    assert list(binding["components"]) == ["task", "unit", "target_files", "stop_condition"]
    assert binding["digest"] == (
        "88bf816ce577633be95215800beec4365ccf2b519b6e47b8effcc5a3686769c4"
    )


def test_role_routing_binds_overlay_claims_at_birth(tmp_path: Path) -> None:
    """Overlays must carry a binding so the mutation path needs no exemption."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "role_routing_probe", REPO_ROOT / "scripts" / "role_routing.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["role_routing_probe"] = module
    spec.loader.exec_module(module)
    source = (REPO_ROOT / "scripts" / "role_routing.py").read_text(encoding="utf-8")
    assert '"scope_binding": claim_store.scope_binding(' in source, (
        "role_routing no longer mints a binding at overlay birth; the "
        "unconditional heartbeat check would strand every new overlay"
    )


def test_heartbeat_still_works_for_a_claim_whose_spec_declares_a_stop_condition(
    tmp_path: Path,
) -> None:
    """The anchor must not reject the ordinary, untampered path.

    `create` does not copy the spec's stop_condition into the claim, so a
    spec-derived comparison that includes it reports drift on every real claim
    from the moment it is created. Fixtures hide this because their generated
    unit specs declare no stop_condition.
    """
    task_id = "TASK-AR-655stopcond"
    _primary, linked = _init_git_worktree(tmp_path, "ar655-stopcond")
    unit_rel = _write_routing_work(linked, task_id)
    unit_path = linked / unit_rel
    unit_path.write_text(
        unit_path.read_text(encoding="utf-8").replace(
            "escalation_triggers:",
            "stop_condition: Stop before anything irreversible\nescalation_triggers:",
        ),
        encoding="utf-8",
    )

    result = _run_dispatcher(
        linked, "create",
        "--task-id", task_id,
        "--agent-role", "lead-engineer",
        "--unit-id", f"UNIT-{task_id}-001",
        "--unit-spec", unit_rel,
        "--worktree-path", ".",
        "--now", datetime.now().astimezone().isoformat(timespec="seconds"),
        "--suffix", "stopcnd",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]

    result = _run_dispatcher(
        linked, "heartbeat",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--json",
    )

    assert result.returncode == 0, (
        "the spec anchor rejected an ordinary untampered claim: "
        + (result.stderr or result.stdout)
    )


def test_heartbeat_refuses_a_claim_repointed_at_an_alternate_unit_spec(
    tmp_path: Path,
) -> None:
    """Door 5: the anchor must not read its own reference out of the claim.

    _current_scope_values re-reads claim["unit_spec"] and only checks that the
    spec's task_id/unit_id match. A second spec file carrying the same ids and
    a wider footprint is therefore accepted as the authority - the overlay-flag
    mistake again, one level up.
    """
    task_id = "TASK-AR-655altspec"
    _primary, linked = _init_git_worktree(tmp_path, "ar655-altspec")
    unit_rel = _write_routing_work(linked, task_id)
    path, claim = _spec_backed_claim(linked, task_id, "altspec")

    alt_rel = f"agents/lead_engineer/tasks/units/{task_id}/UNIT-{task_id}-001-alt.md"
    alt_path = linked / alt_rel
    alt_path.write_text(
        (linked / unit_rel).read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py\n  - scripts/routing_second.py",
            "  - src/agent_runtime/**",
        ),
        encoding="utf-8",
    )

    dispatcher = _load_dispatcher_module()
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["unit_spec"] = alt_rel
    tampered["target_files"] = ["src/agent_runtime/**"]
    tampered["scope_binding"] = dispatcher.claim_store.scope_binding(
        task_id=tampered["task_id"],
        unit_id=tampered["unit_id"],
        unit_spec=alt_rel,
        target_files=tampered["target_files"],
        stop_condition=tampered.get("stop_condition"),
        bound_at=tampered["scope_binding"]["bound_at"],
    )
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked, "heartbeat",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--json",
    )

    assert result.returncode != 0, (
        "a claim repointed at an alternate spec was accepted: " + result.stdout
    )
    assert path.read_bytes() == before


@pytest.mark.parametrize("operation", ["renew", "adopt"])
def test_a_claim_created_before_the_stop_condition_fix_is_not_treated_as_drifted(
    tmp_path: Path, operation: str
) -> None:
    """Every claim in the store predates `create` copying the spec's boundary.

    Those claims carry stop_condition '' while the spec declares text, so a
    naive comparison reports drift and refuses renew and adopt for all of them.
    An unrecorded boundary is "not overridden", not "changed".
    """
    task_id = f"TASK-AR-655legacy{operation}"
    _primary, linked = _init_git_worktree(tmp_path, f"ar655-legacy-{operation}")
    path, claim = _spec_backed_claim(linked, task_id, f"lg{operation[:3]}", minutes="120")

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["stop_condition"] = ""          # the pre-fix shape
    if operation == "adopt":
        payload.pop("mutation_revision", None)
        payload.pop("scope_binding", None)
    else:
        payload["scope_binding"] = _load_dispatcher_module().claim_store.scope_binding(
            task_id=payload["task_id"],
            unit_id=payload["unit_id"],
            unit_spec=payload["unit_spec"],
            target_files=payload["target_files"],
            stop_condition="",
            bound_at=payload["scope_binding"]["bound_at"],
        )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if operation == "adopt":
        args = ["adopt", "--claim-id", claim["claim_id"],
                "--owner-id", _OWNER,
                "--actor-instance-id", _recovery_actor_id(linked),
                "--reason", "legacy claim repair"]
    else:
        args = ["renew", "--claim-id", claim["claim_id"],
                "--agent-instance-id", claim["agent_instance_id"],
                "--callsite-id", claim["callsite_id"],
                "--expected-revision", "0",
                "--expected-scope-digest", payload["scope_binding"]["digest"],
                "--lease-minutes", "60"]

    result = _run_dispatcher(linked, *args, "--json")

    assert result.returncode == 0, (
        f"{operation} refused an ordinary pre-fix claim as drifted: "
        + (result.stderr or result.stdout)
    )


# --- The symmetry invariant: whatever `create` accepts, `heartbeat` must too ---
#
# Three separate defects were each discovered as their own field - stop_condition,
# out-of-spec --target-file, non-canonical unit_spec - and each got its own fix at
# its own layer. They are one bug: create and the mutation path disagreeing about
# what a valid claim looks like. This matrix is the invariant, so a fourth field
# cannot repeat it silently.


@pytest.mark.parametrize(
    "label, extra_create_args, mutate_spec",
    [
        ("plain", (), False),
        ("explicit-target-inside-spec", ("--target-file", "scripts/routing_second.py"), False),
        ("nested-unit-spec", (), True),
        # A spec pointer with no unit identity: `create` accepted it and
        # `_current_scope_values` then refused every beat with "unit_spec unit
        # identity changed" - born unusable, and a fourth instance of the
        # create-versus-mutate disagreement independent of the canonical guard.
        ("unit-spec-without-unit-id", (), False),
        ("spec-less", (), False),
        ("orchestrator-mode", ("--mode", "orchestrator"), False),
        # Frontmatter ids disagreeing with the claim: create validated only
        # that the spec file exists, so these were born unusable too.
        ("spec-frontmatter-task-id-mismatch", (), False),
        ("spec-frontmatter-unit-id-mismatch", (), False),
        # Spec declares no target_files at all: _resolve_target_files' stray
        # guard is gated on `if registered:`, so explicit entries pass straight
        # through and the heartbeat component comparison then refuses forever.
        ("empty-spec-target-files", ("--target-file", "src/agent_runtime/**"), False),
    ],
)
def test_every_claim_create_accepts_can_immediately_heartbeat(
    tmp_path: Path, label: str, extra_create_args: tuple, mutate_spec: bool
) -> None:
    task_id = f"TASK-AR-655sym{label.replace('-', '')}"
    _primary, linked = _init_git_worktree(tmp_path, f"ar655-sym-{label}")
    unit_rel = _write_routing_work(linked, task_id)

    if label == "empty-spec-target-files":
        spec = linked / unit_rel
        body = spec.read_text(encoding="utf-8")
        body = body.replace("target_files:\n  - scripts/routing_target.py\n  - scripts/routing_second.py\n", "")
        spec.write_text(body, encoding="utf-8")
    if label == "spec-frontmatter-task-id-mismatch":
        spec = linked / unit_rel
        spec.write_text(
            spec.read_text(encoding="utf-8").replace(
                f"task_id: {task_id}", "task_id: TASK-AR-OTHER"
            ),
            encoding="utf-8",
        )
    if label == "spec-frontmatter-unit-id-mismatch":
        spec = linked / unit_rel
        spec.write_text(
            spec.read_text(encoding="utf-8").replace(
                f"unit_id: UNIT-{task_id}-001", "unit_id: UNIT-SOMETHING-ELSE-001"
            ),
            encoding="utf-8",
        )
    if mutate_spec:
        nested_rel = (
            f"agents/lead_engineer/tasks/units/{task_id}/nested/UNIT-{task_id}-001.md"
        )
        nested = linked / nested_rel
        nested.parent.mkdir(parents=True, exist_ok=True)
        nested.write_text((linked / unit_rel).read_text(encoding="utf-8"), encoding="utf-8")
        unit_rel = nested_rel

    create_args = ["--task-id", task_id, "--agent-role", "lead-engineer"]
    if label == "unit-spec-without-unit-id":
        create_args += ["--unit-spec", unit_rel]          # deliberately no --unit-id
    elif label != "spec-less":
        create_args += ["--unit-id", f"UNIT-{task_id}-001", "--unit-spec", unit_rel]

    result = _run_dispatcher(
        linked, "create",
        *create_args,
        "--worktree-path", ".",
        "--now", datetime.now().astimezone().isoformat(timespec="seconds"),
        "--suffix", f"sym{label[:6].replace('-','')}",
        *extra_create_args,
        "--json",
    )
    if result.returncode != 0:
        # Refusing at create is a legitimate answer; being born unusable is not.
        return
    claim = json.loads(result.stdout)["claim"]

    beat = _run_dispatcher(
        linked, "heartbeat",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--json",
    )
    assert beat.returncode == 0, (
        f"{label}: create accepted a claim that heartbeat refuses, so it was "
        "born unusable: " + (beat.stderr or beat.stdout)
    )


def test_the_stop_condition_tolerance_extinguishes_itself(tmp_path: Path) -> None:
    """Grandfathering must be once, not forever.

    A tolerated renew that leaves the claim empty keeps it in the tolerated
    state for life, and turns "legacy claims are grandfathered" into "empty is
    permanently acceptable" - reachable forward by clearing a boundary that was
    previously set.
    """
    task_id = "TASK-AR-655extinguish"
    _primary, linked = _init_git_worktree(tmp_path, "ar655-extinguish")
    path, claim = _spec_backed_claim(linked, task_id, "exting", minutes="120")
    dispatcher = _load_dispatcher_module()

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["stop_condition"] = ""
    payload["scope_binding"] = dispatcher.claim_store.scope_binding(
        task_id=payload["task_id"], unit_id=payload["unit_id"],
        unit_spec=payload["unit_spec"], target_files=payload["target_files"],
        stop_condition="", bound_at=payload["scope_binding"]["bound_at"],
    )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = _run_dispatcher(
        linked, "renew",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--expected-scope-digest", payload["scope_binding"]["digest"],
        "--lease-minutes", "60",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout

    healed = json.loads(path.read_text(encoding="utf-8"))
    assert healed["stop_condition"], (
        "the tolerated renew left the claim empty, so the tolerance never "
        "expires and clearing the boundary stays permanently acceptable"
    )
    assert healed["stop_condition"] == "Stop before anything irreversible"

    # Residual, recorded rather than papered over: "never recorded" and
    # "cleared" are indistinguishable in claim-local state, so a determined
    # tamperer can re-enter the tolerated state by clearing the boundary again.
    # A marker saying "already healed" would itself be strippable - the same
    # door as the overlay flag - so the guarantee claimed here is the one that
    # is actually achievable: the tolerated population shrinks monotonically
    # with ordinary use, and a boundary changed to a DIFFERENT value is still
    # refused outright.
    tampered = dict(healed)
    tampered["stop_condition"] = "no limits whatsoever"
    tampered["scope_binding"] = dispatcher.claim_store.scope_binding(
        task_id=tampered["task_id"], unit_id=tampered["unit_id"],
        unit_spec=tampered["unit_spec"], target_files=tampered["target_files"],
        stop_condition=tampered["stop_condition"],
        bound_at=tampered["scope_binding"]["bound_at"],
    )
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    again = _run_dispatcher(
        linked, "renew",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", str(tampered["mutation_revision"]),
        "--expected-scope-digest", tampered["scope_binding"]["digest"],
        "--lease-minutes", "60",
        "--json",
    )
    assert again.returncode != 0, "a rewritten stop boundary was tolerated"


def test_renew_refuses_a_claim_repointed_at_a_non_canonical_spec(tmp_path: Path) -> None:
    """The canonical pin belongs on every path that trusts claim["unit_spec"].

    Enforcing it only on heartbeat leaves the inverse of the born-unusable
    state: a claim anchored to an unregistered spec file cannot beat but can be
    renewed indefinitely. The footprint clause must NOT run here - renew owns
    the drift path and reconciles it against an accepted replan.
    """
    task_id = "TASK-AR-655renewpin"
    _primary, linked = _init_git_worktree(tmp_path, "ar655-renewpin")
    unit_rel = _write_routing_work(linked, task_id)
    path, claim = _spec_backed_claim(linked, task_id, "rnwpin", minutes="120")

    alt_rel = (
        f"agents/lead_engineer/tasks/units/{task_id}/nested/UNIT-{task_id}-001.md"
    )
    alt = linked / alt_rel
    alt.parent.mkdir(parents=True, exist_ok=True)
    alt.write_text((linked / unit_rel).read_text(encoding="utf-8"), encoding="utf-8")

    dispatcher = _load_dispatcher_module()
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["unit_spec"] = alt_rel
    tampered["scope_binding"] = dispatcher.claim_store.scope_binding(
        task_id=tampered["task_id"], unit_id=tampered["unit_id"], unit_spec=alt_rel,
        target_files=tampered["target_files"],
        stop_condition=tampered.get("stop_condition"),
        bound_at=tampered["scope_binding"]["bound_at"],
    )
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    before = path.read_bytes()

    result = _run_dispatcher(
        linked, "renew",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", "0",
        "--expected-scope-digest", tampered["scope_binding"]["digest"],
        "--lease-minutes", "60",
        "--json",
    )

    assert result.returncode != 0, (
        "renew accepted a claim anchored to an unregistered spec: " + result.stdout
    )
    assert "canonical" in (result.stdout + result.stderr)
    assert path.read_bytes() == before


def test_renew_still_reconciles_ordinary_scope_drift(tmp_path: Path) -> None:
    """Guard the other direction: the footprint clause must not leak into renew.

    Renew exists to reconcile drift against an accepted replan. Sharing the
    whole contract here would break that, so this pins the permitted case.
    """
    task_id = "TASK-AR-655renewdrift"
    _primary, linked = _init_git_worktree(tmp_path, "ar655-renewdrift")
    unit_rel = _write_routing_work(linked, task_id)
    path, claim = _spec_backed_claim(linked, task_id, "rnwdft", minutes="120")

    unit_path = linked / unit_rel
    unit_path.write_text(
        unit_path.read_text(encoding="utf-8").replace(
            "  - scripts/routing_second.py",
            "  - scripts/routing_second.py\n  - scripts/routing_third.py",
        ),
        encoding="utf-8",
    )
    replan_rel = "reviews/REVIEW-renew-drift-replan.md"
    (linked / replan_rel).parent.mkdir(parents=True, exist_ok=True)
    (linked / replan_rel).write_text(
        "\n".join([
            "---", "id: REVIEW-renew-drift-replan", f"task_id: {task_id}",
            f"unit_id: UNIT-{task_id}-001", "review_kind: t3-replan", "tier: T3",
            "status: accepted", "signal: pass", "---", "",
        ]),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "plan_assumption_gate.py"),
         "--root", str(linked), "record",
         "--taskset", str(claim["task_set_id"]),
         "--design-record", replan_rel, "--anchor", unit_rel],
        check=True, capture_output=True, text=True,
    )

    persisted = json.loads(path.read_text(encoding="utf-8"))
    result = _run_dispatcher(
        linked, "renew",
        "--claim-id", claim["claim_id"],
        "--agent-instance-id", claim["agent_instance_id"],
        "--callsite-id", claim["callsite_id"],
        "--expected-revision", str(persisted["mutation_revision"]),
        "--expected-scope-digest", persisted["scope_binding"]["digest"],
        "--lease-minutes", "60",
        "--replan-ref", replan_rel,
        "--json",
    )

    assert result.returncode == 0, (
        "renew refused legitimate drift with an accepted replan: "
        + (result.stderr or result.stdout)
    )
    assert "scripts/routing_third.py" in json.loads(
        path.read_text(encoding="utf-8")
    )["target_files"]


# TASK-AR-660: durable work identity ---------------------------------------

WORK_IDENTITY_BINDING_SCHEMA = "agent-runtime-claim-work-identity-binding/v1"
_AR660_TASK_UID = "11111111-1111-4111-8111-111111111111"
_AR660_UNIT_WORK_UID = "22222222-2222-4222-8222-222222222222"
_AR660_REPLACEMENT_UID = "33333333-3333-4333-8333-333333333333"


def _expected_work_identity_binding(
    *,
    task_id: str,
    task_uid: str,
    unit_id: str,
    work_uid: str,
    bound_at: str,
) -> dict[str, object]:
    """Independent oracle for the immutable display-ID/UUID pairing."""

    components = {
        "task": _canonical_sha256(
            {"task_id": task_id, "task_uid": task_uid}
        ),
        "unit": _canonical_sha256(
            {"unit_id": unit_id, "work_uid": work_uid}
        ),
    }
    return {
        "schema": WORK_IDENTITY_BINDING_SCHEMA,
        "digest": _canonical_sha256(components),
        "components": components,
        "bound_at": bound_at,
    }


def _write_work_identity_records(
    root: Path,
    task_id: str,
    *,
    task_uid: str = _AR660_TASK_UID,
    unit_work_uid: str = _AR660_UNIT_WORK_UID,
) -> tuple[Path, Path, str, str]:
    unit_id = f"UNIT-{task_id}-001"
    unit_rel = f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md"
    task_path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    unit_path = root / unit_rel
    task_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                f"id: {task_id}",
                f"display_id: {task_id}",
                f"task_uid: {task_uid}",
                f"work_id: {task_id}",
                f"work_uid: {task_uid}",
                "kind: task",
                f"unit_spec: {unit_rel}",
                "status: worker_ready",
                "---",
                "",
                "# Work identity fixture task",
                "",
            ]
        ),
        encoding="utf-8",
    )
    unit_path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                f"work_id: {unit_id}",
                f"work_uid: {unit_work_uid}",
                "kind: unit",
                f"parent_id: {task_id}",
                f"unit_id: {unit_id}",
                f"task_id: {task_id}",
                "status: worker_ready",
                "target_files:",
                "  - scripts/claim_worker.py",
                f"stop_condition: stop_after:{unit_id}:verification",
                "---",
                "",
                "# Work identity fixture unit",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return task_path, unit_path, unit_id, unit_rel


def _create_work_identity_candidate(
    root: Path,
    *,
    task_id: str,
    suffix: str,
    worktree_path: str = "",
) -> tuple[dict[str, object], Path, Path]:
    (root / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    if not worktree_path:
        _write_worktree(root, task_id)
    task_path, unit_path, unit_id, unit_rel = _write_work_identity_records(
        root, task_id
    )
    args = [
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        unit_id,
        "--unit-spec",
        unit_rel,
        "--stop-condition",
        f"stop_after:{unit_id}:verification",
        "--agent-role",
        "lead-engineer",
        "--agent-instance-id",
        f"le-20260809-090000-kst-{suffix}",
        "--callsite-id",
        f"terminal:wt-{task_id.lower()}:tab-01",
        "--lease-minutes",
        "30",
        "--now",
        "2026-08-09T09:00:00+09:00",
        "--suffix",
        suffix,
        "--json",
    ]
    if worktree_path:
        args.extend(("--worktree-path", worktree_path))
    created = _run_dispatcher(root, *args)
    assert created.returncode == 0, created.stderr or created.stdout
    return json.loads(created.stdout), task_path, unit_path


def _remove_work_identity_metadata(
    task_path: Path,
    unit_path: Path,
    damage: str,
) -> None:
    if damage == "task-record-missing":
        task_path.unlink()
        return
    if damage == "unit-record-missing":
        unit_path.unlink()
        return
    targets = {
        "task-id-missing": (task_path, "id:"),
        "task-uuid-missing": (task_path, "task_uid:"),
        "task-work-uuid-missing": (task_path, "work_uid:"),
        "unit-id-missing": (unit_path, "unit_id:"),
        "unit-uuid-missing": (unit_path, "work_uid:"),
    }
    try:
        path, prefix = targets[damage]
    except KeyError as exc:  # pragma: no cover - parametrizations own the set
        raise AssertionError(f"unknown missing identity metadata: {damage}") from exc
    lines = path.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if not line.startswith(prefix)]
    assert len(filtered) == len(lines) - 1, (path, prefix)
    path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    "damage",
    (
        "task-record-missing",
        "task-id-missing",
        "task-uuid-missing",
        "task-work-uuid-missing",
        "unit-record-missing",
        "unit-id-missing",
        "unit-uuid-missing",
    ),
)
def test_create_fails_closed_when_canonical_work_identity_metadata_is_missing(
    tmp_path: Path,
    damage: str,
) -> None:
    task_id = f"TASK-AR-660-CREATE-{damage.upper()}"
    unit_id = f"UNIT-{task_id}-001"
    unit_rel = f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md"
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    _write_worktree(tmp_path, task_id)
    task_path, unit_path, _unit_id, _unit_rel = _write_work_identity_records(
        tmp_path,
        task_id,
    )
    _remove_work_identity_metadata(task_path, unit_path, damage)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        unit_id,
        "--unit-spec",
        unit_rel,
        "--stop-condition",
        f"stop_after:{unit_id}:verification",
        "--agent-role",
        "lead-engineer",
        "--agent-instance-id",
        f"le-20260809-090000-kst-create-{damage}",
        "--callsite-id",
        f"terminal:wt-{task_id.lower()}:tab-01",
        "--lease-minutes",
        "30",
        "--now",
        "2026-08-09T09:00:00+09:00",
        "--suffix",
        f"create-{damage}",
        "--json",
    )

    assert result.returncode != 0, (
        f"create accepted missing canonical identity metadata ({damage}): "
        + (result.stderr or result.stdout)
    )
    diagnostic = (result.stdout + result.stderr).lower()
    assert any(
        token in diagnostic
        for token in ("identity", "canonical", "unit spec", "unit_spec")
    )
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not list(claim_dir.glob("CLAIM-*.json"))


def test_create_binds_canonical_task_and_unit_uuids_without_changing_scope_wire(
    tmp_path: Path,
) -> None:
    task_id = "TASK-AR-660-IDENTITY-CREATE"
    created, _task_path, _unit_path = _create_work_identity_candidate(
        tmp_path,
        task_id=task_id,
        suffix="identity-create",
    )
    claim = created["claim"]
    unit_id = f"UNIT-{task_id}-001"

    assert claim["work_identity_binding"] == _expected_work_identity_binding(
        task_id=task_id,
        task_uid=_AR660_TASK_UID,
        unit_id=unit_id,
        work_uid=_AR660_UNIT_WORK_UID,
        bound_at="2026-08-09T09:00:00+09:00",
    )
    # Work identity is an additional contract. It must not silently revise the
    # already-persisted scope-binding schema or component digest layout.
    assert claim["scope_binding"] == _expected_scope_binding(
        claim,
        bound_at="2026-08-09T09:00:00+09:00",
    )


def test_adopt_adds_only_missing_work_identity_to_an_otherwise_current_claim(
    tmp_path: Path,
) -> None:
    task_id = "TASK-AR-660-IDENTITY-ADOPT"
    _primary, linked = _init_git_worktree(tmp_path, "ar660-identity-adopt")
    created, _task_path, _unit_path = _create_work_identity_candidate(
        linked,
        task_id=task_id,
        suffix="identity-adopt",
        worktree_path=".",
    )
    path = _claim_path(linked, created)
    claim = json.loads(path.read_text(encoding="utf-8"))
    claim.pop("work_identity_binding", None)
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
    scope_before = json.loads(json.dumps(claim["scope_binding"]))

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "claim predates canonical work identity binding",
        "--now",
        "2026-08-09T09:10:00+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    adopted = json.loads(path.read_text(encoding="utf-8"))
    assert adopted["mutation_revision"] == 0
    assert adopted["scope_binding"] == scope_before
    assert adopted["work_identity_binding"] == _expected_work_identity_binding(
        task_id=task_id,
        task_uid=_AR660_TASK_UID,
        unit_id=f"UNIT-{task_id}-001",
        work_uid=_AR660_UNIT_WORK_UID,
        bound_at="2026-08-09T09:10:00+09:00",
    )


@pytest.mark.parametrize(
    "damage",
    (
        "task-record-missing",
        "task-id-missing",
        "task-uuid-missing",
        "task-work-uuid-missing",
        "unit-record-missing",
        "unit-id-missing",
        "unit-uuid-missing",
    ),
)
def test_adopt_fails_closed_when_canonical_work_identity_metadata_is_missing(
    tmp_path: Path,
    damage: str,
) -> None:
    task_id = f"TASK-AR-660-ADOPT-{damage.upper()}"
    _primary, linked = _init_git_worktree(tmp_path, f"ar660-adopt-{damage}")
    created, task_path, unit_path = _create_work_identity_candidate(
        linked,
        task_id=task_id,
        suffix=f"adopt-missing-{damage}",
        worktree_path=".",
    )
    path = _claim_path(linked, created)
    claim = json.loads(path.read_text(encoding="utf-8"))
    claim.pop("work_identity_binding")
    path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _remove_work_identity_metadata(task_path, unit_path, damage)
    before = path.read_bytes()

    result = _run_dispatcher(
        linked,
        "adopt",
        "--claim-id",
        claim["claim_id"],
        "--owner-id",
        _OWNER,
        "--actor-instance-id",
        _recovery_actor_id(linked),
        "--reason",
        "legacy claim cannot be rebound without canonical UUID authority",
        "--now",
        "2026-08-09T09:10:00+09:00",
        "--json",
    )

    assert result.returncode != 0, (
        f"adopt accepted missing canonical identity metadata ({damage}): "
        + (result.stderr or result.stdout)
    )
    diagnostic = (result.stdout + result.stderr).lower()
    assert any(
        token in diagnostic
        for token in ("identity", "canonical", "unit spec", "unit_spec")
    )
    assert path.read_bytes() == before


def _damage_work_identity_record(
    task_path: Path,
    unit_path: Path,
    damage: str,
) -> None:
    if damage in {
        "task-record-missing",
        "task-id-missing",
        "task-uuid-missing",
        "task-work-uuid-missing",
        "unit-record-missing",
        "unit-id-missing",
    }:
        _remove_work_identity_metadata(task_path, unit_path, damage)
        return
    if damage == "task-display-id-collision":
        text = task_path.read_text(encoding="utf-8")
        text = text.replace(_AR660_TASK_UID, _AR660_REPLACEMENT_UID)
        task_path.write_text(text, encoding="utf-8")
        return
    text = unit_path.read_text(encoding="utf-8")
    if damage == "unit-uuid-drift":
        text = text.replace(_AR660_UNIT_WORK_UID, _AR660_REPLACEMENT_UID)
    elif damage == "unit-uuid-missing":
        text = text.replace(f"work_uid: {_AR660_UNIT_WORK_UID}\n", "")
    else:  # pragma: no cover - the parametrization is the complete call surface
        raise AssertionError(f"unknown damage mode: {damage}")
    unit_path.write_text(text, encoding="utf-8")


def _work_identity_mutation_args(
    root: Path,
    claim: dict[str, object],
    operation: str,
) -> tuple[str, ...]:
    if operation == "heartbeat":
        return _replace_cli_option(
            _heartbeat_without_progress_args(claim),
            "--now",
            "2026-08-09T09:10:00+09:00",
        )
    if operation == "renew":
        return _renew_args(claim, now="2026-08-09T09:10:00+09:00")
    evidence = _write_evidence(
        root,
        "agents/runtime/task_claims/evidence/W4B-AR660-WORK-IDENTITY.md",
    )
    return (
        "release",
        "--claim-id",
        str(claim["claim_id"]),
        "--verified-by",
        "qa-20260809-091000-kst-ar660",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence,
        "--now",
        "2026-08-09T09:10:00+09:00",
        "--json",
    )


@pytest.mark.parametrize("operation", ("heartbeat", "renew", "release"))
@pytest.mark.parametrize(
    "damage",
    (
        "task-display-id-collision",
        "task-record-missing",
        "task-id-missing",
        "task-uuid-missing",
        "task-work-uuid-missing",
        "unit-record-missing",
        "unit-id-missing",
        "unit-uuid-drift",
        "unit-uuid-missing",
    ),
)
def test_claim_mutations_fail_closed_on_canonical_work_identity_damage(
    tmp_path: Path,
    operation: str,
    damage: str,
) -> None:
    task_id = f"TASK-AR-660-{operation.upper()}-{damage.upper()}"
    created, task_path, unit_path = _create_work_identity_candidate(
        tmp_path,
        task_id=task_id,
        suffix=f"{operation}-{damage}",
    )
    claim = created["claim"]
    _damage_work_identity_record(task_path, unit_path, damage)
    path = _claim_path(tmp_path, created)
    before = path.read_bytes()

    result = _run_dispatcher(
        tmp_path,
        *_work_identity_mutation_args(tmp_path, claim, operation),
    )

    assert result.returncode != 0, f"{operation} accepted {damage}"
    diagnostic = (result.stdout + result.stderr).lower()
    assert any(
        token in diagnostic
        for token in ("identity", "canonical", "unit spec", "unit_spec")
    )
    assert path.read_bytes() == before


def test_self_asserted_overlay_cannot_adopt_a_direct_claim_with_empty_uuid(
    tmp_path: Path,
) -> None:
    """Only the immutable role-routing shape may receive synthetic identity."""

    task_id = "TASK-AR-660-SELF-ASSERTED-OVERLAY"
    dispatcher = _load_dispatcher_module()
    created, _task_path, _unit_path = _create_work_identity_candidate(
        tmp_path,
        task_id=task_id,
        suffix="self-overlay",
    )
    claim = created["claim"]
    claim.pop("work_identity_binding")
    claim["overlay"] = True
    claim["parent_task_id"] = ""
    binding = dispatcher._work_identity_binding_for_claim(
        tmp_path,
        claim,
        bound_at="2026-08-09T09:10:00+09:00",
    )

    assert binding == _expected_work_identity_binding(
        task_id=task_id,
        task_uid=_AR660_TASK_UID,
        unit_id=f"UNIT-{task_id}-001",
        work_uid=_AR660_UNIT_WORK_UID,
        bound_at="2026-08-09T09:10:00+09:00",
    )


@pytest.mark.parametrize("colliding_field", ("id", "display_id", "work_id"))
def test_claim_mutation_refuses_any_duplicate_task_alias_in_canonical_namespace(
    tmp_path: Path,
    colliding_field: str,
) -> None:
    task_id = f"TASK-AR-660-NAMESPACE-{colliding_field.upper()}"
    created, _task_path, _unit_path = _create_work_identity_candidate(
        tmp_path,
        task_id=task_id,
        suffix=f"namespace-{colliding_field}",
    )
    claim = created["claim"]
    alternate_id = f"TASK-AR-660-ALTERNATE-{colliding_field.upper()}"
    aliases = {
        "id": alternate_id,
        "display_id": alternate_id,
        "work_id": alternate_id,
    }
    aliases[colliding_field] = task_id
    alternate_uid = _fixture_work_uid("task", alternate_id)
    collision_path = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / f"{alternate_id}.md"
    )
    collision_path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                f"id: {aliases['id']}",
                f"display_id: {aliases['display_id']}",
                f"task_uid: {alternate_uid}",
                f"work_id: {aliases['work_id']}",
                f"work_uid: {alternate_uid}",
                "kind: task",
                "status: worker_ready",
                "---",
                "",
                "# Conflicting canonical task alias",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path = _claim_path(tmp_path, created)
    before = path.read_bytes()

    result = _run_dispatcher(
        tmp_path,
        *_replace_cli_option(
            _heartbeat_without_progress_args(claim),
            "--now",
            "2026-08-09T09:10:00+09:00",
        ),
    )

    assert result.returncode != 0, (
        f"heartbeat accepted duplicate canonical {colliding_field} authority"
    )
    assert "identity" in (result.stdout + result.stderr).lower()
    assert path.read_bytes() == before


@pytest.mark.parametrize("identity_kind", ("task", "unit"))
def test_canonical_work_identity_rejects_uuid_versions_other_than_v4_or_v7(
    tmp_path: Path,
    identity_kind: str,
) -> None:
    dispatcher = _load_dispatcher_module()
    task_id = f"TASK-AR-660-UUID5-{identity_kind.upper()}"
    invalid_uuid = str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"invalid-runtime-{identity_kind}")
    )
    task_path, _unit_path, unit_id, unit_rel = _write_work_identity_records(
        tmp_path,
        task_id,
        task_uid=invalid_uuid if identity_kind == "task" else _AR660_TASK_UID,
        unit_work_uid=(
            invalid_uuid if identity_kind == "unit" else _AR660_UNIT_WORK_UID
        ),
    )
    assert task_path.is_file()

    with pytest.raises(ValueError, match="UUID|uuid|identity"):
        if identity_kind == "task":
            dispatcher._canonical_task_uid(tmp_path, task_id)
        else:
            dispatcher._canonical_unit_work_uid(
                tmp_path,
                task_id=task_id,
                unit_id=unit_id,
                unit_spec=unit_rel,
            )


@pytest.mark.parametrize("identity_kind", ("task", "unit"))
def test_canonical_work_identity_refuses_symlinked_record_authority(
    tmp_path: Path,
    identity_kind: str,
) -> None:
    dispatcher = _load_dispatcher_module()
    task_id = f"TASK-AR-660-SYMLINK-{identity_kind.upper()}"
    task_path, unit_path, unit_id, unit_rel = _write_work_identity_records(
        tmp_path,
        task_id,
    )
    target = task_path if identity_kind == "task" else unit_path
    outside = tmp_path.parent / f"{tmp_path.name}-{identity_kind}-authority.md"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)

    with pytest.raises(ValueError, match="direct|alias|symlink|reparse|identity"):
        if identity_kind == "task":
            dispatcher._canonical_task_uid(tmp_path, task_id)
        else:
            dispatcher._canonical_unit_work_uid(
                tmp_path,
                task_id=task_id,
                unit_id=unit_id,
                unit_spec=unit_rel,
            )


@pytest.mark.parametrize("escape_kind", ("absolute", "parent"))
def test_unit_meta_refuses_out_of_repo_authority_paths(
    tmp_path: Path,
    escape_kind: str,
) -> None:
    dispatcher = _load_dispatcher_module()
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside-unit.md"
    outside.write_text(
        "---\nunit_id: UNIT-OUTSIDE\nwork_uid: "
        + _AR660_UNIT_WORK_UID
        + "\n---\n",
        encoding="utf-8",
    )
    value = str(outside) if escape_kind == "absolute" else "../outside-unit.md"

    with pytest.raises(ValueError, match="repo-relative|outside|direct"):
        dispatcher._unit_meta(root, value)


def _write_duplicate_unit_alias(
    root: Path,
    task_id: str,
    *,
    colliding_field: str,
) -> Path:
    canonical_unit_id = f"UNIT-{task_id}-001"
    alternate_unit_id = f"UNIT-{task_id}-ALTERNATE-{colliding_field.upper()}"
    aliases = {
        "unit_id": alternate_unit_id,
        "work_id": alternate_unit_id,
    }
    aliases[colliding_field] = canonical_unit_id
    path = (
        root
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / task_id
        / f"{alternate_unit_id}.md"
    )
    path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: agent-runtime-work-item/v1",
                f"work_id: {aliases['work_id']}",
                f"work_uid: {_fixture_work_uid('unit', alternate_unit_id)}",
                "kind: unit",
                f"parent_id: {task_id}",
                f"unit_id: {aliases['unit_id']}",
                f"task_id: {task_id}",
                "status: worker_ready",
                "target_files:",
                "  - scripts/alternate_claim_worker.py",
                f"stop_condition: stop_after:{alternate_unit_id}:verification",
                "---",
                "",
                "# Conflicting canonical unit alias",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    "operation",
    ("create", "adopt", "heartbeat", "renew", "release"),
)
@pytest.mark.parametrize("colliding_field", ("unit_id", "work_id"))
def test_every_claim_entrypoint_refuses_duplicate_unit_namespace_authority(
    tmp_path: Path,
    operation: str,
    colliding_field: str,
) -> None:
    task_id = (
        f"TASK-AR-660-UNIT-COLLISION-{operation.upper()}-"
        f"{colliding_field.upper()}"
    )
    suffix = f"unit-collision-{operation}-{colliding_field}"
    if operation == "create":
        (tmp_path / "STATUS.md").write_text(
            "## Handoff Checklist\n- continue here\n",
            encoding="utf-8",
        )
        _write_worktree(tmp_path, task_id)
        _task_path, _unit_path, unit_id, unit_rel = (
            _write_work_identity_records(tmp_path, task_id)
        )
        _write_duplicate_unit_alias(
            tmp_path,
            task_id,
            colliding_field=colliding_field,
        )
        result = _run_dispatcher(
            tmp_path,
            "create",
            "--task-id",
            task_id,
            "--unit-id",
            unit_id,
            "--unit-spec",
            unit_rel,
            "--stop-condition",
            f"stop_after:{unit_id}:verification",
            "--agent-role",
            "lead-engineer",
            "--agent-instance-id",
            f"le-20260809-110000-kst-{suffix}",
            "--callsite-id",
            f"terminal:wt-{task_id.lower()}:tab-01",
            "--lease-minutes",
            "30",
            "--now",
            "2026-08-09T11:00:00+09:00",
            "--suffix",
            suffix,
            "--json",
        )
        assert result.returncode != 0, (
            f"create accepted duplicate canonical unit {colliding_field}"
        )
        diagnostic = (result.stdout + result.stderr).lower()
        assert any(
            token in diagnostic
            for token in ("identity", "canonical", "duplicate", "unit")
        )
        assert not list(
            (tmp_path / "agents/runtime/task_claims").glob("CLAIM-*.json")
        )
        return

    created, _task_path, _unit_path = _create_work_identity_candidate(
        tmp_path,
        task_id=task_id,
        suffix=suffix,
    )
    claim = created["claim"]
    path = _claim_path(tmp_path, created)
    if operation == "adopt":
        persisted = json.loads(path.read_text(encoding="utf-8"))
        persisted.pop("work_identity_binding")
        path.write_text(
            json.dumps(persisted, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        args = (
            "adopt",
            "--claim-id",
            str(claim["claim_id"]),
            "--owner-id",
            _OWNER,
            "--actor-instance-id",
            _recovery_actor_id(tmp_path),
            "--reason",
            "duplicate unit authority must not be adopted",
            "--now",
            "2026-08-09T09:10:00+09:00",
            "--json",
        )
    else:
        args = _work_identity_mutation_args(tmp_path, claim, operation)
    _write_duplicate_unit_alias(
        tmp_path,
        task_id,
        colliding_field=colliding_field,
    )
    before = path.read_bytes()

    result = _run_dispatcher(tmp_path, *args)

    assert result.returncode != 0, (
        f"{operation} accepted duplicate canonical unit {colliding_field}"
    )
    diagnostic = (result.stdout + result.stderr).lower()
    assert any(token in diagnostic for token in ("identity", "canonical", "unit"))
    assert path.read_bytes() == before


def test_unit_namespace_scan_refuses_aliased_sibling_record(
    tmp_path: Path,
) -> None:
    dispatcher = _load_dispatcher_module()
    task_id = "TASK-AR-660-UNIT-NAMESPACE-ALIAS"
    _task_path, _unit_path, unit_id, unit_rel = _write_work_identity_records(
        tmp_path,
        task_id,
    )
    alternate = _write_duplicate_unit_alias(
        tmp_path,
        task_id,
        colliding_field="work_id",
    )
    outside = tmp_path.parent / f"{tmp_path.name}-unit-sibling.md"
    outside.write_bytes(alternate.read_bytes())
    alternate.unlink()
    alternate.symlink_to(outside)

    with pytest.raises(ValueError, match="alias|symlink|direct|identity"):
        dispatcher._canonical_unit_work_uid(
            tmp_path,
            task_id=task_id,
            unit_id=unit_id,
            unit_spec=unit_rel,
        )
