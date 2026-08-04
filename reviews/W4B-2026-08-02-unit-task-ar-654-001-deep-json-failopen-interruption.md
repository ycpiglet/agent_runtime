---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-02-unit-task-ar-654-001-deep-json-failopen-interruption
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
review_kind: w4b
status: revise
signal: fail
verdict: REVISE
review_completion: interrupted_after_confirmed_finding
finding_counts: {P0: 0, P1: 1, P2: 0}
created_at: 2026-08-02T11:14:53+09:00
reviewer: task_ar_654_failclosed_final_w4b
recorded_by: codex-root-task-ar-654-orchestrator
candidate_commit: 1b0db7d8555e12e781d7ddfa0850037a875f05fd
w4a_ref: reviews/W4A-2026-08-01-unit-task-ar-654-001-failclosed-authority-repair.md
tags: [task-ar-654, w4b, interrupted, json, recursion, fail-closed, stop-hook]
---

# TASK-AR-654 deep-JSON fail-open W4b interruption record

## Verdict

`REVISE — at least P0: 0, P1: 1, P2: 0.`

The independent W4b reviewer confirmed a release-blocking P1 before its tool
session was interrupted by a policy error. This file is an orchestrator
transcription of that confirmed finding, not a claim that the requested W4b
matrix completed. The next repaired candidate still requires an entirely
fresh, complete W4b and skeptic review.

## P1: bounded bytes do not bound JSON structural recursion

A 2,401-byte accepted-watch JSON payload consisting of 1,200 nested arrays
around one scalar is far below the 256 KiB byte ceiling. `json.loads` raises
`RecursionError`, which the accepted-watch boundary does not convert into a
bounded invalid-watch finding.

Observed endpoint behavior on exact candidate `1b0db7d8`:

- direct parsing raises `RecursionError`;
- `work close` exits 1 with a traceback; and
- the actual Stop wrapper exits 0 with empty stdout and stderr, silently
  allowing the stop instead of returning a block decision.

Stable signature:
`defect:deep-accepted-watch-json-recursion-fail-open:5d494f605a860dac`.

## Required repair boundary

Add failure-first source/package, direct closure, work-close, and actual Stop
tests for deeply nested JSON below the byte ceiling. Convert parser recursion
to a deterministic bounded finding. The actual Stop wrapper must also return a
fail-closed block on unexpected closure-gate exceptions so a future parser
exception cannot become an empty approval.

