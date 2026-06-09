# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-24-critic-feedback-full-comparison

## Bottom Line

초기 비판 리뷰(5개 핵심 이슈) 기준으로 이번 PASS-24 구간에서 핵심 방향은 정착되었고,
`agent_runtime`는 **공개 배포 가능한 자동화 코어에서 실전 멀티에이전트 런타임으로 이동**할 수 있는
기본 실행성은 확보했습니다.
다만 보안 샌드박스의 플랫폼별 엣지 케이스와 분산 FS에서의 claim 정합성 정량 검증은
다음 사이클 과제로 남아 있습니다.

## Signal

| 항목 | Baseline (초기 비판 리뷰) | PASS-24 상태 | 핵심 근거 |
|---|---|---|---|
| 템플릿 self-contained | ❌ Critical | ✅ Closed | `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 및 필수 문서/참조 정합성 회복 |
| 템플릿 실행 smoke CI | ❌ Critical | ✅ Closed | `.github/workflows/test.yml`에 템플릿 sync/apply → 핵심 스크립트 help/실행 및 더미 메시지 처리를 포함한 `tests/test_template_smoke.py`가 통합 |
| ToolRunner sandbox | ⚠️ High | ⚠️ 부분 개선 | `python -c`/`py`/`git mutate`/셸 우회 패턴이 다수 차단되고 감사 로그(`command_audit`)가 남지만, PowerShell/CMD 특수 토큰 변형은 추가 검증 필요 |
| 병렬 claim 정합성 | ⚠️ High | ✅ 유지 개선 | `message_queue.py` + `tests/test_template_message_queue.py`로 단일/병행 조건에서 중복 claim/reply를 강하게 억제 |
| 의존성 계약 | ⚠️ Medium | ✅ Closed | `pyproject.toml` extras 분리, 템플릿 provider의 lazy-import 경로 강화, `tests/test_provider_import_contract.py`로 설치 시나리오 검증 |

## Current Verification

- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q`
  → `133 passed`
- `... -m pytest tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_inventory_sync_sanitize.py -q`
  → `114 passed`
- `... -m pytest tests/test_template_smoke.py -q`
  → `5 passed`
- `... -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`

## Insight

1. 템플릿 실행성 결함(누락 파일/문서 오연결)은 크게 줄었고, 런타임 아티팩트가
   패키지 테스트만 통과해도 깨질 수 있다는 이전 위험은 대부분 해소되었습니다.
2. 병렬 처리 관점은 구조적으로 크게 좋아졌으며, 가장 위험한 “중복 claim” 루트는
   현재 테스트로 억제됩니다.
3. 보안은 “정책 존재 + 감사 가능” 단계까지 올라갔고, 최근 패스(23)에서
   셸/토큰 우회 패턴을 추가 차단해 플랫폼 변조 표면을 줄였습니다.

## Decision

### 반영한 변경 요약

- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - 메시지 claim/ownership/claim marker 구조로 병렬 충돌 억제 강화.
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
  - command profile 정책 정비, 위험 명령/우회 패턴 블록 리스트 강화, 감사 로그 강화.
- `src/agent_runtime/sanitize.py`
  - 리뷰 산출물( `reviews/` ) 스킵 정책 반영으로 공개 게이트 안정화.
- `tests/test_template_agent_tools.py`
  - 플랫폼별 토큰 인젝션 회귀(Windows/PowerShell/CMD) 케이스 추가.
- `tests/test_template_message_queue.py`, `tests/test_template_smoke.py`,
  `tests/test_inventory_sync_sanitize.py`, `tests/test_provider_import_contract.py`
  - 실행성/경합/의존성/게이트 회귀 테스트를 문서화된 정책과 동기화.

### 다음 주기에서 반드시 닫을 항목

- **R1 플랫폼 샌드박스 완결성:** `cmd/powershell` 특수 인코딩·중첩 치환·우회 인용 패턴의 추가 정량 회귀.
- **R2 분산 FS claim 정합성:** NFS/SMB류 환경에서 atomic claim/lease 회수 동작별 증거 추가.
- **R3 owner/research 정책-감사 정합성:** 정책 문서와 `command_audit` 결과의 자동 매핑/회귀 검증.

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-20-critic-feedback-retrospective.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-22-critic-feedback-continuation.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-23-command-sandbox-review.md`
