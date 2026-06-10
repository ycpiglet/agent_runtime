# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-29

## Bottom Line

초기 비판 리뷰의 핵심 이슈(템플릿 완결성, CI 검증 누락, command sandbox, 병렬 claim, 의존성 계약)를 기준으로 보면,
현재는 `agent_runtime`이 **실행 가능한 배포 템플릿 + 기본 런타임 안전장치 + 최소 동시성 보증**으로 이동했다.
다만 여전히 실무형 멀티에이전트 런타임이라 보기엔 `R1(고도화된 command 우회)`와 `R2(원격/분산 파일시스템 claim 정합성)`이 남아 있다.

## Signal

| 항목 | 초기 비판 상태 | PASS-29(현재) 상태 | 근거 |
|---|---|---|---|
| 템플릿 self-contained | Critical | ✅ 닫힘 | `agent_orchestrator.py`, `auto_runner.py`, `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, `agents/qa/TEST-STRATEGY.md`, `agents/independent_auditor/AUDIT-GATE.md`, `SAFETY-GATE.md` 존재 |
| 템플릿 실행성 CI | Critical | ✅ 닫힘 | `tests/test_template_smoke.py` + 워크플로 반영 (`.github/workflows/test.yml`) |
| ToolRunner 샌드박스 | High risk | ✅ 개선되었으나 미완 | `providers/agent_tools.py`의 금지 토큰 탐지/회피 차단 강화, 감사 로그, 회귀테스트 추가. 단, 플랫폼별 고급 우회는 계속 추적 |
| 병렬 claim 정합성 | High risk | ✅ 크게 개선 | `message_queue.py`의 lease marker/claim 검사, `tests/test_template_message_queue.py`에서 동시성·복구 테스트 |
| 분산/원격 FS claim robustness | High risk | ⚠️ 미해결 잔여 | 본체 테스트는 로컬 FS 기준. 원격 FS 경합/지연/rename 실패 시나리오 정량 검증은 다음 사이클 |
| 의존성 계약 | Medium | ✅ 닫힘 | `pyproject.toml` extras 분리, provider lazy import 정책 반영, `tests/test_provider_import_contract.py` |
| 멀티에이전트 실시간 협업 UX | Medium | ✅ 부분 개선 | `agent_worker`/`auto_dispatch`/이벤트 기반 감시(`watch_fs`) 및 observer/루프 체계 정비 |
| 네이티브 플랫폼 통합(Claude/Codex 등) | Medium | ⚠️ 제한적 | `claude.md` 경계/bridge 표기 문서화 수준은 있으나, 원클릭 통합 경로는 부분 단계 |
| 검증 루프(self-improvement) | Medium | ✅ 부분 개선 | `eval_harness`, 실패 재현/치료성 경향은 증가했으나 자동 회귀 게이트 확장 여지는 남음 |

## What changed since earlier critical review

- `templates/project` 누락 산출물을 사실상 모두 복구해 실행성 단절을 해소했다.
- 템플릿을 설치 후 `agent_orchestrator.py`, `agent_worker.py`, `auto_runner.py` 실행 경로를 CI에서 직접 수행한다.
- `command` 계층은 다중 우회 케이스(인코딩/토큰 변형) 테스트를 넣어 막는 방향으로 진화했다.
- 메시지 큐는 단일 winner 보장/중복 reply 억제 방향으로 고도화돼, 단일 프로세스뿐 아니라 multiprocessing 병렬에서도 검증되었다.
- 의존성은 provider optional/extra 중심으로 정리되어 클린 환경에서의 smoke 경로가 안정화됐다.

## Remaining gaps (re-compare)

- `R1`: 명령 실행 보안은 "대부분 차단"이었고, “정답”이 아니라 "지속 갭 추적 상태"이다.
  - 특히 PowerShell/CMD 혼합 인코딩/중첩 치환/환경변수 치환 우회 시나리오 확대 필요
- `R2`: claim lease 파일은 OS-local atomic create 기반이지만, SMB/NFS 류 원격 파일시스템의 lease race를 모사한 테스트는 아직 없다.
- `R3`: 실전 멀티에이전트 운영의 "공유 메모리/telemetry/replay"는 일부 구현은 있으나 비교적 약한 편.

## Current Verification

- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q`
  → `138 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_smoke.py tests/test_template_message_queue.py tests/test_template_agent_tools.py tests/test_provider_import_contract.py tests/test_doctor.py -q`
  → `43 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli publish-check --root . --check`
  → `findings=0`

## Decision

- 이번 pass에서는 구현 변경 없이 `review` 증적을 남겼다.
- 다음 사이클에는 사용자 요청대로 이전 비판 피드백의 **R1/R2를 1차 닫는 방향**으로 진행한다:
  1. command sandbox 고급 우회 정량 테스트(Windows/Powershell/CMD) 확장
  2. 원격/분산 파일시스템에서 claim lease race/recover 시뮬레이션 테스트
  3. 기존 항목을 동일 포맷으로 PASS-30에서 재점검

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-28.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-final-comparison-pass-26.md`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `tests/test_template_message_queue.py`
- `tests/test_template_agent_tools.py`
