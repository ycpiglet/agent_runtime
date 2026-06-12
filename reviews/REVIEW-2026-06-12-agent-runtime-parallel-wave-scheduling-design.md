---
type: review
id: REVIEW-2026-06-12-agent-runtime-parallel-wave-scheduling-design
audience: owner
status: pass
signal: pass
score: 91
priority: High
tags: [parallel, wave-scheduling, concurrency, dispatcher, merge-queue, design]
---

# Parallel Wave Scheduling Design Review

## Bottom Line

- Summary: Owner가 "멀티페인 병렬 작업이 실질적으로 순차(cascade)로 돌아
  속도가 안 난다"고 진단했고, 증거 조사로 확인한 뒤 wave 기반 병렬 실행
  계층을 설계하고 `TASKSET-AR-PARALLEL-WAVE-EXECUTION`(TASK-AR-500~503)으로
  등록했다.
- Result: 병렬화의 단위는 taskset이 아니라 **wave**(서로소 footprint +
  의존성 없는 unit들의 실행 묶음)로 정의한다. taskset은 의미/목표 축,
  wave는 실행/스케줄링 축으로 직교하며, 풀 사이클(게이트 체인·보드
  재생성·retro)은 task 단위가 아니라 wave 경계에서 돈다.
- Boundary: 설계와 등록만 수행. 구현은 codex의
  `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE`(AR-372 디스패처 CLI)와
  agent-identity 브랜치 merge 이후 시작한다(디스패처·work-items 파일 겹침).

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| 순차 실행 증거 | pass | pane_events seq 8-12 클레임 생성 23:16→23:40→00:08→00:37→00:55 (단일 페인 순차) |
| 스택 체인 증거 | pass | AR-372 워크트리 4개가 직전 PR 위에 순차 적층 (#32 13:20 → #33 13:42 → #34 14:02 → #35 14:23) |
| 병렬 프리미티브 기존재 | pass | claim/lease, worktree-per-task, pane_events, `parallel_worktree_gate`, `collaboration_concurrency_gate` |
| footprint 선언 스키마 기존재 | pass | unit spec `target_files` frontmatter (units/README.md) |
| ID 충돌 회피 검증 | pass | TASK-AR-375는 codex 미머지 브랜치가 선점 — 500 대역 예약으로 회피 |
| 디스패처 현재 한계 | pass | `taskset_dispatcher.py`는 "one task set" plan/start만 지원, multi-claim wave 발급 없음 |

## Insight

- 속도 정체의 3중 원인: ① cascade 직렬 구조(부모 대기 + 순차 호출)
  ② subagent 컨텍스트 콜드스타트(worker-ready unit 미보급, AR-373 planned)
  ③ Amdahl — 직렬 구간(계획·리뷰·머지·공유 SSoT)이 지배하면 페인을
  늘려도 체감 불가.
- 병렬은 디스패처가 만드는 게 아니라 planner가 만든다: 서로소
  `target_files` + 의존성 없는 unit들을 같은 wave로 내놓아야 동시 실행이
  가능하다. 도메인(design/function) 구분은 근사일 뿐 정확한 기준은 파일
  footprint 서로소다. 수직 슬라이스(패널별)는 병렬 적합, 수평
  레이어(전 파일 관통)는 직렬.
- 의존성을 무시한 분배는 rework를 낳는다. 의존성은 wave 경계로 흡수한다:
  DAG → topological wave, wave 내부는 독립 보장, wave 사이만 순서.
- taskset 의미 퇴색 우려(Owner 제기)에 대한 답: wave는 기록 계층이 아니라
  스케줄링 산출물이므로 taskset의 의미(목표 묶음)를 침범하지 않는다.
  하나의 wave가 여러 taskset의 unit을 실을 수도 있다.
- 병렬화는 벽시계 시간을 줄이고 토큰은 늘린다(N 페인 = N 컨텍스트).
  cascade/parallel을 옵션(depth/max-panes)으로 두고 필요할 때만 가속하는
  Owner 제안을 디스패처 설계에 채택한다.

## Decision

- Decision: wave = 실행 시점 스케줄링 묶음(서로소 footprint + 무의존
  unit 집합). taskset과 직교하며 별도 디렉터리/계층을 만들지 않고
  디스패치 메타데이터로만 존재한다.
- Decision: 풀 사이클은 wave 경계에서 실행. unit 완료는 좁은 verification,
  task 완료는 리뷰 기록 1건으로 경량화. 파이프라이닝(planner wave k+1 /
  workers wave k / auditor wave k-1 동시 진행)을 지향한다.
- Decision: 디스패처에 cascade(기본)/parallel(depth·max-panes 옵션) 실행
  모드를 둔다 — 가속이 필요한 작업에만 병렬 비용을 지불한다.
- Decision: TASK-AR-500~503은 의도적 500 대역 예약으로 등록 — 동시 진행
  중인 codex 등록(375+ 선점 확인)과의 display ID 충돌 회피. codex의
  `TASK-ID-RESERVATIONS.json`(agent-runtime-task-id-reservation/v1) merge
  후 동일 원장에 소급 기재한다.
- Decision: 구현 착수는 codex AR-372/identity 브랜치 merge 이후.
  merge 시 `TASKSET-DEFINITIONS.json` 신규 레지스트리가 들어오면
  `TASKSET-AR-PARALLEL-WAVE-EXECUTION` 항목을 그쪽으로 이관한다.

## Risks / Blockers

- Risk: codex merge가 backlog 레지스트리를 JSON 기반으로 바꾸면 본 등록의
  `backlog_board.py` TaskSetInfo 항목은 이관 작업이 필요하다.
- Risk: BACKLOG.md 최상단 등록 섹션은 codex 브랜치와 append-append 충돌이
  예상되나 해소 가능(orchestrator 머지 책임) — AR-371이 근본 해결.
- Blocker: 없음 (등록 범위).

## Next Steps

- codex AR-372 + agent-identity merge 후 TASK-AR-500부터 착수
  (footprint 게이트가 최소 비용·최대 효과).
- merge 시 500 대역을 TASK-ID-RESERVATIONS.json에 소급 기재.
- AR-373(레거시 task unit 마이그레이션)과 병행해 worker-ready unit 보급률을
  올려 콜드스타트 비용을 제거한다.
