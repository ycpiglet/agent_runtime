# Skill Governance (Host Overlay)

## Runbook Contract

Runbook 항목은 아래 6단계 증거가 모두 남아야 완료로 간주한다.

1. clarify: 질문, business_scope, time_window, tolerance, query_tolerance, tradeoff_preference를 명확화한다.
2. retrieve: `CONTEXT-SOURCES.yml`의 source_tier 우선순위와 access_level을 확인한다.
3. execute: 실행 범위와 변경 경계를 기록하고 검증된 스크립트/패턴을 우선 재사용한다.
4. review: 적대적 검토(adversarial review) 또는 reviewer_review 결과를 남긴다.
5. verify: 검증 명령, 점수, 실패/경고 수, source_footer를 기록한다.
6. record: evidence, review_verdict, verified_pattern, correction_path를 task/review/status에 연결한다.

완료 필수 evidence:

- `source_footer`
- `review_verdict`
- `evidence`
- `verified_pattern`
- `correction_path`
- `record_path`

## Context + Verification First (정확도 = 맥락 + 검증)

- 정확도는 모델 단독으로 보장되지 않으며 `context + verification` 조합으로 관리한다.
- 모호성(ambiguity)이 높으면 즉시 follow-up 질문을 통해 질문을 분해하고 범위를 좁힌다.
- 실수로 인한 오답·오탐은 `질문 정제`와 `reviewer` 경로로 흡수한다.

## Query Contract (필수 메타)

각 요청은 최소 아래 메타가 함께 들어와야 한다.

- `owner`
- `question`
- `source_tier`
- `business_scope`
- `time_window`
- `tolerance`
- `access_level`
- `ambiguity_level`
- `query_tolerance`
- `tradeoff_preference` (accuracy / speed / cost)

- 메타 미기재 시 `clarify_required`
- 잘못된 출처 참조 시 `reviewer_review` 후 실행
- query contract violation이 남으면 release routing은 `hold_for_query_contract`
- 고위험·stale·access 불명확 요청은 기본 답변으로 종료하지 않고 `clarify_required` 또는 `reviewer_review`

## Required Footer (지식 응답)

출력에는 아래 태그를 의무 포함한다.

- `source_tier`
- `source`
- `confidence`
- `access_level`
- `ambiguity_score`
- `review_verdict`
- `source_tier_tag`
- `risk_tag`
- `ambiguity_tag`
- `freshness_sla`
- `lineage`
- `review_cycle_id`
- `correction_status`

## Warehouse Document Shape

지식창고 문서는 최소 1개 role 단위 문서부터 아래 순서를 지킨다.

1. 빠른 참조
2. 차원설명
3. 핵심 테이블
4. 주의사항/패턴
5. 연결고리

각 문서는 `source tier`, `lineage`, `history`, `context knowledge`, `freshness_sla`, `owner`, `updated_at`를 포함한다.
stale 또는 메타 누락은 pre-check 경고로 남기고, 반복되면 `TASK-AR-204`의 block 경로로 이관한다.

## Source Ranking Priority

- 1) certified semantic layer
- 2) lineage
- 3) history
- 4) context knowledge

## Cross-project Overlay Rules

- `agents/project/*` 파일은 공용 런타임 동작 변경 없이 프로젝트 문맥만 바인딩한다.
- `agents/*/SKILL.md`, `scripts/*`은 공용 표준으로 두고, 오버레이에서는 프로젝트 정의만 바꾼다.
- 오버레이가 누락되면 `TASK-AR-204`에서 `high-risk` 라우팅하고 해당 TASK로 이관한다.
- 프로젝트 고유성은 `vision`, `roadmap`, `org`, `links`, `teams`, `communication`의 연결고리를 통해 `project context packet`으로 일괄 반영한다.
- 오버레이 내 문서와 스킬이 맞지 않으면 `TASK-AR-204`/`TASK-AR-213` 기준으로 `release block`.

## Co-location Rule

- 스킬 문서는 데이터셋, 훅, 런타임 스키마와 동일 변경 단위로 관리한다.
- 변경 시 `SKILL-DATA-MAP.yml`을 반드시 함께 갱신한다.
- `TASK-AR-204`의 블로커 규칙:
  - 연동 항목 변경 + 매핑 누락 → `release block`
  - 승인된 의도적 제외만 waiver 허용
  - 변경 근거(`owner`, `approval`, `expiry`) 미기재는 즉시 block
