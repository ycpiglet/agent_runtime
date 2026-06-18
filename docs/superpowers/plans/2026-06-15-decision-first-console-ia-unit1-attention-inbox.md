# Decision-First Console IA — Unit 1: Attention Inbox derived read — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/attention_inbox.py` — a stdlib, read-only aggregation that turns existing work-item frontmatter + runtime claims into the 6-group "what needs me now" inbox that the decision-first home cockpit (Unit 2) renders.

**Architecture:** A focused standalone module (like `scripts/org_read_api.py`) the console can import — keeps logic out of the 479KB `ui_console.py` monolith and unit-testable. Each signal group is a small adapter over real records (no new storage, no gate execution, no fabricated items). Stdlib only (repo + CI are PyYAML-free; parse frontmatter via `org_model_gate.parse_frontmatter`).

**Tech Stack:** Python 3.10+, stdlib (`datetime`, `json`, `glob`), pytest. Spec: `docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md` (§A). Reuses `org_model_gate.parse_frontmatter` and `multi_host_claim_gate.detect_conflicts`.

---

## File Structure
- Create `scripts/attention_inbox.py` — `inbox(root, *, now, stale_days)` + 6 group adapters + CLI.
- Create `tests/test_attention_inbox.py` — per-adapter fixtures + aggregation + empty-state.
- (Unit 2, separate plan) `ui_console.py` `/api/inbox` route + cockpit view import this module.

**Item contract (every adapter returns these):** `{"group","id","title","why","age_days","severity","action"}` — `severity` orders within a group (higher first); `action` names the next step.

---

### Task 1: Module skeleton + blocked & approval adapters

**Files:**
- Create: `scripts/attention_inbox.py`
- Test: `tests/test_attention_inbox.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_attention_inbox.py
import importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))  # org_model_gate / multi_host_claim_gate imports

def _load():
    spec = importlib.util.spec_from_file_location("attention_inbox", ROOT / "scripts" / "attention_inbox.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def _task(d, tid, **fm):
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_attention_inbox.py -v`
Expected: FAIL (module/functions missing).

- [ ] **Step 3: Implement the skeleton + two adapters**

```python
# scripts/attention_inbox.py
"""Attention Inbox derived read (decision-first console IA Unit 1).

Aggregate existing work-item frontmatter + runtime claims into the 6-group
"what needs me now" inbox the cockpit renders. Read-only; stdlib-only (PyYAML-free).
"""
from __future__ import annotations
import argparse, datetime as _dt, glob, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from org_model_gate import parse_frontmatter  # noqa: E402  (stdlib frontmatter parser)

DONE = {"completed", "closed", "done"}
ACTIVE = {"active", "in_progress"}


def _load_tasks(tasks_dir: Path) -> list[dict]:
    return [parse_frontmatter((tasks_dir / p).read_text(encoding="utf-8", errors="replace"))
            if False else parse_frontmatter(Path(p).read_text(encoding="utf-8", errors="replace"))
            for p in glob.glob(str(tasks_dir / "TASK-*.md"))]


def _item(group, meta, why, action, severity=1, age_days=0):
    return {"group": group, "id": meta.get("id"), "title": meta.get("title") or meta.get("id"),
            "why": why, "age_days": age_days, "severity": severity, "action": action}


def blocked(tasks: list[dict]) -> list[dict]:
    out = []
    for m in tasks:
        st = str(m.get("status", "")).lower()
        if st == "blocked" or (m.get("blocked_by") and st not in DONE):
            out.append(_item("blocked", m, f"status={st or 'blocked'}", "resolve blocker", severity=2))
    return out


def approval_pending(tasks: list[dict]) -> list[dict]:
    out = []
    for m in tasks:
        if str(m.get("approval_required", "")).lower() in ("true", "1", "yes") \
                and str(m.get("status", "")).lower() not in DONE:
            out.append(_item("approval_pending", m, "approval_required", "approve / gate", severity=3))
    return out
```

