# REVIEW-2026-06-08-agent-runtime-critic-feedback-final-comparison-pass-26

## Bottom Line

초기 비판 리뷰의 핵심 5개 항목은 **실행성/거버넌스 방향은 큰폭으로 정착**되었고, 핵심 이슈 중 4개는 닫혔습니다.
남은 미비는 주로 **플랫폼 기반 command sandbox 극한 우회**와 **분산 파일시스템 환경의 claim 정량 검증**입니다.

## Signal

| 항목 | 초기 비판 상태(요약) | PASS-26 상태 | 현재 근거 |
|---|---|---|---|
| 템플릿 self-contained 결함 | `orchestrator_safety_gate.py`, `pipeline.py`, `task.schema.json`, 메시지 큐/문서 누락 | **해결** | 템플릿 산출물 보강 완료 (`src/agent_runtime/templates/project/scripts/orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, `message_queue.py`, 기본 문서 추가), template smoke 테스트로 검증 |
| 템플릿 CI 미검증 | 패키지 테스트 통과해도 배포 템플릿은 깨질 수 있음 | **해결** | `.github/workflows/test.yml` + `tests/test_template_smoke.py`로 sync 후 핵심 스크립트 실행 및 더미 메시지 처리 검증 |
| ToolRunner 샌드박스 취약 | `python -c`, 임의 스크립트 실행, mutable git로 우회 가능 | **부분 개선(중요 개선)** | `agent_tools.py` profile 정책 강화 + 우회 패턴 차단 + 감사로그 + 회귀 테스트 추가. 다만 cmd/powershell 고급 우회 케이스는 지속 보강 필요 |
| 병렬 claim 경합 | read-modify-write 기반 중복 claim/중복 reply 가능성 | **해결(강화됨)** | `message_queue.py` 도입 + 병렬 claim/reply 회귀 (`tests/test_template_message_queue.py`), Pass-25에서 stale frontmatter 오판 완화 |
| 의존성 계약 불명확 | optional deps 미분리, top-level import 실패 가능 | **해결** | `pyproject.toml` extras 분리, providers lazy import화, `tests/test_provider_import_contract.py` 추가 |

### 점수 비교(비교적 추정)

| 영역 | 초기 비판 | PASS-26 | 변화 |
|---|---:|---:|---|
| 공개 배포 위생 | B+ | B+ | 유지 |
| sync/update 안전성 | B+ | B+ | 유지 |
| 템플릿 실행 완성도 | D | B- | 상당 개선 |
| 병렬 멀티에이전트 병행성 | C- | B- | 개선 |
| 보안 샌드박스 | D+ | C | 실질 개선, 미완성 잔여 |
| 자가 개선 루프 | C- | C | 유지(검증 체계 강화로 실질성 상승) |

## Current Verification

- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q`
  → `134 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_smoke.py tests/test_template_message_queue.py tests/test_template_agent_tools.py tests/test_provider_import_contract.py -q`
  → `31 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_message_queue.py -q`
  → `11 passed`

## Insight

초기 비판의 대부분은 “패키지 테스트만 보는 구조적 위험”이었다.
PASS-26에서 실행성 결함은 거의 종료 단계로 넘어갔고, 병렬 claim은 실제 동시성 보증 방향으로 바뀌었습니다.

현재 남은 공백은 “강화된 우회 공격/셸 변형”과 “원격 FS(또는 경합 주입)에서의 lease 정당성 증거”로 수렴했습니다.

## Decision

### 이 단계에서 승인 기준을 반영해 남은 R리스크

1. `R1-Command`: PowerShell/CMD 고급 우회(인코딩·중첩 따옴표·환경변수/토큰 치환 조합)에 대해 정량 회귀 테스트를 추가한다.
2. `R2-Queue`: 분산 파일시스템/네트워크 지연 하에서 claim reclaim 및 stale 회수 정책을 주입 테스트로 검증한다.
3. `R3-Policy`: owner/research/ci 프로파일 정책 위반을 감사 로그와 UI/CI 리포트에서 자동 매핑한다.

### 다음 리뷰에서 비교할 기준(고정)

- 위의 R1~R3가 각 1개 이상 패스되면 “critic 4개 미해결” 상태를 닫고, 멀티에이전트 런타임 전환 판단으로 진행.

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-comparison-record.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-24-critic-feedback-full-comparison.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-claim-backup-validity-comparison-pass-25.md`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `tests/test_template_message_queue.py`
- `tests/test_template_smoke.py`
