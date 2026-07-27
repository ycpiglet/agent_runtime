import datetime as dt
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))  # org_model_gate / multi_host_claim_gate sibling imports


def _load():
    spec = importlib.util.spec_from_file_location("attention_inbox", ROOT / "scripts" / "attention_inbox.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _task(d: Path, tid: str, **fm):
    lines = "\n".join(f"{k}: {v}" for k, v in fm.items())
    (d / f"{tid}.md").write_text(f"---\nid: {tid}\n{lines}\n---\n", encoding="utf-8")


def test_blocked_adapter(tmp_path):
    mod = _load()
    _task(tmp_path, "TASK-AR-901", status="blocked")
    _task(tmp_path, "TASK-AR-902", status="in_progress")
    items = mod.blocked(mod._load_tasks(tmp_path))
    assert [i["id"] for i in items] == ["TASK-AR-901"]
    assert items[0]["group"] == "blocked" and items[0]["action"]


def test_approval_adapter(tmp_path):
    mod = _load()
    _task(tmp_path, "TASK-AR-903", status="planned", approval_required="true")
    _task(tmp_path, "TASK-AR-904", status="completed", approval_required="true")  # done -> excluded
    items = mod.approval_pending(mod._load_tasks(tmp_path))
    assert [i["id"] for i in items] == ["TASK-AR-903"]
    assert items[0]["group"] == "approval_pending"


def test_stale_adapter(tmp_path):
    mod = _load()
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    _task(tmp_path, "TASK-AR-905", status="in_progress", updated_at="2026-06-01T00:00:00+00:00")  # 14d
    _task(tmp_path, "TASK-AR-906", status="in_progress", updated_at="2026-06-14T00:00:00+00:00")  # 1d
    items = mod.stale(mod._load_tasks(tmp_path), now=now, stale_days=7)
    assert [i["id"] for i in items] == ["TASK-AR-905"]
    assert items[0]["age_days"] >= 7


def test_cost_and_gate_adapters(tmp_path):
    mod = _load()
    _task(tmp_path, "TASK-AR-907", status="in_progress", est_tokens="100", actual_tokens="500")
    _task(tmp_path, "TASK-AR-908", status="in_progress", gate_failure_count="2")
    cost = mod.cost_anomalies(mod._load_tasks(tmp_path))
    gates = mod.gate_failures(mod._load_tasks(tmp_path))
    assert [i["id"] for i in cost] == ["TASK-AR-907"]
    assert [i["id"] for i in gates] == ["TASK-AR-908"]


def test_inbox_aggregates_and_empty_state(tmp_path):
    mod = _load()
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    td = tmp_path / "agents" / "lead_engineer" / "tasks"
    td.mkdir(parents=True)
    empty = mod.inbox(tmp_path, now=now)
    assert empty["total"] == 0
    assert set(empty["groups"]) == {"approval_pending", "blocked", "stale",
                                    "gate_failures", "gate_watch", "cost_anomalies",
                                    "runtime_anomalies", "unowned"}
    assert empty["counts"]["blocked"] == 0
    _task(td, "TASK-AR-909", status="blocked")
    one = mod.inbox(tmp_path, now=now)
    assert one["total"] == 1 and one["counts"]["blocked"] == 1


def test_runtime_anomaly_adapter_uses_claim_conflicts(tmp_path, monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "_claim_conflicts", lambda root: [{"resource": "TASK-AR-1", "hosts": ["a", "b"]}])
    items = mod.runtime_anomalies(tmp_path)
    assert items and items[0]["group"] == "runtime_anomalies"
    assert "a" in items[0]["why"] and "b" in items[0]["why"]


def test_unowned_adapter(tmp_path):
    """Ready/planned work with no owner is the RFC's 'unowned' attention tier."""
    mod = _load()
    _task(tmp_path, "TASK-AR-910", status="planned")  # no owner -> unowned
    _task(tmp_path, "TASK-AR-911", status="planned", owner="lead-engineer")  # owned -> excluded
    _task(tmp_path, "TASK-AR-912", status="completed")  # done -> excluded
    items = mod.unowned(mod._load_tasks(tmp_path))
    assert [i["id"] for i in items] == ["TASK-AR-910"]
    assert items[0]["group"] == "unowned" and items[0]["action"]


def test_inbox_rank_order_is_gate_blocked_stale_risk_unowned(tmp_path):
    """P1 (RFC greenlit): the cockpit ranks the typed attention inbox by the
    Owner-chosen urgency order gate > blocked > stale > risk > unowned."""
    mod = _load()
    assert mod.RANK_TIERS == ["gate", "blocked", "stale", "risk", "unowned"]
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    td = tmp_path / "agents" / "lead_engineer" / "tasks"
    td.mkdir(parents=True)
    # One item per tier (insertion order deliberately NOT the rank order).
    _task(td, "TASK-R1", status="planned")  # unowned
    _task(td, "TASK-R2", status="in_progress", est_tokens="100", actual_tokens="500")  # risk
    _task(td, "TASK-R3", status="in_progress", updated_at="2026-06-01T00:00:00+00:00")  # stale (14d)
    _task(td, "TASK-R4", status="blocked")  # blocked
    _task(td, "TASK-R5", status="planned", approval_required="true")  # gate
    data = mod.inbox(tmp_path, now=now)
    # rank_order is the canonical tier order, exposed for the cockpit.
    assert data["rank_order"] == ["gate", "blocked", "stale", "risk", "unowned"]
    # The flat ranked list is ordered by tier rank (gate first, unowned last).
    ranked_tiers = [item["rank"] for item in data["ranked"]]
    assert ranked_tiers == ["gate", "blocked", "stale", "risk", "unowned"]
    # Every ranked item is tagged with its tier and stays group-aligned.
    by_id = {item["id"]: item for item in data["ranked"]}
    assert by_id["TASK-R5"]["rank"] == "gate"
    assert by_id["TASK-R4"]["rank"] == "blocked"
    assert by_id["TASK-R3"]["rank"] == "stale"
    assert by_id["TASK-R2"]["rank"] == "risk"
    assert by_id["TASK-R1"]["rank"] == "unowned"


def test_inbox_rank_groups_higher_severity_first_within_tier(tmp_path):
    """Within a tier, higher severity sorts first (gate failures vs approval)."""
    mod = _load()
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    td = tmp_path / "agents" / "lead_engineer" / "tasks"
    td.mkdir(parents=True)
    _task(td, "TASK-G1", status="planned", approval_required="true")  # gate tier, sev 3
    _task(td, "TASK-G2", status="in_progress", gate_failure_count="2")  # gate tier, sev 2
    data = mod.inbox(tmp_path, now=now)
    gate_ids = [i["id"] for i in data["ranked"] if i["rank"] == "gate"]
    assert gate_ids == ["TASK-G1", "TASK-G2"]


def test_blocked_item_preserves_work_emitter_encoded_title(tmp_path):
    mod = _load()
    import work

    title = "true"
    (tmp_path / "TASK-AR-913.md").write_text(
        work._frontmatter({"id": "TASK-AR-913", "title": title, "status": "blocked"}) + "\n",
        encoding="utf-8",
    )

    items = mod.blocked(mod._load_tasks(tmp_path))

    assert items[0]["title"] == title


def _gate_json(root: Path, name: str, *, status: str, kind_schema: str, generated_at: str) -> None:
    import json as _json
    reviews = root / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / name).write_text(
        _json.dumps({"schema": kind_schema, "status": status, "generated_at": generated_at}),
        encoding="utf-8",
    )


