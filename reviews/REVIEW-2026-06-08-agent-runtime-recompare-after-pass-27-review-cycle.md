# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-27-review-cycle

## Bottom Line

R1~R3 잔여 리스크 해소를 위한 실제 실행 사이클을 한 번 더 밀어 넣었다.
기존에 고지한 `command sandbox`·`분산 claim`·`감사 정합성`의 취약점을 **테스트 기반으로 추가 강화**했고, 핵심 실행 지표는 모두 통과했다.

## Signal

| 항목 | PASS-26 기준 | PASS-27 기준 | 증거 |
|---|---|---|---|
| R1 Command sandbox | 플랫폼 우회 패턴 일부만 커버 | 우회 패턴 확대 + 감사 추적 기반 추가 | `tests/test_template_agent_tools.py`, `tests/test_template_agent_tools.py::test_run_command_blocks_percent_encoded_and_here_string_variants` |
| R2 Queue 분산/회수 정합성 | 기본 동시 claim + stale 메타 정합성 | `claim` 파싱 실패 파일 자동 회수 + stale claim 회수 동시성 테스트 추가 | `src/agent_runtime/templates/project/scripts/message_queue.py`, `tests/test_template_message_queue.py` 3개 새 경로 |
| R3 감사-정책 정합성 | 정책 위반 시 허가/차단만 간헐 확인 | `doctor`가 `ToolRunner` 차단 명령의 audit-entry 존재를 필수 조건으로 검증하도록 강화 | `src/agent_runtime/doctor.py`, `tests/test_doctor.py::test_doctor_success_for_synced_host` |

### Verification Snapshot

- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_template_message_queue.py tests/test_template_agent_tools.py tests/test_doctor.py -q`
  → `34 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests -q`
  → `137 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m agent_runtime.cli publish-check --root . --check`
  → `findings=0`

## Insight

`ToolRunner`와 `message_queue` 모두 “좋은 실패” 상태로 설계가 더 좋아졌다.

- `message_queue`의 claim 파일 파싱 실패가 더 이상 영구 블로킹으로 이어지지 않고, stale/손상 claim를 복구 경로로 회수할 수 있다.
- command profile 위반은 여전히 차단되며, 이제 doctor 레이어에서 *차단 + 감사 로그 기록* 동시 보존을 점검한다.

## Decision

### 이번 사이클에서 닫은 항목

1. R1 `%%`/here-string 계열 우회 패턴 테스트 추가 완료.
2. R2 claim 파일 손상 복구 + stale-기반 동시 재획득 테스트 추가 완료.
3. R3 정책-감사 정합성(도구 차단 발생 시 audit 기록 생성) CI/회귀 검증 체인 반영.

### 다음 사이클 남은 R1~R3 후보

- R1: 플랫폼별 고급 인코딩 체인(예: 다중 인코딩, 중첩 쉘 확장 문자열) 자동 생성기 기반 fuzz coverage 확대.
- R2: NFS/SMB 특성 하에서의 파일 잠금 특성(동일 경로 rename/열기 시점 편차) 주입 테스트 보강.
- R3: `owner/research` 프로파일을 포함해 감사 로그-경고 매핑을 CI에서 정량 비교로 확장.

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-final-comparison-pass-26.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-23-command-sandbox-review.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-claim-backup-validity-comparison-pass-25.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `src/agent_runtime/doctor.py`
- `tests/test_template_agent_tools.py`
- `tests/test_template_message_queue.py`
- `tests/test_doctor.py`
