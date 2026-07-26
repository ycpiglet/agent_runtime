---
title: Console Overhaul P1 — Core Structure Registration
date: 2026-07-26
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Console Overhaul P1 — Core Structure Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-CONSOLE-OVERHAUL-P1`, taskset
`TASKSET-AR-CONSOLE-OVERHAUL-P1`, `9` task records, and `0` unit specs
from one input file.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Input schema | pass | `agent-runtime-work-registration/v1` |
| Reservation ledger | pass | task display IDs fulfilled during registration |
| Generated records | pass | initiative, taskset plan, task files, unit specs deferred, and generated views refreshed |

## Decision

Use `scripts/work.py new --input <json>` as the deterministic planner-facing
registration path for this taskset shape.

## Action Board

| Task | Title | Status |
| --- | --- | --- |
| `TASK-AR-630` | attention 신호 단일 정본화 (보드=콕핏 로직 공유) | planned |
| `TASK-AR-631` | 홈 Decision Screenfit 완성 | planned |
| `TASK-AR-632` | renderAll() 해체 — 선택 렌더 + 갱신 경로 단일화 | planned |
| `TASK-AR-633` | /clarify 엔지니어링 인터뷰 게이트 (W1.5) + EARS 수용 기준 | planned |
| `TASK-AR-634` | 요구-검증-증거 3자 추적성 게이트 | planned |
| `TASK-AR-635` | W4c 이해도 퀴즈 게이트 승격 + held-out 검증 | planned |
| `TASK-AR-636` | Owner 승인 위험 티어링 (위임 확대) | planned |
| `TASK-AR-637` | FLOW-DIGEST 주간 자동 + actor 스탬프 + Ownership Concentration | planned |
| `TASK-AR-638` | 디자인 패스 1 — KR i18n 전수 + 컬러 상태 문법 + P0 이관 코스메틱 | planned |

## Risks / Blockers

- This deterministic path does not perform AI decomposition, assignment, or
  approval bypass.
- Additional work is still needed for closeout automation and proposal-backed
  AI split/criteria/assign behavior.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
- Continue into unit spec generation, `work close`, `work verify`, and AI proposal tools.
