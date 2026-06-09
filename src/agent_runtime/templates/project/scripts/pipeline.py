"""Sequential handoff pipeline for agent workers (TASK-111, Stage 6 track B).

Decentralized (B2): pipeline state rides in message frontmatter
(`pipeline`/`stage`/`loopbacks`). This module is pure transition logic plus a
self-contained message writer; agent_worker calls compute_next() after a worker
answers and writes the emitted next-stage message. Routing is driven by a
`VERDICT:` line in the agent's reply (V1). Commit stage does local commit only;
push/PR is gated (C2).
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Stage:
    name: str
    role: str
    kind: str  # "work" or "gate"


PIPELINES: dict[str, list[Stage]] = {
    "build": [
        Stage("implement", "backend", "work"),
        Stage("review", "qa", "gate"),
        Stage("commit", "ci-cd", "work"),
    ],
}

DEFAULT_LOOP_CAP = 2

_VERDICT_RE = re.compile(r"(?im)^\\s*VERDICT:\\s*([A-Za-z][\\w-]*)\\s*$")


def parse_verdict(reply_text: str) -> str | None:
    """Return the last `VERDICT: <token>` value (lowercased), or None."""
    matches = _VERDICT_RE.findall(reply_text or "")
    return matches[-1].lower() if matches else None


@dataclass
class Decision:
    action: str  # "advance" | "loopback" | "complete" | "halt"
    target: Stage | None
    loopbacks: int
    reason: str


def _index(pipeline_name: str, stage_name: str) -> int:
    stages = PIPELINES[pipeline_name]
    for i, s in enumerate(stages):
        if s.name == stage_name:
            return i
    raise KeyError(f"unknown stage '{stage_name}' in pipeline '{pipeline_name}'")


def decide(pipeline_name: str, stage_name: str, verdict: str | None,
           loopbacks: int, cap: int = DEFAULT_LOOP_CAP) -> Decision:
    stages = PIPELINES[pipeline_name]
    idx = _index(pipeline_name, stage_name)
    stage = stages[idx]

    if stage.kind == "gate":
        v = verdict or "needs-changes"  # conservative default at a gate
        if v == "pass":
            if idx + 1 < len(stages):
                return Decision("advance", stages[idx + 1], loopbacks, "gate passed")
            return Decision("complete", None, loopbacks, "gate passed at last stage")
        if loopbacks + 1 > cap:
            return Decision("halt", None, loopbacks,
                            f"loop cap {cap} exceeded at '{stage_name}'")
        return Decision("loopback", stages[0], loopbacks + 1,
                        f"gate '{stage_name}' returned '{v}'")

    # work stage: advance (or complete if last)
    if idx + 1 < len(stages):
        return Decision("advance", stages[idx + 1], loopbacks, "work stage done")
    return Decision("complete", None, loopbacks, "work stage done at last stage")


@dataclass
class NextMessage:
    to: str
    task_id: str
    intent: str
    body: str
    pipeline: str
    stage: str
    loopbacks: int
    kind: str = "request"  # "request" | "complete" | "halt"


def stage_instruction(stage: Stage, task_id: str, prior_summary: str,
                      changed_files: list[str]) -> str:
    files = ", ".join(changed_files) if changed_files else "(none reported)"
    head = (
        f"Pipeline stage '{stage.name}' for task {task_id}.\n\n"
        f"Prior stage summary:\n{prior_summary}\n\n"
        f"Changed files so far: {files}\n\n"
    )
    if stage.name == "implement":
        return head + ("Implement the requested change and run the relevant tests. "
                       "End your reply with a final line `VERDICT: done`.")
    if stage.name == "review":
        return head + ("Review the change for correctness and run the tests. If it is "
                       "correct and tests pass, end with `VERDICT: pass`. Otherwise end "
                       "with `VERDICT: needs-changes` and list precisely what to fix.")
    if stage.name == "commit":
        return head + ("Stage and commit the change on the CURRENT branch: run git add "
                       "with the EXPLICIT paths of the files changed in this pipeline "
                       "(never whole-tree flags like `-A` or `--all`), then git commit "
                       "(do NOT push). End with `VERDICT: done`.")
    return head + "End your reply with `VERDICT: done`."


def compute_next(meta: dict, reply_text: str, changed_files: list[str] | None = None,
                cap: int = DEFAULT_LOOP_CAP) -> NextMessage | None:
    pipeline_name = meta.get("pipeline")
    if not pipeline_name:
        return None
    stage_name = meta.get("stage", "")
    loopbacks = int(meta.get("loopbacks", 0) or 0)
    task_id = meta.get("task_id", "none")
    verdict = parse_verdict(reply_text)
    d = decide(pipeline_name, stage_name, verdict, loopbacks, cap)

    if d.action in ("complete", "halt"):
        body = (f"Pipeline '{pipeline_name}' {d.action}: {d.reason}\n\n"
                f"Last stage: {stage_name} (verdict={verdict}).")
        return NextMessage(to="ceo", task_id=task_id, intent=f"pipeline {d.action}",
                           body=body, pipeline=pipeline_name, stage=stage_name,
                           loopbacks=loopbacks, kind=d.action)

    target = d.target
    body = stage_instruction(target, task_id, reply_text.strip(), changed_files or [])
    return NextMessage(to=target.role, task_id=task_id,
                       intent=f"pipeline {pipeline_name}/{target.name}",
                       body=body, pipeline=pipeline_name, stage=target.name,
                       loopbacks=d.loopbacks, kind="request")


def _ts_iso() -> str:
    t = time.localtime()
    off = -time.altzone // 60 if t.tm_isdst else -time.timezone // 60
    sign = "+" if off >= 0 else "-"
    return time.strftime("%Y-%m-%dT%H:%M:%S", t) + f"{sign}{abs(off)//60:02d}:{abs(off)%60:02d}"


def write_stage_message(nxt: NextMessage, inbox_dir) -> Path:
    inbox_dir = Path(inbox_dir)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    mid = f"MSG-{time.strftime('%Y%m%d-%H%M%S', time.localtime())}-{uuid.uuid4().hex[:6]}"
    msg_type = "request" if nxt.kind == "request" else "reply"
    lines = [
        "---",
        f"id: {mid}",
        "from: pipeline",
        f"to: {nxt.to}",
        f"task_id: {nxt.task_id}",
        f"intent: {nxt.intent}",
        f"type: {msg_type}",
        "status: open",
        f"ts: {_ts_iso()}",
        "in_reply_to:",
        "evidence: []",
        "next: []",
        f"pipeline: {nxt.pipeline}",
        f"stage: {nxt.stage}",
        f"loopbacks: {nxt.loopbacks}",
        "---",
        "",
        nxt.body.rstrip() + "\n",
    ]
    path = inbox_dir / f"{mid}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def start_pipeline(pipeline_name: str, task_id: str, inbox_dir, instruction: str = "") -> Path:
    """Create the stage-1 message that kicks off a pipeline."""
    stage = PIPELINES[pipeline_name][0]
    body = stage_instruction(stage, task_id, instruction or "(kickoff)", [])
    nxt = NextMessage(to=stage.role, task_id=task_id,
                      intent=f"pipeline {pipeline_name}/{stage.name}", body=body,
                      pipeline=pipeline_name, stage=stage.name, loopbacks=0, kind="request")
    return write_stage_message(nxt, inbox_dir)


def main(argv: list[str] | None = None) -> int:
    import argparse
    repo_root = Path(__file__).resolve().parent.parent
    default_inbox = repo_root / "agents" / "messages" / "inbox"
    p = argparse.ArgumentParser(prog="pipeline", description="Sequential handoff pipeline (TASK-111).")
    sub = p.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("start", help="kick off a pipeline")
    ps.add_argument("--pipeline", default="build")
    ps.add_argument("--task", required=True)
    ps.add_argument("--instruction", default="")
    ps.add_argument("--inbox", default=str(default_inbox))
    args = p.parse_args(argv)
    if args.cmd == "start":
        path = start_pipeline(args.pipeline, args.task, args.inbox, args.instruction)
        print(f"started {args.pipeline} → {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
