# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-88.md

## Bottom Line

`PASS-88`에서는 `warning-summary` 요약 정책 상수(`PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`)를 `workflow_call`/`workflow_dispatch` 입력으로 주입 가능한 경로로 확장해 수동/재사용 실행에서도 release 요약 게이트와 `release-preflight` 정책 동기화를 동일하게 유지한다.

## Signal

| 항목 | PASS-87 상태 | PASS-88 상태 | 근거 |
|---|---|---|---|
| 정책 입력성 | 릴리스 전용 경로(고정 env) | 워크플로우 입력(`warning_summary_gate_strict_refs`) 추가 | `.github/workflows/test.yml` `on.workflow_call/workflow_dispatch.inputs` 정의 |
| 정책 반영 일관성 | 정해진 브랜치에서만 `--require-send-targets` 판단 | 실행 방식 재사용 시에도 입력값 기반으로 동일 env로 전파 | `Resolve warning summary strict refs input` 스텝 + `release-preflight` 기존 env 전달 |
| 조작성 | 재현/수동 실행에서 정책 커스터마이즈 불가 | 호출자 입력으로 strict-ref 목록 조정 가능 | 테스트 전략 PASS-88 문서 항목 추가 |

## Insight

- CI 내부 정책 상수는 이미 고정되어 있지만, 재사용/수동 트리거에서 같은 정책을 못 쓰면 운영 재현성 문제가 발생할 수 있다.
- 입력 기반 주입은 정책을 외부화하면서도 기본값을 보존해 기존 동작을 깨지 않게 유지한다.
- 별도의 코드 경로를 바꾸지 않고도 현재 `release-preflight`에서 읽는 env 계약만 재활용할 수 있어 변경 리스크가 낮다.

## Decision

- `.github/workflows/test.yml`
  - `workflow_call`/`workflow_dispatch`에 `warning_summary_gate_strict_refs` 입력 추가
  - 기본값으로 기존 strict-ref 목록을 다중행 문자열로 저장
  - 실행 초반 스텝에서 입력값을 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`로 재할당하는 정규화 단계 추가
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-88` 항목으로 workflow 입력 재사용 경로 문서화

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 워크플로우 자체 실행은 CI에서만 가능하므로, 현재는 정적 diff 리뷰로 근거 확인
- 필요한 경우 다음 실행에서 `workflow_dispatch` 입력을 변경해 `require-send-targets` 판단 분기(브랜치 상관없는 재현 실행) 정상 반영 여부를 검증
