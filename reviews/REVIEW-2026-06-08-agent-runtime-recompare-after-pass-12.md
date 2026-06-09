# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-12

## Bottom Line

초기 비판 리뷰의 핵심은 **템플릿 실행 완결성**, **템플릿 산출물 CI**, **의존성 계약**이 모두 달성됐다면,
현재는 여전히 `agent_runtime` 패키지 단에서 실행 가능한 **통합 진단 진입점(doctor)** 미비가 가장 큰 공백이다.
보안 샌드박스와 병렬 claim은 “개선됨” 단계는 맞지만, **공유 파일시스템 병행성 및 고급 우회 패턴**까지 완전히 닫은 단계는 아니다.

## Signal

- 기준 문서
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-11.md`
- 최신 근거 (2026-06-08)
  - `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q` → `116 passed`
  - `tests/test_template_smoke.py` 실행: 템플릿 스크립트(help/json) + 더미 메시지 1건/복수 처리 + stale claim 복구 path 통과
  - `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli --help` 결과에 `doctor` 하위 명령 없음
  - `src/agent_runtime/cli.py`에 `doctor` 파서/dispatch 미추가 상태

## Insight

1. 작업 후 정량 변화는 분명하다. 이전에 `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 누락으로 깨지던 핵심 경로가 폐기되고, 패치된 smoke/queue 테스트로 “클린 host에서 동작”이 증명됐다.
2. 하지만 운영 진단의 단일화가 빠져 있어, "문제가 난 뒤 스스로 진단/수선 제안" 단계가 약하다. 이는 `release-preflight` 계열의 배포 전 점검과는 별개다.
3. 보안/병렬성은 “로컬 다중 프로세스/테스트 셋 기반” 개선 단계에 있고, 네트워크 FS·원격 볼륨·복합 command 우회와 같은 현실 공격면은 아직 다음 단계 위험.

## Decision

### 초기 비판 항목 재평가 (현재 기준)

| 항목 | Pass-11 판정 | Pass-12 판정 | 근거 |
|---|---|---|---|
| 템플릿 배포 자체 완결성 | 해결 | 해결 | 템플릿 필수 파일 동작 경로 보강 및 smoke 통과로 패키지/템플릿 간 실행 경로 연동 안정화 |
| 템플릿 CI 미검증 | 해결 | 해결 | `.github/workflows/test.yml`에 `tests/test_template_smoke.py` 반영, 더미 메시지 처리 + 스크립트 실행 검증 |
| ToolRunner command guard | 부분 해결 | 부분 해결 | `ci/owner/research` 프로파일 분기, `python -c`, `py -c`, `git commit/checkout/restore/stash`, `pip` 차단 강화 |
| 병렬 claim 안전성 | 부분 해결 | 부분 해결 | claim/recover/reply 중복 방지 테스트 + 스테일 claim 복구 루틴 존재, 다중 호스트/공유 FS 미실시 |
| 의존성 계약 | 해결 | 해결 | `pyproject.toml` extras 및 provider lazy import 반영, dummy 경로 의존성 실패 감소 |
| host 진단 진입점 (`doctor`) | 미구현 | 미구현 | `cli.py` help에는 `doctor` 없음 |

### 남은 미비점 (다음 재평가에서 우선 검증)

1. `agent_runtime doctor --root <host> --check` 구현: 템플릿 필수 파일·lock·message queue/stale claim·command policy·provider 설정 상태 한 번에 진단.
2. 공유/네트워크 파일시스템 기반 claim 경쟁성 통합 테스트.
3. `run_command` 고급 우회 테스트 확장(토큰 조합·인코딩·shell escape-like 패턴).
4. 실행 메트릭/재시도율/오류율 루프를 붙인 자체 개선 루프(자동 회귀 증거) 확대.

## Recommendation

- 다음 사이클은 `doctor`를 첫 우선순위로 넣고, 이후에 claim의 분산 FS 검증과 `run_command` 고급 우회 테스트를 붙여야 한다.
- 즉, 이번 라운드 기준으로는 “공개 배포·동기화 코어”는 안정적이지만, “현장 진단 가능한 멀티에이전트 런타임”으로의 점프는 아직 1단계 미만이다.
