"""Consumer-host guard for the template owner governance gate (issue #273).

A generated project ships the template gate without the source repo's full
surface: `planning_loop.py` is not shipped, two checks assume the
`src/agent_runtime/templates/project` tree, and two more assume root-level
state surfaces. Host-proven skip logic (autofolio PR #148) downgrades exactly
those checks — loudly — in a consumer checkout, and skips nothing in the
source repo.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_GATE = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
)


def _load_gate_from(root: Path):
    """Import a deployed copy of the template gate so its ROOT is the consumer root."""
    target = root / "scripts" / "owner_governance_gate.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(TEMPLATE_GATE, target)
    spec = importlib.util.spec_from_file_location(f"gate_under_test_{root.name}", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
    )


def test_consumer_checkout_skips_absent_substrate(tmp_path: Path) -> None:
    gate = _load_gate_from(tmp_path)
    _git(tmp_path, "init", "-q")

    # Un-shipped script -> script-missing skip (planning_loop.py is not in templates).
    assert "script missing" in gate.skip_reason(
        ["scripts/planning_loop.py", "gate", "--trigger", "hook", "--action", "scan"]
    )

    # Shipped scripts whose substrate is absent -> host-checkout skip.
    for name in sorted(gate.SOURCE_ONLY_CHECKS | gate.ROOT_STATE_CHECKS):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("raise SystemExit(1)\n", encoding="utf-8")
    for name in sorted(gate.SOURCE_ONLY_CHECKS | gate.ROOT_STATE_CHECKS):
        reason = gate.skip_reason([name, "--check"])
        assert reason.startswith("host checkout skip"), (name, reason)
        # And run() must return 0 without executing the (failing) script.
        assert gate.run([name, "--check"]) == 0


def test_consumer_skip_is_loud_not_silent(tmp_path: Path, capsys) -> None:
    gate = _load_gate_from(tmp_path)
    rc = gate.run(["scripts/planning_loop.py", "gate"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "owner-governance: skip: scripts/planning_loop.py gate (script missing" in out


def test_root_state_surfaces_present_means_no_skip(tmp_path: Path) -> None:
    gate = _load_gate_from(tmp_path)
    _git(tmp_path, "init", "-q")
    for name in gate.ROOT_STATE_CHECKS:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("raise SystemExit(0)\n", encoding="utf-8")
    for surface in gate.ROOT_STATE_SURFACES:
        (tmp_path / surface).write_text("state\n", encoding="utf-8")
    _git(tmp_path, "add", "--", *gate.ROOT_STATE_SURFACES)
    for name in gate.ROOT_STATE_CHECKS:
        assert gate.skip_reason([name, "--check"]) == ""


def test_portable_state_surfaces_skip_legacy_and_run_portable_checks(
    tmp_path: Path,
) -> None:
    gate = _load_gate_from(tmp_path)
    _git(tmp_path, "init", "-q")
    for name in gate.ROOT_STATE_CHECKS:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("raise SystemExit(0)\n", encoding="utf-8")
    for surface in gate.PORTABLE_STATE_SURFACES:
        path = tmp_path / surface
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("state\n", encoding="utf-8")
    _git(tmp_path, "add", "--", *gate.PORTABLE_STATE_SURFACES)

    for name in gate.LEGACY_ROOT_STATE_CHECKS:
        assert gate.skip_reason([name, "--check"]).startswith(
            "host checkout skip: portable state model selected"
        )
    for name in gate.PORTABLE_STATE_CHECKS:
        assert gate.skip_reason([name, "--check"]) == ""


def _write_root_state_fixture(
    root: Path,
    gate: object,
    *,
    tracked: bool,
) -> None:
    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "taskset_work_gate.py").write_text(
        """from pathlib import Path

