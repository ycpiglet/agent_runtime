"""Dependency cycle gate (TASK-AR-330).

Tasks may declare a subtask/dependency model in their frontmatter:

  parent_id:  <id>          # subtask hierarchy (this task lives under <id>)
  blocks:     [<id>, ...]    # this task must finish before <id> can start
  blocked_by: [<id>, ...]    # this task waits on <id>

`blocks`/`blocked_by` define a directed *blocker -> blocked* graph. A cycle in
that graph is unsatisfiable (A waits on B waits on ... waits on A), so this gate
detects circular blocker chains and fails (warns) when any exist.

Design notes
------------
- No-op safe: when no task declares `blocks`/`blocked_by` the blocker graph is
  empty, no cycle is possible, and the gate exits 0 with `findings=0`. This is
  the current repo state, so wiring this gate into the owner governance chain
  does not change a clean stop-hook decision.
- The edge derivation here mirrors `ui_state._normalize_dependency_edges` so the
  cycle the gate reports is exactly the cycle the board/timeline/graph surface.

Usage:
  python scripts/dependency_cycle_gate.py --check
  python scripts/dependency_cycle_gate.py --check --root /path/to/repo --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:  # Windows 콘솔 cp949 에서도 stdout 안전
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover - reconfigure unavailable
    pass

TASKS_REL = "agents/lead_engineer/tasks"


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_frontmatter(text: str) -> dict[str, object]:
    """Parse the simple YAML frontmatter shape used by runtime markdown files."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}
    meta: dict[str, object] = {}
    current_list_key: str | None = None
    for raw in lines[1:end_index]:
        line = raw.rstrip()
        if not line.strip():
            current_list_key = None
            continue
        if line.startswith("  - ") and current_list_key:
            existing = meta.setdefault(current_list_key, [])
            if isinstance(existing, list):
                existing.append(_parse_scalar(line[4:]))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            meta[key] = []
            current_list_key = key
        else:
            meta[key] = _parse_scalar(value)
            current_list_key = None
    return meta


def _string_list(value: object) -> list[str]:
    if value in (None, "", []):
        return []
    items = [str(v) for v in value] if isinstance(value, (list, tuple)) else [str(value)]
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if text and text.lower() not in seen:
            seen.add(text.lower())
            out.append(text)
    return out


def load_dependency_edges(root: Path) -> list[tuple[str, str]]:
    """Canonical blocker -> blocked edges from every task's frontmatter."""
    tasks_dir = root / TASKS_REL
    edges: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(blocker: str, blocked: str) -> None:
        blocker, blocked = blocker.strip(), blocked.strip()
        if not blocker or not blocked or blocker == blocked:
            return
        key = (blocker, blocked)
        if key not in seen:
            seen.add(key)
            edges.append(key)

    if not tasks_dir.is_dir():
        return edges
    for path in sorted(tasks_dir.glob("TASK-*.md")):
        try:
            meta = _parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not meta:
            continue
        task_id = str(meta.get("id") or path.stem).strip()
        if not task_id:
            continue
        for blocked in _string_list(meta.get("blocks")):
            add(task_id, blocked)
        for blocker in _string_list(meta.get("blocked_by")):
            add(blocker, task_id)
    return edges


def detect_cycles(edges: list[tuple[str, str]]) -> list[list[str]]:
    """Return cycles as ordered node chains (closing node repeated). [] when none."""
    adjacency: dict[str, list[str]] = {}
    for frm, to in edges:
        adjacency.setdefault(frm, []).append(to)
    for node in list(adjacency):
        adjacency[node].sort()

    cycles: list[list[str]] = []
    signatures: set[tuple[str, ...]] = set()
    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def record(chain: list[str]) -> None:
        core = chain[:-1]
        if not core:
            return
        rotation = min(range(len(core)), key=lambda i: core[i])
        normalized = core[rotation:] + core[:rotation]
        signature = tuple(normalized)
        if signature in signatures:
            return
        signatures.add(signature)
        cycles.append(normalized + [normalized[0]])

    def visit(node: str, stack: list[str]) -> None:
        color[node] = GREY
        stack.append(node)
        for neighbour in adjacency.get(node, []):
            state = color.get(neighbour, WHITE)
            if state == WHITE:
                visit(neighbour, stack)
            elif state == GREY:
                start = stack.index(neighbour)
                record(stack[start:] + [neighbour])
        stack.pop()
        color[node] = BLACK

    for node in sorted(adjacency):
        if color.get(node, WHITE) == WHITE:
            visit(node, [])
    return cycles


def cmd_check(root: Path, fmt: str = "human") -> int:
    edges = load_dependency_edges(root)
    cycles = detect_cycles(edges)
    findings = ["cycle:" + " -> ".join(cycle) for cycle in cycles]
    status = "fail" if findings else "pass"
    if fmt == "json":
        print(
            json.dumps(
                {
                    "gate": "dependency-cycle-gate",
                    "status": status,
                    "root": str(root),
                    "dependency_edges": len(edges),
                    "findings": len(findings),
                    "cycles": cycles,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"dependency-cycle-gate: {status}")
        print(f"root={root}")
        print(f"dependency_edges={len(edges)}")
        print(f"findings={len(findings)}")
        for finding in findings:
            print(f"- block {finding}")
        if findings:
            print(
                "action=resolve the circular blocks/blocked_by chain "
                "(remove or redirect one dependency edge so the graph is acyclic)"
            )
    return 1 if findings else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect circular task blocks/blocked_by dependencies")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true", help="Scan task frontmatter for dependency cycles")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.check:
        return cmd_check(root, args.format)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
