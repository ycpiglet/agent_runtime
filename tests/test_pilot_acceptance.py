from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pilot_acceptance  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "pilots" / "bean-wiki" / "evidence.json"


def _payload() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _codes(payload: dict) -> set[str]:
    return {finding["code"] for finding in pilot_acceptance.validate_evidence(payload)}


def test_bean_wiki_fixture_is_replayable_and_truthfully_blocked():
    payload = _payload()
    assert payload["result"] == "blocked"
    assert pilot_acceptance.validate_evidence(payload) == []


def test_host_ownership_tamper_is_detected():
    payload = copy.deepcopy(_payload())
    payload["preservation"]["host_assets"][0]["after"] = "0" * 64
    assert "host-asset-overwrite" in _codes(payload)


def test_missing_task_claim_trace_is_detected():
    payload = copy.deepcopy(_payload())
    payload["tasks"][1]["claim_trace"] = {}
    assert "missing-claim-trace" in _codes(payload)


def test_false_model_observation_is_detected():
    payload = copy.deepcopy(_payload())
    payload["tasks"][1]["routing"]["observed_model"] = "invented-model"
    payload["tasks"][1]["routing"]["actual_model_status"] = "unverified"
    assert "false-model-observation" in _codes(payload)


def test_nonzero_external_effect_is_detected():
    payload = copy.deepcopy(_payload())
    payload["external_effects"]["network_delivery"] = 1
    assert "external-effect-nonzero" in _codes(payload)


def test_cli_check_passes_for_bundled_fixture():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "pilot_acceptance.py"),
            "--host",
            "bean-wiki",
            "--check",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "pass"
