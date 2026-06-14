---
type: research
id: RESEARCH-2026-06-14-product-maturity-ui-assessment
audience: owner
status: watch
signal: watch
score: 80
priority: High
tags: [product-maturity, ui-ux, evaluation, rubric, assessment, improvement-backlog]
---

# Product Maturity & UI Assessment — 2026-06-14

## Bottom Line

- Summary: 현재 agent_runtime의 **프로덕트 성숙도는 4/5(production-hardened)**, **UI/UX는 3.5/5(intermediate polish)**로 평가한다. 거버넌스·신뢰성·릴리스 파이프라인은 강하고, UI는 기능은 풍부하나 e2e/접근성/반응형/실시간에서 갭이 크다.
- Result: 평가 지표를 `agents/project/PRODUCT-MATURITY-UI-RUBRIC.yml`(루브릭, 1-5 척도+기준점수+릴리스 임계치)로 등록하고, 검증 케이스를 `docs/product-maturity-ui-verification-catalog.md`(영역×case-type 다수)로 등록했다. 도출된 개선점은 `TASKSET-AR-PRODUCT-MATURITY-UPLIFT`(TASK-AR-546~555)로 등록한다.
- Boundary: 본 레코드는 평가 + 개선 백로그 등록이다. 점수는 baseline이며, target 달성 주장은 아니다. 근거는 코드/테스트/문서 경로로 추적 가능하다.

## Signal

| 영역 | 차원 | baseline | target | 핵심 근거 / 갭 |
| --- | --- | --- | --- | --- |
| 성숙도 | 기능 폭/깊이 | 4 | 5 | 47-게이트 체인·콘솔·릴리스 6단계 / provider-live·analytics 부분 |
| 성숙도 | 테스트 커버리지 | 4 | 5 | ~97파일/~1,130 테스트, 3.10-3.12 매트릭스 / heartbeat 동시성 약함 |
| 성숙도 | 릴리스·운영 | 4 | 5 | publish_*/sync/update-notify / 원격 publish 자동화 없음 |
| 성숙도 | 아키텍처·거버넌스 | 4 | 5 | owner_governance 서브게이트·458 리뷰 / root↔template 이중화 드리프트 |
| 성숙도 | 신뢰성·관측성 | 4 | 5 | claim_reaper·goal_supervisor·stop_events / 외부 메트릭 export 없음, 단일호스트 |
| UI/UX | 기능 커버리지 | 4.5 | 5 | 32 뷰·템플릿·자동화·리액션 / DnD JS 스텁 |
| UI/UX | 상호작용·피드백 | 3.5 | 4.5 | 마이크로인터랙션·낙관적 UI·단축키 / 느린작업 진행피드백·undo 부족 |
| UI/UX | i18n | 3 | 4 | ko/en·~199 data-i18n / 에러문구 en 하드코딩·로케일 포맷 없음 |
| UI/UX | 접근성 | 3 | 4.5 | ~682 aria·모션 게이트 / skip link·focus trap·table 시맨틱 부재 |
| UI/UX | 테마·커스터마이즈 | 4 | 4.5 | 다크/라이트·토큰·위젯/워크스페이스 / 폰트스케일·고대비 없음 |
| UI/UX | UI 테스트 | 3 | 4.5 | ~326 UI 테스트 / **e2e 브라우저·a11y 스캔·반응형 테스트 없음** |

## Insight

- 성숙도의 강점은 "보이지 않는" 인프라(게이트·복구·감사로그)이고, 약점은 "보이는" 표면(외부 관측성·릴리스 자동화·분산 안전)이다 — 즉 운영 신뢰는 높지만 외부 통합/스케일은 다음 단계.
- UI는 server-rendered HTML+vanilla JS 단일 셸(콘솔 ~12k LOC). 기능은 4.5지만 렌더링 모델(폴링·거대 인라인 템플릿)이 실시간성·유지보수·e2e 테스트를 가로막는 구조적 천장.
- 검증 갭이 점수 갭과 일치한다: e2e/a11y/반응형/실시간/동시성 — 이 다섯이 UI 3.5→4.5와 성숙도 4→5의 공통 병목.

