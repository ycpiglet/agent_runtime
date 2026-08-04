import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import backlog_board  # noqa: E402


def _frontmatter_parsers():
    template_path = (
        ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "backlog_board.py"
    )
    spec = importlib.util.spec_from_file_location(
        "tmpl_backlog_board_frontmatter", template_path
    )
    assert spec is not None and spec.loader is not None
    template = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = template
    spec.loader.exec_module(template)
    return (backlog_board, template)


def _parse_summary(parser, value: str):
    meta, _ = parser.parse_frontmatter(f"---\nsummary: {value}\n---\n")
    return meta["summary"]


def test_frontmatter_preserves_hashes_inside_quoted_scalars() -> None:
    for parser in _frontmatter_parsers():
        assert _parse_summary(parser, '"PR #167 intact" # outside') == "PR #167 intact"
        assert _parse_summary(parser, "'issue #298 intact' # outside") == "issue #298 intact"


def test_frontmatter_preserves_hash_after_escaped_double_quotes() -> None:
    for parser in _frontmatter_parsers():
        assert (
            _parse_summary(parser, '"said \\"PR #167\\" intact" # outside')
            == 'said \\"PR #167\\" intact'
        )


def test_frontmatter_decodes_only_marker_bearing_work_scalars() -> None:
    expected = 'Preserve issue #167 with both \'single\' and "double" quotes.'
    for parser in _frontmatter_parsers():
        encoded = json.dumps(
            parser.ENCODED_WORK_SCALAR_PREFIX + expected,
            ensure_ascii=False,
        )
        assert _parse_summary(parser, encoded) == expected
        meta, _ = parser.parse_frontmatter(
            f"---\nacceptance:\n  - {encoded}\n---\n"
        )
        assert meta["acceptance"] == [expected]
        assert _parse_summary(parser, '"legacy \\"quoted\\" value"') == 'legacy \\"quoted\\" value'


def test_frontmatter_preserves_hashes_inside_flow_lists() -> None:
    text = '---\ntags: ["PR #167", \'issue #298\', plain] # outside\n---\n'
    for parser in _frontmatter_parsers():
        meta, _ = parser.parse_frontmatter(text)
        assert meta["tags"] == ["PR #167", "issue #298", "plain"]


def test_frontmatter_unterminated_quote_preserves_remaining_text() -> None:
    for parser in _frontmatter_parsers():
        assert _parse_summary(parser, '"PR #167 remains') == "PR #167 remains"


def test_frontmatter_still_strips_unquoted_comments() -> None:
    for parser in _frontmatter_parsers():
        assert _parse_summary(parser, "plain value # outside") == "plain value"


def test_frontmatter_distinguishes_plain_apostrophes_and_closed_quotes() -> None:
    for parser in _frontmatter_parsers():
        assert parser.strip_comment("owner's value # outside") == "owner's value "
        assert parser.strip_comment('"PR #167" # outside') == '"PR #167" '
        assert parser.strip_comment("'owner''s PR #167' # outside") == "'owner''s PR #167' "


def test_frontmatter_plain_scalar_quote_does_not_hide_comment() -> None:
    for parser in _frontmatter_parsers():
        assert parser.strip_comment("plain 'PR #167' # outside") == "plain 'PR "
        assert parser.strip_comment('plain "PR #167" # outside') == 'plain "PR '
        assert parser.strip_comment("plain - 'PR #167' # outside") == "plain - 'PR "
        assert parser.strip_comment('plain, "PR #167" # outside') == 'plain, "PR '
        assert (
            parser.strip_comment('summary: plain "unterminated # outside')
            == 'summary: plain "unterminated '
        )


def _write_task(tasks_dir: Path, task_id: str, task_set_id: str, status: str = "planned", priority: str = "P0") -> None:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.md").write_text(
        f"""---
id: {task_id}
task_uid: 11111111-1111-4111-8111-{task_id[-3:]}000000000
registered_at: 2026-06-10T12:00:00+09:00
status: {status}
priority: {priority}
difficulty: M
est_hours: 2
est_tokens: 200
task_set_id: {task_set_id}
tags:
  - test
---

## Goal
- Keep this task inside its task set.
""",
        encoding="utf-8",
    )


