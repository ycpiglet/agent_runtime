from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wave_dispatcher as dispatcher  # noqa: E402


TASKSET = "TASKSET-DYNAMIC-WAVE"
PROJECT = "PROJECT-WAVE-TEST"


def _write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_taskset(
    root: Path,
    taskset: str = TASKSET,
    *,
    filename: str | None = None,
    schema: str = "agent-runtime-work-item/v1",
    kind: str = "taskset",
    title: str = "Dynamic Wave",
    status: str | None = None,
) -> None:
    status_line = [f"status: {status}"] if status is not None else []
    _write(
        root / "agents/project/initiatives" / f"{filename or taskset}.md",
        [
            "---",
            f"schema_version: {schema}",
            f"work_id: {taskset}",
            f"kind: {kind}",
            f"title: {title}",
            *status_line,
            "summary: Test lane.",
            "---",
        ],
    )


def _write_task(
    root: Path,
    task: str,
    *,
    taskset: str = TASKSET,
    status: str = "planned",
) -> None:
    _write(
        root / "agents/lead_engineer/tasks" / f"{task}.md",
        [
            "---",
            f"id: {task}",
            f"status: {status}",
            "priority: P1",
            "difficulty: M",
            "est_hours: 2",
            "est_tokens: 200",
            f"task_set_id: {taskset}",
            f"project_id: {PROJECT}",
            "tags: [test]",
            "---",
        ],
    )


def _write_unit(
    root: Path,
    task: str,
    index: int = 1,
    *,
    taskset: str = TASKSET,
    targets: list[str] | None = None,
    depends: list[str] | None = None,
    status: str = "worker_ready",
    metadata: dict[str, object] | None = None,
) -> str:
    unit = f"UNIT-{task}-{index:03d}"
    fields: dict[str, object] = {
        "unit_id": unit,
        "task_id": task,
        "task_set_id": taskset,
        "project_id": PROJECT,
        "status": status,
        "model_tier": "worker_standard",
        "context": "Wave dispatcher fixture.",
        "inputs": ["README.md"],
        "target_files": targets or [f"scripts/{task.lower()}.py"],
        "scope": "Exercise dispatcher behavior.",
        "acceptance": ["Dispatcher contract holds."],
        "verification": ["pytest"],
        "handoff": "Test assertion is the evidence.",
        "stop_condition": f"stop_after:{unit}:no_adjacent_taskset",
    }
    if depends:
        fields["depends_on"] = depends
    fields.update(metadata or {})
    encoded = [
        f"{key}: [{', '.join(value)}]" if isinstance(value, list) else f"{key}: {value}"
        for key, value in fields.items()
    ]
    _write(
        root / "agents/lead_engineer/tasks/units" / task / f"{unit}.md",
        [
            "---",
            *encoded,
            "---",
            "",
            "## Context",
            "",
            "Wave dispatcher fixture.",
            "",
            "## Inputs",
            "",
            "- README.md",
            "",
            "## Target Files",
            "",
            "- Declared in frontmatter.",
            "",
            "## Scope",
            "",
            "Exercise dispatcher behavior.",
            "",
            "## Steps",
            "",
            "1. Run the dispatcher.",
            "",
            "## Acceptance Criteria",
            "",
            "- Dispatcher contract holds.",
            "",
            "## Verification",
            "",
            "- pytest",
            "",
            "## Handoff",
            "",
            "Test assertion is the evidence.",
            "",
            "## Stop Boundary",
            "",
            "Stop after the declared unit.",
        ],
    )
    return unit


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "wave_dispatcher.py"), "--root", str(root), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _tree_snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
    directories = tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return directories, files


def _write_t0(root: Path, taskset: str, anchor: str = "README.md") -> None:
    target = root / anchor
    payload = {
        "schema": "agent-runtime-plan-assumptions/v1",
        "updated_at": "2026-07-14T18:49:00+09:00",
        "assumption_sets": [
            {
                "taskset_id": taskset,
                "design_record": anchor,
                "recorded_at": "2026-07-14T18:49:00+09:00",
                "revalidation_policy": "block_dispatch_on_drift",
                "anchors": [
                    {
                        "path": anchor,
                        "kind": "sha256",
                        "value": hashlib.sha256(target.read_bytes()).hexdigest(),
                    }
                ],
            }
        ],
    }
    _write(
        root / "agents/project/work-items/PLAN-ASSUMPTIONS.json",
        [json.dumps(payload, ensure_ascii=False, indent=2)],
    )


def _init_repo(root: Path) -> None:
    def git(*args: str) -> int:
        return subprocess.run(["git", "-C", str(root), *args], check=False).returncode

    assert git("init", "-q") == 0
    assert git("config", "user.email", "wave-test@example.com") == 0
    assert git("config", "user.name", "Wave Test") == 0
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    assert git("add", "-A") == git("commit", "-q", "-m", "init") == 0
    assert git("update-ref", "refs/remotes/origin/main", "HEAD") == 0


