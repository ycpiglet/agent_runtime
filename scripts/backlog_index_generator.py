"""BACKLOG.md registration-index generator (TASK-AR-371, Phase 3).

Deconflict BACKLOG.md: instead of every planner hand-appending a top-of-file section
(a shared write hotspot), the taskset registration index is GENERATED from the
structured registration record (TASKSET-DEFINITIONS.json) into a marker-delimited block,
while the human narrative below the block is preserved untouched. Planners register a
taskset in the JSON (one structured entry) and regenerate — no shared manual edit.

`--write` regenerates the block; `--check` fails if stale. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFS = ROOT / "agents" / "project" / "work-items" / "TASKSET-DEFINITIONS.json"
BACKLOG = ROOT / "BACKLOG.md"
START = "<!-- BACKLOG-INDEX:START (generated from TASKSET-DEFINITIONS.json — do not edit by hand) -->"
END = "<!-- BACKLOG-INDEX:END -->"


def render_index(defs_path: Path = DEFS) -> str:
    data = json.loads(defs_path.read_text(encoding="utf-8"))
    rows = sorted(data.get("tasksets", []), key=lambda t: t.get("order", 0))
    lines = [START, "", "## Registered tasksets (generated)", "",
             "| Order | Taskset | Name |", "| --- | --- | --- |"]
    for t in rows:
        lines.append(f"| {t.get('order', '')} | `{t['task_set_id']}` | {t.get('display_name', '')} |")
    lines += ["", END]
    return "\n".join(lines)


def apply_block(text: str, block: str) -> str:
    if START in text and END in text:
        pre = text[: text.index(START)]
        post = text[text.index(END) + len(END):]
        return pre + block + post
    # first insertion: place the block right after the H1 title line
    lines = text.splitlines()
    out, inserted = [], False
    for line in lines:
        out.append(line)
        if not inserted and line.startswith("# "):
            out += ["", block]
            inserted = True
    if not inserted:
        out = [block, ""] + out
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the BACKLOG.md registration index.")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    block = render_index()
    current = BACKLOG.read_text(encoding="utf-8") if BACKLOG.exists() else "# Backlog\n"
    updated = apply_block(current, block)
    if a.write:
        BACKLOG.write_text(updated, encoding="utf-8")
        print("backlog-index: written")
        return 0
    stale = updated != current
    print(f"backlog-index: {'stale' if stale else 'current'}")
    return 1 if (a.check and stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
