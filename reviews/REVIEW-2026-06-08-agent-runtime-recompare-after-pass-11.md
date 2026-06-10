# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-11

## Bottom Line

초기 비판 리뷰의 핵심 5개 항목 중 **템플릿 완결성, 템플릿 CI 검증, 의존성 계약**은 안정적으로 닫혔고,
**ToolRunner 샌드박스 + 병렬 claim 안전성**은 “부분적 완료” 상태로 유지된다.
남은 핵심 미완은 `agent_runtime doctor`와 `agent_runtime` 패키지 CLI의 실제 호스트 점검 단일 진입점 부재다.

## Signal

- 기준 문서:
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md` (초기 비판)
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-10.md` (이전 라운드 재비교)
  - `IMPLEMENTATION_PLAN.md` (Phase 6부터 미완 항목)
- 최신 실행 근거:
  - `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q` → `116 passed`
  - `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_smoke.py tests/test_template_agent_tools.py tests/test_template_message_queue.py -q` → `19 passed`
  - `codex status`는 현재 TTY가 아니면 `Error: stdin is not a terminal` 발생. CLI status는 하위 명령 없고 `codex doctor --json`으로 대체 가능.

## Insight

1. 이번 비교에서 가장 큰 변화는 “패키지 단위 통과”에서 “설치 후 호스트 템플릿 실행까지 통과”로 검증 체인이 이동한 점이다. 즉, 기존 false-positive(패키지 테스트만 통과, 템플릿 실행은 깨지는 상태)가 크게 줄었다.
2. 아직도 남는 리스크는 정책 강화의 남은 간극이다. 샌드박스/claim은 테스트로 상당 부분 막았지만, 다중 worker 환경 확장성과 고급 커맨드 우회 케이스는 계속 공격면이다.

## Decision

### 초기 비판 항목 재평가

| 항목 | 초기 판정 | 현재 판정 | 증거 |
|---|---|---|---|
| 템플릿 배포 자체 완결성 | critical | **해결** | `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 존재. `tests/test_template_smoke.py`에서 핵심 스크립트 실행 통과 |
| 템플릿 산출물 CI 미검증 | critical | **해결** | template smoke가 CI에 반영되어 패키지 테스트와 분리로 검증됨 |
| ToolRunner command guard 위험 | high | **부분 해결** | `python -c`, `py -c`, `python -`, `pip`, mutable git 계열은 차단. 다만 우회형 주입 조합은 추가 하드닝 대상 |
| 병렬 claim 동시성 | high | **부분 해결** | `message_queue.py` 기반 테스트로 동시 claim 단일 승자 및 stale 복구 확인. 단, 분산/공유 FS 실제 병목 실험은 미실시 |
| 의존성 계약 누락 | medium | **해결** | optional extra 분리, lazy provider 로드 패턴 정착, dummy 경로 통과 강화 |

### 남은 미비점 (다음 비교에서 우선 체크)

1. `agent_runtime doctor` 런타임 진단 커맨드 미구현 (`src/agent_runtime/cli.py`에 서브커맨드 없음)
2. 분산 파일시스템(공유 볼륨/NFS)에서 `message_queue` claim race 통합 테스트
3. ToolRunner의 고급 우회 패턴(복합 쉘 토큰·인코딩·경로 인젝션) 회귀 테스트 확장