def test_plan_resolves_canonical_id_and_slug_to_same_validated_units(tmp_path: Path) -> None:
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901")
    unit_id = _write_unit(tmp_path, "TASK-901")

    canonical = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")
    slug = _run(tmp_path, "--taskset", "dynamic-wave", "--plan", "--json")

    assert canonical.returncode == slug.returncode == 0
    first, second = json.loads(canonical.stdout), json.loads(slug.stdout)
    assert first == second
    unit = first["waves"][0][0]
    assert first["selection"] == f"taskset:{TASKSET}"
    assert unit["unit_id"] == unit_id
    assert unit["repository_path"] == str(tmp_path.resolve())
    assert unit["worktree_path"] == ".worktrees/TASK-901"
    assert unit["base_ref"] == ""


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [({"schema": "wrong/v1"}, "schema_version"), ({"kind": "initiative"}, "kind"),
     ({"filename": "TASKSET-WRONG"}, "filename")],
)
def test_plan_rejects_malformed_canonical_taskset(
    tmp_path: Path, kwargs: dict[str, str], message: str
) -> None:
    _write_taskset(tmp_path, **kwargs)
    _write_task(tmp_path, "TASK-901")
    _write_unit(tmp_path, "TASK-901")
    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")
    assert result.returncode == 1
    assert "invalid canonical task set record" in result.stderr
    assert message in result.stderr


def test_plan_rejects_duplicate_canonical_aliases(tmp_path: Path) -> None:
    _write_taskset(tmp_path, "TASKSET-ONE", title="Shared Lane")
    _write_taskset(tmp_path, "TASKSET-TWO", title="Shared Lane")
    result = _run(tmp_path, "--taskset", "TASKSET-ONE", "--plan", "--json")
    assert result.returncode == 1
    assert "duplicate task set alias" in result.stderr


def test_plan_rejects_duplicate_unit_id_from_different_paths_without_mutation(
    tmp_path: Path,
) -> None:
    _write_taskset(tmp_path)
    for task in ("TASK-900", "TASK-901"):
        _write_task(tmp_path, task)
    duplicate_id = _write_unit(tmp_path, "TASK-900")
    _write_unit(
        tmp_path,
        "TASK-901",
        metadata={"unit_id": duplicate_id},
    )
    before = _tree_snapshot(tmp_path)

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 1
    assert "registry:duplicate-unit-id" in result.stderr
    assert duplicate_id in result.stderr
    assert "UNIT-TASK-900-001.md" in result.stderr
    assert "UNIT-TASK-901-001.md" in result.stderr
    assert _tree_snapshot(tmp_path) == before


def test_plan_rejects_duplicate_task_id_from_different_paths_without_mutation(
    tmp_path: Path,
) -> None:
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-900")
    canonical = tmp_path / "agents/lead_engineer/tasks/TASK-900.md"
    duplicate = tmp_path / "agents/lead_engineer/tasks/TASK-DUPLICATE.md"
    duplicate.write_bytes(canonical.read_bytes())
    _write_unit(tmp_path, "TASK-900")
    before = _tree_snapshot(tmp_path)

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 1
    assert "registry:duplicate-task-id" in result.stderr
    assert "TASK-900" in result.stderr
    assert "TASK-900.md" in result.stderr
    assert "TASK-DUPLICATE.md" in result.stderr
    assert _tree_snapshot(tmp_path) == before


