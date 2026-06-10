# REVIEW-2026-06-13-agent-runtime-task-ar-211-overlay-bundle-review

## Bottom Line

`TASK-AR-211` 오버레이 패키지(vision/roadmap/org/links + governance/dataset/eval 매핑)는 생성되어 `TASK-AR-201/204` 연계의 기초 증거가 확보되었다.

## Signal

- `agents/project/PROJECT-CONTEXT.yml` 생성: 프로젝트 메타, 단계, 의사결정 체인.
- `agents/project/CONTEXT-SOURCES.yml` 생성: 4-tier source ranking + definition/query policy.
- `agents/project/SKILL-GOVERNANCE.md`, `SKILL-DATA-MAP.yml`, `MIGRATION-COMPAT-MAP.yml`, `EVAL-POLICY.yml`, `DATASET-CATALOG.yml` 생성.
- `TASK-AR-209/212`가 공통 키(`MIGRATION-COMPAT-MAP.yml`)로 이관될 수 있도록 토대 마련.

## Insight

- 오버레이가 실제로 동작하려면 `agent_context_packet.py`의 project context 탐색 경로(현재 root/agents/project)를 통해 `PROJECT-CONTEXT.yml` 및 TEAM docs를 감지해야 한다.
- 이식 감사는 산출 파일이 아니라 ID 정합 규칙의 누락이 큰 리스크였고, 문서 체계가 정합되어야만 정적 검사로 이어진다.

## Decision

- 다음 단계는 `TASK-AR-204`에서 오버레이 누락을 `high-risk` 경고로 표준화하고, `release-preflight`와 연결해 block 조건을 검증하는 것으로 종료한다.
