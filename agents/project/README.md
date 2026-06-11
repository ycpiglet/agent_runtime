# Project Context Overlay

이 디렉터리는 프로젝트 고유 맥락을 보관하는 오버레이 레이어입니다.

Agent Runtime은 공통 런타임(`agents/*/SKILL.md`, `scripts/*`)을 유지하고,
각 프로젝트는 아래 파일을 통해 제품 정체성·운영 규칙·문서 링크를 오버레이합니다.

- `PROJECT-CONTEXT.yml`: 제품/프로젝트 핵심 메타 정의
- `CONTEXT-SOURCES.yml`: SSoT 정렬, 메타 필수 값, 정책 정의
- `ROADMAP.md`: 단계/마일스톤/릴리스 정책
- `ORG.md`: 조직/권한/승인 경로
- `TEAMS.md`: 팀 구성/역할/문맥
- `LINKS.md`: 결정 로그 및 외부 의존성 링크
- `SKILL-GOVERNANCE.md`: 지식/런북/오버레이 운영 규칙
- `SKILL-DATA-MAP.yml`: 스킬·데이터·스크립트 변경 동기화 맵
- `DATASET-CATALOG.yml`, `EVAL-POLICY.yml`: 오프라인/라이브 평가 정책
- `VISION.md`: 문제/성공 지표/비목표 정의
- `TASK-AR-214`: 질의/메타데이터 게이트 (정의 책임 + 모호성 조정)
- `TASK-AR-215`: 오버레이 고유성 및 context packet 표준화
- 레거시 이관 감사 스냅샷: `reviews/MIGRATION-COMPAT-MAP-2026-06-11-SNAPSHOT.yml`,
  `reviews/MIGRATION-HOLD-ROUTING-2026-06-11-SNAPSHOT.yml`

## 운영 원칙

- 제품 특화 동작은 host overlay 파일로 표현하고, 런타임 핵심 파일은 건드리지 않는다.
- 문서 누락/과도한 구식 문서는 `TASK-AR-204/209/212`에서 릴리스 차단으로 전환한다.
- 멀티 프로젝트 사용 시 이 디렉터리만 변경되어야 한다.
