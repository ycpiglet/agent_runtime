"""Lead orchestrator + swappable WorkerBackend (org-delegation Unit 560, TASK-AR-560).

The Lead orchestrates worker-ready Units into dispatched Worker (and Reviewer) runs:
plan the dispatch (Unit 559) -> for each Unit, spawn a Worker through a WorkerBackend,
enforcing seam-serialization, the concurrency cap, a token budget, and idempotency.

`WorkerBackend` is the swap seam the Owner required: Phase 1 = sub-agents (the spawn
is driven at the assistant level via the Agent tool, using the worker ORDER this module
emits); Phase 2 = a headless daemon. The orchestrator, plan, claim/instance/lease records,
and report are unchanged across backends — only the backend is swapped.

Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (step 4).
"""
from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_dispatch = _load("dispatch_gate")


class WorkerBackend(ABC):
    """The swap seam between 'decide' and 'execute'. Implementations: SubagentBackend
    (Phase 1, assistant-driven Agent tool) and DaemonBackend (Phase 2, headless)."""

    @abstractmethod
    def spawn(self, order: dict) -> str:
        """Start a worker for one order; return an instance_id."""

    @abstractmethod
    def poll(self, instance_id: str) -> dict:
        """Return {"status": "running"|"released"|"failed", "result": ...}."""

    @abstractmethod
    def terminate(self, instance_id: str) -> None:
        ...


class RecordingBackend(WorkerBackend):
    """In-memory backend for tests / dry runs: records spawns, releases immediately."""

    def __init__(self, *, fail: set[str] | None = None):
        self.spawned: list[dict] = []
        self.terminated: list[str] = []
        self._fail = fail or set()

    def spawn(self, order: dict) -> str:
        instance_id = f"inst-{order['role']}-{order['unit_id']}"
        self.spawned.append(order)
        return instance_id

    def poll(self, instance_id: str) -> dict:
        for order in self.spawned:
            if instance_id.endswith(order["unit_id"]) and order["unit_id"] in self._fail:
                return {"status": "failed", "result": None}
        return {"status": "released", "result": "ok"}

    def terminate(self, instance_id: str) -> None:
        self.terminated.append(instance_id)


def build_order(unit_id: str, meta: dict, role: str) -> dict:
    """Build the self-contained worker/reviewer ORDER (the sub-agent prompt context)."""
    return {
        "unit_id": unit_id,
        "role": role,  # "worker" or "reviewer"
        "model_tier": meta.get("model_tier", "worker_standard" if role == "worker" else "reviewer_standard"),
        "context": meta.get("context", ""),
        "scope": meta.get("scope", ""),
        "target_files": list(meta.get("target_files") or []),
        "acceptance": list(meta.get("acceptance") or []),
        "stop_condition": meta.get("stop_condition", ""),
        "worktree": meta.get("worktree", f".worktrees/{unit_id}"),
    }


class Orchestrator:
    def __init__(self, backend: WorkerBackend, *, max_parallel: int = 4,
                 budget_total: int | None = None):
        self.backend = backend
        self.max_parallel = max_parallel
        self.budget_total = budget_total

    def run(self, units: list[tuple[str, dict]], *, done_unit_ids: set[str] | None = None) -> dict:
        done = set(done_unit_ids or set())
        plan = _dispatch.plan_dispatch(units, max_parallel=self.max_parallel)
        meta_by_id = dict(units)
        report = {"workers": [], "reviewers": [], "held_for_owner": [],
                  "skipped_idempotent": [], "stopped_over_budget": []}
        spent = 0
        for entry in plan:
            uid = entry["unit_id"]
            meta = meta_by_id.get(uid, {})
            if uid in done:                                  # idempotency
                report["skipped_idempotent"].append(uid)
                continue
            if entry["mode"] == "owner-gate":                # risk gate
                report["held_for_owner"].append({"unit_id": uid, "reasons": entry["reasons"]})
                continue
            est = int(meta.get("est_tokens", 0) or 0)        # token budget
            if self.budget_total is not None and spent + est > self.budget_total:
                report["stopped_over_budget"].append(uid)
                continue
            spent += est
            # spawn Worker, then an independent Reviewer (reviewer != worker)
            w_inst = self.backend.spawn(build_order(uid, meta, "worker"))
            w_res = self.backend.poll(w_inst)
            report["workers"].append({"unit_id": uid, "instance": w_inst,
                                      "seam": entry["seam"], "status": w_res["status"]})
            if w_res["status"] == "released":
                r_inst = self.backend.spawn(build_order(uid, meta, "reviewer"))
                r_res = self.backend.poll(r_inst)
                report["reviewers"].append({"unit_id": uid, "instance": r_inst,
                                            "status": r_res["status"]})
        report["tokens_spent"] = spent
        return report
