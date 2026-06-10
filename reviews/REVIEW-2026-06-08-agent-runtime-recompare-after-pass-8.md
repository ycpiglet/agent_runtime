# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-8

## Bottom Line

원래 비판 포인트(템플릿 완결성, CI 검증, command 사일로, 병렬 claim, 의존성)를 기준으로 보면, 패스-7 이후 `pass-8`에서 **실행 증거 기반 위험이 실제로 2개( git 프로파일 allowlist의 실제 동작, 멀티프로세스 경합 검증 )에서 유의미하게 줄었고**, 기존 우려 5개 중 4개는 실사용 경로에서 방어 동작이 닫혔습니다.
남은 핵심 리스크는 **(1) profile별 정책의 운영적 분리 범위 문서화, (2) 단일호스트 파일시스템 가정 넘어선 분산/다중 노드 claim 전략, (3) 다중 메시지 연속 처리까지 끌어올린 장기 안정성 테스트**입니다.

## Signal

- 기준:
  - 초기 비판 정합: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
  - 직전 상태: `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-7.md`
- 실행 증거:
  - `C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_template_smoke.py tests/test_provider_import_contract.py -q`
    → `15 passed`
  - `C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests -q`
    → `110 passed`

### pass-7 → pass-8 비교

| 항목 | pass-7 판정 | pass-8 판정 | 근거 |
|---|---|---|---|
| 템플릿 실행 완결성 | 개선 완료 | 개선 완료(변경 없음) | `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, Smoke 테스트가 선행 상태 유지 |
| 템플릿 CI/스모크 | 개선 완료 | 개선 완료(변경 없음) | `test_template_smoke.py` 체계 및 동작 확인 유지 |
| ToolRunner command 정책 분리 | `ci`/`owner`/`research` 개념 도입, 일부 차단 테스트만 완료 | owner에서 의도한 `git add/restore` 허용이 실제 동작으로 고정, 프로파일 경계가 실행 증거로 검증됨 | `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`, `tests/test_template_agent_tools.py` |
| 병렬 claim 경합 | thread 기반 단일 호스트 경합 일부 검증 | **멀티프로세스 경합 검증 추가** (하나의 메시지에서 정확히 1개 claim 성공) | `tests/test_template_message_queue.py`에 `multiprocessing` 기반 `test_concurrent_claim_mp_has_exactly_one_winner` 추가 |
| 스태일/중복 답변 억제 | 개선 완료 | 개선 완료 | 동시 reply 수 1개 보장 테스트 유지 |
| provider 의존성 계약 | 개선 완료 | 개선 완료 | `tests/test_provider_import_contract.py` 통과, 지표 unchanged |

## Insight

패스-7에서 남아 있던 “문서상 계획은 있으나 실행 경로 증거가 부족했다”는 유형의 gap이, 이번 변경으로 두 군데 줄었습니다.
1) `run_command`의 owner 정책이 실제로 동작하지 않던 버그를 바로잡아 **정책-실행 불일치**를 해소했습니다.
2) 경합 조건을 thread에서 process로 확장해 **동시성 보장 증거의 실효성**을 높였습니다.

## Decision

- 보존: 현재 상태를 기준으로 패스-8는 `템플릿 런타임이 공개 적용 가능한 강한 baseline`로 간주 가능.
- 다음 액션: 남은 항목을 다음 패스에서 분리 추적
  1) `research` 프로파일이 `owner`와 물리적으로 다른 정책/허용목록을 가져가도록 설계 완결
  2) lock/lease 경합을 다중 노드(네트워크 공유 FS/다른 드라이브) 조건에서 검증
  3) smoke를 “1개 메시지”에서 “다중 메시지 + 실패 복구 + 재시도”로 넓혀 장기 회복성 확인