board = Path("BACKLOG-BOARD.md")
raise SystemExit(9 if not board.exists() or board.read_text(encoding="utf-8") != "clean\\n" else 0)
""",
        encoding="utf-8",
    )
    for name in gate.ROOT_STATE_SURFACES:
        (root / name).write_text("clean\n", encoding="utf-8")
    _git(root, "init", "-q")
    if tracked:
        _git(
            root,
            "add",
            "--",
            "scripts/taskset_work_gate.py",
            *gate.ROOT_STATE_SURFACES,
        )


def _commit_root_state_fixture(root: Path) -> None:
    _git(
        root,
        "-c",
        "user.name=Agent Runtime Test",
        "-c",
        "user.email=agent-runtime-test@example.invalid",
        "commit",
        "-qm",
        "root state fixture",
    )


def test_untracked_protected_paths_are_not_opened_or_treated_as_root_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _load_gate_from(tmp_path)
    _write_root_state_fixture(tmp_path, gate, tracked=False)
    protected = {
        tmp_path / "BACKLOG-BOARD.md",
        tmp_path / "agents/runtime/events/stop_events-2099-01-01.jsonl",
        tmp_path / "trading_bot.db-shm",
        tmp_path / "trading_bot.db-wal",
    }
    for path in protected:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("must-not-open\n", encoding="utf-8")

    opened: list[Path] = []
    original_open = io.open

    def guarded_open(file: object, *args: object, **kwargs: object):
        if not isinstance(file, int):
            candidate = Path(file)  # type: ignore[arg-type]
            if candidate in protected:
                opened.append(candidate)
                raise AssertionError(
                    f"protected fixture opened: {candidate.name}"
                )
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", guarded_open)

    reason = gate.skip_reason(
        ["scripts/taskset_work_gate.py", "--check"],
        root=tmp_path,
    )

    assert "root state surfaces absent from HEAD and index" in reason
    assert (
        gate.run(
            ["scripts/taskset_work_gate.py", "--check"],
            root=tmp_path,
        )
        == 0
    )
    assert opened == []


@pytest.mark.parametrize("tracked_count", [1, 2])
@pytest.mark.parametrize("commit_partial", [False, True])
def test_partial_head_or_index_root_state_fails_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    tracked_count: int,
    commit_partial: bool,
) -> None:
    gate = _load_gate_from(tmp_path)
    _write_root_state_fixture(tmp_path, gate, tracked=False)
    _git(
        tmp_path,
        "add",
        "--",
        *gate.ROOT_STATE_SURFACES[:tracked_count],
    )
    if commit_partial:
        _commit_root_state_fixture(tmp_path)

    assert (
        gate.run(
            ["scripts/taskset_work_gate.py", "--check"],
            root=tmp_path,
        )
        == 1
    )
    assert "partially tracked" in capsys.readouterr().out


@pytest.mark.parametrize("stage_dirty", [False, True])
def test_tracked_dirty_root_state_runs_real_gate_and_fails_closed(
    tmp_path: Path,
    stage_dirty: bool,
) -> None:
    gate = _load_gate_from(tmp_path)
    _write_root_state_fixture(tmp_path, gate, tracked=True)
    (tmp_path / "BACKLOG-BOARD.md").write_text("dirty\n", encoding="utf-8")
    if stage_dirty:
        _git(tmp_path, "add", "--", "BACKLOG-BOARD.md")

    assert (
        gate.run(
            ["scripts/taskset_work_gate.py", "--check"],
            root=tmp_path,
        )
        == 9
    )


@pytest.mark.parametrize(
    "staged_deleted",
    [
        ("BACKLOG-BOARD.md",),
        ("BACKLOG-BOARD.md", "BACKLOG.md", "STATUS.md"),
    ],
)
def test_head_tracked_staged_deletion_fails_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    staged_deleted: tuple[str, ...],
) -> None:
    gate = _load_gate_from(tmp_path)
    _write_root_state_fixture(tmp_path, gate, tracked=True)
    _commit_root_state_fixture(tmp_path)
    _git(tmp_path, "rm", "-q", "--cached", "--", *staged_deleted)

    assert (
        gate.run(
            ["scripts/taskset_work_gate.py", "--check"],
            root=tmp_path,
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "staged deletion" in output
    assert all(path in output for path in staged_deleted)


def test_tracked_deleted_root_state_remains_visible_to_gate(
    tmp_path: Path,
) -> None:
    gate = _load_gate_from(tmp_path)
    _write_root_state_fixture(tmp_path, gate, tracked=True)
    (tmp_path / "BACKLOG-BOARD.md").unlink()

    assert gate.skip_reason(
        ["scripts/taskset_work_gate.py", "--check"],
        root=tmp_path,
    ) == ""
    assert (
        gate.run(
            ["scripts/taskset_work_gate.py", "--check"],
            root=tmp_path,
        )
        == 9
    )


def test_tracked_probe_failure_blocks_without_starting_subgate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    gate = _load_gate_from(tmp_path)
    scripts = tmp_path / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "taskset_work_gate.py").write_text(
        "raise AssertionError('must not execute')\n",
        encoding="utf-8",
    )
    started = False

    def unexpected_call(*args: object, **kwargs: object) -> int:
        nonlocal started
        started = True
        return 0

    monkeypatch.setattr(gate.subprocess, "call", unexpected_call)

    assert (
        gate.run(
            ["scripts/taskset_work_gate.py", "--check"],
            root=tmp_path,
        )
        == 1
    )
    assert started is False
    assert "tracked-state probe failed" in capsys.readouterr().out


def test_source_repo_never_skips_any_chain_entry() -> None:
    # In the source repo every substrate exists, so the guard must be inert:
    # importing the SHIPPED gate with ROOT=source-repo yields zero skips for
    # the full chain (regression guard for "skip logic ate a real check").
    spec = importlib.util.spec_from_file_location("template_gate_at_source", TEMPLATE_GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The template gate's ROOT is templates/project, which has no planning_loop
    # either — so evaluate against the SOURCE repo root instead by patching ROOT.
    module.ROOT = REPO_ROOT
    module.SOURCE_TEMPLATE_ROOT = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project"
    import re

    text = TEMPLATE_GATE.read_text(encoding="utf-8")
    chain = re.findall(r'\["(scripts/[a-z_]+\.py)"', text)
    assert chain, "failed to parse the check chain"
    for script in chain:
        assert module.skip_reason([script, "--check"]) == "", script


def test_consumer_owner_gate_runs_ownership_aware_continuity_check(
    tmp_path: Path,
    capsys,
) -> None:
    gate = _load_gate_from(tmp_path)
    template_root = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project"
    shutil.copyfile(
        template_root / "scripts" / "continuity_contract_gate.py",
        tmp_path / "scripts" / "continuity_contract_gate.py",
    )
    shutil.copytree(
        template_root / "scripts" / "agent_runtime",
        tmp_path / "scripts" / "agent_runtime",
    )
    shutil.copyfile(template_root / "AGENT_RUNTIME.md", tmp_path / "AGENT_RUNTIME.md")
    (tmp_path / "README.md").write_text("# Consumer product\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Host agent rules\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# Host Claude rules\n", encoding="utf-8")
    pointer = tmp_path / "agents" / "project" / "NEXT-SESSION-POINTER.yml"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(
        "\n".join(
            [
                "schema: agent-runtime-next-session-pointer/v1",
                "updated_at: 2026-07-30T00:00:00+09:00",
                "current_state:",
                "  task_set_id: TASKSET-CONSUMER",
                "  step_index: 1",
                "  step_total: 1",
                "  status_text: ready",
                "active_work:",
                "  current_agents: []",
                "resume:",
                "  active_task: TASK-CONSUMER",
                "roles:",
                "  owner: Owner",
                "pointers:",
                "  active_claims: []",
                "rules:",
                "  fail_closed: true",
                "verification:",
                "  required: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_runtime.yml").write_text(
        "\n".join(
            [
                "schema: agent-runtime-config/v2",
                "project: consumer-host",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/ycpiglet/agent_runtime.git",
                "  ref: exact-product",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
                "profiles:",
                "  - core",
                "ownership:",
                "  host_owned:",
                "    - AGENTS.md",
                "    - CLAUDE.md",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def digest(rel: str) -> str:
        return f"sha256:{hashlib.sha256((tmp_path / rel).read_bytes()).hexdigest()}"

    lock = {
        "schema": "agent-runtime-lock/v2",
        "project": "consumer-host",
        "upstream": {
            "package": "agent_runtime",
            "remote_url": "https://github.com/ycpiglet/agent_runtime.git",
            "ref": "exact-product",
        },
        "installed": {
            "ownership": {
                "AGENTS.md": "host_owned",
                "AGENT_RUNTIME.md": "managed",
                "CLAUDE.md": "host_owned",
                "agents/project/NEXT-SESSION-POINTER.yml": "seed_once",
                "scripts/continuity_contract_gate.py": "managed",
            },
            "managed_files": {
                "AGENT_RUNTIME.md": digest("AGENT_RUNTIME.md"),
                "scripts/continuity_contract_gate.py": digest(
                    "scripts/continuity_contract_gate.py"
                ),
            },
            "seeded": ["agents/project/NEXT-SESSION-POINTER.yml"],
        },
    }
    (tmp_path / "agent_runtime.lock.json").write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    assert gate.skip_reason(["scripts/continuity_contract_gate.py", "--check"]) == ""
    assert gate.run(["scripts/continuity_contract_gate.py", "--check"]) == 0
    assert "scripts/continuity_contract_gate.py --check -> 0" in capsys.readouterr().out
