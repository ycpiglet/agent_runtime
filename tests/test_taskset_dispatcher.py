from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import taskset_dispatcher as dispatcher  # noqa: E402


def _write_task(
    root: Path,
    task_id: str,
    task_set_id: str,
    *,
    status: str = "planned",
    priority: str = "P1",
    depends_on: list[str] | None = None,
) -> None:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    dependency_line = (
        f"depends_on: [{', '.join(depends_on)}]\n" if depends_on is not None else ""
    )
    (tasks_dir / f"{task_id}.md").write_text(
        f"""---
id: {task_id}
status: {status}
priority: {priority}
difficulty: M
est_hours: 2
est_tokens: 200
task_set_id: {task_set_id}
project_id: PROJECT-AGENT-RUNTIME
{dependency_line}tags: [test]
---

## Goal

Test task for {task_set_id}.
""",
        encoding="utf-8",
    )


def _write_taskset(
    root: Path,
    task_set_id: str,
    *,
    filename: str | None = None,
    schema_version: str = "agent-runtime-work-item/v1",
    kind: str = "taskset",
    title: str = "Runtime Liaison",
    task_order: tuple[str, ...] = (),
    tasks: list[str] | str | None = None,
) -> None:
    tasksets_dir = root / "agents" / "project" / "initiatives"
    tasksets_dir.mkdir(parents=True, exist_ok=True)
    target = tasksets_dir / f"{filename or task_set_id}.md"
    task_section = ""
    if task_order:
        rows = "\n".join(f"  - {task_id}" for task_id in task_order)
        task_section = f"""

## 포함 태스크

tasks:
{rows}
"""
    declared_tasks: list[str] | str | None = tasks
    if declared_tasks is None and task_order:
        declared_tasks = list(task_order)
    if declared_tasks is None:
        task_lines = ""
    elif isinstance(declared_tasks, list) and declared_tasks:
        task_lines = "tasks:\n" + "".join(
            f"  - {task_id}\n" for task_id in declared_tasks
        )
    elif isinstance(declared_tasks, list):
        task_lines = "tasks: []\n"
    else:
        task_lines = f"tasks: {declared_tasks}\n"
    target.write_text(
        f"""---
schema_version: {schema_version}
work_id: {task_set_id}
kind: {kind}
title: {title}
summary: Test dynamic task set.
{task_lines}---
{task_section}
""",
        encoding="utf-8",
    )


def _write_unit(
    root: Path,
    task_id: str,
    *,
    status: str = "worker_ready",
    **metadata: str | bool | list[str],
) -> None:
    units_dir = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id
    units_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"unit_id: UNIT-{task_id}-001",
        f"task_id: {task_id}",
        f"status: {status}",
        "model_tier: worker_standard",
    ]
    for key, value in metadata.items():
        if isinstance(value, list):
            encoded = f"[{', '.join(value)}]"
        elif isinstance(value, bool):
            encoded = str(value).lower()
        else:
            encoded = value
        lines.append(f"{key}: {encoded}")
    lines.extend(["---", ""])
    (units_dir / f"UNIT-{task_id}-001.md").write_text("\n".join(lines), encoding="utf-8")


def _run(
    root: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "taskset_dispatcher.py"), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_plan_resolves_canonical_dynamic_taskset_without_static_alias(tmp_path: Path) -> None:
    task_set_id = "TASKSET-AGENT-RUNTIME-DOWNSTREAM-INTAKE"
    _write_taskset(tmp_path, task_set_id, title="Downstream Intake Repair")
    _write_task(tmp_path, "TASK-229", task_set_id)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["task_set_id"] == task_set_id
    assert payload["display_name"] == "Downstream Intake Repair"
    assert payload["next_task_id"] == "TASK-229"

    by_slug = _run(tmp_path, "plan", "agent-runtime-downstream-intake", "--json")
    assert by_slug.returncode == 0, by_slug.stderr or by_slug.stdout
    assert json.loads(by_slug.stdout)["task_set_id"] == task_set_id


def test_plan_honors_canonical_task_order_before_score_sort(tmp_path: Path) -> None:
    task_set_id = "TASKSET-TASK216-KPI-PROFILE-CONDITIONS"
    _write_taskset(
        tmp_path,
        task_set_id,
        task_order=("TASK-219", "TASK-220", "TASK-217"),
    )
    _write_task(tmp_path, "TASK-217", task_set_id, priority="P0")
    _write_task(tmp_path, "TASK-219", task_set_id, priority="P2")
    _write_task(tmp_path, "TASK-220", task_set_id, priority="P1")

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["next_task_id"] == "TASK-219"
    assert [task.task_id for task in dispatcher._tasks_for(tmp_path, task_set_id)] == [  # noqa: SLF001
        "TASK-219",
        "TASK-220",
        "TASK-217",
    ]


@pytest.mark.parametrize(
    "task_id",
    [
        "TASK-AR-20260721-221825-f53b6746",
        "TASK-AR-20260721-221825-F53B6746",
    ],
)
def test_plan_accepts_timestamp_task_ids_without_case_rewriting(
    tmp_path: Path, task_id: str
) -> None:
    task_set_id = "TASKSET-DYNAMIC-TIMESTAMP-IDS"
    _write_taskset(tmp_path, task_set_id, tasks=[task_id])
    _write_task(tmp_path, task_id, task_set_id)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["next_task_id"] == task_id


