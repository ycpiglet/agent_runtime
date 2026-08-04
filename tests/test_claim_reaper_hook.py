"""Tests for the SessionStart claim-reaper hook wrapper (best-effort, non-blocking)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_runtime import claim_store  # noqa: E402
import claim_reaper_hook  # noqa: E402

# A deadline far in the past so the claim is provably dead regardless of wall clock.
DEAD_EXPIRES = "2020-01-01T00:00:00+09:00"


def _dead_claim(tmp_path: Path) -> Path:
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    path = claim_dir / "CLAIM-dead.json"
    path.write_text(json.dumps({
        "schema": claim_store.WITNESS_SCHEMA,
        "claim_id": "CLAIM-dead", "task_id": "TASK-AR-1", "agent_role": "lead-engineer",
        "status": "claimed", "expires_at": DEAD_EXPIRES,
        "lease": {"expires_at": DEAD_EXPIRES},
    }), encoding="utf-8")
    claim_store.initialize_store(tmp_path, witness_claim_id="CLAIM-dead")
    return path


def test_hook_auto_applies_by_default(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("AGENT_RUNTIME_REAPER_AUTO_APPLY", raising=False)
    monkeypatch.delenv("AGENT_RUNTIME_REAPER_DISABLE", raising=False)
    path = _dead_claim(tmp_path)
    rc = claim_reaper_hook.main(["--root", str(tmp_path)])
    assert rc == 0
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "expired"
    assert "reaped" in capsys.readouterr().out


def test_hook_report_only_when_disabled_apply(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RUNTIME_REAPER_AUTO_APPLY", "0")
    path = _dead_claim(tmp_path)
    rc = claim_reaper_hook.main(["--root", str(tmp_path)])
    assert rc == 0
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "claimed"  # untouched


def test_hook_disabled_does_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RUNTIME_REAPER_DISABLE", "1")
    path = _dead_claim(tmp_path)
    rc = claim_reaper_hook.main(["--root", str(tmp_path)])
    assert rc == 0
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "claimed"


def test_hook_is_best_effort_on_bad_root(tmp_path, monkeypatch):
    # Nonexistent root: no claims dir -> nothing to do, still exit 0.
    rc = claim_reaper_hook.main(["--root", str(tmp_path / "does-not-exist")])
    assert rc == 0
