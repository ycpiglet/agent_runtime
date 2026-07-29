from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pilot_acceptance  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "pilots" / "bean-wiki" / "evidence.json"
GREEN_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "pilots"
    / "bean-wiki"
    / "evidence-green-attempt-5.json"
)
CONTRACT_DIR = ROOT / "tests" / "fixtures" / "pilots" / "contracts"


def _payload(path: Path = FIXTURE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _codes(payload: dict) -> set[str]:
    return {
        finding["code"]
        for finding in pilot_acceptance.validate_evidence(
            payload,
            expected_host="bean-wiki",
        )
    }


def test_bean_wiki_fixture_is_replayable_and_truthfully_blocked():
    payload = _payload()
    assert payload["result"] == "blocked"
    assert pilot_acceptance.validate_evidence(payload, expected_host="bean-wiki") == []


def test_historical_red_semantic_digest_is_immutable():
    assert (
        pilot_acceptance._semantic_sha256(_payload())
        == "e8a6119f3c6cef815c352600188f57c48e669e9d650b3e4e1b67f751a1d8582e"
    )


def test_green_attempt_five_uses_its_own_exact_contract():
    payload = _payload(GREEN_FIXTURE)
    assert payload["result"] == "passed"
    assert (
        pilot_acceptance._semantic_sha256(payload)
        == "8a56c8e5a89bfb5bbd7c6224be70f1ec69e41c339dcfe5b0c542b0b26361c39f"
    )
    assert pilot_acceptance.validate_evidence(payload, expected_host="bean-wiki") == []


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


def test_green_required_package_install_effect_is_enforced():
    payload = _payload(GREEN_FIXTURE)
    payload["external_effects"]["package_install"] = 1
    assert "external-effect-nonzero" in _codes(payload)


def test_boolean_false_is_not_accepted_as_an_external_effect_count():
    payload = copy.deepcopy(_payload())
    payload["external_effects"]["network_delivery"] = False
    assert "external-effect-nonzero" in _codes(payload)


def test_finding_priority_downgrade_and_false_pass_are_detected():
    payload = copy.deepcopy(_payload())
    for finding in payload["findings"]:
        if finding["priority"] == "P0":
            finding["priority"] = "P1"
    payload["result"] = "pass"
    codes = _codes(payload)
    assert "finding-contract-mismatch" in codes
    assert "result-contract-mismatch" in codes


def test_regex_valid_but_invented_claim_is_detected():
    payload = copy.deepcopy(_payload())
    payload["tasks"][1]["claim_trace"]["claim_id"] = "CLAIM-invented-but-valid"
    assert "task-contract-mismatch" in _codes(payload)


def test_self_asserted_provider_usage_without_observation_is_detected():
    payload = copy.deepcopy(_payload())
    routing = payload["tasks"][1]["routing"]
    routing["provider_usage_verified"] = True
    routing["input_tokens"] = 100
    routing["output_tokens"] = 20
    routing["cost"] = 0.01
    routing["savings_claim"] = "90%"
    codes = _codes(payload)
    assert "invalid-provider-usage-proof" in codes
    assert "unsupported-savings-claim" in codes


def test_bootstrap_and_post_registration_counts_are_contract_bound():
    payload = copy.deepcopy(_payload())
    payload["bootstrap"]["consumer_commit_count"] = False
    payload["adoption"]["post_work_registration_reconcile"]["conflicts"] = 0
    codes = _codes(payload)
    assert "bootstrap-effect-nonzero" in codes
    assert "post-registration-reconcile-mismatch" in codes


def test_content_count_is_contract_bound():
    payload = copy.deepcopy(_payload())
    payload["preservation"]["content"]["file_count"] = 0
    assert "content-file-count-mismatch" in _codes(payload)


def test_any_unrecognized_semantic_tamper_is_detected():
    payload = copy.deepcopy(_payload())
    payload["unrecognized_claim"] = "still a mutation"
    assert "fixture-semantic-digest-mismatch" in _codes(payload)


def test_absolute_local_path_in_fixture_is_detected():
    payload = copy.deepcopy(_payload())
    payload["tasks"][0]["output_refs"][0] = Path("/", "private", "evidence.json").as_posix()
    assert "absolute-path-leak" in _codes(payload)


def test_unknown_pilot_contract_fails_closed():
    payload = _payload(GREEN_FIXTURE)
    payload["pilot_id"] = "bean-wiki-v080-unknown"
    assert "unknown-pilot-contract" in _codes(payload)


def test_cross_host_evidence_cannot_reuse_a_contract():
    payload = _payload(GREEN_FIXTURE)
    payload["host"] = "other-host"
    codes = {
        finding["code"]
        for finding in pilot_acceptance.validate_evidence(
            payload,
            expected_host="bean-wiki",
        )
    }
    assert "host-contract-mismatch" in codes
    assert "unknown-pilot-contract" in codes


def test_duplicate_contract_pair_fails_registry_load(tmp_path: Path):
    contract = json.loads(
        (
            CONTRACT_DIR / "bean-wiki-v080-red-pilot.json"
        ).read_text(encoding="utf-8")
    )
    for name in ("one.json", "two.json"):
        (tmp_path / name).write_text(
            json.dumps(contract, indent=2) + "\n",
            encoding="utf-8",
        )
    with pytest.raises(
        pilot_acceptance.ContractRegistryError,
        match="duplicate-contract",
    ):
        pilot_acceptance.load_contract_registry(tmp_path)


def test_cross_host_pilot_id_reuse_fails_registry_load(tmp_path: Path):
    contract = json.loads(
        (
            CONTRACT_DIR / "bean-wiki-v080-red-pilot.json"
        ).read_text(encoding="utf-8")
    )
    other = copy.deepcopy(contract)
    other["host"] = "other-host"
    for name, payload in (("one.json", contract), ("two.json", other)):
        (tmp_path / name).write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
    with pytest.raises(
        pilot_acceptance.ContractRegistryError,
        match="cross-host-pilot-reuse",
    ):
        pilot_acceptance.load_contract_registry(tmp_path)


def test_contract_cannot_drop_core_external_effect_guard(tmp_path: Path):
    contract = json.loads(
        (
            CONTRACT_DIR / "bean-wiki-v080-red-pilot.json"
        ).read_text(encoding="utf-8")
    )
    contract["required_external_effects"].remove("network_delivery")
    (tmp_path / "invalid.json").write_text(
        json.dumps(contract, indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        pilot_acceptance.ContractRegistryError,
        match="required-external-effects",
    ):
        pilot_acceptance.load_contract_registry(tmp_path)


def test_malformed_contract_digest_fails_registry_load(tmp_path: Path):
    contract = json.loads(
        (
            CONTRACT_DIR / "bean-wiki-v080-red-pilot.json"
        ).read_text(encoding="utf-8")
    )
    contract["evidence_semantic_sha256"] = "not-a-digest"
    (tmp_path / "invalid.json").write_text(
        json.dumps(contract, indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        pilot_acceptance.ContractRegistryError,
        match="semantic-digest",
    ):
        pilot_acceptance.load_contract_registry(tmp_path)


def test_non_string_contract_path_fails_closed(tmp_path: Path):
    contract = json.loads(
        (
            CONTRACT_DIR / "bean-wiki-v080-red-pilot.json"
        ).read_text(encoding="utf-8")
    )
    contract["post_registration_conflicts"] = [{"path": "owner-docs.yml"}]
    (tmp_path / "invalid.json").write_text(
        json.dumps(contract, indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        pilot_acceptance.ContractRegistryError,
        match="conflict-paths",
    ):
        pilot_acceptance.load_contract_registry(tmp_path)


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
    output = json.loads(result.stdout)
    assert output["status"] == "pass"
    assert output["fixture"] == "tests/fixtures/pilots/bean-wiki/evidence.json"
    assert not output["fixture"].startswith("/")


def test_cli_check_passes_for_truthful_green_fixture():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "pilot_acceptance.py"),
            "--host",
            "bean-wiki",
            "--fixture",
            str(GREEN_FIXTURE.relative_to(ROOT)),
            "--check",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "pass"
    assert output["contract_id"] == "bean-wiki:bean-wiki-v080-green-attempt-5"
