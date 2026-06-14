"""Concurrency + heartbeat + grace-boundary stress tests for the deadlock guardrails.

TASK-AR-552. Covers verification cases VC-REAP-3/4/13/19 and VC-SUP-5/6 from
docs/product-maturity-ui-verification-catalog.md: a live worker that keeps
refreshing its lease is never reaped; the grace boundary is deterministic;
concurrent reapers transition a dead claim exactly once without corrupting it; a
claim resurrected by a heartbeat under the reap lock is not reaped; and the goal
supervisor restart cap is enforced at its boundary.
"""

import json
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_reaper  # noqa: E402
import goal_supervisor  # noqa: E402
import stop_events  # noqa: E402

NOW = "2026-06-14T12:00:00+09:00"
NOW_DT = datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone(timedelta(hours=9)))


def _write_claim(tmp_path: Path, claim_id: str, *, status: str = "claimed",
                 expires_at: str | None = "2026-06-14T11:00:00+09:00",
                 agent_role: str = "lead-engineer", task_id: str = "TASK-AR-1") -> Path:
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "claim_id": claim_id, "task_id": task_id, "agent_role": agent_role,
        "agent_instance_id": f"ai-{claim_id}", "status": status,
        "worktree_path": f".worktrees/{task_id}", "branch": f"codex/{task_id}",
    }
    if expires_at is not None:
        payload["expires_at"] = expires_at
        payload["lease"] = {"expires_at": expires_at, "heartbeat_at": expires_at}
    path = claim_dir / f"{claim_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


# --- VC-REAP-13: a live worker that keeps heartbeating is never reaped ---

def test_live_worker_refreshing_lease_never_reaped_over_window(tmp_path):
    path = _write_claim(tmp_path, "CLAIM-live")
    interval = timedelta(minutes=20)
    for i in range(12):  # ~4 hours of "work", far past the 30-min lease window
        moment = NOW_DT + i * interval
        # the worker heartbeats: lease deadline always stays ahead of now
        claim = _load(path)
        claim["expires_at"] = _iso(moment + interval + timedelta(minutes=5))
        claim["lease"]["expires_at"] = claim["expires_at"]
        path.write_text(json.dumps(claim), encoding="utf-8")
        report = claim_reaper.sweep(tmp_path, now=_iso(moment), apply=True, grace_seconds=600)
        assert report["reaped"] == [], f"reaped a live worker at step {i}"
        assert _load(path)["status"] == "claimed"


# --- VC-REAP-3/4: grace boundary is deterministic ---

def test_grace_boundary_inclusive(tmp_path):
    # deadline == now -> live; deadline+grace == now -> live (inclusive); +1s -> dead.
    grace = 600
    p_now = _write_claim(tmp_path, "CLAIM-atnow", expires_at=NOW)
    p_edge = _write_claim(tmp_path, "CLAIM-edge", task_id="TASK-AR-2",
                          expires_at=_iso(NOW_DT - timedelta(seconds=grace)))
    p_over = _write_claim(tmp_path, "CLAIM-over", task_id="TASK-AR-3",
                          expires_at=_iso(NOW_DT - timedelta(seconds=grace + 1)))
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=grace)
    reaped = {c["claim_id"] for c in report["reaped"]}
    assert reaped == {"CLAIM-over"}
    assert _load(p_now)["status"] == "claimed"
    assert _load(p_edge)["status"] == "claimed"
    assert _load(p_over)["status"] == "expired"


# --- VC-REAP-19: concurrent reapers transition a dead claim exactly once ---

def _concurrent_sweeps(tmp_path: Path, threads: int) -> list[dict]:
    reports: list[dict] = []
    barrier = threading.Barrier(threads)

    def run():
        barrier.wait()  # maximize contention
        reports.append(claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600))

    workers = [threading.Thread(target=run) for _ in range(threads)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return reports


def test_concurrent_reapers_reap_single_claim_exactly_once(tmp_path):
    path = _write_claim(tmp_path, "CLAIM-dead")
    reports = _concurrent_sweeps(tmp_path, threads=8)
    total_reaped = sum(len(r["reaped"]) for r in reports)
    assert total_reaped == 1, f"expected exactly one transition, got {total_reaped}"
    final = _load(path)  # must be valid JSON (no corruption) and expired
    assert final["status"] == "expired"
    assert final["recovered_from_status"] == "claimed"


def test_concurrent_reapers_mixed_no_corruption(tmp_path):
    dead = [_write_claim(tmp_path, f"CLAIM-dead{i}", task_id=f"TASK-AR-{i}",
                         expires_at="2026-06-14T10:00:00+09:00") for i in range(6)]
    _write_claim(tmp_path, "CLAIM-live", task_id="TASK-AR-99",
                 expires_at="2026-06-14T13:00:00+09:00")
    reports = _concurrent_sweeps(tmp_path, threads=8)
    total_reaped = sum(len(r["reaped"]) for r in reports)
    assert total_reaped == len(dead)  # each dead claim transitioned exactly once
    for p in dead:
        assert _load(p)["status"] == "expired"


# --- VC-REAP-13 (race variant): a heartbeat under the lock prevents reaping ---

def test_reap_rechecks_under_lock_and_skips_resurrected_claim(tmp_path):
    path = _write_claim(tmp_path, "CLAIM-resurrect")
    stale_claim = _load(path)  # looks dead at initial read time
    # Simulate a heartbeat landing before _reap acquires the lock: the file on disk
    # is refreshed to a live lease while we still hold the stale (dead) snapshot.
    live = _load(path)
    live["expires_at"] = "2026-06-14T13:00:00+09:00"
    live["lease"]["expires_at"] = live["expires_at"]
    path.write_text(json.dumps(live), encoding="utf-8")
    reaped = claim_reaper._reap(tmp_path, path, stale_claim, NOW_DT, 600)
    assert reaped is False
    assert _load(path)["status"] == "claimed"  # live worker untouched


# --- VC-SUP-5/6: supervisor restart cap boundary ---

def _seed_restarts(tmp_path: Path, goal: str, n: int) -> None:
    for _ in range(n):
        stop_events.bump_counter(tmp_path, reason_code="max_iterations", action="resumed",
                                 klass="intentional", goal=goal, now=NOW)


def _write_loop_stop(tmp_path: Path, goal: str) -> None:
    p = tmp_path / "agents" / "runtime" / "events" / "agent_loop-2026-06-14.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(x) for x in [
        {"event": "loop_start", "goal": goal, "mode": "build"},
        {"event": "loop_stop", "iteration": 6, "reason": "max_iterations reached (5)"},
    ]) + "\n", encoding="utf-8")


def test_supervisor_resumes_at_cap_minus_one(tmp_path):
    goal = "ship it"
    _write_loop_stop(tmp_path, goal)
    _seed_restarts(tmp_path, goal, 2)  # cap=3 -> last allowed resume

    def fake_runner(cmd, root):
        return 0, "ok"

    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=True, max_restarts=3, runner=fake_runner)
    assert report["action"] == "resume"
    assert report["restart_count"] == 2


def test_supervisor_caps_at_boundary(tmp_path):
    goal = "ship it"
    _write_loop_stop(tmp_path, goal)
    _seed_restarts(tmp_path, goal, 3)  # cap=3 reached

    def fake_runner(cmd, root):
        raise AssertionError("must not resume at the cap")

    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=True, max_restarts=3, runner=fake_runner)
    assert report["action"] == "cap"
    assert report["restart_count"] == 3
