"""Generate an Owner-facing backlog decision board from TASK frontmatter.

The board restores the old ACT/ASK/REVIEW/DEFER idea with clearer labels:
Action, Review, Ask, Later, Done. It is intentionally dependency-free so it can
run inside host projects before optional packages are installed.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "agents" / "lead_engineer" / "tasks"
DEFAULT_OUTPUT = ROOT / "BACKLOG-BOARD.md"

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
DIFFICULTY_LABEL = {"S": "Low", "M": "Medium", "L": "High", "XL": "Critical", "하": "Low", "중": "Medium", "상": "High"}


@dataclass
class Task:
    path: Path
    meta: dict[str, object]
    goal: str

    @property
    def task_id(self) -> str:
        return str(self.meta.get("id", self.path.stem))

    @property
    def status(self) -> str:
        return str(self.meta.get("status", "unknown"))

    @property
    def priority(self) -> str:
        return str(self.meta.get("priority", "P2"))

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
    return shorten(text, 86)


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
    if status in {"completed", "done", "완료"}:
        return "Done"
    if "owner" in body_goal or "approval" in body_goal or status.startswith("hold") or "blocked" in status:
        return "Ask"
    if status in {"ready", "review", "ready_for_governance_review"}:
        return "Review"
    if status in {"planned", "pending", "defer", "deferred"} and task.est_hours >= 16:
        return "Later"
    return "Action"


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


def lane_counts(tasks: Iterable[Task]) -> dict[str, int]:
    counts = {"Action": 0, "Ask": 0, "Review": 0, "Later": 0, "Done": 0}
    for task in tasks:
        counts[lane_for(task)] = counts.get(lane_for(task), 0) + 1
    return counts


def render(tasks: list[Task]) -> str:
    today = date.today().isoformat()
    open_tasks = [t for t in tasks if lane_for(t) != "Done"]
    counts = lane_counts(tasks)
    sorted_tasks = sorted(tasks, key=sort_key)
    next_action = next((t for t in sorted_tasks if lane_for(t) == "Action"), None)

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
        "---",
        "",
        "# Backlog Decision Board",
        "",
        "## Bottom Line",
        f"- Summary: `{len(tasks)}` total tasks; `{len(open_tasks)}` open or active.",
        f"- Recommended next: `{next_action.task_id if next_action else 'none'}` - {next_action.goal if next_action else 'no active task'}",
        "",
        "## Signal",
        f"- Status: Action `{counts.get('Action', 0)}` / Ask `{counts.get('Ask', 0)}` / Review `{counts.get('Review', 0)}` / Later `{counts.get('Later', 0)}` / Done `{counts.get('Done', 0)}`.",
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
        "- Format rule: Preserve `Bottom Line / Signal / Insight / Decision` before tables.",
        "",
        "## Action Board",
    ]

    for lane in ("Action", "Ask", "Review", "Later", "Done"):
        lane_tasks = [t for t in sorted_tasks if lane_for(t) == lane]
        lines.extend([
            "",
            f"### {lane}",
            "",
            "| Task | Status | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |",
            "|---|---|---:|---|---|---|---|---:|---|---|---|---|",
        ])
        if not lane_tasks:
            lines.append("| - | - | - | - | - | - | - | - | - | - | - | - |")
            continue
        for task in lane_tasks:
            cost = f"{task.est_hours:g}h/{task.est_tokens}tok"
            row = [
                f"`{task.task_id}`",
                task.status,
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
        "- Promote missing task metadata into frontmatter when repeated inference is needed.",
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
    text = render(tasks)
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