def test_backlog_board_groups_tasks_by_task_set_before_lane(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="in_progress")
    _write_task(tasks_dir, "TASK-AR-902", "TASKSET-AR-QUALITY-LOOP", status="planned", priority="P1")
    _write_task(tasks_dir, "TASK-AR-903", "TASKSET-AR-PANE-PROGRESS", status="planned")

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks)

    assert "task_set_count: 2" in board
    assert "Recommended next:" not in board
    assert "Routing rule: choose a task set first" in board
    assert "## Action Board" in board
    assert "### Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`)" in board
    assert "### Progress Scout (`TASKSET-AR-PANE-PROGRESS`)" in board
    assert "| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |" in board

    quality_section = board.split("### Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`)", 1)[1].split("### Progress Scout", 1)[0]
    assert quality_section.index("TASK-AR-901") < quality_section.index("TASK-AR-902")


def test_backlog_board_reads_registered_taskset_definitions(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-TEST-WORK-CLI", status="planned")
    registry = tmp_path / "agents" / "project" / "work-items" / "TASKSET-DEFINITIONS.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-taskset-definitions/v1",
                "tasksets": [
                    {
                        "task_set_id": "TASKSET-TEST-WORK-CLI",
                        "display_name": "Work CLI Test",
                        "summary": "Structured registration test taskset.",
                        "order": 501,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks, root=tmp_path)

    assert "### Work CLI Test (`TASKSET-TEST-WORK-CLI`)" in board
    assert "- Flow: Structured registration test taskset." in board


def test_backlog_board_shows_project_unit_and_wip_claim_summary(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="in_progress")
    task_path = tasks_dir / "TASK-AR-901.md"
    text = task_path.read_text(encoding="utf-8")
    text = text.replace(
        "task_set_id: TASKSET-AR-QUALITY-LOOP\n",
        "task_set_id: TASKSET-AR-QUALITY-LOOP\n"
        "initiative_id: INIT-TEST\n"
        "project_id: PROJECT-TEST\n"
        "unit_spec: agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md\n",
    )
    task_path.write_text(text, encoding="utf-8")
    claims_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claims_dir.mkdir(parents=True)
    (claims_dir / "CLAIM-901.json").write_text(
        """{
  "claim_id": "CLAIM-901",
  "task_id": "TASK-AR-901",
  "task_set_id": "TASKSET-AR-QUALITY-LOOP",
  "status": "working",
  "claimed_at": "2026-06-10T00:00:00+09:00"
}
""",
        encoding="utf-8",
    )

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks, root=tmp_path)

    assert "- WIP: active `1/3`;" in board
    assert "INIT-TEST" in board
    assert "PROJECT-TEST" in board
    assert "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md" in board


def test_backlog_board_hides_completed_tasks_and_completed_task_sets(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="completed")
    _write_task(tasks_dir, "TASK-AR-902", "TASKSET-AR-QUALITY-LOOP", status="done")
    _write_task(tasks_dir, "TASK-AR-903", "TASKSET-AR-RELEASE-STEWARD", status="in_progress")

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks)

    assert "task_count: 3" in board
    assert "open_count: 1" in board
    assert "task_set_count: 1" in board
    assert "completed_count: 2" in board
    assert "completed_task_set_count: 1" in board
    action_board = board.split("## Action Board", 1)[1].split("## Archived Task Sets", 1)[0]
    assert "### Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`)" not in action_board
    assert "TASK-AR-901" not in action_board
    assert "TASK-AR-902" not in action_board
    assert "### Release Steward (`TASKSET-AR-RELEASE-STEWARD`)" in board
    assert "TASK-AR-903" in board
    assert "## Archived Task Sets" in board
    archived_sets = board.split("## Archived Task Sets", 1)[1]
    assert "| Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`) |" in archived_sets
    assert "| `2/2` done |" in archived_sets
    archived_set_summary = archived_sets.split("## Rollups", 1)[0]
    assert "TASK-AR-901" not in archived_set_summary
    assert "TASK-AR-902" not in archived_set_summary
    # TASK-AR-533: completed task files are no longer dumped inline on the board.
    # The board carries a rollup pointer; per-file detail lives in ARCHIVE-INDEX.md.
    assert "## Archived Task Files" not in board
    assert "## Rollups" in board
    rollups = board.split("## Rollups", 1)[1]
    assert "ARCHIVE-INDEX.md" in rollups
    assert "`2`" in rollups
    assert "TASK-AR-901" not in board
    assert "TASK-AR-902" not in board
    archive_index = backlog_board.render_archive_index(tasks)
    assert "TASK-AR-901" in archive_index
    assert "TASK-AR-902" in archive_index
    assert "registered_at" in archive_index


