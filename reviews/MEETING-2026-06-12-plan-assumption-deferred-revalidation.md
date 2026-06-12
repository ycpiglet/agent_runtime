---
type: meeting
id: MEETING-2026-06-12-plan-assumption-deferred-revalidation
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [parallel, plan-governance, lazy-evaluation, deferred-revalidation]
---

# Plan Assumption Deferred Revalidation Meeting

## Bottom Line

- Summary: Owner가 "codex의 대규모 스키마 변경과 방금 등록한 wave 계획이
  틀어질 수 있으니, 따로 진행 후 나중에 재점검하는 지연평가/다단계
  트리거를 설정하자"고 제안했고, 이를 plan assumption gate(TASK-AR-504)로
  즉시 실행 가능하게 구현했다.
- Result: 계획의 전제 8개(의존 파일 4 sha256 + codex 신설 예정 파일 4
  absent)를 T0 시점에 스냅샷했고, AR-500~503 착수(T2) 전 `--check`가
  드리프트를 발견하면 replan 리뷰 없이는 착수할 수 없다.
- Boundary: 게이트는 dispatch-time 차단이며 owner governance 커밋 체인에는
  편입하지 않는다(merge 후 드리프트는 정상 상태 + codex가 해당 체인 파일
  수정 중).

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| codex 구조 변경 확인 | pass | identity/372 브랜치가 scripts/backlog_board.py, owner_governance_gate.py, task_claim_dispatcher.py, WORK-SCHEMA.yml, work.py 접촉 |
| 게이트 구현 | pass | `scripts/plan_assumption_gate.py` + 테스트 4건 통과 |
| T0 스냅샷 | pass | `agents/project/work-items/PLAN-ASSUMPTIONS.json` anchors=8, `--check` exit 0 |
| 착수 차단 연결 | pass | TASK-AR-500~503 Preconditions 섹션 |
| 충돌 안전성 | pass | 신규 파일명 2개 — codex 양 브랜치 무접촉 확인 |

## Insight

- 병렬 세션의 본질적 한계는 "서로의 미머지 내용을 모른다"이며, 이를
  막으려 동기화를 늘리면 병렬의 이득이 사라진다. 올바른 해법은 계획을
  전제에 바인딩하고 평가를 사용 시점으로 미루는 것(lazy evaluation) —
  드리프트가 없으면 비용 0, 있으면 정확히 그 지점에서 replan.
- absent anchor(아직 없어야 할 파일)는 "상대 세션의 변경이 도착했음"을
  감지하는 가장 싼 센서다 — codex의 WORK-SCHEMA.yml이 main에 나타나는
  순간 게이트가 울린다.

## Decision

- Decision: 트리거 4단계 — T0 등록 스냅샷 / T1 merge 후 관찰 / T2 착수 전
  차단 / T3 replan 후 re-record. T2가 유일한 차단 지점이다.
- Decision: TASK-AR-504로 같은 taskset에 등록하고 같은 세션에서 구현 완료
  (codex 신설 파일이 도착하기 전에 T0 스냅샷이 존재해야 하므로 boundary
  예외가 정당하다; footprint는 codex와 서로소임을 확인).
- Decision: replan 리뷰는 드리프트 보고를 입력으로 받아 영향받은 task만
  수정하고 anchors를 갱신한다 — 전체 재계획이 아니라 차분 재계획.

## Risks / Blockers

- Risk: anchor 목록이 불완전하면 드리프트를 놓친다 — replan 시 anchor를
  재선정하는 것까지가 T3의 범위다.
- Blocker: 없음.

## Next Steps

- codex merge 도착 시 T1 관찰 체크 실행 → 드리프트 보고를 기반으로 replan
  리뷰 작성 → anchors 갱신 → AR-500 착수.