def test_body_order_deduplicates_and_ignores_unrelated_ids(tmp_path: Path) -> None:
    task_set_id = "TASKSET-DYNAMIC-ORDER"
    _write_taskset(tmp_path, task_set_id)
    record = tmp_path / "agents" / "project" / "initiatives" / f"{task_set_id}.md"
    record.write_text(
        record.read_text(encoding="utf-8")
        + (
            "\n## 포함 태스크\n\ntasks:\n"
            "  - TASK-999\n  - TASK-219\n  - TASK-219\n"
            "  - TASK-888\n  - TASK-220\n"
        ),
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-217", task_set_id, priority="P0")
    _write_task(tmp_path, "TASK-219", task_set_id, priority="P2")
    _write_task(tmp_path, "TASK-220", task_set_id, priority="P1")
    _write_task(tmp_path, "TASK-999", "TASKSET-OTHER", priority="P0")

    tasks = dispatcher._tasks_for(tmp_path, task_set_id)  # noqa: SLF001

    assert [task.task_id for task in tasks] == ["TASK-219", "TASK-220", "TASK-217"]


def test_body_order_ignores_task_ids_embedded_in_unicode_words() -> None:
    body = "## Tasks\n\n- 작업TASK-AR-999\n- αTASK-998β\n"

    assert dispatcher._ordered_task_ids(body) == []  # noqa: SLF001


def test_canonical_order_skips_completed_task_without_reordering_remainder(tmp_path: Path) -> None:
    task_set_id = "TASKSET-DYNAMIC-ORDER"
    _write_taskset(tmp_path, task_set_id, task_order=("TASK-219", "TASK-220", "TASK-217"))
    _write_task(tmp_path, "TASK-217", task_set_id, priority="P0")
    _write_task(tmp_path, "TASK-219", task_set_id, status="completed", priority="P2")
    _write_task(tmp_path, "TASK-220", task_set_id, priority="P1")

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["next_task_id"] == "TASK-220"


def test_task_ids_outside_tasks_section_do_not_override_score_fallback(tmp_path: Path) -> None:
    task_set_id = "TASKSET-DYNAMIC-NO-ORDER"
    _write_taskset(tmp_path, task_set_id)
    record = tmp_path / "agents" / "project" / "initiatives" / f"{task_set_id}.md"
    record.write_text(
        record.read_text(encoding="utf-8") + "\n## Risks\n\nTASK-219 must wait for TASK-217.\n",
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-217", task_set_id, priority="P0")
    _write_task(tmp_path, "TASK-219", task_set_id, priority="P2")

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["next_task_id"] == "TASK-217"


def test_localized_body_order_is_used_when_frontmatter_tasks_are_absent(tmp_path: Path) -> None:
    task_set_id = "TASKSET-DYNAMIC-BODY-ORDER"
    _write_taskset(tmp_path, task_set_id)
    record = tmp_path / "agents" / "project" / "initiatives" / f"{task_set_id}.md"
    record.write_text(
        record.read_text(encoding="utf-8")
        + "\n## 포함 태스크\n\ntasks:\n  - TASK-219\n  - TASK-220\n  - TASK-217\n",
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-217", task_set_id, priority="P0")
    _write_task(tmp_path, "TASK-219", task_set_id, priority="P2")
    _write_task(tmp_path, "TASK-220", task_set_id, priority="P1")

    assert [task.task_id for task in dispatcher._tasks_for(tmp_path, task_set_id)] == [  # noqa: SLF001
        "TASK-219",
        "TASK-220",
        "TASK-217",
    ]


def test_frontmatter_tasks_take_precedence_over_conflicting_body_order(tmp_path: Path) -> None:
    task_set_id = "TASKSET-DYNAMIC-FRONTMATTER-ORDER"
    _write_taskset(tmp_path, task_set_id, task_order=("TASK-219", "TASK-220", "TASK-217"))
    record = tmp_path / "agents" / "project" / "initiatives" / f"{task_set_id}.md"
    record.write_text(
        record.read_text(encoding="utf-8").replace(
            "## 포함 태스크\n\ntasks:\n  - TASK-219\n  - TASK-220\n  - TASK-217",
            "## 포함 태스크\n\ntasks:\n  - TASK-217\n  - TASK-220\n  - TASK-219",
        ),
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-217", task_set_id, priority="P0")
    _write_task(tmp_path, "TASK-219", task_set_id, priority="P2")
    _write_task(tmp_path, "TASK-220", task_set_id, priority="P1")

    assert [task.task_id for task in dispatcher._tasks_for(tmp_path, task_set_id)] == [  # noqa: SLF001
        "TASK-219",
        "TASK-220",
        "TASK-217",
    ]


@pytest.mark.parametrize(
    ("record_kwargs", "message"),
    [
        ({"schema_version": "wrong/v1"}, "schema_version"),
        ({"kind": "initiative"}, "kind"),
        ({"filename": "TASKSET-WRONG"}, "filename"),
    ],
)
def test_dynamic_taskset_parser_rejects_malformed_canonical_record(
    tmp_path: Path,
    record_kwargs: dict[str, str],
    message: str,
) -> None:
    task_set_id = "TASKSET-DYNAMIC-ONE"
    _write_taskset(tmp_path, task_set_id, **record_kwargs)
    _write_task(tmp_path, "TASK-901", task_set_id)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 1
    assert message in (result.stderr or result.stdout)
    assert "invalid canonical task set record" in (result.stderr or result.stdout)


def test_dynamic_taskset_parser_rejects_duplicate_aliases(tmp_path: Path) -> None:
    _write_taskset(tmp_path, "TASKSET-DYNAMIC-ONE", title="Shared Lane")
    _write_taskset(tmp_path, "TASKSET-DYNAMIC-TWO", title="Shared Lane")
    _write_task(tmp_path, "TASK-901", "TASKSET-DYNAMIC-ONE")

    result = _run(tmp_path, "plan", "TASKSET-DYNAMIC-ONE", "--json")

    assert result.returncode == 1
    assert "duplicate task set alias" in (result.stderr or result.stdout)
    assert "shared-lane" in (result.stderr or result.stdout)


def test_plan_uses_canonical_tasks_order_before_backlog_score(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ORDERED"
    _write_taskset(tmp_path, taskset, tasks=["TASK-902", "TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["next_task_id"] == "TASK-902"
    assert (payload["step_index"], payload["step_total"]) == (1, 2)


def test_plan_advances_to_next_canonical_task_after_first_is_complete(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ADVANCE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset, status="completed")
    _write_task(tmp_path, "TASK-902", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["next_task_id"] == "TASK-902"
    assert (payload["step_index"], payload["step_total"]) == (2, 2)


def test_plan_rejects_non_list_canonical_tasks_field(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-TASKS-SCALAR"
    _write_taskset(tmp_path, taskset, tasks="TASK-901")
    _write_task(tmp_path, "TASK-901", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "tasks must be a YAML list" in (result.stderr or result.stdout)


def test_plan_preserves_score_based_fallback_without_tasks_field(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-LEGACY"
    _write_taskset(tmp_path, taskset)
    _write_task(tmp_path, "TASK-901", taskset, priority="P3")
    _write_task(tmp_path, "TASK-902", taskset, priority="P0")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["next_task_id"] == "TASK-902"


@pytest.mark.parametrize(
    ("declared", "task_records", "message"),
    [
        (
            ["TASK-901", "TASK-901"],
            [("TASK-901", "TASKSET-DYNAMIC-MEMBERS")],
            "duplicate task ids",
        ),
        (["TASK-999"], [], "unknown task ids"),
        (
            ["TASK-901"],
            [("TASK-901", "TASKSET-OTHER")],
            "wrong task_set_id membership",
        ),
        (
            ["TASK-901"],
            [
                ("TASK-901", "TASKSET-DYNAMIC-MEMBERS"),
                ("TASK-902", "TASKSET-DYNAMIC-MEMBERS"),
            ],
            "omitted",
        ),
    ],
)
def test_plan_rejects_invalid_canonical_task_membership(
    tmp_path: Path,
    declared: list[str],
    task_records: list[tuple[str, str]],
    message: str,
) -> None:
    taskset = "TASKSET-DYNAMIC-MEMBERS"
    _write_taskset(tmp_path, taskset, tasks=declared)
    for task_id, membership in task_records:
        _write_task(tmp_path, task_id, membership)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert message in (result.stderr or result.stdout)


def test_plan_blocks_on_first_open_task_dependency_instead_of_skipping(
    tmp_path: Path,
) -> None:
    taskset = "TASKSET-DYNAMIC-DEPENDENCY"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-900", "TASKSET-OTHER", status="planned")
    _write_task(tmp_path, "TASK-901", taskset, depends_on=["TASK-900"])
    _write_task(tmp_path, "TASK-902", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "TASK-901 has incomplete dependencies" in (result.stderr or result.stdout)
    assert "refusing to skip ahead: TASK-900" in (result.stderr or result.stdout)


@pytest.mark.parametrize("dependency", ["TASK-999", "TASK-901"], ids=["unknown", "self"])
def test_plan_rejects_invalid_selected_task_dependency(
    tmp_path: Path,
    dependency: str,
) -> None:
    taskset = "TASKSET-DYNAMIC-TASK-DEPS-INVALID"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset, depends_on=[dependency])

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    message = result.stderr or result.stdout
    assert "depend" in message.lower()
    assert "TASK-901" in message
    assert dependency in message


def test_plan_allows_completed_selected_task_dependency(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-TASK-DEPS-COMPLETE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset, depends_on=["TASK-902"])
    _write_task(tmp_path, "TASK-902", taskset, status="completed")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["next_task_id"] == "TASK-901"


def test_plan_blocks_when_selected_unit_dependency_is_not_complete(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-DEPS"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset)
    _write_unit(tmp_path, "TASK-901", depends_on=["UNIT-TASK-902-001"])
    _write_unit(tmp_path, "TASK-902")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    message = result.stderr or result.stdout
    assert "UNIT-TASK-901-001" in message
    assert "UNIT-TASK-902-001" in message


def test_plan_allows_completed_selected_unit_dependency(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-DEPS-COMPLETE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset)
    _write_unit(tmp_path, "TASK-901", depends_on=["UNIT-TASK-902-001"])
    _write_unit(tmp_path, "TASK-902", status="completed")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["unit_id"] == "UNIT-TASK-901-001"


@pytest.mark.parametrize(
    "dependency",
    ["UNIT-TASK-999-001", "UNIT-TASK-901-001"],
    ids=["unknown", "self"],
)
def test_plan_rejects_invalid_selected_unit_dependency(
    tmp_path: Path,
    dependency: str,
) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-DEPS-INVALID"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901", depends_on=[dependency])

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    message = result.stderr or result.stdout
    assert "UNIT-TASK-901-001" in message
    assert dependency in message


def test_plan_allows_completed_task_dependency_for_selected_unit(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-TASK-DEPS-COMPLETE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset, status="completed")
    _write_unit(tmp_path, "TASK-901", depends_on=["TASK-902"])

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["unit_id"] == "UNIT-TASK-901-001"


def test_plan_rejects_open_task_when_all_unit_specs_are_completed(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-COMPLETED-UNIT"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901", status="completed")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "TASK-901 has unit specs but no open unit" in (result.stderr or result.stdout)


def test_resolve_taskset_preserves_static_alias_import_contract() -> None:
    resolved = dispatcher._resolve_taskset("quality-loop")  # noqa: SLF001

    assert resolved.task_set_id == "TASKSET-AR-QUALITY-LOOP"
    assert resolved.display_name == "Quality Sentinel"


def test_plan_uses_complete_structured_worktree_tuple(tmp_path: Path) -> None:
    task_set_id = "TASKSET-DYNAMIC-EXTERNAL"
    task_id = "TASK-902"
    repository = (tmp_path / "external-repository").resolve()
    repository.mkdir()
    worktree = repository / ".worktrees" / task_id
    _write_taskset(tmp_path, task_set_id)
    _write_task(tmp_path, task_id, task_set_id)
    _write_unit(
        tmp_path,
        task_id,
        repository_path=str(repository),
        worktree_path=str(worktree),
        branch="fix/task-902",
        base_ref="origin/main",
    )

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["repository_path"] == str(repository)
    assert payload["worktree_path"] == str(worktree)
    assert payload["branch"] == "fix/task-902"
    assert payload["base_ref"] == "origin/main"
    assert payload["worktree_command"] == [
        "git",
        "worktree",
        "add",
        "-b",
        "fix/task-902",
        str(worktree),
        "origin/main",
    ]
    claim_command = payload["claim_command"]
    assert claim_command[claim_command.index("--mode") + 1] == "orchestrator"
    assert claim_command[claim_command.index("--worktree-path") + 1] == str(worktree)


def _git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _init_repository(repository: Path) -> None:
    repository.mkdir()
    _git(repository, "init", "-q", "-b", "main")
    _git(repository, "config", "user.email", "taskset-test@example.com")
    _git(repository, "config", "user.name", "Taskset Test")
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-q", "-m", "fixture")


def test_adoption_reuses_existing_local_branch_without_dash_b(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/existing")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/fix/existing",
    )
    worktree = repository / ".worktrees" / "TASK-905"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert payload["adopt_existing_branch"] is True
    assert payload["worktree_command"] == [
        "git", "worktree", "add", str(worktree), "fix/existing"
    ]
    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001
    assert _git(worktree, "branch", "--show-current").stdout.strip() == "fix/existing"


def test_adoption_normalizes_full_local_ref_before_worktree_add(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/existing")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/fix/existing",
    )
    worktree = repository / ".worktrees" / "TASK-905-FULL-REF"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "refs/heads/fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001
    assert payload["worktree_command"] == [
        "git", "worktree", "add", str(worktree), "fix/existing"
    ]
    assert _git(worktree, "branch", "--show-current").stdout.strip() == "fix/existing"


def test_adoption_normalizes_full_ref_before_fresh_branch_creation(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    worktree = repository / ".worktrees" / "TASK-905-FRESH-FULL-REF"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "refs/heads/fix/fresh",
            "base_ref": "main",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001
    assert payload["worktree_command"] == [
        "git", "worktree", "add", "-b", "fix/fresh", str(worktree), "main"
    ]
    assert _git(worktree, "branch", "--show-current").stdout.strip() == "fix/fresh"


@pytest.mark.parametrize(
    "branch",
    [
        "refs/heads/HEAD",
        "refs/heads/-danger",
        "refs/heads/.hidden",
        "refs/heads/foo/.hidden",
    ],
)
def test_adoption_rejects_invalid_normalized_local_branch_before_worktree_add(
    tmp_path: Path,
    branch: str,
) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    if branch == "refs/heads/HEAD":
        _git(repository, "update-ref", branch, "refs/heads/main")
    worktree = repository / ".worktrees" / "TASK-905-INVALID-FULL-REF"

    with pytest.raises(SystemExit, match="invalid local branch name"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            tmp_path,
            {
                "repository_path": str(repository),
                "worktree_path": str(worktree),
                "branch": branch,
                "base_ref": "main",
                "adopt_existing_branch": True,
            },
            default_worktree="unused",
            default_branch="unused",
        )

    assert not worktree.exists()
    assert str(worktree) not in _git(repository, "worktree", "list", "--porcelain").stdout


def test_adoption_rejects_local_branch_behind_declared_base_ref(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/existing")
    (repository / "NEXT.md").write_text("remote advance\n", encoding="utf-8")
    _git(repository, "add", "NEXT.md")
    _git(repository, "commit", "-q", "-m", "advance remote base")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/main",
    )

    with pytest.raises(SystemExit, match="behind or diverged"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            tmp_path,
            {
                "repository_path": str(repository),
                "worktree_path": str(repository / ".worktrees" / "TASK-905"),
                "branch": "fix/existing",
                "base_ref": "origin/fix/existing",
                "adopt_existing_branch": True,
            },
            default_worktree="unused",
            default_branch="unused",
        )


def test_adoption_accepts_local_branch_ahead_of_declared_base_ref(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    base_sha = _git(repository, "rev-parse", "HEAD").stdout.strip()
    _git(repository, "branch", "fix/existing")
    _git(repository, "update-ref", "refs/remotes/origin/fix/existing", base_sha)
    _git(repository, "switch", "-q", "fix/existing")
    (repository / "AHEAD.md").write_text("local advance\n", encoding="utf-8")
    _git(repository, "add", "AHEAD.md")
    _git(repository, "commit", "-q", "-m", "advance local branch")
    _git(repository, "switch", "-q", "main")
    worktree = repository / ".worktrees" / "TASK-905"

    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert payload["worktree_command"] == [
        "git", "worktree", "add", str(worktree), "fix/existing"
    ]
    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001


def test_adoption_rejects_missing_base_before_fresh_branch_creation(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)

    with pytest.raises(SystemExit, match="base_ref is missing or not a commit"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            tmp_path,
            {
                "repository_path": str(repository),
                "worktree_path": str(repository / ".worktrees" / "TASK-905"),
                "branch": "fix/missing",
                "base_ref": "origin/fix/missing",
                "adopt_existing_branch": True,
            },
            default_worktree="unused",
            default_branch="unused",
        )


def test_adoption_rechecks_preexisting_worktree_after_base_moves(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    base_sha = _git(repository, "rev-parse", "HEAD").stdout.strip()
    _git(repository, "branch", "fix/existing")
    _git(repository, "update-ref", "refs/remotes/origin/fix/existing", base_sha)
    worktree = repository / ".worktrees" / "TASK-905"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )
    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001

    (repository / "NEXT.md").write_text("remote advance\n", encoding="utf-8")
    _git(repository, "add", "NEXT.md")
    _git(repository, "commit", "-q", "-m", "advance remote base")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/main",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is False  # noqa: SLF001
    assert "behind or diverged" in capsys.readouterr().err


def test_adoption_rejects_preexisting_worktree_on_wrong_branch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/expected")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/expected",
        "refs/heads/fix/expected",
    )
    worktree = repository / ".worktrees" / "TASK-906"
    _git(repository, "worktree", "add", "-q", "-b", "fix/actual", str(worktree), "main")
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/expected",
            "base_ref": "origin/fix/expected",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is False  # noqa: SLF001
    assert "worktree branch mismatch" in capsys.readouterr().err


def test_adoption_requires_complete_structured_tuple() -> None:
    with pytest.raises(SystemExit, match="requires a complete structured worktree tuple"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            Path.cwd(),
            {"adopt_existing_branch": True},
            default_worktree=".worktrees/TASK-907",
            default_branch="fix/task-907",
        )


def test_plan_treats_explicit_false_adoption_as_legacy_default(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ADOPT-FALSE"
    task_id = "TASK-907"
    _write_taskset(tmp_path, taskset, tasks=[task_id])
    _write_task(tmp_path, task_id, taskset)
    _write_unit(tmp_path, task_id, adopt_existing_branch=False)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["adopt_existing_branch"] is False
    assert payload["worktree_path"] == f".worktrees/{task_id}"


def test_plan_rejects_non_boolean_adoption_flag(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ADOPT-INVALID"
    task_id = "TASK-908"
    _write_taskset(tmp_path, taskset, tasks=[task_id])
    _write_task(tmp_path, task_id, taskset)
    _write_unit(tmp_path, task_id, adopt_existing_branch="invalid")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "adopt_existing_branch must be a boolean" in (result.stderr or result.stdout)


@pytest.mark.parametrize("missing", ["repository_path", "worktree_path", "branch", "base_ref"])
def test_plan_rejects_partial_structured_worktree_tuple(tmp_path: Path, missing: str) -> None:
    task_set_id = "TASKSET-DYNAMIC-PARTIAL"
    task_id = "TASK-903"
    repository = (tmp_path / "external-repository").resolve()
    worktree = repository / ".worktrees" / task_id
    metadata = {
        "repository_path": str(repository),
        "worktree_path": str(worktree),
        "branch": "fix/task-903",
        "base_ref": "origin/main",
    }
    metadata.pop(missing)
    _write_taskset(tmp_path, task_set_id)
    _write_task(tmp_path, task_id, task_set_id)
    _write_unit(tmp_path, task_id, **metadata)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 1
    assert "structured worktree metadata must define all fields" in (result.stderr or result.stdout)
    assert missing in (result.stderr or result.stdout)


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        (
            {
                "repository_path": "relative/repository",
                "worktree_path": "/tmp/repository/.worktrees/TASK-904",
                "branch": "fix/task-904",
                "base_ref": "origin/main",
            },
            "repository_path must be absolute",
        ),
        (
            {
                "repository_path": "/tmp/repository",
                "worktree_path": "/tmp/outside/TASK-904",
                "branch": "fix/task-904",
                "base_ref": "origin/main",
            },
            "worktree_path must be under",
        ),
        (
            {
                "repository_path": "/tmp/repository",
                "worktree_path": "/tmp/repository/.worktrees/TASK-904",
                "branch": "main",
                "base_ref": "origin/main",
            },
            "protected branch",
        ),
        (
            {
                "repository_path": "/tmp/repository",
                "worktree_path": "/tmp/repository/.worktrees/TASK-904",
                "branch": "fix/task-904",
                "base_ref": "--upload-pack=unsafe",
            },
            "unsafe base_ref",
        ),
    ],
)
def test_plan_rejects_unsafe_structured_worktree_tuple(
    tmp_path: Path,
    metadata: dict[str, str],
    message: str,
) -> None:
    repository = str((tmp_path / "repository").resolve())
    outside = str((tmp_path / "outside").resolve())
    metadata = {
        key: value.replace("/tmp/repository", repository).replace("/tmp/outside", outside)
        for key, value in metadata.items()
    }
    task_set_id = "TASKSET-DYNAMIC-UNSAFE"
    task_id = "TASK-904"
    _write_taskset(tmp_path, task_set_id)
    _write_task(tmp_path, task_id, task_set_id)
    _write_unit(tmp_path, task_id, **metadata)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 1
    assert message in (result.stderr or result.stdout)


def test_plan_preserves_legacy_static_alias_and_host_worktree_defaults(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP")

    result = _run(tmp_path, "plan", "quality-loop", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["task_set_id"] == "TASKSET-AR-QUALITY-LOOP"
    assert payload["worktree_path"] == ".worktrees/TASK-AR-901"
    assert payload["branch"] == "codex/task-ar-901-quality-loop"


def _start_args(root: Path) -> argparse.Namespace:
    return argparse.Namespace(root=root, taskset="unused", json=True)


def _start_payload(root: Path) -> dict[str, object]:
    worktree = root / ".worktrees" / "TASK-905"
    return {
        "task_set_id": "TASKSET-DYNAMIC-START",
        "next_task_id": "TASK-905",
        "next_task_path": str(root / "agents" / "lead_engineer" / "tasks" / "TASK-905.md"),
        "next_task_status": "planned",
        "unit_spec_path": "",
        "model_tier": "planner",
        "repository_path": str(root),
        "worktree_path": str(worktree),
        "branch": "fix/task-905",
        "base_ref": "origin/main",
        "worktree_command": [
            "git",
            "worktree",
            "add",
            "-b",
            "fix/task-905",
            str(worktree),
            "origin/main",
        ],
        "claim_command": ["claim"],
    }


def _claim_result(
    root: Path,
    *,
    persist: bool,
    persisted_overrides: dict[str, str] | None = None,
    declared_overrides: dict[str, str] | None = None,
    path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    claim_id = "CLAIM-test-task-905"
    claim_path = path or root / "agents" / "runtime" / "task_claims" / f"{claim_id}.json"
    claim = {
        "claim_id": claim_id,
        "task_id": "TASK-905",
        "task_set_id": "TASKSET-DYNAMIC-START",
        "status": "claimed",
        "mode": "orchestrator",
        "worktree_path": str(root / ".worktrees" / "TASK-905"),
        "branch": "fix/task-905",
    }
    claim.update(persisted_overrides or {})
    if persist:
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(json.dumps(claim), encoding="utf-8")
    declared = {**claim, **(declared_overrides or {})}
    stdout = json.dumps(
        {
            "status": "created",
            "path": claim_path.relative_to(root).as_posix(),
            "claim": declared,
        }
    )
    return subprocess.CompletedProcess(["claim"], 0, stdout=stdout, stderr="")


def _prepare_start(monkeypatch: pytest.MonkeyPatch, root: Path) -> dict[str, object]:
    payload = _start_payload(root)
    monkeypatch.setattr(dispatcher, "_plan_payload", lambda _args: payload)
    monkeypatch.setattr(dispatcher, "_active_taskset_claims", lambda _root, _taskset: [])
    monkeypatch.setattr(dispatcher, "_sync_backlog_board", lambda _root: True)
    monkeypatch.delenv("AGENT_RUNTIME_GIT", raising=False)
    return payload


def test_start_claim_failure_does_not_run_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return subprocess.CompletedProcess(command, 17, stdout="", stderr="claim refused\n")
        raise AssertionError("worktree command must not run after claim failure")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 17
    assert calls == ["claim"]


def test_start_missing_persisted_claim_does_not_run_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=False)
        raise AssertionError("worktree command must not run without a persisted claim")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert calls == ["claim"]
    assert "persisted claim is missing" in capsys.readouterr().err


def test_start_creates_worktree_once_after_persisted_orchestrator_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        worktree = Path(str(payload["worktree_path"]))
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: fake\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 0
    assert calls == ["claim", "git"]


def test_start_worktree_failure_leaves_persisted_claim_for_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        return subprocess.CompletedProcess(command, 23, stdout="", stderr="worktree failed\n")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    claim_path = tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-test-task-905.json"
    assert claim_path.is_file()
    assert calls == ["claim", "git"]
    stderr = capsys.readouterr().err
    assert "reservation claim remains active" in stderr
    assert "CLAIM-test-task-905" in stderr


def test_start_worktree_spawn_error_leaves_persisted_claim_for_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        raise FileNotFoundError("external repository is unavailable")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    claim_path = tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-test-task-905.json"
    assert claim_path.is_file()
    stderr = capsys.readouterr().err
    assert "failed to run worktree command" in stderr
    assert "reservation claim remains active" in stderr


@pytest.mark.parametrize(
    ("stdout", "message"),
    [
        ("{not-json", "invalid JSON"),
        ("[]", "non-object JSON"),
    ],
)
def test_start_rejects_invalid_claim_json_without_running_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stdout: str,
    message: str,
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        raise AssertionError("worktree command must not run for invalid claim JSON")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert calls == ["claim"]
    assert message in capsys.readouterr().err


def test_start_rejects_claim_path_outside_canonical_claim_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    outside = tmp_path / "outside-claim.json"

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True, path=outside)
        raise AssertionError("worktree command must not run for an unsafe claim path")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert "persisted claim path is outside" in capsys.readouterr().err


def test_start_rejects_persisted_claim_field_mismatch_without_running_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(
                tmp_path,
                persist=True,
                persisted_overrides={"branch": "fix/other"},
                declared_overrides={"branch": "fix/task-905"},
            )
        raise AssertionError("worktree command must not run for a mismatched claim")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert calls == ["claim"]
    assert "persisted claim field mismatch: branch" in capsys.readouterr().err


def test_start_accepts_preexisting_worktree_after_persisting_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    worktree = Path(str(payload["worktree_path"]))
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: existing\n", encoding="utf-8")
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        raise AssertionError("git must not run for a pre-existing valid worktree")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 0
    assert calls == ["claim"]


def test_plan_keeps_machine_readable_claim_response_for_non_json_outer_cli(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP")
    args = argparse.Namespace(
        root=tmp_path,
        taskset="quality-loop",
        agent_role=None,
        team_id=None,
        mode="implement",
        now=None,
        suffix=None,
        json=False,
    )

    payload = dispatcher._plan_payload(args)  # noqa: SLF001

    assert payload["claim_command"][-1] == "--json"
    mode_index = payload["claim_command"].index("--mode")
    assert payload["claim_command"][mode_index + 1] == "orchestrator"


def test_non_json_start_integrates_with_claim_dispatcher_and_existing_worktree(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP")
    worktree = tmp_path / ".worktrees" / "TASK-AR-901"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: existing\n", encoding="utf-8")

    result = _run(
        tmp_path,
        "start",
        "quality-loop",
        "--now",
        "2026-07-14T18:50:00+09:00",
        "--suffix",
        "integration",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "taskset-dispatcher: Quality Sentinel" in result.stdout
    claim_paths = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_paths) == 1
    claim = json.loads(claim_paths[0].read_text(encoding="utf-8"))
    assert claim["mode"] == "orchestrator"
    assert claim["task_id"] == "TASK-AR-901"
    assert claim["worktree_path"] == ".worktrees/TASK-AR-901"
    assert (tmp_path / "BACKLOG-BOARD.md").is_file()


def test_ensure_worktree_runs_git_in_declared_external_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "external-repository"
    repository.mkdir()
    worktree = repository / ".worktrees" / "TASK-906"
    payload = {
        "repository_path": str(repository),
        "worktree_path": str(worktree),
        "worktree_command": [
            "git",
            "worktree",
            "add",
            "-b",
            "fix/task-906",
            str(worktree),
            "origin/main",
        ],
    }
    observed_cwd: list[Path] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed_cwd.append(Path(str(kwargs["cwd"])))
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: external\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)
    monkeypatch.delenv("AGENT_RUNTIME_GIT", raising=False)

    assert dispatcher._ensure_worktree(tmp_path, payload)  # noqa: SLF001
    assert observed_cwd == [repository.resolve()]


def test_start_readiness_failure_blocks_claim_and_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    payload["unit_spec_path"] = "agents/lead_engineer/tasks/units/TASK-905/UNIT-001.md"
    payload["unit_id"] = "UNIT-001"
    payload["model_tier"] = "worker_standard"
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 9, stdout="readiness failed\n", stderr="")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 9
    assert len(calls) == 1
    assert calls[0][1].endswith("task_unit_readiness_gate.py")


def test_start_active_taskset_claim_blocks_before_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    monkeypatch.setattr(
        dispatcher,
        "_active_taskset_claims",
        lambda _root, _taskset: [{"claim_id": "CLAIM-existing", "_path": "claim.json"}],
    )
    monkeypatch.setattr(
        dispatcher.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("no subprocess may run while the taskset is already claimed")
        ),
    )

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert payload["task_set_id"] in capsys.readouterr().err


def test_plan_accepts_human_friendly_taskset_alias_and_emits_next_commands(
    tmp_path: Path,
) -> None:
    _write_task(
        tmp_path,
        "TASK-AR-901",
        "TASKSET-AR-QUALITY-LOOP",
        status="planned",
        priority="P0",
    )
    _write_task(
        tmp_path,
        "TASK-AR-902",
        "TASKSET-AR-QUALITY-LOOP",
        status="planned",
        priority="P1",
    )

    result = _run(tmp_path, "plan", "quality-loop", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["task_set_id"] == "TASKSET-AR-QUALITY-LOOP"
    assert payload["display_name"] == "Quality Sentinel"
    assert payload["next_task_id"] == "TASK-AR-901"
    assert payload["claim_command"][0].endswith(("python.exe", "python"))
    assert "--task-set-id" in payload["claim_command"]
    assert "TASKSET-AR-QUALITY-LOOP" in payload["claim_command"]
    assert payload["project_id"] == "PROJECT-AGENT-RUNTIME"
    assert payload["model_tier"] == "worker_standard"
    assert payload["wip_slot"] == 1
    assert payload["stop_condition"] == "stop_after:TASK-AR-901:no_adjacent_taskset"
    assert "--project-id" in payload["claim_command"]
    assert "--model-tier" in payload["claim_command"]
    assert payload["worktree_path"] == ".worktrees/TASK-AR-901"
    assert payload["branch"].startswith("codex/task-ar-901-quality-loop")


def test_plan_accepts_numeric_and_letter_taskset_aliases(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="planned")

    by_number = _run(tmp_path, "plan", "2", "--json")
    by_letter = _run(tmp_path, "plan", "B", "--json")
    by_prefixed_letter = _run(tmp_path, "plan", "taskset B", "--json")

    assert by_number.returncode == 0, by_number.stderr or by_number.stdout
    assert by_letter.returncode == 0, by_letter.stderr or by_letter.stdout
    assert by_prefixed_letter.returncode == 0, by_prefixed_letter.stderr or by_prefixed_letter.stdout
    assert json.loads(by_number.stdout)["task_set_id"] == "TASKSET-AR-QUALITY-LOOP"
    assert json.loads(by_letter.stdout)["task_set_id"] == "TASKSET-AR-QUALITY-LOOP"
    assert json.loads(by_prefixed_letter.stdout)["task_set_id"] == "TASKSET-AR-QUALITY-LOOP"


def test_plan_skips_completed_tasks(tmp_path: Path) -> None:
    _write_task(
        tmp_path,
        "TASK-AR-901",
        "TASKSET-AR-RELEASE-STEWARD",
        status="completed",
    )
    _write_task(
        tmp_path,
        "TASK-AR-902",
        "TASKSET-AR-RELEASE-STEWARD",
        status="planned",
    )

    result = _run(tmp_path, "plan", "release-steward", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["next_task_id"] == "TASK-AR-902"
    assert payload["next_task_status"] == "planned"


def test_plan_fails_when_taskset_has_no_open_tasks(tmp_path: Path) -> None:
    _write_task(
        tmp_path,
        "TASK-AR-901",
        "TASKSET-AR-RELEASE-STEWARD",
        status="completed",
    )

    result = _run(tmp_path, "plan", "release-steward", "--json")

    assert result.returncode == 1
    assert "task set has no open tasks" in (result.stderr or result.stdout)


def test_start_creates_claim_with_taskset_progress_metadata(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-PANE-PROGRESS", status="planned")
    worktree = tmp_path / ".worktrees" / "TASK-AR-901"
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text(
        "gitdir: ../../.git/worktrees/test\n",
        encoding="utf-8",
    )

    result = _run(
        tmp_path,
        "start",
        "progress-scout",
        "--agent-role",
        "lead-engineer",
        "--team-id",
        "agent-runtime-core",
        "--mode",
        "implement",
        "--now",
        "2026-06-10T19:40:00+09:00",
        "--suffix",
        "p1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    claim = payload["claim"]["claim"]
    assert payload["next_task_id"] == "TASK-AR-901"
    assert claim["task_set_id"] == "TASKSET-AR-PANE-PROGRESS"
    assert claim["project_id"] == "PROJECT-AGENT-RUNTIME"
    assert claim["model_tier"] == "worker_standard"
    assert claim["wip_slot"] == 1
    assert claim["stop_condition"] == "stop_after:TASK-AR-901:no_adjacent_taskset"
    assert claim["step_index"] == 1
    assert claim["step_total"] == 1
    assert claim["status_text"] == "Starting Progress Scout: TASK-AR-901"
    assert claim["phase"] == "taskset-claimed"
    assert claim["progress_pct"] == 0


def test_start_creates_missing_worktree_after_claiming_taskset(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-PANE-PROGRESS", status="planned")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / ("git.cmd" if os.name == "nt" else "git")
    if os.name == "nt":
        fake_git.write_text(
            "\n".join(
                [
                    "@echo off",
                    'dir /b "%CD%\\agents\\runtime\\task_claims\\*.json" >nul 2>nul || exit /b 42',
                    'echo %*>>"%GIT_FAKE_LOG%"',
                    'mkdir "%CD%\\.worktrees\\TASK-AR-901" 2>nul',
                    'echo gitdir: fake>"%CD%\\.worktrees\\TASK-AR-901\\.git"',
                    "exit /b 0",
                ]
            ),
            encoding="utf-8",
        )
    else:
        fake_git.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'ls "$PWD/agents/runtime/task_claims/"*.json >/dev/null 2>&1 || exit 42',
                    'echo "$@" >> "$GIT_FAKE_LOG"',
                    'mkdir -p "$PWD/.worktrees/TASK-AR-901"',
                    'printf "gitdir: fake\\n" > "$PWD/.worktrees/TASK-AR-901/.git"',
                    "exit 0",
                ]
            ),
            encoding="utf-8",
        )
        fake_git.chmod(0o755)
    fake_log = tmp_path / "fake-git.log"
    env = dict(os.environ)
    env["GIT_FAKE_LOG"] = str(fake_log)
    env["AGENT_RUNTIME_GIT"] = str(fake_git)

    result = _run(tmp_path, "start", "progress-scout", "--json", env=env)

    assert result.returncode == 0, result.stderr or result.stdout
    assert (
        "worktree add -b codex/task-ar-901-pane-progress .worktrees/TASK-AR-901"
        in fake_log.read_text(encoding="utf-8")
    )
    assert (tmp_path / ".worktrees" / "TASK-AR-901" / ".git").exists()
    assert list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))


def test_start_blocks_when_taskset_already_has_active_claim(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="planned")
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    (claim_dir / "CLAIM-active.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-active",
                "task_id": "TASK-AR-900",
                "task_set_id": "TASKSET-AR-QUALITY-LOOP",
                "agent_role": "qa",
                "agent_instance_id": "qa-1",
                "display_name": "qa@eval-01",
                "callsite_id": "terminal-1",
                "pane_id": "terminal-1",
                "team_id": "validation-team",
                "status": "working",
                "phase": "implement",
                "progress_pct": 20,
                "status_text": "Already working",
                "worktree_path": ".worktrees/TASK-AR-900",
                "branch": "codex/task-ar-900-quality-loop",
                "claimed_at": "2026-06-10T19:30:00+09:00",
                "last_heartbeat": "2026-06-10T19:35:00+09:00",
                "handoff_path": "STATUS.md",
                "log_path": "STATUS.md",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run(tmp_path, "start", "TASKSET-AR-QUALITY-LOOP", "--json")

    assert result.returncode == 1
    assert "task set already has an active claim" in (result.stderr or result.stdout)