def test_sync_taskset_registry_creates_updates_and_archives(tmp_path: Path) -> None:
    # TASK-AR-329: the registry auto-sync path used when a UI taskset proposal is
    # consumed. The registry-lock test below pins task-file classification; this
    # gives that lock an automated registry-write path so a UI-created taskset
    # lands in TASKSET-DEFINITIONS.json without a hand edit.
    created = backlog_board.sync_taskset_registry(
        tmp_path,
        "TASKSET-UI-NEW",
        display_name="UI New",
        summary="made in the console",
        order=600,
    )
    assert created["action"] == "created"
    assert created["order"] == 600

    registry_path = tmp_path / "agents" / "project" / "work-items" / "TASKSET-DEFINITIONS.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "agent-runtime-taskset-definitions/v1"
    assert payload["tasksets"][0]["task_set_id"] == "TASKSET-UI-NEW"

    # The board picks the new taskset up via the merged registry info map.
    info_map = backlog_board._task_set_info_map(tmp_path)
    assert "TASKSET-UI-NEW" in info_map
    assert info_map["TASKSET-UI-NEW"].display_name == "UI New"

    # Rename = upsert/update; archive flips the flag, both idempotent.
    updated = backlog_board.sync_taskset_registry(
        tmp_path, "TASKSET-UI-NEW", display_name="UI Renamed", summary="made in the console"
    )
    assert updated["action"] == "updated"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    assert payload["tasksets"][0]["display_name"] == "UI Renamed"
    assert len(payload["tasksets"]) == 1

    archived = backlog_board.sync_taskset_registry(
        tmp_path, "TASKSET-UI-NEW", display_name="", summary="", archived=True
    )
    assert archived["action"] == "archived"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    assert payload["tasksets"][0]["archived"] is True


def test_ui_created_taskset_renders_on_the_board(tmp_path: Path) -> None:
    # A UI-created taskset (registry row) plus a task assigned to it must render
    # in the generated board, proving registry/board consistency.
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write_task(tasks_dir, "TASK-AR-950", "TASKSET-UI-MADE", status="in_progress")
    backlog_board.sync_taskset_registry(
        tmp_path,
        "TASKSET-UI-MADE",
        display_name="Console Made",
        summary="created from the console UI",
        order=700,
    )

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks, root=tmp_path)

    assert "### Console Made (`TASKSET-UI-MADE`)" in board
    assert "- Flow: created from the console UI" in board


