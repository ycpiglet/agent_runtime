---
type: meeting
id: MEETING-2026-06-12-independent-verification-rule
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [verification, independence, self-review-prohibition, lifecycle, rule]
---

# Independent Verification Rule Meeting

## Bottom Line

- Summary: Owner가 "작업자가 스스로 검증하면 안 되고 항상 다른 에이전트가
  검증해야 한다 — 규칙이 없으면 강제하라"고 지시했고, 점검 결과 라이브에
  실행 강제가 없음을 확인해(EVAL-POLICY advisory + release council 역할
  구성뿐) 규칙을 명문화하고 실행 게이트를 TASK-AR-507로 등록했다.
- Result: W4를 분리한다 — W4a(작업자가 verification 명령 실행·증거 첨부)
  / W4b(작업자와 **다른** 에이전트 인스턴스/역할이 검토·승인해야 claim
  release 가능). self-approve 금지는 즉시 발효, 실행 강제는 codex
  agent-identity(인스턴스 귀속) merge 후 AR-507이 게이트로 닫는다.
- Boundary: 본 세션의 500번대 작업부터 즉시 적용 — 메인 세션이 구현한
  변경은 독립 reviewer 에이전트의 검토를 통과해야 merge한다.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| 기존 실행 강제 부재 | pass | `EVAL-POLICY.yml` reviewer_agent는 live_verification 한정 + advisory; 일반 worker≠verifier 게이트 없음 |
| 역할 독립성 개념 기존재 | pass | 템플릿 roles.yml `forbidden_inputs`/`audit_gate`, release council 4역할, lead_engineer self-review 명시 규칙 |
| 귀속 식별 기반 | watch | 인스턴스 귀속(agent_instance_id 스폰 기록·attribution gate)은 codex AR-375 미머지 — 실행 강제의 전제 |

## Decision

- Decision: W4 분리 — W4a 작업자 verification 실행, W4b 독립 검증(작업자와
  다른 agent_instance_id 또는 역할이 승인). self-approve로 claim release·
  closeout·merge 진입 금지.
- Decision: 독립 검증자의 최소 요건 — 같은 대화 컨텍스트를 공유하지 않는
  별도 인스턴스(서브에이전트 reviewer 가능) 또는 별도 역할 페인.
  검증 결과는 closeout/handoff에 verifier 식별자와 함께 기록한다.
- Decision: 실행 강제는 TASK-AR-507 — closeout/release 시 verifier ≠
  worker를 검사하는 게이트. codex identity 스키마(인스턴스 스폰 기록)
  merge 후 착수.
- Decision: 게이트 도착 전 과도기에는 운영 규칙으로 즉시 적용하고, 본
  세션의 AR-500 구현부터 reviewer 서브에이전트 독립 검토를 증거로 남긴다.

## Risks / Blockers

- Risk: 서브에이전트 reviewer는 별도 인스턴스지만 같은 모델 계열일 수
  있다 — 장기적으로는 역할 페인(codex↔claude 교차 검증)이 더 강한 독립성.
- Blocker: 없음.

## Next Steps

- AR-500 코어 구현 → reviewer 서브에이전트 검증 → merge (본 세션).
- codex identity merge 후 AR-507 착수.
