from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import idea_vault, planning_loop

VAULT_HEADER = (
    "# IDEA VAULT\n\n"
    "## Entries\n\n"
    "| id | idea | shelved_at | shelved_reason | origin_ref | revisit_after | revival_criteria | status |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
)

ROW_FMT = "| {id} | {idea} | {shelved_at} | {reason} | {origin} | {revisit} | {criteria} | {status} |\n"


def _row(
    *,
    id: str,
    revisit: str,
    status: str = "shelved",
    idea: str = "an idea",
    reason: str = "a reason",
    criteria: str = "a criterion",
    origin: str = "RESEARCH-X",
    shelved_at: str = "2026-06-11",
) -> str:
    return ROW_FMT.format(
        id=id, idea=idea, shelved_at=shelved_at, reason=reason, origin=origin,
        revisit=revisit, criteria=criteria, status=status,
    )


def seed_vault(root: Path, rows: list[str], *, footer: str = "\n- Action Board: x\n") -> Path:
    path = root / idea_vault.VAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(VAULT_HEADER + "".join(rows) + footer, encoding="utf-8")
    return path


def test_list_parses_all_entries(tmp_path: Path) -> None:
    seed_vault(
        tmp_path,
        [
            _row(id="IV-001", revisit="2026-09-01"),
            _row(id="IV-002", revisit="2026-10-01", status="adopted"),
        ],
    )
    _, entries = idea_vault.load_registry(tmp_path)
    assert [e["id"] for e in entries] == ["IV-001", "IV-002"]
    assert entries[0]["status"] == "shelved"
    assert entries[1]["status"] == "adopted"


def test_due_is_date_based_with_fixture_clock(tmp_path: Path) -> None:
    seed_vault(
        tmp_path,
        [
            _row(id="IV-001", revisit="2026-09-01"),  # due before now
            _row(id="IV-002", revisit="2027-01-01"),  # equal to now -> due
            _row(id="IV-003", revisit="2027-06-01"),  # after now -> not due
            _row(id="IV-004", revisit="2026-01-01", status="adopted"),  # not active -> never due
            _row(id="IV-005", revisit="2026-01-01", status="re-deferred"),  # active alt status -> due
        ],
    )
    _, entries = idea_vault.load_registry(tmp_path)
    due = idea_vault.due_entries(entries, "2027-01-01")
    assert sorted(e["id"] for e in due) == ["IV-001", "IV-002", "IV-005"]


def test_due_command_always_exits_zero(tmp_path: Path) -> None:
    seed_vault(tmp_path, [_row(id="IV-001", revisit="2099-01-01")])  # nothing due
    rc = idea_vault.main(["--root", str(tmp_path), "due", "--now", "2026-01-01", "--json"])
    assert rc == 0


def test_revive_emits_proposal_not_a_task(tmp_path: Path) -> None:
    path = seed_vault(tmp_path, [_row(id="IV-001", revisit="2026-09-01")])
    rc = idea_vault.main(["--root", str(tmp_path), "revive", "IV-001", "--now", "2027-01-01", "--json"])
    assert rc == 0

    # A proposal was written to the planning outbox.
    outbox = tmp_path / "agents" / "planning" / "outbox"
    proposals = list(outbox.glob("PROP-*.json"))
    assert len(proposals) == 1
    proposal = json.loads(proposals[0].read_text(encoding="utf-8"))
    assert proposal["origin_type"] == "idea_vault_revival"
    assert proposal["proposal_output"] == "owner_decision"
    assert proposal["canonical_mutation_allowed"] is False
    assert proposal["entry_id"] == "IV-001"
    assert "ab_experiment" in proposal

    # NO task was created anywhere.
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    assert not tasks_dir.exists() or not list(tasks_dir.glob("*.md"))

    # Entry status flipped to revived in the registry table.
    _, entries = idea_vault.load_registry(tmp_path)
    assert entries[0]["status"] == "revived"
    assert "revived" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("status", ["retired", "adopted"])
def test_revive_rejects_terminal_status(tmp_path: Path, status: str) -> None:
    seed_vault(tmp_path, [_row(id="IV-001", revisit="2026-09-01", status=status)])
    rc = idea_vault.main(["--root", str(tmp_path), "revive", "IV-001", "--json"])
    assert rc == 1
    assert not (tmp_path / "agents" / "planning" / "outbox").exists()