def test_template_backlog_board_merges_registry_reader(tmp_path: Path) -> None:
    # TASK-AR-329 (W4b fix): the shipped template board must mirror BOTH the
    # registry writer AND the reader merge, so a UI-created taskset renders with
    # its registered name in downstream host projects instead of "Unclassified".
    import importlib.util

    tmpl_path = (
        ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "backlog_board.py"
    )
    spec = importlib.util.spec_from_file_location("tmpl_backlog_board", tmpl_path)
    tmpl = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = tmpl
    spec.loader.exec_module(tmpl)

    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write_task(tasks_dir, "TASK-AR-951", "TASKSET-TMPL-MADE", status="in_progress")
    tmpl.sync_taskset_registry(
        tmp_path,
        "TASKSET-TMPL-MADE",
        display_name="Template Console Made",
        summary="created from the console UI in a host project",
        order=700,
    )

    # Reader merge resolves the registered name (not the Unclassified fallback).
    assert tmpl.task_set_info("TASKSET-TMPL-MADE", tmp_path).display_name == "Template Console Made"
    assert tmpl.task_set_info("TASKSET-TMPL-MADE").display_name == "Unclassified"  # no root -> base only

    tasks = tmpl.load_tasks(tasks_dir)
    board = tmpl.render(tasks, root=tmp_path)
    assert "Template Console Made" in board
    assert "`TASKSET-TMPL-MADE`" in board


def test_triage_tasks_are_held_out_of_active_and_shown_in_triage(tmp_path: Path) -> None:
    # TASK-AR-538: status:triage is an intake state -- excluded from the Active
    # board, surfaced in a Triage inbox, and counted in the needs-attention rollup.
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="triage")
    _write_task(tasks_dir, "TASK-AR-902", "TASKSET-AR-QUALITY-LOOP", status="in_progress")

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks, root=tmp_path)

    assert "## Triage" in board
    triage_section = board.split("## Triage", 1)[1].split("\n## ", 1)[0]
    assert "TASK-AR-901" in triage_section
    # The active task set tables (above Triage) must NOT contain the triage task.
    active_zone = board.split("## Action Board", 1)[1].split("## Triage", 1)[0]
    assert "TASK-AR-901" not in active_zone
    assert "TASK-AR-902" in active_zone  # in_progress task stays active
    # Needs-attention rollup reflects the triage item.
    rollups = board.split("## Rollups", 1)[1]
    assert "Needs attention" in rollups
    assert backlog_board.is_triage(tasks[0]) or backlog_board.is_triage(tasks[1])


