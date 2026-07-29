from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from copy import deepcopy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "pilot_isolation_gate.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pilot_isolation_gate  # noqa: E402


SHA_A = "a" * 64
SHA_B = "b" * 64
HEAD_A = "1" * 40
HEAD_B = "2" * 40


def _snapshot(
    head: str = HEAD_A,
    status: str = SHA_A,
    tracked_diff: str = SHA_A,
) -> dict[str, str]:
    return {
        "head": head,
        "status_sha256": status,
        "tracked_diff_sha256": tracked_diff,
    }


def _payload(tmp_path: Path) -> dict[str, object]:
    target = (tmp_path / "attempt-5").resolve()
    frozen = (tmp_path / "attempt-4-frozen").resolve()
    live = (tmp_path / "bean-primary-live").resolve()
    return {
        "schema": "agent-runtime-pilot-isolation/v1",
        "pilot_id": "bean-wiki-attempt-5",
        "observed_write_roots": [str(target)],
        "checkouts": [
            {
                "id": "attempt-5",
                "role": "disposable_target",
                "root": str(target),
                "before": _snapshot(),
                "after": _snapshot(status=SHA_B, tracked_diff=SHA_B),
                "change_attribution": "authorized_target",
            },
            {
                "id": "attempt-4",
                "role": "frozen_control",
                "root": str(frozen),
                "before": _snapshot(),
                "after": _snapshot(),
                "change_attribution": "none",
            },
            {
                "id": "primary",
                "role": "live_observation",
                "root": str(live),
                "before": _snapshot(),
                "after": _snapshot(),
                "change_attribution": "none",
            },
        ],
    }


