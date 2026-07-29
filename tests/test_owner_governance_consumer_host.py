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
import json
import shutil
import subprocess
import sys
from pathlib import Path

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


def test_consumer_checkout_skips_absent_substrate(tmp_path: Path) -> None:
    gate = _load_gate_from(tmp_path)

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
    for name in gate.ROOT_STATE_CHECKS:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("raise SystemExit(0)\n", encoding="utf-8")
    for surface in gate.ROOT_STATE_SURFACES:
        (tmp_path / surface).write_text("state\n", encoding="utf-8")
    for name in gate.ROOT_STATE_CHECKS:
        assert gate.skip_reason([name, "--check"]) == ""


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