def test_real_backlog_tasks_are_classified_into_registered_task_sets() -> None:
    tasks = backlog_board.load_tasks(ROOT / "agents" / "lead_engineer" / "tasks")
    task_set_ids = {task.task_set_id for task in tasks}

    assert len(tasks) >= 55
    assert task_set_ids == {
        "TASKSET-AR-CONTEXT-KNOWLEDGE",
        "TASKSET-AR-QUALITY-LOOP",
        "TASKSET-AR-MIGRATION-PARITY",
        "TASKSET-AR-MERGE-QUEUE-SAFETY",
        "TASKSET-AR-HOST-REQUIRED-MERGE-GATES",
        "TASKSET-AR-RELEASE-STEWARD",
        "TASKSET-AR-UI-CONSOLE",
        "TASKSET-AR-RSI-PLANNING",
        "TASKSET-AR-RSI-OPERATING-SYSTEM",
        "TASKSET-AR-PANE-PROGRESS",
        "TASKSET-AR-COLLAB-CONCURRENCY",
        "TASKSET-AR-GOVERNANCE-OPS",
        "TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE",
        "TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION",
        "TASKSET-AR-TASK-IDENTITY",
        "TASKSET-AR-UI-DESIGN-SYSTEM",
        "TASKSET-AR-UI-DESIGN-IMPLEMENTATION",
        "TASKSET-AR-REPO-HYGIENE",
        "TASKSET-AR-OPS-FEEDBACK-ANALYSIS",
        "TASKSET-AR-VISION-GAP-CLOSURE",
        "TASKSET-AR-UI-UX-V2",
        "TASKSET-AR-UI-PLATFORM-EXTENSIONS",
        "TASKSET-AR-UI-LIVING-CONSOLE",
        "TASKSET-AR-PM-OPERATING-SYSTEM",
        "TASKSET-AR-DOC-TO-PLAN",
        "TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE",
        "TASKSET-AR-PARALLEL-WAVE-EXECUTION",
        "TASKSET-AR-AGENT-IDENTITY-CONTRACT",
        "TASKSET-AR-WORK-METADATA-ANALYTICS",
        "TASKSET-AR-OPS-ERGONOMICS",
        "TASKSET-AR-HOST-FEEDBACK-INTAKE",
        "TASKSET-AR-WORK-STORE-RESTRUCTURE",
        "TASKSET-AR-UNIFIED-DECISION-CONSOLE",
        "TASKSET-AR-PRODUCT-MATURITY-UPLIFT",
        "TASKSET-AR-AGENT-ORG-DELEGATION",
        "TASKSET-AR-DECISION-FIRST-CONSOLE-IA",
        "TASKSET-AR-BUSINESS-OPERATIONS-TEAMS",
        "TASKSET-AR-BUSINESS-OPERATING-SYSTEM",
        "TASKSET-AR-SELF-IMPROVEMENT-CADENCE",
        "TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE",
        "TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE",
        "TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION",
        "TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS",
        "TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT",
        "TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT",
        "TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION",
        "TASKSET-AR-RELEASE-AUTO-NONCRITICAL",
        "TASKSET-AR-AUTO-MERGE-INTEGRITY",
        "TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION",
        "TASKSET-AR-PR303-CI-SCHEMA-RECOVERY",
        "TASKSET-AR-BACKLOG-TASKSET-TEST-RECOVERY",
            "TASKSET-AR-TERMINAL-STATUS-START-GUARD",
            "TASKSET-AR-WORK-CLI-INTEGRITY",
            "TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION",
            "TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY",
            "TASKSET-AR-RELEASE-CADENCE-QUERY-RECOVERY",
        "TASKSET-AR-SELF-EVAL-QUERY-INTEGRITY",
        "TASKSET-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY",
        "TASKSET-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW",
        "TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY",
        "TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT",
        "TASKSET-AR-V080-ADOPTION-ENFORCEMENT",
        "TASKSET-AR-V080-OPERABILITY-HARDENING",
        "TASKSET-AR-VISUAL-ASSET-ADOPTION",
        "TASKSET-AR-VISUAL-SYSTEM-INTEGRATION",
        "TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY",
        "TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY",
        "TASKSET-AR-CONSOLE-OVERHAUL-P0",
        "TASKSET-AR-CONSOLE-OVERHAUL-P1",
    }


def test_ar627_weekly_throughput_counts_recent_completions(tmp_path):
    # TASK-AR-627: board Rollups surfaces a 7-day throughput number.
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=1)).isoformat()
    old = (now - timedelta(days=40)).isoformat()
    def _mk(tid, completed_at):
        return backlog_board.Task(
            path=tmp_path / f"{tid}.md",
            meta={"id": tid, "status": "completed", "completed_at": completed_at},
            goal="g",
        )
    tasks = [_mk("TASK-AR-991", recent), _mk("TASK-AR-992", old)]
    assert backlog_board.weekly_throughput(tasks) == 1
    board = backlog_board.render(tasks, root=tmp_path)
    assert "Throughput (7d)" in board


def test_ar630_board_needs_attention_matches_console_inbox(tmp_path):
    # TASK-AR-630: the board's headline attention number and the console cockpit
    # must come from the same module and agree on the same state.
    import attention_inbox
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="blocked")
    _write_task(tasks_dir, "TASK-AR-902", "TASKSET-AR-QUALITY-LOOP", status="in_progress")
    canonical = attention_inbox.inbox(tmp_path)
    assert canonical["total"] > 0  # W4b: guard against a degenerate 0==0 pass
    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks, root=tmp_path)
    assert f"- Needs attention: `{canonical['total']}`" in board
    assert "single source: scripts/attention_inbox.py" in board


def test_ar630_board_without_root_falls_back_to_lane_heuristic(tmp_path):
    # Rootless render (host degraded path) keeps the legacy triage+Ask line.
    tasks_dir = tmp_path / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="in_progress")
    board = backlog_board.render(backlog_board.load_tasks(tasks_dir))
    assert "- Needs attention:" in board
    assert "single source" not in board