def test_plan_deduplicates_same_unit_path_selected_twice(tmp_path: Path) -> None:
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901")
    unit_id = _write_unit(tmp_path, "TASK-901")

    result = _run(
        tmp_path,
        "--unit",
        unit_id,
        "--unit",
        unit_id,
        "--plan",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert [[unit["unit_id"] for unit in wave] for wave in payload["waves"]] == [
        [unit_id]
    ]


def test_compute_waves_allows_same_path_duplicate_registry_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901")
    unit_id = _write_unit(tmp_path, "TASK-901")
    node = dispatcher._all_units(tmp_path)[0]
    task = dispatcher.backlog_board.load_tasks(
        tmp_path / "agents/lead_engineer/tasks"
    )[0]
    monkeypatch.setattr(
        dispatcher.backlog_board,
        "load_tasks",
        lambda _tasks_dir: [task, task],
    )

    plan = dispatcher.compute_waves(tmp_path, [node, node])

    assert [item.unit_id for item in plan.nodes] == [unit_id]
    assert [[item.unit_id for item in wave] for wave in plan.waves] == [[unit_id]]


def _external(root: Path) -> tuple[dict[str, object], Path, Path]:
    repo = (root / "external").resolve()
    repo.mkdir()
    worktree = repo / ".worktrees/TASK-901"
    return {
        "repository_path": str(repo),
        "worktree_path": str(worktree),
        "branch": "fix/task-901",
        "base_ref": "origin/main",
    }, repo, worktree


def test_plan_uses_complete_structured_external_tuple(tmp_path: Path) -> None:
    metadata, repo, worktree = _external(tmp_path)
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901")
    _write_unit(tmp_path, "TASK-901", metadata=metadata)
    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")
    unit = json.loads(result.stdout)["waves"][0][0]
    assert result.returncode == 0
    assert (unit["repository_path"], unit["worktree_path"], unit["branch"], unit["base_ref"]) == (
        str(repo), str(worktree), "fix/task-901", "origin/main"
    )
    assert unit["adopt_existing_branch"] is False


def test_plan_and_dispatch_payload_preserve_adopt_existing_branch(tmp_path: Path) -> None:
    metadata, repo, _worktree = _external(tmp_path)
    _init_repo(repo)
    metadata["adopt_existing_branch"] = True
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901")
    _write_unit(tmp_path, "TASK-901", metadata=metadata)

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["waves"][0][0]["adopt_existing_branch"] is True
    node = _node(tmp_path, metadata=metadata)
    payload = dispatcher._dispatch_payload(
        tmp_path,
        node,
        wave_no=1,
        args=_args(tmp_path),
        allow_parallel_task_set=False,
        suffix=None,
    )
    assert payload["adopt_existing_branch"] is True


@pytest.mark.parametrize("missing", ["repository_path", "worktree_path", "branch", "base_ref"])
def test_plan_rejects_partial_structured_tuple(tmp_path: Path, missing: str) -> None:
    metadata, _, _ = _external(tmp_path)
    metadata.pop(missing)
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901")
    _write_unit(tmp_path, "TASK-901", metadata=metadata)
    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")
    assert result.returncode == 1
    assert missing in result.stderr
    assert "structured worktree metadata must define all fields" in result.stderr


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ({"repository_path": "/tmp/repo", "worktree_path": "/tmp/out/TASK-901",
          "branch": "fix/task", "base_ref": "origin/main"}, "worktree_path must be under"),
        ({"repository_path": "/tmp/repo", "worktree_path": "/tmp/repo/.worktrees/TASK-901",
          "branch": "main", "base_ref": "origin/main"}, "protected branch"),
        ({"repository_path": "/tmp/repo", "worktree_path": "/tmp/repo/.worktrees/TASK-901",
          "branch": "fix/task", "base_ref": "--unsafe"}, "unsafe base_ref"),
    ],
)
def test_plan_rejects_unsafe_structured_tuple(
    tmp_path: Path, metadata: dict[str, str], message: str
) -> None:
    repository = str((tmp_path / "repository").resolve())
    outside = str((tmp_path / "outside").resolve())
    metadata = {
        key: value.replace("/tmp/repo", repository).replace("/tmp/out", outside)
        for key, value in metadata.items()
    }
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901")
    _write_unit(tmp_path, "TASK-901", metadata=metadata)
    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")
    assert result.returncode == 1
    assert message in result.stderr


def test_plan_preserves_static_alias_explicit_dag_and_footprint(tmp_path: Path) -> None:
    taskset = "TASKSET-AR-QUALITY-LOOP"
    for task in ("TASK-AR-901", "TASK-AR-902"):
        _write_task(tmp_path, task, taskset=taskset)
    first = _write_unit(tmp_path, "TASK-AR-901", taskset=taskset, targets=["shared.py"])
    second = _write_unit(tmp_path, "TASK-AR-902", taskset=taskset, targets=["shared.py"])
    alias = _run(tmp_path, "--taskset", "quality-loop", "--plan", "--json")
    explicit = _run(tmp_path, "--unit", first, "--unit", second, "--plan", "--json")
    assert alias.returncode == explicit.returncode == 0
    assert [[u["unit_id"] for u in wave] for wave in json.loads(alias.stdout)["waves"]] == [
        [first], [second]
    ]
    assert json.loads(explicit.stdout)["deferrals"][0]["conflicts_with"] == first


def test_status_preserves_wave_boundary_guidance(tmp_path: Path) -> None:
    _write_taskset(tmp_path)
    _write_task(tmp_path, "TASK-901", status="completed")
    _write_task(tmp_path, "TASK-902")
    first = _write_unit(tmp_path, "TASK-901", status="completed")
    second = _write_unit(tmp_path, "TASK-902", depends=[first])
    result = _run(tmp_path, "--taskset", TASKSET, "--status", "--json")
    payload = json.loads(result.stdout)
    assert payload["current_wave"] == 2
    assert payload["waves"][1]["unit_states"][second] == "pending"
    assert {line.split(":", 1)[0] for line in payload["guidance"]} == {
        "wave-boundary", "full-cycle"
    }