## Action

| # | 개선점(갭) | Task | 영역 |
| --- | --- | --- | --- |
| 1 | UI e2e 브라우저 테스트(Playwright): DnD·키보드·폼·폴링 | TASK-AR-546 | UI 테스트 |
| 2 | 모바일/태블릿 반응형 레이아웃 | TASK-AR-547 | UI |
| 3 | 폼 검증·에러 UX(인라인+토스트+undo) | TASK-AR-548 | UI |
| 4 | 접근성 향상(skip link·focus trap·table 시맨틱·label·대비) | TASK-AR-549 | UI |
| 5 | 실시간 갱신(SSE)로 폴링 대체 | TASK-AR-550 | UI |
| 6 | i18n 심화(에러문구·로케일 날짜/숫자·외부 리소스) | TASK-AR-551 | UI |
| 7 | claim_reaper 동시성·heartbeat 스트레스 테스트 | TASK-AR-552 | 신뢰성 |
| 8 | 외부 관측성 export(stop_counters/pane_events→메트릭) | TASK-AR-553 | 관측성 |
| 9 | 멀티호스트 claim 안전(파일락/원자성) | TASK-AR-554 | 신뢰성 |
| 10 | 엔드투엔드 릴리스 자동화(owner-gated tag/PR/merge/publish) | TASK-AR-555 | 릴리스 |

## Risk

- 점수는 단발 평가(baseline)다 — 정기 재평가가 없으면 회귀를 못 잡는다. 루브릭에 `block_on_regression: true`를 두었으나 자동 측정 파이프라인은 후속(TASK-AR-546이 e2e 토대).
- UI 렌더링 모델을 바꾸지 않으면 e2e/실시간/유지보수 개선이 국소적 미봉에 그칠 위험 — SSE/컴포넌트화(550)는 구조적 변경이라 리스크·비용 큼, 단계적 접근 필요.
- 개선 task는 **후보 백로그**다. ready lane 이동·우선순위 확정은 Owner 결정이며, 본 등록이 "착수/채택"을 의미하지 않는다.
- 평가는 코드 정적 분석 기반이다 — 실제 사용자 사용성(UX 설문/세션)은 미반영. 정성 신호 보강 필요.

## Decision

- Decision: 평가 지표를 `agents/project/PRODUCT-MATURITY-UI-RUBRIC.yml`로 등록하고, 검증 케이스 카탈로그를 `docs/product-maturity-ui-verification-catalog.md`로 등록한다.
- Decision: 개선점을 `TASKSET-AR-PRODUCT-MATURITY-UPLIFT`(TASK-AR-546~555)로 등록하되, 모두 `planned` 후보로 두고 채택/우선순위는 Owner가 결정한다.
- Decision: 점수는 baseline으로 기록하고, target 상향은 매핑된 검증 케이스 통과를 조건으로 한다(루브릭 release_readiness).
- Decision: 본 레코드와 taskset 등록 레코드를 `owner-docs.yml`에 등재해 owner_doc_format_gate로 거버넌스한다.

## Next

- 등록 부킹(`TASKSET-DEFINITIONS.json`·`BACKLOG-BOARD.md`·`owner-docs.yml`·인덱스/분류기 재생성)은 `reviews/MEETING-2026-06-14-product-maturity-uplift-taskset-registration.md`의 레시피대로 wave89 closeout과 함께 일괄 반영한다(미커밋 526~545와 인덱스 충돌 회피).
- 첫 착수 후보는 TASK-AR-546(e2e 토대) — 이후 a11y(549)/폼 UX(548)가 빠른 사용자 체감 개선.
- 다음 정기 재평가 시 본 루브릭 차원을 재채점하고 회귀 여부를 기록한다.