def test_ar630_gate_watch_promotes_latest_watch_only(tmp_path):
    # TASK-AR-630: only gates whose LATEST record is watch are promoted, as
    # low-severity items in the gate tier.
    mod = _load()
    _gate_json(tmp_path, "COMPOUND-GATE-1.json", status="watch",
               kind_schema="agent-runtime-compound-cadence/v1", generated_at="2026-07-20T10:00:00+09:00")
    _gate_json(tmp_path, "OTHER-GATE-old.json", status="watch",
               kind_schema="agent-runtime-other-gate/v1", generated_at="2026-07-01T10:00:00+09:00")
    _gate_json(tmp_path, "OTHER-GATE-new.json", status="pass",
               kind_schema="agent-runtime-other-gate/v1", generated_at="2026-07-25T10:00:00+09:00")
    _gate_json(tmp_path, "BLOCKED-GATE-1.json", status="block",
               kind_schema="agent-runtime-blocked-gate/v1", generated_at="2026-07-25T10:00:00+09:00")
    items = mod.gate_watch(tmp_path)
    assert [i["id"] for i in items] == ["compound-cadence"]  # recovered + block excluded
    assert items[0]["severity"] == 0 and items[0]["group"] == "gate_watch"
    assert mod.GROUP_TIER["gate_watch"] == "gate"


def test_ar630_inbox_includes_gate_watch_group(tmp_path):
    mod = _load()
    _gate_json(tmp_path, "COMPOUND-GATE-1.json", status="watch",
               kind_schema="agent-runtime-compound-cadence/v1", generated_at="2026-07-20T10:00:00+09:00")
    data = mod.inbox(tmp_path)
    assert "gate_watch" in data["groups"] and data["counts"]["gate_watch"] == 1
    assert data["total"] >= 1


def test_ar630_recovered_pass_without_stamp_clears_watch(tmp_path):
    # W4b(630): a recovery record missing generated_at must still supersede an
    # older watch (file-order fallback), not leave the watch stuck forever.
    import json as _json
    reviews = tmp_path / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "X-GATE-1-watch.json").write_text(
        _json.dumps({"schema": "agent-runtime-x-gate/v1", "status": "watch",
                     "generated_at": "2026-07-20T10:00:00+09:00"}), encoding="utf-8")
    (reviews / "X-GATE-2-recovered.json").write_text(
        _json.dumps({"schema": "agent-runtime-x-gate/v1", "status": "pass"}), encoding="utf-8")
    mod = _load()
    assert mod.gate_watch(tmp_path) == []
