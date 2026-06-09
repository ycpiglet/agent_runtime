# SEMINAR-2026-06-13-agent-runtime-task-ar-211-overlay-seminar-notes

## Discussion Notes

1. overlay-first vs script-first: 이번 프로젝트는 오버레이 우선 원칙으로 고정.
2. 오버레이 파일은 4개 그룹으로 필수화 (`ROADMAP`, `ORG`, `LINKS`, `TEAMS`) + 계약 파일 집합.
3. `TASK-AR-204` 게이트는 규칙만으로 경고를 띄우지 않고, release-preflight 연동 시 block으로 전환.

## Technical Outcome

- `agents/project/`에 다음 12개 파일을 정식 오버레이 자산으로 배치:
  - README, PROJECT-CONTEXT.yml, CONTEXT-SOURCES.yml, VISION.md, ROADMAP.md, ORG.md, TEAMS.md, LINKS.md, SKILL-GOVERNANCE.md, SKILL-DATA-MAP.yml, MIGRATION-COMPAT-MAP.yml, DATASET-CATALOG.yml, EVAL-POLICY.yml.
- `TASK-AR-209`와 `TASK-AR-212`는 `MIGRATION-COMPAT-MAP.yml`의 키(`id`, `status`, `category`, `approved_by`, `decision_date`)로 통합 정합.
- `TASK-AR-211`은 다음 액션으로 오버레이 누락 경고를 `TASK-AR-204` 차단 루프로 전달하는 항목을 기록.

## Seminar Action

- 다음 세션: `TASK-AR-211` 완료 로그를 `TASK-AR-204`/`209`/`212`로 전달하고, `BACKLOG`/`STATUS` 링크 갱신.
