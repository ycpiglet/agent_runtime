---
type: meeting
id: MEETING-2026-06-12-parallel-work-lifecycle-rules
audience: owner
status: pass
signal: pass
score: 91
priority: High
tags: [parallel, lifecycle, rules, worktree-hygiene, claim-first, protocol]
---

# Parallel Work Lifecycle Rules Meeting

## Bottom Line

- Summary: Owner가 "이번 건만이 아니라 모든 작업이 충돌 없이 정확한 규칙과
  순서로 돌아가길 원한다 — 더러운 워크트리, 충돌, ahead(N), 같은 문제에
  여럿이 달려드는 현상이 반복됐다"고 요구했고, 증상별 방지 장치를 전수
  점검해 갭 매트릭스를 만들고 표준 수명주기(W0~W6)를 결정했다.
- Result: 6개 증상 중 4개는 등록된 계획(AR-500~503)으로 커버되지만 2개는
  구멍이었다 — 좀비 워크트리 수명주기(미등록), 지연평가 규율의 전 작업
  기본화(미등록). TASK-AR-505, TASK-AR-506으로 등록해 메웠다.
- Boundary: 규칙 결정과 등록만 수행. 계약 문서(AGENTS.md,
  PROJECT-MANAGEMENT-CONTRACT.md) 명문화는 codex가 두 파일을 미머지
  브랜치에서 수정 중이므로 merge 후 AR-506에서 수행한다(지연평가 패턴
  일관 적용).

## Signal

| 증상 (Owner 보고) | 방지 장치 | 상태 |
| --- | --- | --- |
| 같은 문제에 여럿이 달려듦 | W0 세션 시작 클레임 확인 + W2 claim-first | AR-503 planned + 규칙 본 기록으로 명문화 |
| 누가 만지는지 모름 | claim/pane_events/ui-console | 장치 존재, claim 누락 시 무용(AR-372 실측) → AR-503이 강제 |
| 파일 충돌 | claim-time footprint 교차 차단 | AR-500 planned |
| ahead(N)/머지 적체 | orchestrator 직렬 merge 큐 | AR-502 planned |
| 더러운/좀비 워크트리 | 수명주기 게이트 + retention 정책 | **미등록이었음 → TASK-AR-505 신규** |
| 계획 드리프트 | plan assumption gate 전 작업 기본화 | 이번 taskset만 적용 중 → **TASK-AR-506 신규** |

- 실측(2026-06-12 21:00): 워크트리 11개 중 3개가 좀비(ahead=0,
  TASK-AR-316 behind=14 / TASK-AR-320 behind=3 / TASK-AR-369 behind=6) —
  merge 완료 후 정리 단계가 수명주기에 없어서 누적.

## Decision — 표준 작업 수명주기 (W0~W6)

모든 에이전트(codex/claude, 모든 pane)는 아래 순서를 따른다. 역행 금지.

- W0 세션 시작: `agents/runtime/task_claims/*.json` 활성 클레임 +
  `git worktree list` + NEXT-SESSION-POINTER 확인. 이미 클레임된 문제에
  진입 금지 — 같은 문제 중복 공격의 차단 지점.
- W1 등록: 기존 task/claim 검색(중복 등록 방지) → ID 예약(원장, AR-370) →
  task/unit 등록 → 계획 전제 스냅샷 `plan_assumption_gate record` (T0).
- W2 착수: `plan_assumption_gate --check` (T2) → main 체크아웃에 claim
  생성(claim-first, AR-503) → footprint 교차 검사(AR-500) → worktree 생성.
  claim 없이 worktree부터 만드는 것을 금지.
- W3 작업 중: heartbeat/pane_events 갱신. 공유 SSoT(BACKLOG, STATUS, 보드,
  INDEX, 레지스트리) 쓰기 금지 — orchestrator 전용. 작업 중 발견한 인접
  문제는 직접 수정 금지, intake 등록만(중복 공격 방지의 두 번째 차단 지점).
- W4 완료: verification 실행 → handoff/log 작성 → claim release.
- W5 통합: merge 큐(AR-502)가 직렬 rebase-test-merge → 보드/INDEX 재생성 →
  **워크트리 제거 + merge된 브랜치 정리(AR-505)**. ahead(N)와 좀비
  워크트리가 소멸하는 단계.
- W6 사이클: wave 경계에서 풀 사이클 + retro.

- Decision: 증상→차단 지점 매핑 — 중복 공격=W0/W3, 상호 불가시=W2,
  충돌=W2, 적체=W5, 좀비 워크트리=W5, 드리프트=W1/W2.
- Decision: 기존 좀비 워크트리 3개는 즉시 수동 삭제하지 않는다 — git
  이력에 "Preserve TASK-AR-369 worktree branch" 등 의도적 보존 흔적이
  있어, retention 정책(AR-505)이 결정된 뒤 일괄 처리한다.
- Decision: 계약 문서 명문화는 codex merge 후(AR-506) — AGENTS.md와
  PROJECT-MANAGEMENT-CONTRACT.md가 codex 미머지 브랜치에서 수정 중.

## Insight

- "구조가 충분한가"에 대한 정직한 답: 프리미티브(claim/worktree/이벤트/
  게이트)는 충분하지만, 수명주기의 양 끝(W0 진입 확인, W5 정리)이 규칙
  없이 비어 있어 증상이 거기서 발생했다. 가운데(W2~W4)만 강제하고 끝을
  안 닫으면 적체는 필연이다.
- 규칙은 문서가 아니라 게이트가 지킨다 — W0~W6 중 게이트 없는 단계(W0,
  W5)가 정확히 Owner가 고통을 보고한 단계다.

## Risks / Blockers

- Risk: AR-505 retention 정책이 과도하면 디버깅용 브랜치를 잃는다 —
  보존 태그 예외를 설계에 포함.
- Blocker: 없음 (등록 범위).

## Next Steps

- codex merge 도착 → T1 관찰 체크 → replan 리뷰 → AR-500부터 착수.
- AR-505 구현 시 기존 좀비 3개를 retention 정책으로 일괄 처리.
- AR-506에서 W0~W6을 계약 문서에 명문화 + 등록/디스패치 플로우에 T0/T2
  자동 편입.
