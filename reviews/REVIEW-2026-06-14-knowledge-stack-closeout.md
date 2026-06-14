---
type: review
id: REVIEW-2026-06-14-knowledge-stack-closeout
audience: owner
status: watch
signal: watch
score: 84
priority: High
tags: [closeout, knowledge-graph, digest, lint, rag, agent-primitive, review]
recorded_at: 2026-06-14T12:40:00+09:00
---

# REVIEW 2026-06-14 — Agent knowledge stack closeout (#1–#4)

## Bottom Line

- Summary: 프로덕트 전용 LLM wiki/graph를 **에이전트 우선(자동화 우선)** 프리미티브로 4개 서브프로젝트로 분해해 main에 머지했다 — #1 graph(#143), #2 digest+memory(#145), #3 lint(#146), #4 RAG ask(#147). 모두 결정적 우선 + LLM 옵인.
- Result: `scripts/knowledge_{graph,digest,lint,ask}.py` + 미러 + fixture lock 일관, 테스트 41건(graph 12 / digest 7 / lint 14 / ask 8) green, 거버넌스/host-lock/clean-bundle preflight 전부 EXIT=0. 추가로 막혀 있던 PR 4건(#135 reaper 동시성, #142 closure gate, #145/#146/#147)을 fixture-lock 재생성으로 풀어 auto-merge.
- Boundary: #5(UI graph/wiki 뷰)는 미착수 — 명시적 최저 우선순위 + UI 렌더링 구조적 천장이라 별도 결정 필요(아래 Decision). 본 레코드는 평가가 아니라 머지 완료된 작업의 종합 + 시스템 이슈 기록.

## Signal

| 서브프로젝트 | PR | 핵심 | 검증 |
| --- | --- | --- | --- |
| #1 graph | #143 | 타입드 엔티티 그래프(ingest work-items/reviews/claims/git), index/query/context-pack | 12 tests; 실레포 929 nodes |
| #2 digest+memory | #145 | 엔티티+그래프 컨텍스트를 에이전트 페이지로 응축, 기억/freshness(fingerprint) | 7 tests |
| #3 lint | #146 | stale/orphan memory·duplicate-id·dangling(구조 block)·orphan work-item, severity 게이트 | 14 tests; 실레포 0 findings |
| #4 ask(RAG) | #147 | 다중-term 결정적 검색→cited evidence pack 기본, LLM 합성 옵인+degrade | 8 tests |

## Insight

- 사용자 재프레이밍("메인 유저는 에이전트")이 설계를 끌었다: 모든 산출물의 **기본 경로가 결정적**이고 LLM은 옵인 렌더러다 — CI/자동화에서 모델 비용 0으로 동작. #4의 cited evidence pack이 그 철학의 정점(답=인용 증거 묶음).
- #3의 orphan-entity를 전 kind에 적용하니 실레포 474 watch(전부 관측성 노드) → 노이즈. work-item kind로 한정해 0 findings 고신호 게이트로 교정. "게이트는 신호가 0에 가까울 때만 읽힌다"를 재확인.
- #4에서 실레포 타이틀의 em-dash가 cp949 콘솔을 깨뜨림 → CLI는 unicode 출력에 robust해야 한다(__main__ stdout utf-8 재설정).

## Action

| # | 항목 | 상태 |
| --- | --- | --- |
| 1 | #1–#4 main 머지 + 미러 + lock 일관 | 완료 |
| 2 | 막힌 PR 4건 fixture-lock 재생성 후 auto-merge | 완료 |
| 3 | COMPOUND-2026-06-14-003 (fixture-lock derived-artifact thrash) | 본 closeout과 함께 기록 |
| 4 | #5 UI 뷰 scope 결정 | Owner 결정 대기(RETRO 참조) |
| 5 | #1 ingest 갭(review/meeting reference 엣지 미연결 → 260 reviews orphan) | RETRO forward action |

## Risk

- fixture lock을 git-tracked 파생물로 커밋하기 때문에 lock을 건드리는 PR끼리 쌍별 충돌 → #135가 3회 DIRTY 재머지. systemic(COMPOUND-003). 미완화 시 동시 다발 템플릿 PR에서 재발.
- #4 LLM 경로는 실제 provider 호출 시에만 동작 — CI 미커버. degrade/주입 합성기로 배선만 검증했으므로 실 provider 회귀는 별도 라이브 평가 필요(provider_live_eval_runner 계열).
- #3 lint는 아직 거버넌스 체인에 비강제(available). 강제 레인 편입은 Owner 결정.

## Decision

- Decision: 에이전트 프리미티브 4종(graph/digest/lint/ask)을 단일 기준으로 채택한다. 결정적 기본 + LLM 옵인 계약을 유지한다.
- Decision: #5(UI graph/wiki 뷰)는 최저 우선순위 + 구조적 천장이므로 본 wave에서 분리하고 scope를 Owner가 정한다(최소 read-only 뷰 / 전체 시각화 / 후속 task 등록 중 택1).
- Decision: fixture-lock 충돌은 단발 회피가 아니라 자동화로 해소한다(merge 시 lock 재생성 또는 derived lock 비커밋) — RETRO forward action.

## Next

- COMPOUND-003 + 본 REVIEW + RETRO를 owner-docs에 등재(governance).
- #5 scope 확정 후 진행 또는 task 등록.
- #1 ingest reference-edge 보강으로 digest backlink/ask grounding 강화.
