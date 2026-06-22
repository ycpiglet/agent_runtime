"""TDD tests for scripts/asset_lifecycle.py.

Tests verify:
- --propose lists low-reuse assets (reuse <= threshold, lifecycle=keep, status=active)
- --apply demotes keep->observe and is idempotent
- already-observe/deprecated assets are untouched
- high-reuse assets are never demoted
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "asset_lifecycle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("asset_lifecycle", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_registry(path: Path, assets: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent-runtime-asset-registry/v1",
        "version": 1,
        "updated_at": "2026-06-17T00:00:00+09:00",
        "status_scale": ["active", "watch", "deprecated", "removed"],
        "lifecycle_decisions": ["keep", "modify", "deprecate", "remove", "observe"],
        "assets": assets,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_file(path: Path, content: str = "# stub\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _registry_path(root: Path) -> Path:
    return root / "agents" / "project" / "RUNTIME-ASSET-REGISTRY.json"


# ---- fixture helpers -------------------------------------------------------


def _low_reuse_asset(asset_id: str = "capability.session_dashboard") -> dict:
    """Active keep asset with a single evidence hit (reuse=1)."""
    return {
        "id": asset_id,
        "kind": "script",
        "status": "active",
        "lifecycle": "keep",
        "paths": [f"scripts/{asset_id.split('.', 1)[1]}.py"],
        "evidence_paths": ["evidence.md"],
        "tokens": [asset_id],
        "min_recent_uses": 1,
    }


def _high_reuse_asset(asset_id: str = "gate.owner_governance") -> dict:
    """Active keep asset with many evidence hits (reuse > 1)."""
    return {
        "id": asset_id,
        "kind": "gate",
        "status": "active",
        "lifecycle": "keep",
        "paths": [f"scripts/owner_governance_gate.py"],
        "evidence_paths": ["evidence.md", "evidence2.md"],
        "tokens": [asset_id, "owner_governance_gate.py"],
        "min_recent_uses": 1,
    }


def _observe_asset(asset_id: str = "trigger.planning") -> dict:
    """Asset already in observe lifecycle."""
    return {
        "id": asset_id,
        "kind": "trigger",
        "status": "watch",
        "lifecycle": "observe",
        "paths": [f"scripts/planning_trigger.py"],
        "evidence_paths": [],
        "tokens": [asset_id],
        "min_recent_uses": 0,
    }


def _deprecated_asset(asset_id: str = "capability.old_thing") -> dict:
    return {
        "id": asset_id,
        "kind": "script",
        "status": "active",
        "lifecycle": "deprecate",
        "paths": [f"scripts/old_thing.py"],
        "evidence_paths": [],
        "tokens": [asset_id],
        "min_recent_uses": 0,
        "rationale": "replaced by new_thing",
    }


# ---- test helpers -----------------------------------------------------------


def _setup_low_reuse_fixture(tmp_path: Path) -> None:
    """Set up a registry with one low-reuse asset and stub files."""
    asset = _low_reuse_asset("capability.session_dashboard")
    write_registry(_registry_path(tmp_path), [asset])
    # Asset file must exist for runtime_asset_usage not to block
    write_file(tmp_path / "scripts" / "session_dashboard.py")
    # Evidence file contains ONE reference to the asset id (reuse=1)
    write_file(tmp_path / "evidence.md", "capability.session_dashboard appears here once.\n")


def _setup_high_reuse_fixture(tmp_path: Path) -> None:
    """Registry with a high-reuse asset (reuse=2 — two distinct evidence files)."""
    asset = _high_reuse_asset("gate.owner_governance")
    write_registry(_registry_path(tmp_path), [asset])
    write_file(tmp_path / "scripts" / "owner_governance_gate.py")
    # Two distinct evidence paths each containing a token -> reuse=2
    write_file(tmp_path / "evidence.md", "owner_governance_gate.py gate.owner_governance\n")
    write_file(tmp_path / "evidence2.md", "owner_governance_gate.py gate.owner_governance\n")


# ---- propose tests ----------------------------------------------------------


def test_propose_lists_low_reuse_asset(tmp_path):
    lc = load_module()
    _setup_low_reuse_fixture(tmp_path)

    proposals = lc.propose(root=tmp_path, reuse_threshold=1)

    assert len(proposals) == 1
    assert proposals[0]["asset_id"] == "capability.session_dashboard"
    assert proposals[0]["current_lifecycle"] == "keep"
    assert proposals[0]["proposed_lifecycle"] == "observe"
    assert proposals[0]["reuse"] <= 1


def test_propose_json_output_is_valid(tmp_path):
    lc = load_module()
    _setup_low_reuse_fixture(tmp_path)

    proposals = lc.propose(root=tmp_path, reuse_threshold=1)
    # Must be JSON-serialisable
    encoded = json.dumps(proposals)
    decoded = json.loads(encoded)
    assert decoded[0]["asset_id"] == "capability.session_dashboard"


def test_propose_skips_high_reuse_asset(tmp_path):
    lc = load_module()
    _setup_high_reuse_fixture(tmp_path)

    proposals = lc.propose(root=tmp_path, reuse_threshold=1)

    # reuse=2 > threshold=1, so nothing should be proposed
    assert proposals == []


def test_propose_skips_already_observe_asset(tmp_path):
    lc = load_module()
    asset = _observe_asset()
    write_registry(_registry_path(tmp_path), [asset])
    write_file(tmp_path / "scripts" / "planning_trigger.py")

    proposals = lc.propose(root=tmp_path, reuse_threshold=1)

    assert proposals == []


def test_propose_skips_deprecated_asset(tmp_path):
    lc = load_module()
    asset = _deprecated_asset()
    write_registry(_registry_path(tmp_path), [asset])
    write_file(tmp_path / "scripts" / "old_thing.py")

    proposals = lc.propose(root=tmp_path, reuse_threshold=1)

    assert proposals == []


def test_propose_default_threshold_is_one(tmp_path):
    """Calling propose() with no threshold arg uses 1 by default."""
    lc = load_module()
    _setup_low_reuse_fixture(tmp_path)

    proposals = lc.propose(root=tmp_path)  # no reuse_threshold arg

    assert len(proposals) == 1


# ---- apply tests ------------------------------------------------------------


def test_apply_demotes_keep_to_observe(tmp_path):
    lc = load_module()
    _setup_low_reuse_fixture(tmp_path)

    result = lc.apply(root=tmp_path, reuse_threshold=1)

    assert result["demoted"] == ["capability.session_dashboard"]
    assert result["skipped"] == []

    reg = json.loads(_registry_path(tmp_path).read_text(encoding="utf-8"))
    asset = next(a for a in reg["assets"] if a["id"] == "capability.session_dashboard")
    assert asset["lifecycle"] == "observe"


def test_apply_is_idempotent(tmp_path):
    lc = load_module()
    _setup_low_reuse_fixture(tmp_path)

    result1 = lc.apply(root=tmp_path, reuse_threshold=1)
    result2 = lc.apply(root=tmp_path, reuse_threshold=1)

    # First run demotes; second run is a no-op
    assert result1["demoted"] == ["capability.session_dashboard"]
    assert result2["demoted"] == []
    assert "capability.session_dashboard" in result2["skipped"]


def test_apply_does_not_touch_observe_asset(tmp_path):
    lc = load_module()
    asset = _observe_asset()
    write_registry(_registry_path(tmp_path), [asset])
    write_file(tmp_path / "scripts" / "planning_trigger.py")

    result = lc.apply(root=tmp_path, reuse_threshold=1)

    assert result["demoted"] == []
    reg = json.loads(_registry_path(tmp_path).read_text(encoding="utf-8"))
    reloaded = next(a for a in reg["assets"] if a["id"] == "trigger.planning")
    assert reloaded["lifecycle"] == "observe"


def test_apply_does_not_touch_deprecated_asset(tmp_path):
    lc = load_module()
    asset = _deprecated_asset()
    write_registry(_registry_path(tmp_path), [asset])
    write_file(tmp_path / "scripts" / "old_thing.py")

    result = lc.apply(root=tmp_path, reuse_threshold=1)

    assert result["demoted"] == []
    reg = json.loads(_registry_path(tmp_path).read_text(encoding="utf-8"))
    reloaded = next(a for a in reg["assets"] if a["id"] == "capability.old_thing")
    assert reloaded["lifecycle"] == "deprecate"


def test_apply_does_not_demote_high_reuse(tmp_path):
    lc = load_module()
    _setup_high_reuse_fixture(tmp_path)

    result = lc.apply(root=tmp_path, reuse_threshold=1)

    assert result["demoted"] == []
    reg = json.loads(_registry_path(tmp_path).read_text(encoding="utf-8"))
    asset = next(a for a in reg["assets"] if a["id"] == "gate.owner_governance")
    assert asset["lifecycle"] == "keep"


def test_apply_preserves_registry_structure(tmp_path):
    """Applying should not drop unrelated fields like schema, version, etc."""
    lc = load_module()
    _setup_low_reuse_fixture(tmp_path)

    lc.apply(root=tmp_path, reuse_threshold=1)

    reg = json.loads(_registry_path(tmp_path).read_text(encoding="utf-8"))
    assert reg["schema"] == "agent-runtime-asset-registry/v1"
    assert "version" in reg
    assert "lifecycle_decisions" in reg


def test_apply_mixed_registry(tmp_path):
    """With multiple assets, only the qualifying ones are demoted."""
    lc = load_module()
    low = _low_reuse_asset("capability.session_dashboard")
    high = _high_reuse_asset("gate.owner_governance")
    obs = _observe_asset("trigger.planning")
    write_registry(_registry_path(tmp_path), [low, high, obs])
    write_file(tmp_path / "scripts" / "session_dashboard.py")
    write_file(tmp_path / "scripts" / "owner_governance_gate.py")
    write_file(tmp_path / "scripts" / "planning_trigger.py")
    write_file(tmp_path / "evidence.md",
               "capability.session_dashboard once\n"
               "owner_governance_gate.py gate.owner_governance\n")
    write_file(tmp_path / "evidence2.md", "owner_governance_gate.py gate.owner_governance\n")

    result = lc.apply(root=tmp_path, reuse_threshold=1)

    assert result["demoted"] == ["capability.session_dashboard"]
    reg = json.loads(_registry_path(tmp_path).read_text(encoding="utf-8"))
    by_id = {a["id"]: a for a in reg["assets"]}
    assert by_id["capability.session_dashboard"]["lifecycle"] == "observe"
    assert by_id["gate.owner_governance"]["lifecycle"] == "keep"
    assert by_id["trigger.planning"]["lifecycle"] == "observe"
