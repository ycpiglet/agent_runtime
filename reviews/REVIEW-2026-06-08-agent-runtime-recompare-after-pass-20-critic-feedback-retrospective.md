# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-20-critic-feedback-retrospective

## Bottom Line

초기 비판 리뷰(`user_action: review`)의 5개 핵심 이슈 기준으로 보면, 이번 PASS-20 구간에서는
`템플릿 self-contained`, `템플릿 실행 smoke CI`, `의존성 계약`, `병렬 claim의 중복 방지`는 실질적으로 닫혔고,
`ToolRunner sandbox`는 커버리지가 크게 확장되었지만 **여전히 추가 공격면이 남아 있어 C급으로 낮은 임계점만 줄어든 상태**다.

## Signal

| 항목 | Baseline | PASS-20 상태 | 증거(날짜: 2026-06-08) |
|---|---|---|---|
| 템플릿 자체 완결성 | Critical | ✅ Closed | `src/agent_runtime/templates/project/scripts/{agent_orchestrator.py,orchestrator_safety_gate.py,pipeline.py}` 존재, `schemas/task.schema.json` 추가, `tests/test_template_smoke.py`에서 sync 후 help 실행 |
| 템플릿 실행 검증 CI | Critical | ✅ Closed | `.github/workflows/test.yml`에 `tests/test_template_smoke.py` 단계 추가 |
| ToolRunner 샌드박스 | High | ⚠️ 일부 완화 | `providers/agent_tools.py` 커맨드 프로파일(ci/owner/research), `python -c`, `python -`, `pip`, mutable git 기본 block 테스트 통과 |
| 메시지 claim 병렬 안전성 | High | ✅ 크게 개선됨 | `src/agent_runtime/templates/project/scripts/message_queue.py` 추가, 동시 claim 12개/다중 프로세스 테스트로 한 건만 성공 보장 |
| 의존성 계약 | Medium | ✅ Closed | `pyproject.toml` optional extras 추가, providers lazy-import 계약, `tests/test_provider_import_contract.py`로 dummy import 실패-보호 검증 |

요약 성능 지표:

- `PYTHONPATH=src python -m pytest tests -q` → `129 passed`
- `tests/test_template_smoke.py`, `tests/test_template_message_queue.py`, `tests/test_template_agent_tools.py` 통합(선택) 실행 모두 pass

## Insight

1. baseline에서 가장 치명적이었던 실행성 실패(템플릿 누락)와 CI 미검증은 제거됐다.
2. 병렬 처리 위험은 "atomic claim + lease + 소유권 검증 + reply idempotency" 조합으로 실질적으로 낮아졌다.
3. ToolRunner는 프로파일 경계가 생겨 `python -c`류/임의 mutable git/파이프/리다이렉션/경로 탈출을 차단하는 흐름이 정착했지만,
   보안은 **기능 회귀를 막기 위한 추가 규칙 보강이 필요한 중간 단계**로 봐야 한다.

## Decision

### 이번 패스에서 반영/확인된 항목

- `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 추가 및 템플릿 경로 정합성 복구
- `tests/test_template_smoke.py`로 sync → `agent_orchestrator.py --help`, `agent_worker.py --help`, `auto_runner.py --json`, `check_messages.py`, 더미 메시지 처리까지 검증
- `providers/agent_tools.py`에 프로파일 기반 `run_command` 정책 적용
- `src/agent_runtime/templates/project/scripts/message_queue.py` + `tests/test_template_message_queue.py`로 동시 claim/reply 경합을 기계적으로 검증
- `tests/test_provider_import_contract.py`로 optional dependency/lazy import 계약 강화
- `agent_runtime doctor` 추가 및 `tests/test_doctor.py`로 런타임 블로커 항목 자동 진단

### 남은 미완 결합점 (다음 재평가 대상)

- **ToolRunner 샌드박스의 남은 표면**
  - 외부 호출 경로가 아닌 우회 인자 조합(예: 특수 인용, 환경 치환 변형, 플랫폼별 셸 동작) 점검 필요
  - `research`/`owner` 모드에서 허용 커맨드가 커지는 지점의 감사 로그가 미흡
- **분산 환경 정합성**
  - claim lease는 `NFS/SMB` 같은 원격 FS에서의 락 일관성이 전제되지 않음
  - 현재 테스트는 단일 FS 위주의 동시성 검증
- **실행 리스크의 운영 레이어**
  - 병렬 워커/파이프/observability 통합은 동작은 하지만 성능/가시성 경보 계측은 다음 단계에서 별도 지표화 필요

## Re-score (현재 vs Baseline)

| Area | Baseline | 현재 |
|---|---|---|
| Public release hygiene | B+ | B+ |
| Sync/update safety | B+ | B+ |
| Template execution completeness | D | B- |
| Real multi-agent parallelism | C- | B- |
| Security / command sandbox | D+ / D | C- |
| Collaboration/governance design | B | B |
| Self-improvement loop | C- | C- |

## Remaining Risk Register

- **R1 (High):** ToolRunner 우회 가능성(플랫폼별 셸/토큰 변조) 정량 테스트 미흡
- **R2 (High):** 분산 FS/네트워크 FS에서의 claim lease 충돌 모형 미검증
- **R3 (Medium):** Owner/research 모드 허용군 확장 시, 실제 운영 정책 문서와 감사 로그 정합성 미완성

## 참고

- `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-19-critic-feedback-archive.md`
- `IMPLEMENTATION_PLAN.md`
