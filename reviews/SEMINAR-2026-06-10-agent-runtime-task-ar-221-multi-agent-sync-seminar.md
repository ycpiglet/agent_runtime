# SEMINAR-2026-06-10-agent-runtime-task-ar-221-multi-agent-sync-seminar

## Bottom Line

- 멀티 에이전트 협업에서 가장 우선순위는 `강제 규칙 동기화`이며, 그 다음이 `migration 근거 추적`이다.

## Discussion

- 참석: lead-engineer, doc-steward, independent-auditor, qa, owner.
- 논의 주제:
  - `SKILL-DATA-MAP.yml`가 모델/provider/문서 변경을 함께 포착해 `TASK-AR-204`/`TASK-AR-210` block로 전이 가능한지
  - `MIGRATION-COMPAT-MAP.yml`의 누락/추가 항목이 `query-risk / cost / freshness` 맥락으로 분류되는지
  - 오버레이 문서(stale/누락)가 `hold_for_overlay`로만 이동되는지
- 합의:
  - `SKILL-DATA-MAP.yml` `required_when`에 `provider-config-changed`, `mapping-doc-changed`, `runtime-script-changed`, `task-policy-changed`를 추가.
  - `MIGRATION-COMPAT-MAP.yml` 항목마다 `risk_profile`을 붙이고 보류사유를 `TASK-AR-220` 이관 근거와 링크.
  - `TASK-AR-221` 완료 시점 이전에 `TASK-AR-219` 판정 문구 동기화는 잠금.

## Action

- `SKILL-DATA-MAP` 교차본(agents/project / template) 동기화 후 리뷰.
- `TASK-AR-221` 산출 문서군에서 협업 기록 3종 모두 링크되었는지 검증.
- 다음 회차: `TASK-AR-220` 근거 마감으로 넘어감.
