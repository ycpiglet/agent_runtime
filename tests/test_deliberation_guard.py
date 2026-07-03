from __future__ import annotations

import importlib.util
import json
import shutil
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_SRC = REPO_ROOT / "agents" / "project" / "DELIBERATION-GUARDRAILS.yml"

_spec = importlib.util.spec_from_file_location(
    "deliberation_guard_under_test", REPO_ROOT / "scripts" / "deliberation_guard.py"
)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


def _seed(root: Path) -> Path:
    policy = root / "agents" / "project" / "DELIBERATION-GUARDRAILS.yml"
    policy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(POLICY_SRC, policy)
    return root


def test_missing_policy_fails_closed(tmp_path: Path) -> None:
    decision = guard.check_run(tmp_path)
    assert decision["allowed"] is False
    assert any("fail closed" in reason for reason in decision["reasons"])


def test_kill_switch_blocks_run(tmp_path: Path, monkeypatch) -> None:
    _seed(tmp_path)
    monkeypatch.setenv("AGENT_RUNTIME_DELIBERATION_DISABLE", "1")
    decision = guard.check_run(tmp_path)
    assert decision["allowed"] is False
    assert any("kill switch" in reason for reason in decision["reasons"])


def test_allowed_run_within_limits(tmp_path: Path, monkeypatch) -> None:
    _seed(tmp_path)
    monkeypatch.delenv("AGENT_RUNTIME_DELIBERATION_DISABLE", raising=False)
    decision = guard.check_run(tmp_path, personas=5, est_tokens=20000)
    assert decision["allowed"] is True, decision["reasons"]


def test_per_run_caps_block_oversized_runs(tmp_path: Path, monkeypatch) -> None:
    _seed(tmp_path)
    monkeypatch.delenv("AGENT_RUNTIME_DELIBERATION_DISABLE", raising=False)
    decision = guard.check_run(tmp_path, personas=99, est_tokens=999999)
    assert decision["allowed"] is False
    assert any("max_personas_per_run" in reason for reason in decision["reasons"])
    assert any("max_est_tokens_per_run" in reason for reason in decision["reasons"])


def test_min_interval_throttles_back_to_back_runs(tmp_path: Path, monkeypatch) -> None:
    _seed(tmp_path)
    monkeypatch.delenv("AGENT_RUNTIME_DELIBERATION_DISABLE", raising=False)
    now = time.time()
    guard.record_run(tmp_path, personas=3, est_tokens=1000, now_ts=now - 60)
    decision = guard.check_run(tmp_path, personas=3, est_tokens=1000, now_ts=now)
    assert decision["allowed"] is False
    assert any("min interval" in reason for reason in decision["reasons"])


def test_daily_ceiling_blocks_after_max_runs(tmp_path: Path, monkeypatch) -> None:
    _seed(tmp_path)
    monkeypatch.delenv("AGENT_RUNTIME_DELIBERATION_DISABLE", raising=False)
    now = time.time()
    for index in range(8):
        guard.record_run(tmp_path, personas=3, est_tokens=1000, now_ts=now - 86000 + index * 3700)
    decision = guard.check_run(tmp_path, personas=3, est_tokens=1000, now_ts=now)
    assert decision["allowed"] is False
    assert any("max_runs_per_day" in reason for reason in decision["reasons"])


def test_output_contract_requires_advisory_only(tmp_path: Path) -> None:
    _seed(tmp_path)
    ok = guard.validate_output(tmp_path, {"mutation": "none", "verdict": "adopt"})
    assert ok["valid"] is True, ok["violations"]

    bad_mutation = guard.validate_output(tmp_path, {"mutation": "apply", "verdict": "adopt"})
    assert bad_mutation["valid"] is False

    side_effect = guard.validate_output(tmp_path, {"mutation": "none", "execute": "git push"})
    assert side_effect["valid"] is False
    assert any("execute" in violation for violation in side_effect["violations"])


def test_ledger_round_trip_and_record(tmp_path: Path, monkeypatch) -> None:
    _seed(tmp_path)
    monkeypatch.delenv("AGENT_RUNTIME_DELIBERATION_DISABLE", raising=False)
    ledger = guard.record_run(tmp_path, personas=4, est_tokens=5000, topic="test topic")
    lines = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert lines[-1]["personas"] == 4
    assert lines[-1]["topic"] == "test topic"
