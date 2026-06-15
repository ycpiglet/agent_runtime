"""Lead decomposition tool (org-delegation Unit 558, TASK-AR-558).

A Lead decomposes a Task into worker-ready Units. Renders UNIT-<task>-NNN records
that satisfy task_unit_readiness_gate (required frontmatter + sections), writes
them under agents/lead_engineer/tasks/units/<task_id>/, stamps decomposition
provenance (which Lead role, when, seam/footprint), and is idempotent.

Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (step 2).
Complements scripts/work.py with a Lead-facing, provenance + seam-aware entry point
for the agent org (the seam metadata feeds the Unit-559 dispatch gate).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNITS_DIR = ROOT / "agents" / "lead_engineer" / "tasks" / "units"
DEFAULT_PROJECT = "PROJECT-AGENT-RUNTIME"

# Keys that render as YAML scalars vs lists in the unit frontmatter.
_SCALAR = ("context", "scope", "handoff", "stop_condition", "model_tier")
_LIST = ("inputs", "target_files", "acceptance", "verification")
_SECTIONS = (
    ("Context", "context", False),
    ("Inputs", "inputs", True),
    ("Target Files", "target_files", True),
    ("Scope", "scope", False),
    ("Steps", "steps", True),
    ("Acceptance Criteria", "acceptance", True),
    ("Verification", "verification", True),
    ("Handoff", "handoff", False),
    ("Stop Boundary", "stop_condition", False),
)


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # safe-quote, keeps unicode


def render_unit(*, task_id: str, task_set_id: str, n: int, brief: dict,
                project_id: str = DEFAULT_PROJECT, decomposed_by: str = "lead-engineer") -> tuple[str, str]:
    """Return (unit_id, markdown) for a worker-ready unit from a brief dict."""
    unit_id = f"UNIT-{task_id}-{n:03d}"
    fm = [
        "---",
        f"unit_id: {unit_id}",
        f"task_id: {task_id}",
        f"task_set_id: {task_set_id}",
        f"project_id: {project_id}",
        "kind: unit",
        f"parent_id: {task_id}",
        "status: worker_ready",
        "verification_status: pending",
        "horizon: unit",
        f"model_tier: {brief.get('model_tier', 'worker_standard')}",
        f"decomposed_by: {decomposed_by}",
        f"context: {_yaml_scalar(brief['context'])}",
        f"scope: {_yaml_scalar(brief['scope'])}",
        f"handoff: {_yaml_scalar(brief['handoff'])}",
        f"stop_condition: {_yaml_scalar(brief['stop_condition'])}",
    ]
    for key in _LIST:
        fm.append(f"{key}:")
        for item in brief.get(key, []):
            fm.append(f"  - {_yaml_scalar(item)}")
    fm.append("---")

    body = ["", f"# {unit_id} - {brief.get('title', task_id + ' unit ' + str(n))}", ""]
    for heading, key, is_list in _SECTIONS:
        body.append(f"## {heading}")
        body.append("")
        if is_list:
            for item in brief.get(key, []):
                body.append(f"- {item}")
        else:
            body.append(str(brief.get(key, "")))
        body.append("")
    return unit_id, "\n".join(fm) + "\n".join(body) + "\n"


def decompose(*, task_id: str, task_set_id: str, briefs: list[dict],
              project_id: str = DEFAULT_PROJECT, decomposed_by: str = "lead-engineer",
              units_root: Path = UNITS_DIR) -> dict:
    """Write worker-ready units for a task. Idempotent: existing unit files are kept."""
    out_dir = units_root / task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    created, existing = [], []
    for i, brief in enumerate(briefs, start=1):
        unit_id, md = render_unit(
            task_id=task_id, task_set_id=task_set_id, n=i, brief=brief,
            project_id=project_id, decomposed_by=decomposed_by,
        )
        path = out_dir / f"{unit_id}.md"
        if path.exists():
            existing.append(str(path))
            continue
        path.write_text(md, encoding="utf-8")
        created.append(str(path))
    # decomposition provenance (who decomposed, seam footprint per unit)
    prov = out_dir / "DECOMPOSITION.json"
    record = {
        "task_id": task_id,
        "task_set_id": task_set_id,
        "decomposed_by": decomposed_by,
        "units": [f"UNIT-{task_id}-{i:03d}" for i in range(1, len(briefs) + 1)],
        "footprints": {f"UNIT-{task_id}-{i:03d}": b.get("target_files", [])
                       for i, b in enumerate(briefs, start=1)},
    }
    prov.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"created": created, "existing": existing, "provenance": str(prov)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lead decomposes a task into worker-ready units.")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--task-set-id", required=True)
    ap.add_argument("--input", required=True, help="JSON file: a list of unit briefs")
    ap.add_argument("--project-id", default=DEFAULT_PROJECT)
    ap.add_argument("--by", default="lead-engineer", help="decomposing Lead role id")
    a = ap.parse_args(argv)
    briefs = json.loads(Path(a.input).read_text(encoding="utf-8"))
    result = decompose(
        task_id=a.task_id, task_set_id=a.task_set_id, briefs=briefs,
        project_id=a.project_id, decomposed_by=a.by,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
