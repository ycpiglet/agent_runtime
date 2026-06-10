from __future__ import annotations

import json
from pathlib import Path

from scripts import planning_loop, planning_trigger


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_repo(root: Path) -> None:
    write(root / "BACKLOG.md", "# Backlog\n")
    write(root / "BACKLOG-BOARD.md", "# Board\n")
    write(root / "STATUS.md", "# Status\n")
    write(root / "AGENT_RUNTIME_RSI_PLANNING_BRIEF.md", "# RSI Brief\n")
    write(root / "docs/superpowers/plans/2026-06-10-rsi-planning-loop.md", "# Plan\n")
    write(root / "agents/project/STATE-MACHINES.yml", "planning_loop:\n  states: []\n")
    write(root / "agents/project/PLANNING-LOOP-CONTRACT.md", "# Contract\n")
    write(root / "schemas/planning-proposal.schema.json", "{}\n")
    write(root / "agents/project/PLANNING-GUARDRAILS.yml", "planning_loop: {}\n")
    write(root / "agents/project/C-MODE-PROMOTION-CHECKLIST.md", "# C-mode\n")
    write(root / "agents/project/ORG.md", "# Org\n")
    write(root / "agents/project/TEAMS.md", "# Teams\n")


def test_scan_reports_missing_sources_and_is_deterministic(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    (tmp_path / "agents/project/PLANNING-GUARDRAILS.yml").unlink()
    first = planning_loop.scan(tmp_path, trigger="manual")
    second = planning_loop.scan(tmp_path, trigger="manual")
    assert first == second
    assert any(item["category"] == "missing-source" for item in first["findings"])
    finding = first["findings"][0]
    assert {"source_path", "category", "confidence", "suggested_next_action"} <= set(finding)


def test_proposal_outbox_dedupes_and_writes_draft_task(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    scan = {
        "findings": [
            {
                "category": "missing-audit-link",
                "source_path": "agents/lead_engineer/tasks/TASK-X.md",
                "confidence": 0.9,
                "risk_tier": "low",
                "trace_id": None,
                "suggested_next_action": "repair audit link",
                "evidence": [{"summary": "missing audit", "confidence": 0.9}],
                "proposal_allowed": True,
            },
            {
                "category": "missing-audit-link",
                "source_path": "agents/lead_engineer/tasks/TASK-X.md",
                "confidence": 0.8,
                "risk_tier": "low",
                "trace_id": None,
                "suggested_next_action": "repair audit link",
                "evidence": [{"summary": "second missing audit", "confidence": 0.8}],
                "proposal_allowed": True,
            }
        ]
    }
    created = planning_loop.create_proposals(tmp_path, scan)
    repeated = planning_loop.create_proposals(tmp_path, scan)
    assert created["created_count"] == 1
    assert repeated["deduped_count"] == 1
    proposal = created["created"][0]
    assert len(proposal["evidence"]) == 2
    draft = tmp_path / proposal["draft_task_path"]
    text = draft.read_text(encoding="utf-8")
    assert "## Completion Criteria" in text
    assert "## Source Evidence" in text
    assert "## Verifier List" in text
    assert "## Risk Boundary" in text


def test_dedupe_outbox_marks_older_records_superseded(tmp_path: Path) -> None:
    outbox = tmp_path / "agents/planning/outbox"
    outbox.mkdir(parents=True)
    first = {
        "id": "PROP-AAAAAAAAAAAA",
        "status": "proposed",
        "dedupe_key": "doc_repair:x:y",
        "supersedes": [],
    }
    second = {
        "id": "PROP-BBBBBBBBBBBB",
        "status": "proposed",
        "dedupe_key": "doc_repair:x:y",
        "supersedes": ["PROP-AAAAAAAAAAAA"],
    }
    (outbox / "PROP-AAAAAAAAAAAA.json").write_text(json.dumps(first), encoding="utf-8")
    (outbox / "PROP-BBBBBBBBBBBB.json").write_text(json.dumps(second), encoding="utf-8")

    result = planning_loop.dedupe_outbox(tmp_path, apply=True, now="2026-06-10T00:00:00+00:00")

    assert result["status"] == "pass"
    updated = json.loads((outbox / "PROP-AAAAAAAAAAAA.json").read_text(encoding="utf-8"))
    kept = json.loads((outbox / "PROP-BBBBBBBBBBBB.json").read_text(encoding="utf-8"))
    assert updated["status"] == "superseded"
    assert updated["superseded_by"] == "PROP-BBBBBBBBBBBB"
    assert kept["status"] == "proposed"


def test_gate_blocks_hook_mutation_budget_and_kill_switch(tmp_path: Path, monkeypatch) -> None:
    seed_repo(tmp_path)
    assert planning_loop.planning_gate(tmp_path, trigger="hook", action="apply")["status"] == "block"
    assert planning_loop.planning_gate(tmp_path, proposal_count=99)["status"] == "block"
    monkeypatch.setenv("AGENT_RUNTIME_RSI_DISABLE", "1")
    assert planning_loop.planning_gate(tmp_path)["status"] == "block"


def test_schedule_trigger_writes_scan_without_canonical_mutation(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    result = planning_trigger.run_trigger(tmp_path, trigger="schedule", now="2026-06-10T00:00:00+00:00")
    assert result["status"] == "pass"
    assert result["canonical_mutation_allowed"] is False
    assert (tmp_path / result["scan_path"]).exists()


def test_release_version_mismatch_creates_high_risk_finding(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    write(tmp_path / "pyproject.toml", "[project]\nversion = \"1.2.3\"\n")
    write(tmp_path / "agents/project/release/RELEASE-DECISION.yml", "version: 1.2.4\n")
    report = planning_loop.scan(tmp_path)
    finding = next(item for item in report["findings"] if item["category"] == "release-version-mismatch")
    assert finding["risk_tier"] == "high"


def test_eval_trace_and_retro_inputs_create_proposal_categories(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    write(tmp_path / "agents/project/evals/trace.jsonl", '{"trace_id":"T1","status":"failed"}\n')
    write(
        tmp_path / "agents/lead_engineer/compound_log.md",
        "BRIEF drift\nresponse contract drift\nwrong language\nstatus vocabulary\n",
    )
    report = planning_loop.scan(tmp_path)
    categories = {item["category"] for item in report["findings"]}
    assert "eval-trace-regression" in categories
    assert "retro-compound-pattern" in categories


def test_c_mode_gate_requires_three_cycles_and_release_pass(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    blocked = planning_loop.c_mode_gate(tmp_path)
    assert blocked["status"] == "block"
    for index in range(3):
        write(tmp_path / f"agents/planning/cycles/cycle-{index}.json", json.dumps({"mode": "B", "status": "pass"}))
    write(tmp_path / "reviews/RELEASE-VERSION-CONSISTENCY-STEWARD.json", json.dumps({"status": "pass"}))
    assert planning_loop.c_mode_gate(tmp_path)["status"] == "pass"
