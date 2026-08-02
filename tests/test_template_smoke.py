from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None,
         expect_zero: bool = True, stdout_text: bool = True) -> subprocess.CompletedProcess:
    if env is None:
        env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=stdout_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    if expect_zero and result.returncode != 0:
        detail = result.stdout or result.stderr or "<no output>"
        raise AssertionError(
            f"command failed ({command!r}) returncode={result.returncode}. output:\n{detail}"
        )
    return result


def _host_from_fixture(tmp_path: Path) -> Path:
    host = tmp_path / "host"
    shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "host", host)
    return host


def _canonical_digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _write_plan_snapshot(host: Path, taskset_id: str) -> None:
    path = host / "agents/project/work-items/PLAN-ASSUMPTIONS.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-plan-assumptions/v1",
                "assumption_sets": [
                    {
                        "taskset_id": taskset_id,
                        "anchors": [
                            {
                                "path": "reviews/portable-core-plan.md",
                                "kind": "absent",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    out: dict[str, str] = {}
    for raw in parts[1].splitlines():
        line = raw.strip()
        if not line:
            continue
        if ": " not in line and ":" not in line:
            continue
        key, sep, value = line.partition(":")
        out[key.strip()] = (value[1:] if sep else "").strip()
    return out


def _yaml_scalar(value: object) -> str:
    if value is None or value == "":
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def _write_live_pointer_from_projection(
    host: Path,
    projection: dict[str, object],
    claim: dict[str, object],
) -> None:
    pointer = projection["pointer"]
    assert isinstance(pointer, dict)
    agents = pointer["current_agents"]
    assert isinstance(agents, list) and len(agents) == 1
    agent = agents[0]
    assert isinstance(agent, dict)
    lines = [
        "schema: agent-runtime-next-session-pointer/v1",
        f"updated_at: {_yaml_scalar(claim['last_heartbeat'])}",
        "updated_by: serial-projection-owner",
        "current_state:",
        "  status: active",
        f"  task_set_id: {_yaml_scalar(pointer['active_task_set'])}",
        f"  step_index: {_yaml_scalar(agent['step_index'])}",
        f"  step_total: {_yaml_scalar(agent['step_total'])}",
        f"  status_text: {_yaml_scalar(agent['status_text'])}",
        "active_work:",
        "  current_agents:",
    ]
    for index, (field, value) in enumerate(agent.items()):
        lines.append(
            f"{'    - ' if index == 0 else '      '}{field}: {_yaml_scalar(value)}"
        )
    lines.extend(
        [
            "  current_teams: []",
            "resume:",
            f"  active_task: {_yaml_scalar(pointer['active_task'])}",
            f"  active_task_set: {_yaml_scalar(pointer['active_task_set'])}",
            "  next_actions:",
            "    - Run the claim governance gates.",
            "roles:",
            "  accountable: Lead Engineer",
            "  reviewers: []",
            "pointers:",
            "  active_claims:",
        ]
    )
    lines.extend(
        f"    - {_yaml_scalar(ref)}" for ref in pointer["active_claims"]
    )
    lines.extend(
        [
            "rules:",
            "  present_status_precedence: A present STATUS candidate remains strict.",
            "  pointer_fallback: Without STATUS, require the exact live claim projection.",
            "verification:",
            "  required:",
            "    - python scripts/parallel_worktree_gate.py --check",
            "  last_known:",
            "    status: not-run",
        ]
    )
    path = host / "agents/project/NEXT-SESSION-POINTER.yml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_message(inbox: Path, message_id: str, *, status: str = "open") -> Path:
    path = inbox / f"{message_id}.md"
    path.write_text(
        "\n".join(
            [
                "---",
                f"id: {message_id}",
                "from: orchestrator",
                "to: qa",
                "type: question",
                f"status: {status}",
                "task_id: none",
                "intent: template smoke",
                "ts: 2026-06-08T11:11:11+09:00",
                "---",
                "run one dummy response",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_sync_and_smoke_runtime_scripts(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync_result = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync_result.returncode == 0
    assert "applied=" in (sync_result.stdout or "")

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    (host / "agents" / "messages").mkdir(parents=True, exist_ok=True)
    (host / "agents" / "runtime" / "events").mkdir(parents=True, exist_ok=True)
    scripts_dir = host / "scripts"
    for script in ("agent_orchestrator.py", "agent_worker.py", "auto_runner.py", "check_messages.py"):
        result = _run(
            [PYTHON, str(scripts_dir / script), "--help"] if script != "check_messages.py" else [PYTHON, str(scripts_dir / script)],
            cwd=host,
            env=command_env,
        )
        assert result.returncode == 0


def test_clean_installed_core_claim_to_governance_journey_without_status(
    tmp_path: Path,
) -> None:
    host = _host_from_fixture(tmp_path)
    (host / "agent_runtime.yml").write_text(
        "\n".join(
            [
                "schema: agent-runtime-config/v2",
                "project: portable-core-host",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/ycpiglet/agent_runtime.git",
                "  ref: v0.8.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
                "profiles:",
                "  - core",
                "host:",
                "  state_adapters:",
                "    backlog: BACKLOG.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    _run(
        [PYTHON, "-m", "agent_runtime.cli", "lock", "--root", str(host), "--write"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert not (host / "STATUS.md").exists()
    assert not (host / "agents/lead_engineer/STATUS.md").exists()

    task_id = "TASK-AR-990"
    unit_id = "UNIT-TASK-AR-990-001"
    task_set_id = "TASKSET-PORTABLE-CORE"
    target = host / "portable_probe.py"
    target.write_text("print('portable core')\n", encoding="utf-8")
    task = host / f"agents/lead_engineer/tasks/{task_id}.md"
    unit = host / f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md"
    task.parent.mkdir(parents=True, exist_ok=True)
    unit.parent.mkdir(parents=True, exist_ok=True)
    (host / "README.md").write_text(
        "# Portable Core Host\n\n"
        "## 한국어\n\n"
        "AGENTS.md, CLAUDE.md, agents/project/NEXT-SESSION-POINTER.yml을 먼저 읽습니다.\n\n"
        "## English\n\n"
        "Read AGENTS.md, CLAUDE.md, and agents/project/NEXT-SESSION-POINTER.yml first.\n",
        encoding="utf-8",
    )
    task.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        f"id: {task_id}\n"
        f"work_id: {task_id}\n"
        "work_uid: 71e29977-1fd8-4563-bb89-735e03b8ebd1\n"
        f"task_id: {task_id}\n"
        "task_uid: 71e29977-1fd8-4563-bb89-735e03b8ebd1\n"
        "kind: task\n"
        f"parent_id: {task_set_id}\n"
        f"task_set_id: {task_set_id}\n"
        "status: in_progress\n"
        "verification_status: pending\n"
        "owner: lead-engineer\n"
        "registered_at: 2026-07-30T00:00:00+09:00\n"
        "created_at: 2026-07-30T00:00:00+09:00\n"
        "updated_at: 2026-07-30T00:00:00+09:00\n"
        "started_at: 2026-07-30T00:00:00+09:00\n"
        "origin_type: owner_request\n"
        "origin_ref: tests/test_template_smoke.py\n"
        "created_by: test\n"
        "---\n\n# Portable core task\n",
        encoding="utf-8",
    )
    unit.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        f"work_id: {unit_id}\n"
        "work_uid: f7228336-9c01-4f8f-8f1a-309bfe729112\n"
        f"unit_id: {unit_id}\n"
        f"task_id: {task_id}\n"
        f"parent_id: {task_id}\n"
        f"task_set_id: {task_set_id}\n"
        "project_id: PROJECT-PORTABLE-CORE\n"
        "kind: unit\n"
        "status: in_progress\n"
        "verification_status: pending\n"
        "owner: lead-engineer\n"
        "created_at: 2026-07-30T00:00:00+09:00\n"
        "updated_at: 2026-07-30T00:00:00+09:00\n"
        "origin_type: owner_request\n"
        "origin_ref: tests/test_template_smoke.py\n"
        "created_by: test\n"
        "model_tier: worker_standard\n"
        "context: Exercise the portable core claim journey.\n"
        "inputs:\n"
        f"  - agents/lead_engineer/tasks/{task_id}.md\n"
        "target_files:\n"
        "  - portable_probe.py\n"
        "scope: Only the synthetic portable core fixture.\n"
        "acceptance:\n"
        "  - The claim journey completes without STATUS.md.\n"
        "verification:\n"
        "  - python -m pytest tests/test_template_smoke.py -q\n"
        "handoff: Report the portable continuity result.\n"
        f"stop_condition: stop_after:{unit_id}:portable_core\n"
        "---\n\n"
        "# Portable continuity unit\n\n"
        "## Context\n\n"
        "Exercise the portable core claim journey.\n\n"
        "## Inputs\n\n"
        f"- agents/lead_engineer/tasks/{task_id}.md\n\n"
        "## Target Files\n\n"
        "- portable_probe.py\n\n"
        "## Scope\n\n"
        "Only the synthetic portable core fixture.\n\n"
        "## Steps\n\n"
        "1. Create and project the claim.\n"
        "2. Run governance checks.\n\n"
        "## Acceptance Criteria\n\n"
        "- The claim journey completes without STATUS.md.\n\n"
        "## Verification\n\n"
        "- python -m pytest tests/test_template_smoke.py -q\n\n"
        "## Handoff\n\n"
        "Report the portable continuity result.\n\n"
        "## Stop Boundary\n\n"
        "Stop after this portable core unit.\n",
        encoding="utf-8",
    )
    (host / "BACKLOG-BOARD.md").write_text(
        f"# Board\n\n{task_set_id}\n{task_id}\n{unit_id}\n",
        encoding="utf-8",
    )
    (host / "BACKLOG.md").write_text(
        f"# Backlog\n\n{task_set_id}\n{task_id}\n",
        encoding="utf-8",
    )
    _write_plan_snapshot(host, task_set_id)
    _run(["git", "init", "-q", "-b", "main"], cwd=host)
    _run(["git", "config", "user.email", "test@example.com"], cwd=host)
    _run(["git", "config", "user.name", "Test"], cwd=host)
    _run(["git", "add", "."], cwd=host)
    _run(["git", "commit", "-qm", "portable core baseline"], cwd=host)
    worktree = host / ".worktrees" / task_id
    branch = "codex/task-ar-990-portable-core"
    _run(
        ["git", "worktree", "add", "-q", "-b", branch, str(worktree)],
        cwd=host,
    )
    runtime_root = worktree
    task = runtime_root / task.relative_to(host)
    unit = runtime_root / unit.relative_to(host)

    head_before_claim = _run(
        ["git", "rev-parse", "HEAD"],
        cwd=runtime_root,
    ).stdout.strip()
    pointer_path = runtime_root / "agents/project/NEXT-SESSION-POINTER.yml"
    standby_pointer = pointer_path.read_bytes()
    created = _run(
        [
            PYTHON,
            "scripts/task_claim_dispatcher.py",
            "--root",
            str(runtime_root),
            "create",
            "--task-id",
            task_id,
            "--task-set-id",
            task_set_id,
            "--unit-id",
            unit_id,
            "--unit-spec",
            unit.relative_to(runtime_root).as_posix(),
            "--agent-role",
            "lead-engineer",
            "--worktree-path",
            ".",
            "--branch",
            branch,
            "--scope-transition-approved",
            "--skip-plan-check",
            "--now",
            "2026-07-30T00:05:00+09:00",
            "--suffix",
            "portable-core",
            "--json",
        ],
        cwd=runtime_root,
        env=env,
    )
    claim = json.loads(created.stdout)["claim"]
    assert _run(["git", "rev-parse", "HEAD"], cwd=runtime_root).stdout.strip() == head_before_claim
    assert pointer_path.read_bytes() == standby_pointer

    projected = _run(
        [
            PYTHON,
            "scripts/task_claim_dispatcher.py",
            "--root",
            str(runtime_root),
            "projection",
            "--claim-id",
            str(claim["claim_id"]),
            "--now",
            "2026-07-30T00:06:00+09:00",
            "--json",
        ],
        cwd=runtime_root,
        env=env,
    )
    projection = json.loads(projected.stdout)
    assert pointer_path.read_bytes() == standby_pointer
    claim_ref = str(projection["task_claim_ref"])
    task.write_text(
        task.read_text(encoding="utf-8").replace(
            "verification_status: pending\n",
            f"verification_status: pending\nclaim_refs:\n  - {claim_ref}\n",
        ),
        encoding="utf-8",
    )
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "verification_status: pending\n",
            f"verification_status: pending\nclaim_refs:\n  - {claim_ref}\n",
        ),
        encoding="utf-8",
    )
    _write_live_pointer_from_projection(runtime_root, projection, claim)
    _run(
        [
            PYTHON,
            "scripts/scribe_due.py",
            "--root",
            str(runtime_root),
            "--write-projection",
            "--now",
            "2026-07-30T00:05:00+09:00",
            "--json",
        ],
        cwd=runtime_root,
        env=env,
    )
    _run(
        [PYTHON, "scripts/work_item_classifier.py", "--root", str(runtime_root), "--write"],
        cwd=runtime_root,
        env=env,
    )
    _run(
        [PYTHON, "scripts/evidence_index_generator.py", "--root", str(runtime_root), "--write"],
        cwd=runtime_root,
        env=env,
    )

    for command, success in (
        ([PYTHON, "scripts/parallel_worktree_gate.py", "--root", str(runtime_root), "--check", "--now", "2026-07-30T00:06:00+09:00"], "parallel-worktree-gate: pass"),
        ([PYTHON, "scripts/state_sync_gate.py", "--root", str(runtime_root), "--check", "--now", "2026-07-30T00:06:00+09:00"], "state-sync-gate: pass"),
        ([PYTHON, "scripts/rbac_write_gate.py", "--root", str(runtime_root), "--check"], "rbac-write-gate: pass"),
    ):
        result = _run(command, cwd=runtime_root, env=env)
        assert success in result.stdout

    docs = _run(
        [PYTHON, "scripts/check_agent_docs.py"],
        cwd=runtime_root,
        env=env,
        expect_zero=False,
    )
    docs_output = (docs.stdout or "") + (docs.stderr or "")
    assert "agents/lead_engineer/STATUS.md: missing status board." not in docs_output

    governance = _run(
        [
            PYTHON,
            "scripts/owner_governance_gate.py",
            "--allow-empty-owner-docs",
            "--now",
            "2026-07-30T00:06:00+09:00",
        ],
        cwd=runtime_root,
        env=env,
    )
    assert governance.returncode == 0


def test_synced_host_scribe_projection_is_explicit_and_bounded(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    source = host / "STATUS.md"
    source.write_text(
        "# State\n" + "".join(f"- active {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    source_mtime = source.stat().st_mtime_ns

    read_only = _run(
        [PYTHON, "scripts/scribe_due.py", "--root", str(host), "--json"],
        cwd=host,
        env=env,
    )
    assert json.loads(read_only.stdout)["projection"]["status"] == "missing"
    projection = host / "agents/project/state/SCRIBE-PROJECTION.json"
    assert not projection.exists()

    written = _run(
        [
            PYTHON,
            "scripts/scribe_due.py",
            "--root",
            str(host),
            "--write-projection",
            "--now",
            "2026-07-29T00:00:00+09:00",
            "--json",
        ],
        cwd=host,
        env=env,
    )
    written_payload = json.loads(written.stdout)
    assert written_payload["projection"]["status"] == "fresh"
    assert written_payload["source_debt"]["status"] == "overdue"
    assert written_payload["closure_blocking"] is True
    assert projection.stat().st_size <= 32 * 1024
    assert source.stat().st_mtime_ns == source_mtime


def test_synced_host_records_a_bounded_cleanup_receipt(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    source = host / "STATUS.md"
    source.write_text(
        "# State\n" + "".join(f"- active {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    authorization = host / "agents/lead_engineer/tasks/TASK-SCRIBE.md"
    authorization.parent.mkdir(parents=True, exist_ok=True)
    authorization_template = (
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "id: TASK-SCRIBE\n"
        "work_id: TASK-SCRIBE\n"
        "kind: task\n"
        "status: in_progress\n"
        "scribe_authorization: cleanup\n"
        "scribe_authorized_by: lead-engineer-fixture\n"
        "scribe_authorized_role: lead-engineer\n"
        "scribe_source_binding_digest: {source_digest}\n"
        "scribe_cleanup_plan_digest: {plan_digest}\n"
        "---\n\n"
        "# Authorized Scribe cleanup\n"
    )
    authorization.write_text(
        authorization_template.format(
            source_digest="0" * 64,
            plan_digest="0" * 64,
        ),
        encoding="utf-8",
    )
    _run(
        [
            PYTHON,
            "scripts/scribe_due.py",
            "--root",
            str(host),
            "--write-projection",
            "--now",
            "2026-07-29T00:00:00+09:00",
            "--json",
        ],
        cwd=host,
        env=env,
    )
    projection_path = host / "agents/project/state/SCRIBE-PROJECTION.json"
    baseline = json.loads(projection_path.read_text(encoding="utf-8"))
    before_sources = [
        {
            "adapter": item["adapter"],
            "path": item["path"],
            "present": item["present"],
            "digest": item["digest"],
            "hot_count": item["hot_count"],
        }
        for item in baseline["sources"]
    ]
    authorization.write_text(
        authorization_template.format(
            source_digest=_canonical_digest(before_sources),
            plan_digest=baseline["cleanup_plan"]["plan_digest"],
        ),
        encoding="utf-8",
    )
    _run(["git", "init", "-q"], cwd=host)
    _run(
        ["git", "config", "user.email", "scribe-smoke@example.invalid"],
        cwd=host,
    )
    _run(["git", "config", "user.name", "Scribe Smoke"], cwd=host)
    _run(["git", "config", "commit.gpgsign", "false"], cwd=host)
    _run(["git", "add", "-A"], cwd=host)
    _run(
        ["git", "commit", "-q", "-m", "anchor Scribe cleanup baseline"],
        cwd=host,
    )
    source.write_text(
        "# State\n" + "".join(f"- active {index}\n" for index in range(5, 16)),
        encoding="utf-8",
    )

    recorded = _run(
        [
            PYTHON,
            "scripts/scribe_due.py",
            "--root",
            str(host),
            "--record-cleanup",
            "--authorization-ref",
            "agents/lead_engineer/tasks/TASK-SCRIBE.md",
            "--now",
            "2026-07-29T00:10:00+09:00",
            "--json",
        ],
        cwd=host,
        env=env,
    )
    payload = json.loads(recorded.stdout)
    projection = json.loads(
        projection_path.read_text(encoding="utf-8")
    )

    assert payload["cleanup_outcome"]["status"] == "verified_reduction"
    assert payload["closure_blocking"] is False
    assert projection["cleanup_receipt"]["schema"] == (
        "agent-runtime-scribe-cleanup-receipt/v1"
    )
    assert projection["cleanup_receipt"]["resulting_hot_count"] == 11


def test_synced_host_state_scripts_run_without_source_package_or_pythonpath(
    tmp_path: Path,
) -> None:
    host = _host_from_fixture(tmp_path)
    sync_env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=sync_env,
    )

    task_id = "TASK-AR-648"
    task_set_id = "TASKSET-PORTABLE-STATE"
    task = host / "agents/lead_engineer/tasks" / f"{task_id}.md"
    task.parent.mkdir(parents=True, exist_ok=True)
    task.write_text(
        "\n".join(
            [
                "---",
                f"id: {task_id}",
                "status: in_progress",
                f"task_set_id: {task_set_id}",
                "verification_status: pending",
                "---",
                "",
                "# Portable state task",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (host / "BACKLOG-BOARD.md").write_text(
        f"# Board\n\n{task_set_id}\n{task_id}\n",
        encoding="utf-8",
    )
    (host / "BACKLOG.md").write_text(
        f"# Backlog\n\n{task_set_id}\n",
        encoding="utf-8",
    )
    (host / "STATUS.md").write_text(
        f"# Status\n\n{task_set_id}\n{task_id}\n" + "".join(
            f"- active {index}\n" for index in range(16)
        ),
        encoding="utf-8",
    )
    pointer = host / "agents/project/NEXT-SESSION-POINTER.yml"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(
        "\n".join(
            [
                "current_state:",
                "  status: active",
                f"  task_set_id: {task_set_id}",
                "resume:",
                f"  active_task: {task_id}",
                f"  active_task_set: {task_set_id}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    isolated_env = dict(os.environ)
    isolated_env.pop("PYTHONPATH", None)
    isolated_env["PYTHONNOUSERSITE"] = "1"
    isolated_env["PYTHONIOENCODING"] = "utf-8"

    written = _run(
        [
            PYTHON,
            "-S",
            "scripts/scribe_due.py",
            "--root",
            str(host),
            "--write-projection",
            "--now",
            "2026-07-29T00:00:00+09:00",
            "--json",
        ],
        cwd=host,
        env=isolated_env,
    )
    assert json.loads(written.stdout)["projection"]["status"] == "fresh"

    checked = _run(
        [
            PYTHON,
            "-S",
            "scripts/state_sync_gate.py",
            "--root",
            str(host),
            "--check",
        ],
        cwd=host,
        env=isolated_env,
    )
    assert "state-sync-gate: pass" in checked.stdout


def test_synced_host_creates_and_searches_canonical_compound_record(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )

    created = _run(
        [
            PYTHON,
            "scripts/compound_record.py",
            "--root",
            str(host),
            "create",
            "--work-id",
            "TASK-AR-645",
            "--signature",
            "kedb ignored canonical records",
            "--title",
            "Search canonical knowledge",
            "--summary",
            "The legacy reader did not see per-record knowledge.",
            "--cause",
            "KEDB only parsed one Markdown file.",
            "--prevention",
            "Search validated canonical records before legacy fallback.",
            "--source-ref",
            "reviews/REVIEW-source.md",
            "--prevention-ref",
            "scripts/kedb_search.py",
            "--verification-ref",
            "tests/test_template_smoke.py",
            "--created-at",
            "2026-07-29T05:00:00+09:00",
        ],
        cwd=host,
    )
    assert json.loads(created.stdout)["status"] == "created"

    searched = _run(
        [
            PYTHON,
            "scripts/kedb_search.py",
            "--root",
            str(host),
            "--work-id",
            "TASK-AR-645",
            "--format",
            "json",
        ],
        cwd=host,
    )
    rows = json.loads(searched.stdout)
    assert rows[0]["source"] == "record"
    assert rows[0]["work_ids"] == ["TASK-AR-645"]


def test_worker_processes_one_dummy_message(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    report_path = Path(
        os.getenv(
            "PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH",
            str(tmp_path / "template-warning-summary-gate-report.jsonl"),
        )
    )

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    inbox = host / "agents" / "messages" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    message_id = "MSG-20260608-111111-aaaaaa"
    incoming = _write_message(inbox, message_id)

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    worker = _run(
        [PYTHON, "scripts/agent_worker.py", "--role", "qa", "--provider", "dummy", "--once", "--quiet"],
        cwd=host,
        env=command_env,
    )
    assert worker.returncode == 0

    source = _parse_frontmatter(incoming)
    assert source.get("status") == "answered"
    replies = [p for p in inbox.iterdir() if p.suffix == ".md" and p.name != incoming.name]
    assert replies, "worker should create a reply message file"
    parsed = [_parse_frontmatter(p) for p in replies]
    assert any(p.get("type") == "reply" and p.get("in_reply_to") == message_id for p in parsed)


def test_sync_does_not_seed_default_claim_artifacts(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync_result = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync_result.returncode == 0

    claim_dir = host / "agents" / "runtime" / "claims"
    assert not claim_dir.exists() or not any(p.suffix == ".claim" for p in claim_dir.glob("*.claim"))


def test_clean_host_runs_work_session_report_and_dependency_lifecycle(tmp_path):
    """Exercise generic lifecycle helpers in a synced, clean Git host."""
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    _run([PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"], cwd=REPO_ROOT, env=env)
    _run(["git", "init", "-q", "-b", "main"], cwd=host); _run(["git", "config", "user.email", "test@example.com"], cwd=host); _run(["git", "config", "user.name", "Test"], cwd=host); _run(["git", "add", "."], cwd=host); _run(["git", "commit", "-qm", "baseline"], cwd=host)
    probe = host / "scripts/verification_probe.py"; probe.write_text("print('ok')\n", encoding="utf-8")
    payload = {"schema_version":"agent-runtime-work-registration/v1","project_id":"PROJECT-TEMPLATE-SMOKE","origin_type":"owner_request","origin_ref":"tests","created_by":"test","now":"2026-07-29T00:00:00+09:00","initiative":{"id":"INIT-TEMPLATE-SMOKE","title":"Smoke","summary":"Smoke","owner":"lead_engineer"},"taskset":{"id":"TASKSET-TEMPLATE-SMOKE","display_name":"Smoke","summary":"Smoke","order":990,"plan_slug":"smoke"},"tasks":[{"display_id":"TASK-AR-990","title":"Smoke","goal":"Smoke","acceptance":["probe"],"verification":["python scripts/verification_probe.py"],"units":[{"title":"Unit","context":"Smoke","inputs":["scripts/verification_probe.py"],"target_files":["scripts/verification_probe.py"],"scope":"Smoke","steps":["Run probe"],"acceptance":["probe"],"verification":["python scripts/verification_probe.py"],"handoff":"done","stop_condition":"done"}]}]}
    registration = host / "registration.json"; registration.write_text(json.dumps(payload), encoding="utf-8")
    work = host / "scripts/work.py"
    now = _run([PYTHON, str(work), "--root", str(host), "now"], cwd=host)
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}\n?",
        now.stdout,
    )
    _run([PYTHON, str(work), "--root", str(host), "new", "--input", str(registration), "--json"], cwd=host)
    _run([PYTHON, str(work), "--root", str(host), "status", "--json"], cwd=host)
    _run([PYTHON, str(work), "--root", str(host), "verify", "UNIT-TASK-AR-990-001", "--json"], cwd=host)
    _run([PYTHON, str(work), "--root", str(host), "close", "UNIT-TASK-AR-990-001", "--actual-hours", "1", "--actual-tokens", "1", "--json"], cwd=host)
    _run([PYTHON, str(work), "--root", str(host), "verify", "TASK-AR-990", "--json"], cwd=host)
    _run([PYTHON, str(work), "--root", str(host), "close", "TASK-AR-990", "--actual-hours", "1", "--actual-tokens", "1", "--json"], cwd=host)
    _run(["git", "add", "."], cwd=host); _run(["git", "commit", "-qm", "lifecycle"], cwd=host)
    baseline = _run([PYTHON, "scripts/session_baseline.py", "--root", str(host), "--output-dir", str(host / "agents/runtime/session_baselines"), "--json"], cwd=host)
    baseline_path = Path(json.loads(baseline.stdout)["baseline"])
    session_cache = f"scripts/__pycache__/session_baseline.{sys.implementation.cache_tag}.pyc"
    _run([PYTHON, "scripts/dirty_intake.py", "--root", str(host), "--baseline", str(baseline_path), "--declared-path", str(baseline_path.relative_to(host)), "--declared-path", session_cache, "--check", "--json"], cwd=host)
    body = host / "body.md"; body.write_text("ready", encoding="utf-8")
    _run([PYTHON, "scripts/save_report.py", "brief", "--title", "Smoke", "--audience", "Owner", "--scale", "mini", "--body-file", str(body), "--now", "2026-07-29T00:00:00+09:00", "--root", str(host)], cwd=host)
    report = next((host / "agents/lead_engineer/reports").glob("BRIEF-*.md"))
    assert 'type: "report"' in report.read_text(encoding="utf-8") and 'kind: "BRIEF"' in report.read_text(encoding="utf-8") and "Bottom Line:" in report.read_text(encoding="utf-8")
    index = (host / "agents/lead_engineer/reports/INDEX.md").read_text(encoding="utf-8")
    assert "| ID | Kind | Date | Audience | Title |" in index and f"[{report.stem}]({report.name})" in index
    assert (host / "agents/lead_engineer/reports/VIEW-by-kind.md").exists()
    docs = _run([PYTHON, "scripts/check_agent_docs.py"], cwd=host, expect_zero=False)
    # The minimal fixture intentionally lacks several legacy documentation
    # baseline records, so its whole-project checker is not yet zero-exit.
    # A saved report must nevertheless add no validator diagnostic on either
    # stream (the checker has emitted diagnostics on both across versions).
    docs_output = (docs.stdout or "") + (docs.stderr or "")
    assert report.name not in docs_output
    _run([PYTHON, "scripts/generate_report_views.py", "--check"], cwd=host)
    gate = _run([PYTHON, "scripts/runtime_asset_usage.py", "--root", str(host), "--check"], cwd=host)
    assert "block=0" in gate.stdout


def test_concurrent_workers_on_same_message_generate_single_reply(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    inbox = host / "agents" / "messages" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    message_id = "MSG-20260608-999999-race"
    incoming = _write_message(inbox, message_id)

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")

    command = [
        PYTHON, "scripts/agent_worker.py", "--role", "qa", "--provider", "dummy",
        "--once", "--timeout", "4", "--poll-interval", "0.1", "--quiet",
    ]
    p1 = subprocess.Popen(
        command,
        cwd=host,
        env=command_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # Small overlap window to stress the claim race.
    time.sleep(0.05)
    p2 = subprocess.Popen(
        command,
        cwd=host,
        env=command_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    out1, err1 = p1.communicate(timeout=20)
    out2, err2 = p2.communicate(timeout=20)
    assert p1.returncode == 0, out1 + err1
    assert p2.returncode == 0, out2 + err2

    source = _parse_frontmatter(incoming)
    assert source.get("status") == "answered"

    replies = [p for p in inbox.iterdir() if p.suffix == ".md" and p.name != incoming.name]
    assert len(replies) == 1, replies
    parsed = [_parse_frontmatter(p) for p in replies]
    assert parsed[0].get("type") == "reply"
    assert parsed[0].get("in_reply_to") == message_id


def test_worker_processes_multiple_messages_with_stale_recovery(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    inbox = host / "agents" / "messages" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    runtime = host / "agents" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    claim_dir = runtime / "claims"
    claim_dir.mkdir(parents=True, exist_ok=True)

    message_ids = [
        "MSG-20260608-111111-batch",
        "MSG-20260608-222222-batch",
        "MSG-20260608-333333-batch",
    ]
    messages = [_write_message(inbox, message_id) for message_id in message_ids]

    stale_claim = {
        "message_id": message_ids[1],
        "role": "qa",
        "pid": 12345,
        "hostname": "stale-worker",
        "claimed_at": 1.0,
        "expires_at": 2.0,
        "path": message_ids[1],
    }
    (claim_dir / f"{message_ids[1]}.claim").write_text(
        json.dumps(stale_claim, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    worker = _run(
        [
            PYTHON, "scripts/agent_worker.py", "--role", "qa", "--provider", "dummy",
            "--poll-interval", "0.05", "--timeout", "6", "--quiet"
        ],
        cwd=host,
        env=command_env,
    )
    assert worker.returncode == 0

    claimed = [_parse_frontmatter(p).get("status") for p in messages]
    assert all(s == "answered" for s in claimed), claimed

    replies = [p for p in inbox.iterdir() if p.suffix == ".md" and p.name not in {m.name for m in messages}]
    assert len(replies) == len(message_ids), replies
    reply_targets = {
        _parse_frontmatter(r).get("in_reply_to")
        for r in replies
    }
    assert reply_targets == set(message_ids)

    assert not (claim_dir / f"{message_ids[1]}.claim").exists()


def test_warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    report_path = Path(
        os.getenv(
            "PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH",
            str(tmp_path / "template-warning-summary-gate-report.jsonl"),
        )
    )

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    summary_path = tmp_path / "template-warning-summaries.jsonl"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_records = [
        {
            "schema_version": "pass39-warning-summary-v0",
            "warning_code_counts": {
                "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1
            },
            "run": "run-template-smoke-76",
            "event": "smoke",
            "ts_window_start": "2026-06-09T00:00:00Z",
            "window_end_time": "2026-06-09T00:01:00Z",
            "total_warnings": 2,
        },
        {
            "schema_version": "pass39-warning-summary-legacy",
            "warning_code_counts": {
                "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1
            },
            "run": "run-template-smoke-76",
            "event": "smoke",
            "window": "2026-06-09T00:00:00Z/2026-06-09T00:01:00Z",
            "total_warnings": 1,
        },
    ]
    summary_path.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in legacy_records) + "\n",
        encoding="utf-8",
    )

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    command = [
        PYTHON,
        "scripts/message_queue.py",
        "warning-summary-gate",
        "--summary-path",
        str(summary_path),
        "--run-id",
        "run-template-smoke-76",
        "--event-name",
        "smoke",
        "--window-start",
        "2026-06-09T00:00:00Z",
        "--window-end",
        "2026-06-09T00:01:00Z",
        "--warning",
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=1",
        "--max-warnings-per-context",
        "2",
        "--code-threshold",
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=2",
        "--report-path",
        str(report_path),
    ]
    pass_result = _run(command, cwd=host, env=command_env)
    pass_report = json.loads(pass_result.stdout.strip())
    assert pass_report["policy_passed"] is True
    assert pass_report["record_count"] == 1
    merged = pass_report["records"][0]
    assert merged["schema_version"] == "pass39-warning-summary-legacy"
    assert merged["total_warnings"] == 2
    assert merged["warning_code_counts"]["PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"] == 1
    assert report_path.exists()
    artifact_records = [
        json.loads(line)
        for line in report_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(artifact_records) == 1
    assert artifact_records[0]["record_count"] == 1
    assert artifact_records[0]["code_warning_limits"].get("PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE") == 2

    fail_command = list(command)
    fail_command[fail_command.index("--max-warnings-per-context") + 1] = "1"
    fail_result = _run(fail_command, cwd=host, env=command_env, expect_zero=False)
    fail_report = json.loads(fail_result.stdout.strip())
    assert fail_result.returncode != 0
    assert fail_report["policy_passed"] is False
    assert any("max 1" in reason for reason in fail_report["reasons"])

    code_fail_command = list(command)
    code_fail_command[code_fail_command.index("--max-warnings-per-context") + 1] = "99"
    threshold_arg_index = code_fail_command.index("--code-threshold") + 1
    code_fail_command[threshold_arg_index] = (
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=0"
    )
    code_fail_result = _run(
        code_fail_command,
        cwd=host,
        env=command_env,
        expect_zero=False,
    )
    code_fail_report = json.loads(code_fail_result.stdout.strip())
    assert code_fail_result.returncode != 0
    assert code_fail_report["policy_passed"] is False
    assert any(
        "code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE" in reason
        for reason in code_fail_report["reasons"]
    )

    dry_run_command = list(code_fail_command)
    dry_run_command.extend(["--dry-run"])
    dry_run_result = _run(dry_run_command, cwd=host, env=command_env)
    dry_run_report = json.loads(dry_run_result.stdout.strip())
    assert dry_run_result.returncode == 0
    assert dry_run_report["policy_passed"] is False
    assert dry_run_report["dry_run"] is True
