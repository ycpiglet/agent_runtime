from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "claim_lease.py"


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
