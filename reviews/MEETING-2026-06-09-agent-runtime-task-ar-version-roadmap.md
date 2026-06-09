# MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap

## Participants
- lead engineer
- doc steward
- owner steward

## Agenda
- 다음 공개 버전 일정(v0.1.6/ v0.1.7) 확인
- task-ar 연속 항목(201~209)의 우선순위 고정
- `tag_manual` 이식 누락 항목의 증빙 방식 결정

## Decisions

- v0.1.6 공개 처리 기준일은 2026-06-13(릴리스 리허설 통과 전제)로 임시 고정.
- v0.1.7 공개 목표일은 2026-06-18로 상향.
- `TASK-AR-204`가 선행되어 스킬-데이터 동기화 불일치 차단이 활성화되어야 한다.
- `TASK-AR-209`을 새 태스크로 추가해 `tag_manual`에서 이식 누락·의도 변경을 증빙.
- 실시간 리뷰/교정 수집은 `TASK-AR-206/207`로 설계되며, `source footer + tags`를 최소 출력 규격으로 둔다.

## Action Items

- 1) `BACKLOG.md`에서 v0.1.6/v0.1.7 후보 및 P0 순서를 반영.
- 2) `AGENTIC_KNOWLEDGE_EVAL_PLAN.md`에 공식 가이드(Anthropic/OpenAI) 링크 추가 및 실행 protocol 보강.
- 3) `TASK-AR-209` 초안(Task 스키마 + migration map) 생성.
- 4) 다음 세션에서 `TASK-AR-204`에서 `SKILL-DATA-MAP.yml` 차단 규칙 초안 작성.
