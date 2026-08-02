from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pytest

from agent_runtime import knowledge_records


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "task_claim_dispatcher.py"
GATE = REPO_ROOT / "scripts" / "parallel_worktree_gate.py"
CONCURRENCY_GATE = REPO_ROOT / "scripts" / "collaboration_concurrency_gate.py"
IDENTITY_GATE = REPO_ROOT / "scripts" / "agent_identity_gate.py"


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


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), "--root", str(root), "--check"],
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


def _write_worktree(root: Path, task_id: str) -> None:
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
) -> subprocess.CompletedProcess[str]:
    return _run_dispatcher(
        linked,
        "create",
        "--task-id",
        f"TASK-AR-{suffix}",
        "--worktree-path",
        ".",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T08:00:00+09:00",
        "--suffix",
        suffix,
        "--json",
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
            + "[" * 1100
            + "0"
            + "]" * 1100
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
    assert not (linked / "agents").exists()

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
    task_path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "\n".join(
            [
                "---",
                f"work_id: {task_id}",
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
        f"unit_id: {unit_id}",
        f"task_id: {task_id}",
        f"model_tier: {worker_tier}",
        "target_files:",
        "  - scripts/routing_target.py",
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
    assert claim["task_set_id"] == ""
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

    gate = _run_gate(tmp_path)
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
    _write_worktree(tmp_path, "TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--task-set-id",
        "TASKSET-AR-PROJECTION",
        "--unit-id",
        "UNIT-TASK-AR-246-001",
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

    result = _run_dispatcher(tmp_path, "projection", "--claim-id", claim["claim_id"], "--json")

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


def test_projection_rejects_released_or_overlay_claims(tmp_path: Path):
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
    overlay = _run_dispatcher(tmp_path, "projection", "--claim-id", claim["claim_id"], "--json")
    assert overlay.returncode == 1
    assert "does not apply to overlay claim" in overlay.stderr


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
    _write_worktree(tmp_path, "TASK-AR-248")

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
    _write_worktree(tmp_path, "TASK-AR-344")

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
    _write_worktree(tmp_path, "TASK-AR-248")
    _write_worktree(tmp_path, "TASK-AR-249")
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


def test_explicit_target_files_are_unioned_with_registered_unit_footprint(
    tmp_path: Path,
) -> None:
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

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["target_files"] == ["README.md", "scripts/routing_target.py"]


def test_create_claim_normalizes_new_targets_and_surfaces_matching_compound(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    _write_worktree(tmp_path, "TASK-AR-645")
    task_path = tmp_path / "agents/lead_engineer/tasks/TASK-AR-645.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "---\nwork_id: TASK-AR-645\ndefect_signatures:\n"
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
        "---\nunit_id: UNIT-TASK-AR-645-001\ntask_id: TASK-AR-645\n"
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
    _write_worktree(tmp_path, "TASK-AR-328")

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
            "overlay",
            lambda claim: claim.update(overlay=True),
            "2026-08-03T09:10:00+09:00",
            0,
            "",
            "",
            "overlay",
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
        ("overlay", lambda claim: claim.update(overlay=True), "2026-08-03T09:10:00+09:00", 0),
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