@pytest.mark.parametrize("status", ["retired", "adopted"])
def test_defer_rejects_terminal_status(tmp_path: Path, status: str) -> None:
    path = seed_vault(tmp_path, [_row(id="IV-001", revisit="2026-09-01", status=status)])
    rc = idea_vault.main(["--root", str(tmp_path), "defer", "IV-001", "--until", "2027-12-01", "--json"])
    assert rc == 1
    # Terminal decision-history is preserved unchanged.
    _, entries = idea_vault.load_registry(tmp_path)
    assert entries[0]["status"] == status
    assert entries[0]["revisit_after"] == "2026-09-01"
    assert status in path.read_text(encoding="utf-8")


def test_defer_updates_revisit_after_and_status(tmp_path: Path) -> None:
    path = seed_vault(tmp_path, [_row(id="IV-001", revisit="2026-09-01")])
    rc = idea_vault.main(["--root", str(tmp_path), "defer", "IV-001", "--until", "2027-12-01", "--json"])
    assert rc == 0
    _, entries = idea_vault.load_registry(tmp_path)
    assert entries[0]["revisit_after"] == "2027-12-01"
    assert entries[0]["status"] == "re-deferred"
    # Untouched cells are preserved.
    assert "an idea" in path.read_text(encoding="utf-8")


def test_defer_rejects_bad_date(tmp_path: Path) -> None:
    seed_vault(tmp_path, [_row(id="IV-001", revisit="2026-09-01")])
    rc = idea_vault.main(["--root", str(tmp_path), "defer", "IV-001", "--until", "not-a-date", "--json"])
    assert rc == 1


def test_validate_passes_clean_registry(tmp_path: Path) -> None:
    seed_vault(
        tmp_path,
        [
            _row(id="IV-001", revisit="2026-09-01"),
            _row(id="IV-002", revisit="2026-10-01", status="adopted"),
        ],
    )
    _, entries = idea_vault.load_registry(tmp_path)
    assert idea_vault.validate_entries(entries) == []


def test_validate_catches_schema_violations(tmp_path: Path) -> None:
    seed_vault(
        tmp_path,
        [
            _row(id="IV-001", revisit="bad-date"),
            _row(id="IV-002", revisit="2026-10-01", status="bogus"),
            _row(id="IV-001", revisit="2026-11-01"),  # duplicate id
            _row(id="IV-003", revisit="2026-12-01", reason=""),  # empty required cell
        ],
    )
    _, entries = idea_vault.load_registry(tmp_path)
    errors = idea_vault.validate_entries(entries)
    joined = " ".join(errors)
    assert "revisit_after not YYYY-MM-DD" in joined
    assert "bad status" in joined
    assert "duplicate id" in joined
    assert "empty shelved_reason" in joined


def test_real_registry_validates(tmp_path: Path) -> None:
    # The shipped registry must always pass its own schema check.
    root = Path(idea_vault.ROOT)
    _, entries = idea_vault.load_registry(root)
    assert len(entries) >= 12  # 12 shipped seeds; guards against silent seed deletion
    assert idea_vault.validate_entries(entries) == []


def test_planning_scan_surfaces_due_ideas_non_blocking(tmp_path: Path) -> None:
    seed_vault(
        tmp_path,
        [
            _row(id="IV-001", revisit="2026-09-01"),  # due
            _row(id="IV-002", revisit="2099-01-01"),  # not due
        ],
    )
    report = planning_loop.scan(tmp_path, trigger="manual", now="2027-01-01T00:00:00+00:00")
    revival = [f for f in report["findings"] if f["category"] == "idea-vault-revival-due"]
    assert len(revival) == 1
    assert revival[0]["source_path"].endswith("#IV-001")
    # Owner-boundary but non-blocking: scan status stays pass (no high-risk finding).
    assert report["status"] == "pass"
    assert revival[0]["risk_tier"] == "owner"


def test_planning_scan_no_vault_is_noop(tmp_path: Path) -> None:
    # No vault file -> no idea-vault findings, scan still works.
    report = planning_loop.scan(tmp_path, trigger="manual", now="2027-01-01T00:00:00+00:00")
    assert not any(f["category"] == "idea-vault-revival-due" for f in report["findings"])