def _cross_taskset_dependency_fixture(
    root: Path,
    *,
    upstream_status: str = "worker_ready",
) -> tuple[str, str, str]:
    upstream_taskset = "TASKSET-WAVE-UPSTREAM"
    downstream_taskset = "TASKSET-WAVE-DOWNSTREAM"
    _write_taskset(root, upstream_taskset, title="Wave Upstream")
    _write_taskset(root, downstream_taskset, title="Wave Downstream")
    _write_task(root, "TASK-900", taskset=upstream_taskset)
    _write_task(root, "TASK-901", taskset=downstream_taskset)
    upstream = _write_unit(
        root,
        "TASK-900",
        taskset=upstream_taskset,
        status=upstream_status,
    )
    downstream = _write_unit(
        root,
        "TASK-901",
        taskset=downstream_taskset,
        depends=[upstream],
    )
    return upstream_taskset, downstream_taskset, upstream


def test_plan_refuses_unresolved_external_unit_dependency_without_mutation(
    tmp_path: Path,
) -> None:
    _upstream_taskset, downstream_taskset, upstream = (
        _cross_taskset_dependency_fixture(tmp_path)
    )
    before = _tree_snapshot(tmp_path)

    result = _run(tmp_path, "--taskset", downstream_taskset, "--plan", "--json")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "dependency:external-unresolved" in result.stderr
    assert f"ref={upstream}" in result.stderr
    assert "status=worker_ready" in result.stderr
    assert _tree_snapshot(tmp_path) == before