def _run(
    tmp_path: Path, payload: dict[str, object]
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    evidence = tmp_path / "isolation.json"
    evidence.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence",
            str(evidence),
            "--check",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    parsed = json.loads(result.stdout)
    return result, parsed


def _codes(result: dict[str, object]) -> set[str]:
    return {
        str(item["code"])
        for item in result["findings"]
        if isinstance(item, dict) and "code" in item
    }


def test_disposable_change_and_stable_controls_pass(tmp_path: Path) -> None:
    result, payload = _run(tmp_path, _payload(tmp_path))

    assert result.returncode == 0, result.stdout or result.stderr
    assert payload["status"] == "pass"
    assert payload["block_count"] == 0
    assert payload["watch_count"] == 0


def test_unrelated_live_primary_drift_is_watch_not_block(tmp_path: Path) -> None:
    evidence = _payload(tmp_path)
    primary = evidence["checkouts"][2]
    primary["after"] = _snapshot(status=SHA_B, tracked_diff=SHA_B)
    primary["change_attribution"] = "external_or_unattributed"

    result, payload = _run(tmp_path, evidence)

    assert result.returncode == 0, result.stdout or result.stderr
    assert payload["status"] == "pass_with_watch"
    assert payload["block_count"] == 0
    assert payload["watch_count"] == 1
    assert "isolation:live-drift-unattributed:primary" in _codes(payload)


def test_frozen_control_change_blocks(tmp_path: Path) -> None:
    evidence = _payload(tmp_path)
    frozen = evidence["checkouts"][1]
    frozen["after"] = _snapshot(head=HEAD_B)

    result, payload = _run(tmp_path, evidence)

    assert result.returncode == 1
    assert "isolation:frozen-control-changed:attempt-4" in _codes(payload)


def test_observed_write_outside_disposable_target_blocks(tmp_path: Path) -> None:
    evidence = _payload(tmp_path)
    primary = evidence["checkouts"][2]
    evidence["observed_write_roots"].append(primary["root"])
    primary["after"] = _snapshot(status=SHA_B)
    primary["change_attribution"] = "external_or_unattributed"

    result, payload = _run(tmp_path, evidence)

    assert result.returncode == 1
    assert "isolation:write-outside-disposable-target" in _codes(payload)


def test_live_snapshot_difference_cannot_claim_pilot_causation(tmp_path: Path) -> None:
    evidence = _payload(tmp_path)
    primary = evidence["checkouts"][2]
    primary["after"] = _snapshot(tracked_diff=SHA_B)
    primary["change_attribution"] = "pilot_caused"

    result, payload = _run(tmp_path, evidence)

    assert result.returncode == 1
    assert "isolation:unsupported-live-causality:primary" in _codes(payload)


def test_checkout_roots_must_be_pairwise_disjoint(tmp_path: Path) -> None:
    evidence = _payload(tmp_path)
    duplicate = deepcopy(evidence["checkouts"][1])
    duplicate["id"] = "nested-frozen"
    duplicate["root"] = str(
        Path(evidence["checkouts"][0]["root"]) / "nested-control"
    )
    evidence["checkouts"].append(duplicate)

    result, payload = _run(tmp_path, evidence)

    assert result.returncode == 1
    assert "isolation:overlapping-checkout-roots" in _codes(payload)


def test_missing_frozen_control_blocks(tmp_path: Path) -> None:
    evidence = _payload(tmp_path)
    evidence["checkouts"] = [
        item for item in evidence["checkouts"] if item["role"] != "frozen_control"
    ]

    result, payload = _run(tmp_path, evidence)

    assert result.returncode == 1
    assert "isolation:missing-frozen-control" in _codes(payload)


def _portable_projection(tmp_path: Path) -> dict[str, object]:
    raw = _payload(tmp_path)
    encoded = (
        json.dumps(raw, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return pilot_isolation_gate.project_sanitized_evidence(
        raw,
        evidence_path=tmp_path / "raw.json",
        raw_evidence_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def test_sanitized_projection_preserves_identity_without_local_roots(
    tmp_path: Path,
) -> None:
    projection = _portable_projection(tmp_path)
    serialized = json.dumps(projection, sort_keys=True)

    assert projection["schema"] == "agent-runtime-pilot-isolation/v2"
    assert projection["evidence_mode"] == "sanitized_projection"
    assert str(tmp_path) not in serialized
    assert "root" not in projection["checkouts"][0]
    assert projection["observed_write_checkout_ids"] == ["attempt-5"]

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert result["status"] == "pass"
    assert result["block_count"] == 0


def test_projection_rejects_invalid_raw_binding(tmp_path: Path) -> None:
    projection = _portable_projection(tmp_path)
    projection["raw_proof"]["evidence_sha256"] = "not-a-digest"

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert "isolation:invalid-raw-evidence-digest" in _codes(result)


def test_projection_rejects_asserted_raw_blocker(tmp_path: Path) -> None:
    projection = _portable_projection(tmp_path)
    projection["raw_proof"]["block_count"] = 1
    projection["raw_proof"]["status"] = "fail"

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert "isolation:raw-proof-blocked" in _codes(result)


def test_projection_rejects_unknown_observed_write_id(tmp_path: Path) -> None:
    projection = _portable_projection(tmp_path)
    projection["observed_write_checkout_ids"] = ["missing"]

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert "isolation:unknown-observed-write-checkout" in _codes(result)


def test_projection_rejects_write_mapped_to_non_target(tmp_path: Path) -> None:
    projection = _portable_projection(tmp_path)
    projection["observed_write_checkout_ids"] = ["attempt-4"]

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert "isolation:write-outside-disposable-target" in _codes(result)


def test_projection_requires_changed_target_in_observed_writes(
    tmp_path: Path,
) -> None:
    projection = _portable_projection(tmp_path)
    projection["observed_write_checkout_ids"] = []

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert (
        "isolation:changed-target-write-unrecorded:attempt-5"
        in _codes(result)
    )


def test_projection_rejects_duplicate_raw_watch_codes(tmp_path: Path) -> None:
    projection = _portable_projection(tmp_path)
    projection["raw_proof"].update(
        {
            "status": "pass_with_watch",
            "watch_count": 2,
            "finding_codes": ["isolation:watch", "isolation:watch"],
        }
    )

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert "isolation:invalid-raw-proof-decision" in _codes(result)


def test_projection_rejects_absolute_path_leak(tmp_path: Path) -> None:
    projection = _portable_projection(tmp_path)
    projection["checkouts"][0]["root"] = str(tmp_path)

    result = pilot_isolation_gate.analyze(
        projection,
        tmp_path / "portable.json",
    )
    assert "isolation:absolute-path-leak" in _codes(result)


def test_cli_writes_deterministic_sanitized_projection(tmp_path: Path) -> None:
    raw = tmp_path / "raw.json"
    output = tmp_path / "portable.json"
    raw.write_text(
        json.dumps(_payload(tmp_path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence",
            str(raw),
            "--sanitize-out",
            str(output),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stdout or result.stderr
    projection = json.loads(output.read_text(encoding="utf-8"))
    assert pilot_isolation_gate.analyze(
        projection,
        output,
    )["status"] == "pass"