(Note: keep `_load_tasks` simple — `return [parse_frontmatter(Path(p).read_text(encoding="utf-8", errors="replace")) for p in glob.glob(str(tasks_dir / "TASK-*.md"))]`.)

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_attention_inbox.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/attention_inbox.py tests/test_attention_inbox.py
git commit -m "feat(ia): attention inbox skeleton + blocked/approval adapters (decision-first Unit 1)"
```

---

### Task 2: stale, cost-anomaly, gate-failure adapters

**Files:**
- Modify: `scripts/attention_inbox.py`
- Test: `tests/test_attention_inbox.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_stale_adapter(tmp_path):
    import datetime as dt
    mod = _load()
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    _task(tmp_path, "TASK-AR-905", status="in_progress", updated_at="2026-06-01T00:00:00+00:00")  # 14d -> stale
    _task(tmp_path, "TASK-AR-906", status="in_progress", updated_at="2026-06-14T00:00:00+00:00")  # 1d -> fresh
    items = mod.stale(mod._load_tasks(tmp_path), now=now, stale_days=7)
    assert [i["id"] for i in items] == ["TASK-AR-905"]
    assert items[0]["age_days"] >= 7

def test_cost_and_gate_adapters(tmp_path):
    mod = _load()
    _task(tmp_path, "TASK-AR-907", status="in_progress", est_tokens="100", actual_tokens="500")  # overspend
    _task(tmp_path, "TASK-AR-908", status="in_progress", gate_failure_count="2")
    cost = mod.cost_anomalies(mod._load_tasks(tmp_path))
    gates = mod.gate_failures(mod._load_tasks(tmp_path))
    assert [i["id"] for i in cost] == ["TASK-AR-907"]
    assert [i["id"] for i in gates] == ["TASK-AR-908"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_attention_inbox.py -v`
Expected: FAIL (`stale`/`cost_anomalies`/`gate_failures` missing).

- [ ] **Step 3: Implement the three adapters**

```python
def _parse_dt(value):
    try:
        return _dt.datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None

def stale(tasks, *, now, stale_days=7):
    out = []
    for m in tasks:
        if str(m.get("status", "")).lower() not in ACTIVE:
            continue
        ts = _parse_dt(m.get("updated_at"))
        if ts is None:
            continue
        age = (now - ts).days
        if age >= stale_days:
            out.append(_item("stale", m, f"no update {age}d", "review / refresh", severity=1, age_days=age))
    return out

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def cost_anomalies(tasks):
    out = []
    for m in tasks:
        est, act = _num(m.get("est_tokens")), _num(m.get("actual_tokens"))
        cap = _num(m.get("budget_cap"))
        if act is not None and ((est is not None and act > est) or (cap is not None and act > cap)):
            out.append(_item("cost_anomalies", m, f"actual {int(act)} > budget", "review cost", severity=2))
    return out

def gate_failures(tasks):
    out = []
    for m in tasks:
        n = _num(m.get("gate_failure_count"))
        if n and n > 0:
            out.append(_item("gate_failures", m, f"{int(n)} gate failures", "fix gate", severity=2))
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_attention_inbox.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/attention_inbox.py tests/test_attention_inbox.py
git commit -m "feat(ia): stale/cost/gate-failure inbox adapters (decision-first Unit 1)"
```

---

### Task 3: runtime-anomaly adapter + inbox() aggregation + empty state

**Files:**
- Modify: `scripts/attention_inbox.py`
- Test: `tests/test_attention_inbox.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_inbox_aggregates_and_empty_state(tmp_path):
    import datetime as dt
    mod = _load()
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    # empty repo -> total 0, all groups present and empty
    empty = mod.inbox(tmp_path, now=now)
    assert empty["total"] == 0
    assert set(empty["groups"]) == {"approval_pending","blocked","stale","gate_failures","cost_anomalies","runtime_anomalies"}
    assert empty["counts"]["blocked"] == 0
    # one blocked task -> total 1
    _task(tmp_path, "TASK-AR-909", status="blocked")
    one = mod.inbox(tmp_path, now=now)
    assert one["total"] == 1 and one["counts"]["blocked"] == 1

def test_runtime_anomaly_adapter_uses_claim_conflicts(tmp_path, monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "_claim_conflicts", lambda root: [{"resource": "TASK-AR-1", "hosts": ["a","b"]}])
    items = mod.runtime_anomalies(tmp_path)
    assert items and items[0]["group"] == "runtime_anomalies"
    assert "a" in items[0]["why"] and "b" in items[0]["why"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_attention_inbox.py -v`
Expected: FAIL (`inbox`/`runtime_anomalies`/`_claim_conflicts` missing).

- [ ] **Step 3: Implement runtime adapter + aggregation**

```python
def _claim_conflicts(root: Path):
    try:
        from multi_host_claim_gate import detect_conflicts, load_claims
        return detect_conflicts(load_claims(root / "agents" / "runtime" / "task_claims"))
    except Exception:
        return []

def runtime_anomalies(root: Path):
    out = []
    for c in _claim_conflicts(root):
        out.append({"group": "runtime_anomalies", "id": c.get("resource"),
                    "title": c.get("resource"), "why": "cross-host claim conflict: " + ",".join(c.get("hosts", [])),
                    "age_days": 0, "severity": 3, "action": "resolve claim"})
    return out

GROUP_ORDER = ["approval_pending", "blocked", "gate_failures", "runtime_anomalies", "cost_anomalies", "stale"]

def inbox(root: Path, *, now=None, stale_days: int = 7) -> dict:
    now = now or _dt.datetime.now(_dt.timezone.utc).astimezone()
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks = _load_tasks(tasks_dir) if tasks_dir.exists() else []
    groups = {
        "approval_pending": approval_pending(tasks),
        "blocked": blocked(tasks),
        "gate_failures": gate_failures(tasks),
        "runtime_anomalies": runtime_anomalies(root),
        "cost_anomalies": cost_anomalies(tasks),
        "stale": stale(tasks, now=now, stale_days=stale_days),
    }
    for items in groups.values():
        items.sort(key=lambda i: i["severity"], reverse=True)
    counts = {g: len(groups[g]) for g in GROUP_ORDER}
    return {"groups": {g: groups[g] for g in GROUP_ORDER}, "counts": counts,
            "total": sum(counts.values())}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Attention inbox (what needs a human now).")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    data = inbox(ROOT)
    if a.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"attention-inbox: {data['total']} items needing attention" if data["total"]
              else "attention-inbox: nothing needs you")
        for g, n in data["counts"].items():
            if n:
                print(f"  {g}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify pass + real-repo smoke**

Run: `python -m pytest tests/test_attention_inbox.py -v` → PASS (6 tests).
Run: `python scripts/attention_inbox.py` → prints a real count or "nothing needs you" (exit 0).

- [ ] **Step 5: Commit**

```bash
git add scripts/attention_inbox.py tests/test_attention_inbox.py
git commit -m "feat(ia): runtime-anomaly adapter + inbox aggregation + empty state (decision-first Unit 1)"
```

---

## Self-Review
- **Spec coverage (§A):** all 6 groups implemented from existing sources (approval_required, status/blocked_by, updated_at, gate_failure_count, est/actual/budget_cap, multi_host_claim_gate); item contract `{group,id,title,why,age_days,severity,action}` matches the spec; empty state = "nothing needs you". Open-PR (gh) signal is intentionally deferred to Unit 2's endpoint (where gh availability is handled) — noted, not a gap.
- **Placeholder scan:** none — every step has runnable code/commands. (Fix the `_load_tasks` one-liner per the Task 1 note when implementing.)
- **Type consistency:** adapters all return the same item dict; `inbox()` consumes `_load_tasks` output + `now`; `now`/`stale_days` keyword-only throughout; PyYAML-free (parse_frontmatter).

## Out of scope (subsequent units, each its own plan)
Unit 2 `/api/inbox` + cockpit home view; Unit 3 nav prune; Unit 4 progressive-disclosure panel; Unit 5 work state board; Unit 6 i18n toggle; Unit 7 E2E + DOM budget.