def test_dispatch_refuses_unresolved_external_dependency_before_subprocess_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _upstream_taskset, downstream_taskset, upstream = (
        _cross_taskset_dependency_fixture(tmp_path)
    )
    before = _tree_snapshot(tmp_path)
    calls: list[list[str]] = []

    def forbidden_subprocess(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        pytest.fail("external dependency refusal must happen before subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)
    args = _args(tmp_path)
    args.taskset = downstream_taskset

    with pytest.raises(dispatcher.WaveError):
        dispatcher.cmd_dispatch(args)

    assert calls == []
    stderr = capsys.readouterr().err
    assert "dependency:external-unresolved" in stderr
    assert upstream in stderr
    assert _tree_snapshot(tmp_path) == before


def _write_released_claim(root: Path, *, task_id: str, unit_id: str) -> None:
    claim = {
        "claim_id": "CLAIM-released-external",
        "task_id": task_id,
        "unit_id": unit_id,
        "status": "released",
    }
    _write(
        root / "agents/runtime/task_claims/CLAIM-released-external.json",
        [json.dumps(claim)],
    )


def test_plan_released_external_unit_remains_unresolved_until_canonical_completion(
    tmp_path: Path,
) -> None:
    _upstream_taskset, downstream_taskset, upstream = (
        _cross_taskset_dependency_fixture(tmp_path, upstream_status="in_progress")
    )
    _write_released_claim(tmp_path, task_id="TASK-900", unit_id=upstream)
    before = _tree_snapshot(tmp_path)

    result = _run(tmp_path, "--taskset", downstream_taskset, "--plan", "--json")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "dependency:external-unresolved" in result.stderr
    assert f"ref={upstream}" in result.stderr
    assert "status=in_progress" in result.stderr
    assert _tree_snapshot(tmp_path) == before


def test_dispatch_released_external_unit_remains_unresolved_before_subprocess_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _upstream_taskset, downstream_taskset, upstream = (
        _cross_taskset_dependency_fixture(tmp_path, upstream_status="in_progress")
    )
    _write_released_claim(tmp_path, task_id="TASK-900", unit_id=upstream)
    before = _tree_snapshot(tmp_path)
    calls: list[list[str]] = []

    def forbidden_subprocess(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        pytest.fail("released external dependency must fail before subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)
    args = _args(tmp_path)
    args.taskset = downstream_taskset

    with pytest.raises(dispatcher.WaveError):
        dispatcher.cmd_dispatch(args)

    assert calls == []
    stderr = capsys.readouterr().err
    assert "dependency:external-unresolved" in stderr
    assert f"ref={upstream}" in stderr
    assert "status=in_progress" in stderr
    assert _tree_snapshot(tmp_path) == before


def test_dispatch_explicit_cross_taskset_released_upstream_waits_for_w5(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    upstream_taskset, downstream_taskset, upstream = (
        _cross_taskset_dependency_fixture(tmp_path, upstream_status="worker_ready")
    )
    _init_repo(tmp_path)
    _write_t0(tmp_path, downstream_taskset)
    for target in ("scripts/task-900.py", "scripts/task-901.py"):
        target_path = tmp_path / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("fixture\n", encoding="utf-8")
    downstream = "UNIT-TASK-901-001"
    _write_released_claim(tmp_path, task_id="TASK-900", unit_id=upstream)
    before = _tree_snapshot(tmp_path)
    calls: list[list[str]] = []

    def forbidden_subprocess(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        pytest.fail("cross-taskset W5 barrier must fail before subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)
    args = _args(tmp_path)
    args.taskset = ""
    args.unit = [upstream, downstream]

    with pytest.raises(dispatcher.WaveError):
        dispatcher.cmd_dispatch(args)

    assert calls == []
    stderr = capsys.readouterr().err
    assert "dependency:external-unresolved" in stderr
    assert f"unit={downstream} ref={upstream}" in stderr
    assert "status=worker_ready" in stderr
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize("completed_status", ["completed", "완료"])
def test_dispatch_explicit_cross_taskset_completed_upstream_allows_downstream(
    tmp_path: Path,
    completed_status: str,
) -> None:
    _upstream_taskset, downstream_taskset, upstream = (
        _cross_taskset_dependency_fixture(
            tmp_path,
            upstream_status=completed_status,
        )
    )
    _init_repo(tmp_path)
    _write_t0(tmp_path, downstream_taskset)
    for target in ("scripts/task-900.py", "scripts/task-901.py"):
        target_path = tmp_path / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("fixture\n", encoding="utf-8")
    _write_released_claim(tmp_path, task_id="TASK-900", unit_id=upstream)

    result = _run(
        tmp_path,
        "--unit",
        upstream,
        "--unit",
        "UNIT-TASK-901-001",
        "--dispatch",
        "--now",
        "2026-07-27T19:00:00+09:00",
        "--suffix",
        f"w5-{completed_status}",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert [item["unit_id"] for item in payload["issued"]] == [
        "UNIT-TASK-901-001"
    ]


@pytest.mark.parametrize(
    ("second_task_status", "second_unit_status", "message"),
    [
        ("planned", "planned", "unit:not-worker-ready:planned"),
        ("held", "worker_ready", "task:blocked-status:held"),
        ("unblocked/R3", "planned", "unit:not-worker-ready:planned"),
    ],
)
def test_dispatch_preflights_entire_mixed_batch_before_subprocess_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    second_task_status: str,
    second_unit_status: str,
    message: str,
) -> None:
    _init_repo(tmp_path)
    _write_taskset(tmp_path)
    _write_t0(tmp_path, TASKSET)
    _write_task(tmp_path, "TASK-901")
    _write_unit(tmp_path, "TASK-901", targets=["TASK-901.py"])
    _write_task(tmp_path, "TASK-902", status=second_task_status)
    _write_unit(
        tmp_path,
        "TASK-902",
        status=second_unit_status,
        targets=["TASK-902.py"],
    )
    for target in ("TASK-901.py", "TASK-902.py"):
        (tmp_path / target).write_text("fixture\n", encoding="utf-8")
    before = _tree_snapshot(tmp_path)
    calls: list[list[str]] = []

    def forbidden_subprocess(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        pytest.fail("batch preflight must happen before every subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)
    args = _args(tmp_path, mode="parallel")
    args.taskset = TASKSET
    args.now = "2026-07-14T21:00:00+09:00"
    args.suffix = "mixed"

    with pytest.raises(dispatcher.WaveError):
        dispatcher.cmd_dispatch(args)

    assert calls == []
    stderr = capsys.readouterr().err
    assert message in stderr
    if second_task_status == "unblocked/R3":
        assert "blocked-status:unblocked/R3" not in stderr
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    ("task_status", "taskset_status", "message"),
    [
        ("blocked/R3", "active", "task:blocked-status:blocked/R3"),
        ("planned", "blocked/R3", "taskset:blocked-status:blocked/R3"),
    ],
)
def test_dispatch_refuses_composite_blocked_parent_before_subprocess_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    task_status: str,
    taskset_status: str,
    message: str,
) -> None:
    _init_repo(tmp_path)
    _write_taskset(tmp_path, status=taskset_status)
    _write_t0(tmp_path, TASKSET)
    _write_task(tmp_path, "TASK-901", status=task_status)
    _write_unit(tmp_path, "TASK-901", targets=["TASK-901.py"])
    (tmp_path / "TASK-901.py").write_text("fixture\n", encoding="utf-8")
    before = _tree_snapshot(tmp_path)
    calls: list[list[str]] = []

    def forbidden_subprocess(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        pytest.fail("composite blocked parent must fail before subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)
    args = _args(tmp_path)
    args.taskset = TASKSET

    with pytest.raises(dispatcher.WaveError):
        dispatcher.cmd_dispatch(args)

    assert calls == []
    assert message in capsys.readouterr().err
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize("active_status", ["claimed", "active", "running"])
def test_dispatch_preflights_all_candidate_footprints_before_batch_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    active_status: str,
) -> None:
    _init_repo(tmp_path)
    _write_taskset(tmp_path)
    _write_t0(tmp_path, TASKSET)
    for task in ("TASK-901", "TASK-902"):
        _write_task(tmp_path, task)
        _write_unit(tmp_path, task, targets=[f"{task}.py"])
        (tmp_path / f"{task}.py").write_text("fixture\n", encoding="utf-8")
    active_claim = {
        "claim_id": "CLAIM-existing-footprint",
        "task_id": "TASK-900",
        "unit_id": "UNIT-TASK-900-001",
        "status": active_status,
        "target_files": ["TASK-902.py"],
    }
    _write(
        tmp_path / "agents/runtime/task_claims/CLAIM-existing-footprint.json",
        [json.dumps(active_claim)],
    )
    before = _tree_snapshot(tmp_path)
    calls: list[list[str]] = []

    def forbidden_subprocess(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        pytest.fail("footprint preflight must happen before every subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)
    args = _args(tmp_path, mode="parallel")
    args.taskset = TASKSET
    args.now = "2026-07-14T21:00:00+09:00"
    args.suffix = "footprint"

    with pytest.raises(dispatcher.WaveError):
        dispatcher.cmd_dispatch(args)

    assert calls == []
    assert "footprint:active-claim-conflict:CLAIM-existing-footprint" in (
        capsys.readouterr().err
    )
    assert _tree_snapshot(tmp_path) == before


def test_plan_orders_explicit_cross_taskset_dependency() -> None:
    root = Path("/virtual")
    upstream = dispatcher.UnitNode(
        root / "UNIT-TASK-900-001.md",
        {
            "unit_id": "UNIT-TASK-900-001",
            "task_id": "TASK-900",
            "task_set_id": "TASKSET-WAVE-UPSTREAM",
            "status": "worker_ready",
            "target_files": ["upstream.py"],
        },
    )
    downstream = dispatcher.UnitNode(
        root / "UNIT-TASK-901-001.md",
        {
            "unit_id": "UNIT-TASK-901-001",
            "task_id": "TASK-901",
            "task_set_id": "TASKSET-WAVE-DOWNSTREAM",
            "status": "worker_ready",
            "target_files": ["downstream.py"],
            "depends_on": [upstream.unit_id],
        },
    )

    plan = dispatcher.compute_waves(root, [upstream, downstream])

    assert [[node.unit_id for node in wave] for wave in plan.waves] == [
        [upstream.unit_id],
        [downstream.unit_id],
    ]
    assert plan.external_deps == [(downstream.unit_id, upstream.unit_id)]


@pytest.mark.parametrize("completed_status", ["completed", "완료"])
def test_plan_accepts_completed_external_unit_dependency(
    tmp_path: Path,
    completed_status: str,
) -> None:
    _upstream_taskset, downstream_taskset, upstream = (
        _cross_taskset_dependency_fixture(tmp_path, upstream_status=completed_status)
    )
    _write_released_claim(tmp_path, task_id="TASK-900", unit_id=upstream)

    result = _run(tmp_path, "--taskset", downstream_taskset, "--plan", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert [[unit["unit_id"] for unit in wave] for wave in payload["waves"]] == [
        ["UNIT-TASK-901-001"]
    ]
    assert payload["external_deps"] == [
        {"unit_id": "UNIT-TASK-901-001", "ref": upstream}
    ]


@pytest.mark.parametrize(
    ("mode", "panes", "expected"),
    [("cascade", "1", ["TASK-901"]), ("parallel", "2", ["TASK-901", "TASK-902"])],
)
def test_dispatch_preserves_cascade_and_parallel_contracts(
    tmp_path: Path, mode: str, panes: str, expected: list[str]
) -> None:
    _init_repo(tmp_path)
    _write_taskset(tmp_path)
    _write_t0(tmp_path, TASKSET)
    for task in ("TASK-901", "TASK-902"):
        _write_task(tmp_path, task)
        _write_unit(tmp_path, task, targets=[f"{task}.py"])
        (tmp_path / f"{task}.py").write_text("fixture\n", encoding="utf-8")
    result = _run(
        tmp_path, "--taskset", TASKSET, "--dispatch", "--mode", mode,
        "--max-panes", panes, "--now", "2026-07-14T21:00:00+09:00",
        "--suffix", mode, "--json",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert [item["task_id"] for item in payload["issued"]] == expected
    claims = [json.loads(path.read_text()) for path in
              (tmp_path / "agents/runtime/task_claims").glob("*.json")]
    assert {claim["mode"] for claim in claims} == {"orchestrator"}
    assert {claim["task_id"] for claim in claims} == set(expected)
    assert all((tmp_path / item["worktree_path"] / ".git").exists() for item in payload["issued"])


def _args(root: Path, mode: str = "cascade") -> argparse.Namespace:
    return argparse.Namespace(
        root=root, taskset=TASKSET, unit=[], mode=mode, max_panes=2,
        agent_role="", team_id="", now=None, suffix=None, json=True,
    )


def _node(
    root: Path,
    task: str = "TASK-901",
    metadata: dict[str, object] | None = None,
) -> dispatcher.UnitNode:
    unit = f"UNIT-{task}-001"
    meta: dict[str, object] = {
        "unit_id": unit, "task_id": task, "task_set_id": TASKSET,
        "project_id": PROJECT, "status": "worker_ready", "model_tier": "worker_standard",
        "target_files": [f"{task}.py"], "stop_condition": f"stop_after:{unit}",
    }
    meta.update(metadata or {})
    return dispatcher.UnitNode(root / f"{unit}.md", meta)


def _prepare(monkeypatch: pytest.MonkeyPatch, root: Path, nodes: list[dispatcher.UnitNode]) -> None:
    plan = dispatcher.WavePlan(nodes, [nodes], [])
    monkeypatch.setattr(dispatcher, "select_units", lambda *_a, **_k: (nodes, f"taskset:{TASKSET}"))
    monkeypatch.setattr(dispatcher, "compute_waves", lambda *_a, **_k: plan)
    monkeypatch.setattr(dispatcher, "_load_claims", lambda _root: [])
    monkeypatch.setattr(dispatcher, "_candidate_preflight_findings", lambda *_a, **_k: [])
    monkeypatch.setattr(dispatcher, "role_routing", None)


def _claim_result(
    root: Path, node: dispatcher.UnitNode, worktree: Path, *, persist: bool = True,
    returncode: int = 0, stdout: str | None = None,
    persisted: dict[str, str] | None = None, declared: dict[str, str] | None = None,
    path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if returncode:
        return subprocess.CompletedProcess(["claim"], returncode, "", "claim refused\n")
    claim_id = f"CLAIM-test-{node.task_id.lower()}"
    claim_path = path or root / "agents/runtime/task_claims" / f"{claim_id}.json"
    claim = {
        "claim_id": claim_id, "task_id": node.task_id, "task_set_id": node.task_set_id,
        "unit_id": node.unit_id, "project_id": node.project_id, "status": "claimed",
        "mode": "orchestrator", "worktree_path": str(worktree), "branch": "fix/task-901",
    }
    claim.update(persisted or {})
    if persist:
        _write(claim_path, [json.dumps(claim)])
    response = {**claim, **(declared or {})}
    envelope = {
        "status": "created",
        "path": claim_path.relative_to(root).as_posix() if claim_path.is_relative_to(root) else str(claim_path),
        "claim": response,
    }
    return subprocess.CompletedProcess(["claim"], 0, stdout or json.dumps(envelope), "")


def _success_runner(
    root: Path, node: dispatcher.UnitNode, worktree: Path,
    calls: list[tuple[str, Path]], *, fail_git: bool = False,
):
    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command[0], Path(str(kwargs["cwd"]))))
        if command[0] != "git":
            return _claim_result(root, node, worktree)
        if fail_git:
            return subprocess.CompletedProcess(command, 23, "", "worktree failed\n")
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: fake\n")
        return subprocess.CompletedProcess(command, 0, "", "")
    return run


def test_claim_command_uses_orchestrator_reservation_mode(tmp_path: Path) -> None:
    command = dispatcher._claim_command(
        tmp_path, _node(tmp_path), wave_no=1, worktree_path=".worktrees/TASK-901",
        branch="fix/task-901", args=_args(tmp_path), allow_parallel_task_set=False, suffix=None,
    )
    assert command[command.index("--mode") + 1] == "orchestrator"
    assert command[-1] == "--json"


def test_dispatch_preflights_all_candidates_before_claim_or_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nodes = [_node(tmp_path), _node(tmp_path, "TASK-902", {"repository_path": "/tmp/repo"})]
    _prepare(monkeypatch, tmp_path, nodes)
    calls: list[list[str]] = []
    monkeypatch.setattr(dispatcher.subprocess, "run", lambda command, **_k: calls.append(command))
    with pytest.raises(SystemExit, match="structured worktree metadata must define all fields"):
        dispatcher.cmd_dispatch(_args(tmp_path, "parallel"))
    assert calls == []


FAILURES = [
    ("process", "claim refused"), ("json", "invalid JSON"),
    ("missing", "persisted claim is missing"), ("inactive", "not active"),
    ("task", "field mismatch: task_id"), ("taskset", "field mismatch: task_set_id"),
    ("unit", "field mismatch: unit_id"), ("project", "field mismatch: project_id"),
    ("worktree", "field mismatch: worktree_path"), ("branch", "field mismatch: branch"),
    ("mode", "field mismatch: mode"), ("status", "field mismatch: status"),
    ("path", "field mismatch: path"), ("outside", "persisted claim path is outside"),
]


@pytest.mark.parametrize(("case", "message"), FAILURES)
def test_claim_failures_never_run_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    case: str, message: str,
) -> None:
    metadata, _, worktree = _external(tmp_path)
    node = _node(tmp_path, metadata=metadata)
    _prepare(monkeypatch, tmp_path, [node])
    bad = {
        "task": ("task_id", "TASK-X", node.task_id),
        "taskset": ("task_set_id", "TASKSET-X", node.task_set_id),
        "unit": ("unit_id", "UNIT-X", node.unit_id),
        "project": ("project_id", "PROJECT-X", node.project_id),
        "worktree": ("worktree_path", str(worktree.parent / "X"), str(worktree)),
        "branch": ("branch", "fix/x", "fix/task-901"),
        "mode": ("mode", "wave", "orchestrator"),
    }

    def run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        assert command[0] != "git"
        if case == "process":
            return _claim_result(tmp_path, node, worktree, returncode=17)
        if case == "json":
            return _claim_result(tmp_path, node, worktree, stdout="{bad")
        if case == "missing":
            return _claim_result(tmp_path, node, worktree, persist=False)
        if case == "inactive":
            return _claim_result(tmp_path, node, worktree, persisted={"status": "released"})
        if case in bad:
            field, persisted, declared = bad[case]
            return _claim_result(
                tmp_path, node, worktree,
                persisted={field: persisted}, declared={field: declared},
            )
        if case == "status":
            return _claim_result(
                tmp_path, node, worktree,
                persisted={"status": "assigned"}, declared={"status": "claimed"},
            )
        if case == "path":
            return _claim_result(
                tmp_path, node, worktree,
                path=tmp_path / "agents/runtime/task_claims/CLAIM-wrong.json",
            )
        return _claim_result(tmp_path, node, worktree, path=tmp_path.parent / "outside.json")

    monkeypatch.setattr(dispatcher.subprocess, "run", run)
    assert dispatcher.cmd_dispatch(_args(tmp_path)) != 0
    assert message in capsys.readouterr().err


def test_dispatch_creates_external_worktree_once_after_exact_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    metadata, repo, worktree = _external(tmp_path)
    node = _node(tmp_path, metadata=metadata)
    _prepare(monkeypatch, tmp_path, [node])
    calls: list[tuple[str, Path]] = []
    monkeypatch.setattr(dispatcher.subprocess, "run", _success_runner(tmp_path, node, worktree, calls))
    assert dispatcher.cmd_dispatch(_args(tmp_path)) == 0
    assert [call[0] for call in calls] == [sys.executable, "git"]
    assert calls[1][1] == repo
    assert json.loads(capsys.readouterr().out)["issued"][0]["worktree_path"] == str(worktree)


def test_dispatch_preserves_dormant_role_routing_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata, _, worktree = _external(tmp_path)
    node = _node(tmp_path, metadata=metadata)
    _prepare(monkeypatch, tmp_path, [node])
    routed: list[dict[str, object]] = []

    class Routing:
        dispatch_wave_hooks = staticmethod(lambda _root, **kwargs: routed.append(kwargs))

    monkeypatch.setattr(dispatcher.subprocess, "run", _success_runner(tmp_path, node, worktree, []))
    monkeypatch.setattr(dispatcher, "role_routing", Routing())
    assert dispatcher.cmd_dispatch(_args(tmp_path)) == 0
    assert routed == [{"task_set_id": TASKSET, "wave_no": 1, "is_w6": False, "now": None}]


def test_worktree_failure_reports_claim_id_and_retry_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    metadata, _, worktree = _external(tmp_path)
    node = _node(tmp_path, metadata=metadata)
    _prepare(monkeypatch, tmp_path, [node])
    calls: list[tuple[str, Path]] = []
    monkeypatch.setattr(
        dispatcher.subprocess, "run", _success_runner(tmp_path, node, worktree, calls, fail_git=True)
    )
    assert dispatcher.cmd_dispatch(_args(tmp_path)) == 1
    assert [call[0] for call in calls] == [sys.executable, "git"]
    stderr = capsys.readouterr().err
    assert "CLAIM-test-task-901" in stderr and "retry" in stderr and "release" in stderr
