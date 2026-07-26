---
title: Console Overhaul P0 — Trust & Hygiene Registration
date: 2026-07-26
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Console Overhaul P0 — Trust & Hygiene Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-CONSOLE-OVERHAUL-P0`, taskset
`TASKSET-AR-CONSOLE-OVERHAUL-P0`, `7` task records, and `7` unit specs
from one input file.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Input schema | pass | `agent-runtime-work-registration/v1` |
| Reservation ledger | pass | task display IDs fulfilled during registration |
| Generated records | pass | initiative, taskset plan, task files, unit specs included, and generated views refreshed |

## Decision

Use `scripts/work.py new --input <json>` as the deterministic planner-facing
registration path for this taskset shape.

## Action Board

| Task | Title | Status |
| --- | --- | --- |
| `TASK-AR-623` | 신뢰 복구 — 신선도 배지 + 캐시 사각지대 해소 | planned |
| `TASK-AR-624` | 홈 위계 1차 — 요약 소음 제거 | planned |
| `TASK-AR-625` | 프론트 위생 — 죽은 코드·아이콘·i18n·다크베이스·칸반 | planned |
| `TASK-AR-626` | 데이터 위생 — 타임스탬프 게이트 + actuals/rework 자동 파생 | planned |
| `TASK-AR-627` | 전달 씨앗 — 세션 delta + 보드 throughput | planned |
| `TASK-AR-628` | Owner-facing 계약 봉합 — REPORTING-FORMAT + 참조 드리프트 | planned |
| `TASK-AR-629` | 축3 씨앗 — requirements-lint + NEEDS CLARIFICATION 마커 + checkpoints 필드 | planned |

## Risks / Blockers

- This deterministic path does not perform AI decomposition, assignment, or
  approval bypass.
- Additional work is still needed for closeout automation and proposal-backed
  AI split/criteria/assign behavior.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
- Continue into `work close`, `work verify`, and AI proposal tools after unit generation is covered.
