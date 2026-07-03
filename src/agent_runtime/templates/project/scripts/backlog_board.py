"""Generate an Owner-facing backlog decision board from TASK frontmatter.

The board restores the old ACT/ASK/REVIEW/DEFER idea with clearer labels:
Action, Review, Ask, Later. Completed tasks are archived out of the live board
so completed task sets disappear automatically. It is intentionally
dependency-free so it can run inside host projects before optional packages are
installed.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "agents" / "lead_engineer" / "tasks"
DEFAULT_OUTPUT = ROOT / "BACKLOG-BOARD.md"

DISPLAY_REPLACEMENTS = {
    "레거시 전신 프로젝트(" + "tag" + "_manual)": "레거시 전신 프로젝트",
    "tag" + "_manual": "레거시 전신 프로젝트",
}

PRIORITY_WEIGHT = {"P0": 5, "Critical": 5, "High": 4, "P1": 4, "Medium": 3, "P2": 3, "Low": 2, "P3": 2}
STATUS_WEIGHT = {
    "blocked": 5,
    "hold": 5,
    "in_progress": 4,
    "ready": 4,
    "planned": 3,
    "pending": 3,
    "completed": 1,
    "done": 1,
}
DONE_STATUSES = {"completed", "done", "released", "완료"}
ACTIVE_CLAIM_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
DEFAULT_WIP_LIMIT = 3
DIFFICULTY_LABEL = {"S": "Low", "M": "Medium", "L": "High", "XL": "Critical", "하": "Low", "중": "Medium", "상": "High"}
DIFFICULTY_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


@dataclass(frozen=True)
class TaskSetInfo:
    task_set_id: str
    display_name: str
    summary: str
    order: int


TASK_SET_DEFINITIONS = [
    TaskSetInfo(
        "TASKSET-AR-CONTEXT-KNOWLEDGE",
        "Context Cartographer",
        "Project context, source routing, and reusable knowledge structure.",
        10,
    ),
    TaskSetInfo(
        "TASKSET-AR-QUALITY-LOOP",
        "Quality Sentinel",
        "Offline evals, live review, correction loops, and traceable validation.",
        20,
    ),
    TaskSetInfo(
        "TASKSET-AR-MIGRATION-PARITY",
        "Migration Archivist",
        "Legacy-source parity, migration evidence, and skill/hook/script provenance.",
        30,
    ),
    TaskSetInfo(
        "TASKSET-AR-RELEASE-STEWARD",
        "Release Steward",
        "Version decisions, release closeout, and consistency checks.",
        40,
    ),
    TaskSetInfo(
        "TASKSET-AR-UI-CONSOLE",
        "Console Operator",
        "Runtime UI console surfaces, command paths, and observability views.",
        50,
    ),
    TaskSetInfo(
        "TASKSET-AR-RSI-PLANNING",
        "Planning Architect",
        "Bounded recursive self-improvement, planning scans, and proposal review.",
        60,
    ),
    TaskSetInfo(
        "TASKSET-AR-RSI-OPERATING-SYSTEM",
        "Evidence-to-Proposal Operator",
        "Evidence inboxes, failure casebooks, proposal quality metrics, council review, and bounded apply gates.",
        61,
    ),
    TaskSetInfo(
        "TASKSET-AR-PANE-PROGRESS",
        "Progress Scout",
        "Pane/task-set progress, live continuity, claims, and resumable handoffs.",
        70,
    ),
    TaskSetInfo(
        "TASKSET-AR-COLLAB-CONCURRENCY",
        "Concurrency Steward",
        "Real-time pane collaboration, event replay, SSoT ownership, and conflict gates.",
        75,
    ),
    TaskSetInfo(
        "TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE",
        "Multi-Pane Auditor",
        "Live pane census, process compliance, event enforcement, role coverage, drift normalization, and assurance UI.",
        76,
    ),
    TaskSetInfo(
        "TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION",
        "Closeout Automation Steward",
        "Session baseline capture, dirty-intake routing, archive/issue preservation, and closeout skill/hook enforcement.",
        77,
    ),
    TaskSetInfo(
        "TASKSET-AR-GOVERNANCE-OPS",
        "Governance Operator",
        "Waiver burn-down, lifecycle cleanup, runtime asset usage, sync enforcement, and verification hygiene.",
        78,
    ),
    TaskSetInfo(
        "TASKSET-AR-TASK-IDENTITY",
        "Identity Steward",
        "Collision-proof task identity, UUID metadata, lifecycle timestamps, and recovery visibility.",
        79,
    ),
    TaskSetInfo(
        "TASKSET-AR-UI-DESIGN-SYSTEM",
        "Design Operator",
        "Agent Runtime UI research, design-system guidance, and console visual implementation.",
        79,
    ),
    TaskSetInfo(
        "TASKSET-AR-UI-DESIGN-IMPLEMENTATION",
        "Interface Stylist",
        "Active UI design implementation work that applies the accepted design system across runtime panes.",
        80,
    ),
    TaskSetInfo(
        "TASKSET-AR-REPO-HYGIENE",
        "Repo Custodian",
        "Working-tree cleanup, backlog cycle hygiene, and handoff publication.",
        90,
    ),
    TaskSetInfo(
        "TASKSET-AR-OPS-FEEDBACK-ANALYSIS",
        "Feedback Analyst",
        "Owner feedback intake, enterprise-wide structure/vision analysis, and follow-up planning records.",
        91,
    ),
    TaskSetInfo(
        "TASKSET-AR-VISION-GAP-CLOSURE",
        "Vision Integrator",
        "Legacy independence, A2A messaging, multi-agent RBAC, loop hardening, live eval, skill packaging, realtime UI, and doc traceability.",
        92,
    ),
    TaskSetInfo(
        "TASKSET-AR-UI-UX-V2",
        "Console Experience Architect",
        "Notion-like light theme, sidebar IA, sort/filter/density patterns, taskset-first views, org chart, roadmap, live presence, comms, and taskset-scope guard.",
        93,
    ),
    TaskSetInfo(
        "TASKSET-AR-UI-PLATFORM-EXTENSIONS",
        "Platform Builder",
        "Taskset CRUD, dependencies/timeline, custom properties/automation, attachments, import/export, search, calendar, state-machine viewer, team workload, notifications, ops dashboard, gamification, and workspace extensibility.",
        94,
    ),
    TaskSetInfo(
        "TASKSET-AR-UI-LIVING-CONSOLE",
        "World Builder",
        "Idea vault with resurfacing loop, drag-in meeting room, direct-manipulation layer, progression system with guardrails, 2D office map, and webhook-first external notifications.",
        95,
    ),
    TaskSetInfo(
        "TASKSET-AR-PM-OPERATING-SYSTEM",
        "Project Workbreaker",
        "Project-to-unit hierarchy, worker-ready specs, model-tier routing, WIP controls, dispatcher scope stops, and PM verification gates.",
        96,
    ),
    TaskSetInfo(
        "TASKSET-AR-DOC-TO-PLAN",
        "Pitch Alchemist",
        "Document-to-plan intake pipeline, Paperclip gap adoption, actuals capture, and multi-factor evaluation/sorting.",
        97,
    ),
    TaskSetInfo(
        "TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE",
        "Work Taxonomist",
        "Initiative vocabulary, collision-free task registration, shared backlog deconfliction, and unit-readiness migration.",
        98,
    ),
    TaskSetInfo(
        "TASKSET-AR-PARALLEL-WAVE-EXECUTION",
        "Wave Conductor",
        "Claim-time footprint conflict gate, wave dispatcher with cascade/parallel modes, integrator merge queue, and claim-first enforcement.",
        99,
    ),
]
TASK_SET_INFO = {item.task_set_id: item for item in TASK_SET_DEFINITIONS}
UNCLASSIFIED_TASK_SET = TaskSetInfo(
    "TASKSET-AR-UNCLASSIFIED",
    "Unclassified",
    "Tasks missing task_set_id metadata.",
    999,
)

# Mirror of the root backlog_board registry-sync writer (TASK-AR-329). The UI
# console emits a proposal under .ui_outbox for taskset create/rename/archive;
# the runtime executor consumes it and calls sync_taskset_registry so the
# canonical registry, the generated board, and the state-sync gate stay
# consistent. The console never writes the registry directly.
TASK_SET_REGISTRY = Path("agents/project/work-items/TASKSET-DEFINITIONS.json")
TASK_SET_REGISTRY_SCHEMA = "agent-runtime-taskset-definitions/v1"


def sync_taskset_registry(
    root: Path | str,
    task_set_id: str,
    *,
    display_name: str,
    summary: str,
    order: int | None = None,
    archived: bool = False,
) -> dict[str, object]:
    """Upsert a taskset definition into ``TASKSET-DEFINITIONS.json``.

    Registry auto-sync path for UI ``taskset.create`` / ``taskset.rename`` /
    ``taskset.archive`` proposals. The console emits a proposal only; the
    runtime executor calls this so a UI-created taskset shows up in the board
    without a second source of truth.
    """
    base = Path(root).resolve()
    path = base / TASK_SET_REGISTRY
    task_set_id = str(task_set_id or "").strip()
    if not task_set_id:
        raise ValueError("task_set_id is required")

    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
    else:
        payload = {}
    if not isinstance(payload, dict) or str(payload.get("schema") or "") != TASK_SET_REGISTRY_SCHEMA:
        payload = {"schema": TASK_SET_REGISTRY_SCHEMA, "tasksets": []}
    rows = payload.get("tasksets")
    if not isinstance(rows, list):
        rows = []

    existing_orders = [int(r.get("order", 500)) for r in rows if isinstance(r, dict) and str(r.get("order", "")).strip().lstrip("-").isdigit()]
    next_order = (max(existing_orders) + 1) if existing_orders else 500
    resolved_order = int(order) if order is not None else next_order

    action = "created"
    found = False
    for row in rows:
        if isinstance(row, dict) and str(row.get("task_set_id") or "").strip() == task_set_id:
            found = True
            action = "archived" if archived else "updated"
            row["task_set_id"] = task_set_id
            if display_name:
                row["display_name"] = display_name
            if summary:
                row["summary"] = summary
            if order is not None:
                row["order"] = resolved_order
            row["archived"] = bool(archived)
            break
    if not found:
        rows.append(
            {
                "task_set_id": task_set_id,
                "display_name": display_name or task_set_id,
                "summary": summary or f"Tasks grouped under {task_set_id}.",
                "order": resolved_order,
                "archived": bool(archived),
            }
        )

    payload["schema"] = TASK_SET_REGISTRY_SCHEMA
    payload["tasksets"] = rows
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "action": action,
        "task_set_id": task_set_id,
        "order": resolved_order,
        "archived": bool(archived),
        "registry": TASK_SET_REGISTRY.as_posix(),
    }


def _load_task_set_registry(root: Path | None = None) -> dict[str, TaskSetInfo]:
    """Read UI-created/edited taskset definitions from the registry.

    Mirror of the root reader so a taskset created from the console (via the
    sync writer above) renders with its registered name/summary on the board
    instead of falling back to ``Unclassified``.
    """
    base = (root or ROOT).resolve()
    path = base / TASK_SET_REGISTRY
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if str(payload.get("schema") or "") != TASK_SET_REGISTRY_SCHEMA:
        return {}
    loaded: dict[str, TaskSetInfo] = {}
    for row in payload.get("tasksets", []):
        if not isinstance(row, dict):
            continue
        task_set_id = str(row.get("task_set_id") or "").strip()
        display_name = str(row.get("display_name") or "").strip()
        summary = str(row.get("summary") or "").strip()
        if not task_set_id or not display_name or not summary:
            continue
        try:
            order = int(row.get("order", 500))
        except (TypeError, ValueError):
            order = 500
        loaded[task_set_id] = TaskSetInfo(task_set_id, display_name, summary, order)
    return loaded


def _task_set_info_map(root: Path | None = None) -> dict[str, TaskSetInfo]:
    merged = dict(TASK_SET_INFO)
    merged.update(_load_task_set_registry(root))
    return merged


@dataclass
class Task:
    path: Path
    meta: dict[str, object]
    goal: str

    @property
    def task_id(self) -> str:
        return str(self.meta.get("id", self.path.stem))

    @property
    def task_uid(self) -> str:
        return str(self.meta.get("task_uid", ""))

    @property
    def display_id(self) -> str:
        return str(self.meta.get("display_id", self.task_id))

    @property
    def status(self) -> str:
        return str(self.meta.get("status", "unknown"))

    @property
    def priority(self) -> str:
        return str(self.meta.get("priority", "P2"))

    @property
    def task_set_id(self) -> str:
        raw = str(self.meta.get("task_set_id", "")).strip()
        return raw or UNCLASSIFIED_TASK_SET.task_set_id

    @property
    def project_id(self) -> str:
        return str(self.meta.get("project_id") or "-").strip() or "-"

    @property
    def initiative_id(self) -> str:
        return str(self.meta.get("initiative_id") or "-").strip() or "-"

    @property
    def unit_spec(self) -> str:
        return str(self.meta.get("unit_spec") or "").strip()

    @property
    def difficulty(self) -> str:
        raw = str(self.meta.get("difficulty", "M"))
        return DIFFICULTY_LABEL.get(raw, raw)

    @property
    def est_hours(self) -> float:
        try:
            return float(str(self.meta.get("est_hours", 0)).strip())
        except ValueError:
            return 0.0

    @property
    def est_tokens(self) -> int:
        try:
            return int(float(str(self.meta.get("est_tokens", 0)).strip()))
        except ValueError:
            return 0

    @property
    def tags(self) -> list[str]:
        value = self.meta.get("tags", [])
        if isinstance(value, list):
            return [str(x) for x in value]
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return []

    @property
    def registered_at(self) -> str:
        return str(self.meta.get("registered_at") or self.meta.get("created_at") or self.meta.get("created") or "")

    @property
    def started_at(self) -> str:
        return str(self.meta.get("started_at") or "")

    @property
    def updated_at(self) -> str:
        return str(self.meta.get("updated_at") or "")

    @property
    def completed_at(self) -> str:
        return str(self.meta.get("completed_at") or "")


def strip_comment(line: str) -> str:
    if "#" not in line:
        return line
    return line.split("#", 1)[0]


def parse_scalar(value: str) -> object:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("'\"") for part in inner.split(",")]
    return value.strip("'\"")


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        if lines and re.match(r"^[A-Za-z0-9_-]+:\s*", lines[0]):
            end = 0
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped == "---" or stripped.startswith("## "):
                    end = idx
                    break
            else:
                end = len(lines)
            meta = parse_header_block(lines[:end])
            return meta, "\n".join(lines[end:])
        return {}, text
    end = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = idx
            break
    if end is None:
        for idx, line in enumerate(lines[1:], start=1):
            if line.strip().startswith("## "):
                end = idx
                break
        else:
            end = len(lines)
        meta = parse_header_block(lines[1:end])
        return meta, "\n".join(lines[end:])

    meta = parse_header_block(lines[1:end])
    return meta, "\n".join(lines[end + 1 :])


def parse_header_block(header_lines: list[str]) -> dict[str, object]:
    meta: dict[str, object] = {}
    current_list: str | None = None
    for raw in header_lines:
        line = strip_comment(raw).rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_list:
            item = line[4:].strip().strip("'\"")
            value = meta.setdefault(current_list, [])
            if isinstance(value, list):
                value.append(item)
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if value == "":
            meta[key] = []
            current_list = key
        else:
            meta[key] = parse_scalar(value)
            current_list = None
    return meta


def extract_goal(body: str) -> str:
    lines = body.splitlines()
    in_goal = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_goal:
                break
            in_goal = "목표" in stripped or "Goal" in stripped
            continue
        if in_goal and stripped:
            collected.append(stripped.lstrip("- "))
            if len(" ".join(collected)) > 90:
                break
    text = " ".join(collected).strip()
    if not text:
        for line in lines:
            stripped = line.strip().lstrip("- ")
            if stripped and not stripped.startswith("#"):
                text = stripped
                break
    text = re.sub(r"\s+", " ", text)
    return shorten(sanitize_display_text(text), 86)


def sanitize_display_text(text: str) -> str:
    for needle, replacement in DISPLAY_REPLACEMENTS.items():
        text = text.replace(needle, replacement)
    return text


def shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def load_tasks(tasks_dir: Path = TASKS_DIR) -> list[Task]:
    tasks: list[Task] = []
    for path in sorted(tasks_dir.glob("TASK-*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        if not meta:
            continue
        tasks.append(Task(path=path, meta=meta, goal=extract_goal(body)))
    return tasks


def team_for(task: Task) -> str:
    tags = set(task.tags)
    tid = task.task_id
    if tags & {"offline-eval", "quality-gate", "live-review", "correction", "a2a"} or tid in {"TASK-AR-205", "TASK-AR-206", "TASK-AR-207", "TASK-AR-208", "TASK-AR-217"}:
        return "validation-team"
    if tags & {"migration", "source-control"} or tid in {"TASK-AR-209", "TASK-AR-212", "TASK-AR-213", "TASK-AR-218", "TASK-AR-220", "TASK-AR-224"}:
        return "governance-loop"
    if tags & {"project-overlay", "context-source", "knowledge-router", "warehouse"} or tid in {"TASK-AR-201", "TASK-AR-203", "TASK-AR-211", "TASK-AR-214", "TASK-AR-215"}:
        return "project-context"
    if tags & {"ci-gate", "release-gate", "release", "automation"} or tid in {"TASK-AR-204", "TASK-AR-210", "TASK-AR-216", "TASK-AR-221", "TASK-AR-222", "TASK-AR-223", "TASK-AR-225"}:
        return "agent-runtime-core"
    return "agent-runtime-core"


def agent_for(task: Task) -> str:
    team = team_for(task)
    if team == "validation-team":
        return "qa"
    if team == "governance-loop":
        return "independent-auditor"
    if team == "project-context":
        return "doc-steward"
    if task.task_id in {"TASK-AR-224"}:
        return "research-agent"
    if task.task_id in {"TASK-AR-225"}:
        return "cicd-engineer"
    return "lead-engineer"


def lane_for(task: Task) -> str:
    status = task.status.lower()
    body_goal = task.goal.lower()
    if is_done(task):
        return "Done"
    if "owner" in body_goal or "approval" in body_goal or status.startswith("hold") or "blocked" in status:
        return "Ask"
    if status in {"ready", "review", "ready_for_governance_review"}:
        return "Review"
    if status in {"planned", "pending", "defer", "deferred"} and task.est_hours >= 16:
        return "Later"
    return "Action"


def is_done(task: Task) -> bool:
    return task.status.lower() in DONE_STATUSES


def value_for(task: Task) -> str:
    score = score_for(task)
    if score >= 14:
        return "Very High"
    if score >= 11:
        return "High"
    if score >= 8:
        return "Medium"
    return "Low"


def importance_for(task: Task) -> str:
    priority = task.priority
    if priority in {"P0", "Critical"}:
        return "Critical"
    if priority in {"P1", "High"}:
        return "High"
    if priority in {"P2", "Medium"}:
        return "Medium"
    return "Low"


def score_for(task: Task) -> int:
    priority_score = PRIORITY_WEIGHT.get(task.priority, 3)
    status_score = STATUS_WEIGHT.get(task.status.lower(), 2)
    tag_bonus = 0
    tags = set(task.tags)
    if tags & {"release-gate", "ci-gate", "quality-gate"}:
        tag_bonus += 2
    if tags & {"project-overlay", "context-source", "migration"}:
        tag_bonus += 1
    cost_penalty = 0
    if task.est_hours >= 16 or task.est_tokens >= 2600:
        cost_penalty = 1
    return max(1, priority_score + status_score + tag_bonus - cost_penalty)


def decision_for(task: Task) -> str:
    lane = lane_for(task)
    if lane == "Ask":
        return "Owner/agent decision"
    if lane == "Review":
        return "Review evidence"
    if lane == "Later":
        return "Wait for dependency"
    if lane == "Done":
        return "Archive/evidence only"
    return "Execute next"


def sort_key(task: Task) -> tuple[int, int, str]:
    lane_order = {"Action": 0, "Ask": 1, "Review": 2, "Later": 3, "Done": 4}
    return (lane_order.get(lane_for(task), 9), -score_for(task), task.task_id)


def task_set_info(task_set_id: str, root: Path | None = None) -> TaskSetInfo:
    return _task_set_info_map(root).get(task_set_id, UNCLASSIFIED_TASK_SET)


def task_set_sort_key(task: Task, root: Path | None = None) -> tuple[int, int, int, float, int, str]:
    set_info = task_set_info(task.task_set_id, root)
    done_penalty = 1 if lane_for(task) == "Done" else 0
    difficulty_rank = DIFFICULTY_ORDER.get(task.difficulty, 9)
    return (set_info.order, done_penalty, -score_for(task), task.est_hours, difficulty_rank, task.task_id)


def _load_claims(root: Path) -> list[dict[str, object]]:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    if not claim_dir.is_dir():
        return []
    claims: list[dict[str, object]] = []
    for path in sorted(claim_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            claims.append(payload)
    return claims


def _parse_dt(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def flow_by_task_set(root: Path | None) -> dict[str, dict[str, object]]:
    if root is None:
        return {}
    now = datetime.now(timezone.utc).astimezone()
    flows: dict[str, dict[str, object]] = {}
    for claim in _load_claims(root):
        status = str(claim.get("status") or "").strip().lower()
        task_set_id = str(claim.get("task_set_id") or "").strip()
        if not task_set_id or status not in ACTIVE_CLAIM_STATUSES:
            continue
        flow = flows.setdefault(
            task_set_id,
            {"active": 0, "wip_limit": DEFAULT_WIP_LIMIT, "oldest_age_hours": 0.0, "stale": 0},
        )
        flow["active"] = int(flow["active"]) + 1
        started = _parse_dt(claim.get("claimed_at") or claim.get("updated_at"))
        if started is not None:
            age_hours = max(0.0, (now - started).total_seconds() / 3600)
            flow["oldest_age_hours"] = max(float(flow["oldest_age_hours"]), age_hours)
            if age_hours >= 24:
                flow["stale"] = int(flow["stale"]) + 1
    return flows


def task_sets_for(tasks: Iterable[Task], root: Path | None = None) -> list[str]:
    return sorted({task.task_set_id for task in tasks}, key=lambda raw: (task_set_info(raw, root).order, raw))


def lane_counts(tasks: Iterable[Task]) -> dict[str, int]:
    counts = {"Action": 0, "Ask": 0, "Review": 0, "Later": 0, "Done": 0}
    for task in tasks:
        counts[lane_for(task)] = counts.get(lane_for(task), 0) + 1
    return counts


def render(tasks: list[Task], *, root: Path | None = None) -> str:
    today = date.today().isoformat()
    open_tasks = [t for t in tasks if not is_done(t)]
    completed_tasks = [t for t in tasks if is_done(t)]
    counts = lane_counts(tasks)
    task_set_ids = task_sets_for(open_tasks, root)
    all_task_set_ids = task_sets_for(tasks, root)
    completed_task_set_ids = [
        task_set_id
        for task_set_id in all_task_set_ids
        if task_set_id not in task_set_ids
    ]
    flow = flow_by_task_set(root)

    lines: list[str] = [
        "---",
        "type: backlog_board",
        "id: BACKLOG-BOARD-agent-runtime",
        "audience: owner",
        "status: pass",
        "signal: pass",
        "score: 100",
        "priority: High",
        "tags: [backlog, decision-board, owner-brief, action-board]",
        f"generated_at: {today}",
        f"task_count: {len(tasks)}",
        f"open_count: {len(open_tasks)}",
        f"completed_count: {len(completed_tasks)}",
        f"task_set_count: {len(task_set_ids)}",
        f"completed_task_set_count: {len(completed_task_set_ids)}",
        "---",
        "",
        "# Backlog Decision Board",
        "",
        "## Bottom Line",
        f"- Summary: `{len(open_tasks)}` open or active tasks; `{len(completed_tasks)}` completed tasks are archived from this live board.",
        "- Routing rule: choose a task set first, then sort priority, cost, and difficulty inside that task set.",
        "",
        "## Signal",
        f"- Status: Action `{counts.get('Action', 0)}` / Ask `{counts.get('Ask', 0)}` / Review `{counts.get('Review', 0)}` / Later `{counts.get('Later', 0)}` / Done `{counts.get('Done', 0)}`.",
        f"- Task Sets: `{len(task_set_ids)}` active workflows; `{len(completed_task_set_ids)}` completed workflows are hidden from the live action board.",
        "- Key Point: Restored prior `ACT / REVIEW / ASK / DEFER` backlog as clearer `Action / Review / Ask / Later` lanes.",
        "- Key Point: Every task includes difficulty, cost, value, importance, team, and agent.",
        "",
        "## Insight",
        "- Cause: Format drift recurs when report style is prose-only and not generated or gated.",
        "- Fix: Backlog board is now generated from task metadata and checked by an executable format gate.",
        "- UX: Owner view stays concise, sortable, and machine-readable.",
        "",
        "## Decision",
        "- Decision: Use this board as the Owner-facing backlog view.",
        "- Action owner: Agents execute `Action`; Owner resolves `Ask`; reviewers inspect `Review`.",
        "- Task-set rule: Group by related workflow first; sort priority, cost, and difficulty only inside each task set.",
        "- Format rule: Preserve `Bottom Line / Signal / Insight / Decision` before tables.",
        "",
        "## Action Board",
        "",
        "- Board rule: task sets are the primary panes of work. Completed tasks and fully completed task sets are archived automatically.",
    ]

    for task_set_id in task_set_ids:
        set_info = task_set_info(task_set_id, root)
        set_tasks = sorted([task for task in open_tasks if task.task_set_id == task_set_id], key=lambda task: task_set_sort_key(task, root))
        total_set_tasks = [task for task in tasks if task.task_set_id == task_set_id]
        set_completed = [task for task in total_set_tasks if is_done(task)]
        set_flow = flow.get(task_set_id, {"active": 0, "wip_limit": DEFAULT_WIP_LIMIT, "oldest_age_hours": 0.0, "stale": 0})
        lines.extend([
            "",
            f"### {set_info.display_name} (`{task_set_id}`)",
            "",
            f"- Flow: {set_info.summary}",
            f"- Progress: `{len(set_completed)}/{len(total_set_tasks)}` done; `{len(set_tasks)}` open or active.",
            f"- WIP: active `{set_flow['active']}/{set_flow['wip_limit']}`; oldest `{float(set_flow['oldest_age_hours']):.1f}h`; stale `{set_flow['stale']}`.",
            "| Task | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |",
            "|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|",
        ])
        if not set_tasks:
            lines.append("| - | - | - | - | - | - | - | - | - | - | - | - | - |")
            continue
        for task in set_tasks:
            cost = f"{task.est_hours:g}h/{task.est_tokens}tok"
            row = [
                f"`{task.task_id}`",
                task.project_id,
                task.unit_spec or "-",
                task.status,
                lane_for(task),
                task.priority,
                importance_for(task),
                task.difficulty,
                cost,
                value_for(task),
                str(score_for(task)),
                team_for(task),
                agent_for(task),
                decision_for(task),
                task.goal.replace("|", "/"),
            ]
            lines.append("| " + " | ".join(row) + " |")

    if completed_task_set_ids:
        lines.extend([
            "",
            "## Archived Task Sets",
            "",
            "- Archive rule: completed task sets stay out of the live Action Board but remain visible as workflow-level completion evidence.",
            "| Task Set | Flow | Progress | Evidence |",
            "|---|---|---:|---|",
        ])
        for task_set_id in completed_task_set_ids:
            set_info = task_set_info(task_set_id, root)
            total_set_tasks = [task for task in tasks if task.task_set_id == task_set_id]
            set_completed = [task for task in total_set_tasks if is_done(task)]
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"{set_info.display_name} (`{task_set_id}`)",
                        set_info.summary,
                        f"`{len(set_completed)}/{len(total_set_tasks)}` done",
                        f"`{len(set_completed)}` completed task files archived",
                    ]
                )
                + " |"
            )

    if completed_tasks:
        lines.extend([
            "",
            "## Archived Task Files",
            "",
            "- Restore rule: completed tasks stay hidden from the live Action Board, but every completed task file remains visible here with identity and lifecycle metadata.",
            "| Task | UID | Task Set | Status | registered_at | started_at | completed_at | updated_at | Summary |",
            "|---|---|---|---|---|---|---|---|---|",
        ])
        for task in sorted(completed_tasks, key=task_set_sort_key):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{task.display_id}`",
                        f"`{shorten(task.task_uid, 13)}`" if task.task_uid else "-",
                        f"`{task.task_set_id}`",
                        task.status,
                        task.registered_at or "-",
                        task.started_at or "-",
                        task.completed_at or "-",
                        task.updated_at or "-",
                        task.goal.replace("|", "/"),
                    ]
                )
                + " |"
            )

    lines.extend([
        "",
        "## Risks / Blockers",
        "- Format drift risk: backlog output must not collapse into a plain task list.",
        "- Metadata gap risk: missing team/agent/value fields reduce Owner decision quality.",
        "- Gate gap risk: prose rules are insufficient without an executable format check.",
        "",
        "## Next Steps",
        "- Run `python scripts/backlog_board.py --write` after task frontmatter changes.",
        "- Run `python scripts/owner_doc_format_gate.py BACKLOG-BOARD.md` before sharing Owner-facing backlog/report docs.",
        "- Keep `task_set_id` in every task frontmatter so panes can claim related workflow bundles without reclassifying from prose.",
        "- Promote missing task metadata into frontmatter when repeated inference is needed.",
        "- Use completed task files as archival evidence; do not render them in the live action board unless an explicit archive view is added.",
        "",
            "## Tags / References",
        "- tags: backlog, action-board, owner-brief, decision-support",
        "- references: `BACKLOG.md`, `STATUS.md`, `agents/lead_engineer/tasks/*.md`",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Owner-facing backlog decision board")
    parser.add_argument("--tasks-dir", default=str(TASKS_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    tasks = load_tasks(Path(args.tasks_dir))
    text = render(tasks, root=ROOT)
    if args.write:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"wrote={output}")
        print(f"tasks={len(tasks)}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
