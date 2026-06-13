---
type: meeting
id: MEETING-2026-06-14-host-feedback-intake-registration
audience: owner
status: watch
signal: watch
score: 78
priority: High
tags: [planning-record, host-feedback, dogfooding, council, seminar, intake, registration]
---

# Host Feedback Intake — Deliberation Topic + Taskset Registration

## Bottom Line

- Summary: host(autofolio)가 올린 dogfooding 피드백 이슈(#121 관계, #125 footprint 안전성, #128 self-eval/RSI, #131 intake 프로세스)와 미해결 BUG(#19/#20/#21)를 "무시 못할 민원"으로 취급하기 위해, 이를 심의할 **새 토의 주제**와 이를 소비하는 **`TASKSET-AR-HOST-FEEDBACK-INTAKE`**(Host Liaison)를 등록한다.
- Result: 토의 주제(아래 Deliberation Agenda) + taskset 7건(TASK-AR-526~532)을 레지스트리·BACKLOG·보드에 등록. #131이 요청한 intake→심의→결정→회신 루프가 파이프라인의 캐노니컬 능력이고, 나머지 피드백 항목(#121/#125/#128 + 버그)은 첫 심의에서 채택/보류/기각이 결정될 후보로 사전 등록.
- Boundary: 이 레코드는 등록 + 토의 의제 설정이다. 후보 task가 구현됐다거나 채택됐다고 주장하지 않는다. #131 자체가 이 파이프라인의 첫 시험 입력이다.

## Signal

| Issue | 분류(category) | 라우팅 | Task |
| --- | --- | --- | --- |
| #131 host feedback intake 파이프라인 | 프로세스 | 캐노니컬 파이프라인 구축 | TASK-AR-526/527/528 |
| #121 autofolio↔agent_runtime 관계 + host-fit 갭 | 설계 | 후보(첫 심의에서 결정) | TASK-AR-531 |
| #125 병렬 wave footprint 사후검증 부재 | 결함 | 후보(첫 심의에서 결정) | TASK-AR-529 |
| #128 self-eval 하네스 + RSI fitness gate | 설계 | 후보(첫 심의에서 결정) | TASK-AR-530 |
| #21 BUG-002 sync --diff cp949 UnicodeEncodeError | 결함(High) | 후보(triage) | TASK-AR-532 |
| #20 BUG-001 build_sync_plan stale config AttributeError | 결함(Medium) | 후보(triage) | TASK-AR-532 |
| #19 BUG-004 template role docs 미배포 링크 | 결함(Low) | 후보(triage, #531과 조정) | TASK-AR-532 |

## Deliberation Agenda (토의 주제)

블라인드 Delphi(독립 노트 → 합의)로 다음을 심의한다. 가드레일: 관점 다양성(유사 모델 가짜 합의 방지), 제품 방향 최종 결정은 Owner(다수결로 product 방향 결정 불가 — host 고유 IP), 안전/주문 경계는 항상 사람(R3), 투표는 우선순위 신호이지 방향 결정자가 아님.

1. host 피드백을 1급 입력으로 소비하는 intake→심의→회신 루프를 가동할 것인가, 어떤 형태로(라벨/큐/주기)?
2. #125 사후 footprint 검증 게이트와 undeclared watch→block 정책을 채택/보류/기각?
3. #128 고정+변동 지표 self-eval + RSI fitness gate를 채택할 것인가, 어느 지표부터?
4. #121 host-fit 4개 갭(wheel dotfile 패키징·read-location 규약·work_cli·status 현지화)의 우선순위와 채택 범위?
5. #19/#20/#21 버그 triage 순서(심각도=우선순위 신호)?

## Action

| # | Action | Owner boundary |
| --- | --- | --- |
| 1 | TASK-AR-526 intake/triage 분류기로 7개 이슈를 큐에 적재 | local |
| 2 | TASK-AR-527 council/seminar(blind Delphi) 1회차 심의 가동 | owner_review (방향 결정 시) |
| 3 | TASK-AR-528 결정+근거를 각 이슈에 회신(gh issue comment) | owner_review |
| 4 | 후보 529/530/531/532 채택 여부는 1회차 심의 산출물로 확정 | owner_review |

## Risk

- 심의 끝단(소비)이 안 돌면 intake는 무용 — host 측 council/seminar도 dormant로 확인됨(양쪽 "만들었지만 안 도는" 문제). 가동 자체가 리스크 완화의 핵심.
- 유사 모델 다수로 가짜 합의가 날 위험 → 관점 다양성 가드레일 필수.
- 후보 사전 등록이 "이미 채택됨"으로 오독될 위험 → 모든 후보 task에 candidate 경계 명시.
- #121 wheel 패키징·#19 doc 링크는 기존 AR-511/AR-525 작업과 중복 가능 → 구현 전 dedupe 필요.

## Decision

- Decision: `TASKSET-AR-HOST-FEEDBACK-INTAKE`(Host Liaison, order 524)를 `TASKSET-DEFINITIONS.json`에 등록하고 TASK-AR-526~532를 캐노니컬 task 파일로 등록한다.
- Decision: 526/527/528은 파이프라인 캐노니컬 능력으로 진행, 529/530/531/532는 후보로 등록하되 채택/보류/기각은 TASK-AR-527 첫 심의의 산출물로 결정한다(#131 가드레일).
- Decision: 제품 방향·안전 경계는 Owner/R3 고정, 투표는 우선순위 신호로만 사용한다.
- Decision: 본 레코드를 `owner-docs.yml` 매니페스트에 등재해 owner_doc_format_gate로 거버넌스한다.

## Next

- TASK-AR-527 1회차 심의를 가동해 후보 4건의 채택/보류/기각과 우선순위를 산출하고 결과를 본 레코드와 각 이슈에 회신(TASK-AR-528).
- 채택분은 dispatcher claim 후 구현; 보류분은 사유와 재검토 기한을 기록.
- 등록 자체는 ready lane을 이동하지 않는다 — 다음 taskset 선택은 BACKLOG-BOARD.md 기준.
