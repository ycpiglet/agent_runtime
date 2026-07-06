"""Consumer-host guard for the template owner governance gate (issue #273).

A generated project ships the template gate without the source repo's full
surface: `planning_loop.py` is not shipped, two checks assume the
`src/agent_runtime/templates/project` tree, and two more assume root-level
state surfaces. Host-proven skip logic (autofolio PR #148) downgrades exactly
those checks — loudly — in a consumer checkout, and skips nothing in the
source repo.
"""

from __future__ import annotations

import importlib.util
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
