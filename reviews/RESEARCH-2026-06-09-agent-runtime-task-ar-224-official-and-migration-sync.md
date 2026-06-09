# RESEARCH: TASK-AR-224 official + migration sync (2026-06-09)

수집일: 2026-06-09

## 배경

- `TASK-AR-224`는 v0.1.8 판정 전에 공식 가이드, migration 근거, 강제 규칙이 같은 closeout 번들에 묶이는지 확인하는 선행 gate다.
- 이번 연구는 `TASK-AR-219` 공식 권고, `TASK-AR-220` tag_manual 이식 근거, `TASK-AR-223` closeout 통합을 한 번에 연결하기 위한 사전 정합이다.

## 확인한 공식 근거

- OpenAI Trace grading:
  - trace 단위로 결정, 도구 호출, reasoning 경로에 구조화된 점수/라벨을 붙여 실패 지점을 찾는 방식.
  - v0.1.8에서는 offline eval 점수만으로 통과하지 않고 trace key와 reviewer verdict가 같이 남아야 한다.
  - source: https://platform.openai.com/docs/guides/trace-grading
- OpenAI Agent evals:
  - workflow 수준 오류 진단에는 trace grading을 우선 권장하고, datasets/evals를 통해 재현 가능한 평가 루프를 유지한다.
  - source: https://platform.openai.com/docs/guides/agent-evals
- OpenAI Running Codex safely:
  - sandbox, approval policy, network policy, rules, telemetry를 함께 운영해 low-risk는 빠르게, high-risk는 명시적 검토로 보내는 방향.
  - `agent_runtime`에는 warn-only 경로가 남으면 안 되고, 고위험 항목은 hold/block으로 라우팅해야 한다.
  - source: https://openai.com/index/running-codex-safely/
- A2A specification:
  - `contextId`와 `taskId`를 유지해 멀티턴 작업의 연속성과 재개 가능성을 보장한다.
  - `TASK-AR-208`/`TASK-AR-223`에서는 A2A trace가 correction/reviewer와 같은 decision cycle에 연결되어야 한다.
  - source: https://github.com/a2aproject/A2A/blob/main/docs/specification.md

## migration 정합 판단

- `MIGRATION-COMPAT-MAP.yml` 기준 핵심 분류는 현재 다음과 같다.
  - `scripts-source-only`: 53건, status `missing`, approved_by `TASK-AR-218`, expiry `2026-07-16`
  - `scripts-runtime-extra`: 2건, status `deprecated`, approved_by `TASK-AR-218`, expiry `2026-07-16`
  - `hooks-wrapper`: 1건, status `changed`, approved_by `TASK-AR-213`, expiry `2026-07-16`
  - `skills-pack`: 16개 중 15 changed / 1 kept
- 이 상태는 “완료”가 아니라 release 판정에서 hold/block 라우팅 가능한 근거가 생긴 상태다.
- `scripts-source-only` 53건은 다음 사이클에서 세분류가 필요하다: intentional-drop, legacy-scope, runtime-gap, needs-port, duplicate-covered.

## 결론

- `TASK-AR-224`는 `planned`에서 `in_progress`로 이동 가능하다.
- 1차 판정 전 최소 산출은 아래 4개다.
  - 공식 근거 링크 세트
  - migration hold routing table
  - warn-to-block 판정 기준
  - `TASK-AR-223` closeout bundle 링크
- 아직 완료로 볼 수 없는 항목은 overlay-only 시뮬레이션과 실제 release-preflight block 증적이다.
