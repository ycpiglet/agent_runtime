# REVIEW-2026-06-08-agent-runtime-critic-feedback-comparison-record

## Bottom Line

이전 비판 리뷰의 핵심 5개 이슈를 기준선으로 삼아 재평가한 결과,
`agent_runtime`는 **템플릿 실행성·의존성·CI 증명** 측면은 통과점으로 이동했고,
남은 미흡점은 주로 **플랫폼별 명령어 우회 방어의 극한 케이스**와 **분산 FS claim 정합성의 정량 검증**으로 좁혀졌다.

## Signal (초기 비판 기준 대비 재비교)

| 항목 | 초기 비판(요약) | 현재 상태 (2026-06-08) | 근거 |
|---|---|---|---|
| 템플릿 self-contained 결함 | `orchestrator_safety_gate`, `pipeline`, `task.schema.json` 누락으로 즉시 실패 | 닫힘 | 템플릿 파일 정합성 복구 및 템플릿 smoke 경로 검증 강화 |
| 템플릿 실행 검증 부재 | CI가 패키지만 통과하고 배포 템플릿은 검증 안 함 | 닫힘 | `tests/test_template_smoke.py` 및 워크플로 연동으로 핵심 스크립트 직접 실행 |
| ToolRunner 샌드박스 약함 | `python`/`git mutate`/쉘 우회로 정책 우회 가능 | 부분 개선 | `agent_tools`에서 위험 토큰 및 명령어 패턴을 대폭 차단, 감사 로그 기록 추가. 다만 PowerShell/CMD 고급 우회는 지속 점검 필요 |
| 병렬 claim 정합성 | read-modify-write 방식으로 중복 claim 위험 | 개선됨 | `message_queue`의 claim marker/소유권 처리 강화 및 동시성 회귀테스트 존재 |
| 의존성 선언/계약 미정 | core/optional 분리 미흡, lazy import 미흡 | 닫힘 | `pyproject` extras 정리, provider import 게이트/테스트 강화 |

## Current Evidence

- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q`
  → `133 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py tests/test_provider_import_contract.py -q`
  → `122 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`

## Insight

1. 초기에서 위험도가 높았던 “배포 템플릿 자체가 깨져서 동작하지 않는다”는 문제는 기본 축으로 해결됐다.
2. 이제 남은 주요 리스크는 “포괄적 명령어 우회 표면(플랫폼별 정교 변형)”과 “원격 파일시스템에서의 클레임 경합 실증”에 집중된다.
3. 비판 피드백을 재활용하기에 좋은 상태가 되었다. 이번 비교 문서는 다음 패스에서 `R1`/`R2` 마일스톤 달성 확인용 베이스라인이다.

## Decision

- 남은 판단 포인트는 다음과 같이 고정한다.
  - **R1**: 플랫폼별 command sandbox 우회 케이스 정량 회귀 강화
  - **R2**: 분산/원격 FS에서 claim-stale/회수 정책을 재현 테스트로 확증
- `reviews/` 이력을 기준선-현재 비교 저장소로 사용하고, 다음 리뷰는 반드시 동일 5개 항목에서 상태 재채점한다.

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-24-critic-feedback-full-comparison.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-23-command-sandbox-review.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-22-critic-feedback-continuation.md`
