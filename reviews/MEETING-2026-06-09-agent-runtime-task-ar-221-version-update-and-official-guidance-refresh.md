# MEETING (2026-06-09): TASK-AR-221 공식 가이드 동기화 및 버전 업데이트 일정 정합 회의

## Bottom Line

- `v0.1.8` 판정 일자는 **2026-07-02(1차)**, **2026-07-09(2차)**, **2026-07-16(최종 freeze)**로 고정.
- 다음 단계는 `TASK-AR-221` → `TASK-AR-219` → `TASK-AR-220` → `TASK-AR-216` → `TASK-AR-218` 순으로 진행해
  판정 문구(`release-state`, `release_cause`)와 근거 번들을 단일 체인으로 묶는다.
- `tag_manual` 이식 누락 의심 항목은 “임의 유실”이 아니라 `mapped / intentionally dropped / migration-only`의 근거 분기 기반으로 정리되어야 한다.

## Signal

- 공식 가이드(Claude/OpenAI/Codex) 정렬 핵심은 모델 점수보다 **Context + Verification + Governance trace**.
- A2A trace, reviewer footer, correction path, migration 근거, 오버레이 누락 경로를 분리해 `release-preflight`에서 직접 참조 가능해야 함.
- `MIGRATION-COMPAT-MAP.yml` 기준에서는 현재:
  - `scripts` 171개 중 `kept 59 / changed 59 / missing 53 / runtime-only 2`
  - `skills 16개` 중 `changed 15 / kept 1`
  - `hooks`: `src/hooks/.gitkeep` placeholder → `*_hook.py 4개` 재구성
  - `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper`는 `approval/motive/expiry`가 있으면 허용, 미입력 시 즉시 hold/block

## Insight

- 정답 자체를 데이터에서 증명할 수 없다는 제약 때문에, 질문 계약(`ambiguity`, `time_window`, `tradeoff`)과 이행 루프(`clarify/reviewer/correction`)가 릴리스 판정의 실질적 안전장치다.
- “문서/규칙이 있고 동기화되지 않은 상태”가 실제 품질 위험을 만든다. 그래서 `warn`가 아닌 `block` 전환 규칙을 고정해야 한다.
- 멀티 프로젝트 운영은 런타임 교체보다 오버레이(`vision/roadmap/org/links/teams/communication`)의 정합성으로 성패가 갈린다.

## Decision

1. `v0.1.8` 판정 문구와 evidence path는 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에 동일한 문구로 남긴다.
2. `TASK-AR-210`는 기존 `v0.1.7` 판정 기록을 유지하되 `v0.1.8` 3단계 판정(07-02/07-09/07-16) 및 hold 루트를 우선 반영한다.
3. `TASK-AR-220`는 `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper`를
   의도적 제외/변경/보류 사유로 분해해 `TASK-AR-204`/`TASK-AR-213`/`TASK-AR-210`으로 1:1 추적되도록 한다.
4. 다음 세션의 우선순위는 `TASK-AR-221` 완료 증거 정합 점검 후 즉시 1차 판정 패키지(오프라인 90%, reviewer footer, correction, A2A, migration map) 번들 생성이다.
