# MEETING-2026-06-11-agent-runtime-task-ar-summary-and-version-closeout

## Participants
- lead engineer
- runtime owner
- doc steward

## Agenda
- 버전 업데이트 일정 확정
- TASK-AR 항목(201~209) 실행 순서 확정
- tag_manual 이식 누락 우려 검증 방식 정리

## Decisions

1) 버전 일정
- v0.1.6 공개 후보는 2026-06-13 기준 마감점검을 유지한다.
- v0.1.7 공개 목표일은 2026-06-18으로 확정한다.

2) 실행 우선순위(첫 세션)
- 1순위: `TASK-AR-201` 마감조건 정합(필수 메타, 경고/이관 경로)
- 2순위: `TASK-AR-204` + `TASK-AR-209`를 동시에 수행해 누락/변경 이슈의 근거를 먼저 고정
- 3순위: `TASK-AR-202`, `TASK-AR-203`, `TASK-AR-205`
- 4순위: `TASK-AR-206`, `TASK-AR-207`, `TASK-AR-208`

3) tag_manual 대비 이식 검증
- 즉시 코어 코드 변경 없이, 먼저 비교 산출물(`MIGRATION-COMPAT-MAP.example.yml`)을 기준으로 판단한다.
- `missing`이 발견되어도 즉시 실패가 아니라 `dropped/changed` 이유와 owner 승인 근거를 기록한다.

4) 통합 규칙
- `source=.`, `release-preflight`, `SKILL-DATA-MAP`은 같은 release loop에서 연동해 평가한다.
- 출처/태그 footer, uncertainty 태그, source tier 표기 의무화를 다음 릴리스 게이트 조건으로 반영한다.

## Action Items

- `BACKLOG.md` 업데이트(버전일정/우선순위/리스크)
- `AGENTIC_KNOWLEDGE_EVAL_PLAN.md`에 1~16 항목 매핑 항목 반영
- TASK 파일 201~209 전체 생성 및 상호 의존성 점검
- `SKILL-DATA-MAP.example.yml`, `MIGRATION-COMPAT-MAP.example.yml` 템플릿 생성
