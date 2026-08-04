from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "claim_lease.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import claim_lease  # noqa: E402


def _run(*args: str, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _parse(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def _source(root: Path) -> Path:
    path = root / "agents" / "messages" / "inbox" / "MSG-1.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("message source\n", encoding="utf-8")
    return path


def _lease_mutation_snapshot(root: Path) -> dict[str, bytes]:
    runtime = root / "agents" / "runtime" / "claims"
    if not runtime.exists():
        return {}
    snapshot = {runtime.relative_to(root).as_posix(): b"directory"}
    for path in sorted(runtime.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        snapshot[relative] = b"directory" if path.is_dir() else path.read_bytes()
    return snapshot


@pytest.mark.parametrize("ttl_seconds", (True, False, 0, -1, 10**100))
def test_acquire_api_refuses_invalid_ttl_before_mutation(
    tmp_path: Path,
    ttl_seconds: object,
) -> None:
    source = _source(tmp_path)
    before = _lease_mutation_snapshot(tmp_path)

    with pytest.raises(ValueError):
        claim_lease.acquire_claim(
            tmp_path,
            resource_id="MSG-invalid-acquire",
            owner_id="worker-1",
            ttl_seconds=ttl_seconds,  # type: ignore[arg-type]
            source_path=source.relative_to(tmp_path).as_posix(),
            now=claim_lease._parse_now("2026-06-12T00:00:00+09:00"),
        )

    assert _lease_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("ttl_seconds", (True, False, 0, -1, 10**100))
def test_heartbeat_api_refuses_invalid_ttl_before_mutation(
    tmp_path: Path,
    ttl_seconds: object,
) -> None:
    source = _source(tmp_path)
    acquired = claim_lease.acquire_claim(
        tmp_path,
        resource_id="MSG-invalid-heartbeat",
        owner_id="worker-1",
        ttl_seconds=60,
        source_path=source.relative_to(tmp_path).as_posix(),
        now=claim_lease._parse_now("2026-06-12T00:00:00+09:00"),
    )
    assert acquired["acquired"] is True
    before = _lease_mutation_snapshot(tmp_path)

    with pytest.raises(ValueError):
        claim_lease.heartbeat_claim(
            tmp_path,
            resource_id="MSG-invalid-heartbeat",
            owner_id="worker-1",
            ttl_seconds=ttl_seconds,  # type: ignore[arg-type]
            now=claim_lease._parse_now("2026-06-12T00:00:30+09:00"),
        )

    assert _lease_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("ttl_seconds", ("0", "-1", "100000000000000000000"))
def test_acquire_cli_refuses_invalid_ttl_without_traceback_or_mutation(
    tmp_path: Path,
    ttl_seconds: str,
) -> None:
    source = _source(tmp_path)
    before = _lease_mutation_snapshot(tmp_path)

    result = _run(
        "acquire",
        "--resource-id",
        "MSG-invalid-acquire-cli",
        "--owner-id",
        "worker-1",
        "--ttl-seconds",
        ttl_seconds,
        "--source-path",
        source.relative_to(tmp_path).as_posix(),
        "--now",
        "2026-06-12T00:00:00+09:00",
        root=tmp_path,
    )

    assert result.returncode != 0
    assert "Traceback" not in result.stdout + result.stderr
    assert _lease_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("ttl_seconds", ("0", "-1", "100000000000000000000"))
def test_heartbeat_cli_refuses_invalid_ttl_without_traceback_or_mutation(
    tmp_path: Path,
    ttl_seconds: str,
) -> None:
    source = _source(tmp_path)
    acquired = claim_lease.acquire_claim(
        tmp_path,
        resource_id="MSG-invalid-heartbeat-cli",
        owner_id="worker-1",
        ttl_seconds=60,
        source_path=source.relative_to(tmp_path).as_posix(),
        now=claim_lease._parse_now("2026-06-12T00:00:00+09:00"),
    )
    assert acquired["acquired"] is True
    before = _lease_mutation_snapshot(tmp_path)

    result = _run(
        "heartbeat",
        "--resource-id",
        "MSG-invalid-heartbeat-cli",
        "--owner-id",
        "worker-1",
        "--ttl-seconds",
        ttl_seconds,
        "--now",
        "2026-06-12T00:00:30+09:00",
        root=tmp_path,
    )

    assert result.returncode != 0
    assert "Traceback" not in result.stdout + result.stderr
    assert _lease_mutation_snapshot(tmp_path) == before


def test_acquire_and_heartbeat_accept_exactly_one_second(tmp_path: Path) -> None:
    source = _source(tmp_path)
    acquired = claim_lease.acquire_claim(
        tmp_path,
        resource_id="MSG-one-second",
        owner_id="worker-1",
        ttl_seconds=1,
        source_path=source.relative_to(tmp_path).as_posix(),
        now=claim_lease._parse_now("2026-06-12T00:00:00+09:00"),
    )

    assert acquired["acquired"] is True
    assert (
        datetime.fromisoformat(acquired["lease"]["expires_at"])
        - datetime.fromisoformat(acquired["lease"]["claimed_at"])
    ).total_seconds() == 1

    heartbeat = claim_lease.heartbeat_claim(
        tmp_path,
        resource_id="MSG-one-second",
        owner_id="worker-1",
        ttl_seconds=1,
        now=claim_lease._parse_now("2026-06-12T00:00:30+09:00"),
    )

    assert heartbeat["updated"] is True
    assert (
        datetime.fromisoformat(heartbeat["lease"]["expires_at"])
        - datetime.fromisoformat(heartbeat["lease"]["heartbeat_at"])
    ).total_seconds() == 1


def test_concurrent_claim_two_workers(tmp_path: Path) -> None:
    source = _source(tmp_path)
    command = [
        sys.executable,
        str(SCRIPT),
        "--root",
        str(tmp_path),
        "acquire",
        "--resource-id",
        "MSG-1",
        "--ttl-seconds",
        "60",
        "--source-path",
        source.relative_to(tmp_path).as_posix(),
    ]
    p1 = subprocess.Popen(
        [*command, "--owner-id", "worker-1"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    p2 = subprocess.Popen(
        [*command, "--owner-id", "worker-2"],
        cwd=REPO_ROOT,
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
    results = [json.loads(out1), json.loads(out2)]
    winners = [item for item in results if item["acquired"] is True]
    blocked = [item for item in results if item["acquired"] is False]

    assert len(winners) == 1
    assert len(blocked) == 1
    assert blocked[0]["reason"] == "lease-active"
    lease_path = tmp_path / winners[0]["lease_path"]
    saved = json.loads(lease_path.read_text(encoding="utf-8"))
    assert saved["owner_id"] == winners[0]["lease"]["owner_id"]


def test_stale_leader_recovery_requires_expired_lease_and_source_file(tmp_path: Path) -> None:
    source = _source(tmp_path)
    source_rel = source.relative_to(tmp_path).as_posix()
    first = _parse(
        _run(
            "acquire",
            "--resource-id",
            "MSG-1",
            "--owner-id",
            "worker-old",
            "--ttl-seconds",
            "60",
            "--source-path",
            source_rel,
            "--now",
            "2026-06-12T00:00:00+09:00",
            root=tmp_path,
        )
    )
    assert first["acquired"] is True

    not_recovered = _parse(
        _run(
            "acquire",
            "--resource-id",
            "MSG-1",
            "--owner-id",
            "worker-new",
            "--ttl-seconds",
            "1",
            "--source-path",
            source_rel,
            "--now",
            "2026-06-12T00:00:30+09:00",
            root=tmp_path,
        )
    )
    assert not_recovered["acquired"] is False
    assert not_recovered["reason"] == "lease-active"

    recovered = _parse(
        _run(
            "acquire",
            "--resource-id",
            "MSG-1",
            "--owner-id",
            "worker-new",
            "--ttl-seconds",
            "1",
            "--source-path",
            source_rel,
            "--recover-stale",
            "--now",
            "2026-06-12T00:01:30+09:00",
            root=tmp_path,
        )
    )
    assert recovered["acquired"] is True
    assert recovered["lease"]["recovered_from"] == "worker-old"

    source.unlink()
    missing_source = _parse(
        _run(
            "acquire",
            "--resource-id",
            "MSG-1",
            "--owner-id",
            "worker-third",
            "--ttl-seconds",
            "1",
            "--source-path",
            source_rel,
            "--recover-stale",
            "--now",
            "2026-06-12T00:02:00+09:00",
            root=tmp_path,
        )
    )
    assert missing_source["acquired"] is False
    assert missing_source["reason"] == "source-missing"
