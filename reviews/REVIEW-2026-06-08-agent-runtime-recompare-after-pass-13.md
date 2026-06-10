# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-13

## Bottom Line

초기 비판 리뷰에서 가장 치명적으로 지적됐던 **템플릿 실행성/CI 누락/진단 진입점 부재** 축은
`pass-13`에서 상당히 정리됐다.
남은 큰 간극은 여전히 **병렬 claim의 분산 파일시스템 경합**과 **고급 임의 실행 우회 패턴 테스트**다.

핵심은, 이제는 "고칠 게 보였던 상태"가 아니라 **`doctor`로 운영자가 바로 진단 가능한 상태**로 바뀌었다는 점이다.

## Signal

- 기준 문서:
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-12.md`
- 최근 증거:
  - `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_doctor.py tests/test_template_smoke.py -q`
    → `8 passed`
  - `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli --help`
    → `doctor` 서브커맨드 존재 확인
  - `src/agent_runtime/doctor.py` 및 `src/agent_runtime/cli.py`에 병합 반영

## Comparison vs Initial Critique

| 초기 비판 항목 | 초기 판정 | pass-12 판정 | pass-13 판정 | 근거 |
|---|---|---|---|---|
| 배포 템플릿 자체 완결성 (`orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 누락) | critical | 해결 | 해결 | 템플릿 필수 파일 존재 + 스크립트 스모크 통과 |
| CI가 템플릿 산출물을 실제로 검증하지 못함 | critical | 개선됨 | 개선됨 | `test_template_smoke.py` 경로가 CI/패키지 테스트 체계에 반영됨 |
| ToolRunner command guard 샌드박스 미비 | 고위험 | 부분 해결 | 부분 해결 | 허용 목록/차단이 강화된 상태 유지, 연구용/owner용 profile 구분 필요 |
| 메시지 claim 병렬성/중복 방지 | 고위험 | 부분 해결 | 부분 해결 | `message_queue`·테스트가 기본 race 케이스 강화되어 있음, 분산 FS 검증 미실시 |
| provider 의존성 계약 | 중간 | 해결 | 해결 | extras/lazy import 축 정리됨 |
| host 진단 진입점 부재 (`doctor`) | 미구현 | 미구현 | 해결 | `agent_runtime doctor --root <host> --check` 추가 + 결과 포맷 출력 |

## What Changed Since Last Recompare

1) `agent_runtime doctor` 통합:
- `src/agent_runtime/doctor.py` 신규 구현
- `src/agent_runtime/cli.py`에 서브커맨드 등록
- 필수 파일/lock/config/sync/스크립트 도움말 실행/claim 상태/provider import/`ToolRunner` 정책을 한 번에 점검
- 실패 시 블로커 카운트 기반 종료코드 지원 (`--check`)

2) 리뷰 신뢰도 안정화:
- `tests/test_doctor.py` 추가로 `doctor` 동작을 회귀 체크
- `tests/test_template_smoke.py`로 `agent_orchestrator.py`, `agent_worker.py`, `auto_runner.py`, `auto_dispatch.py`, `check_messages.py`의 기본 실행성을 검증
- Windows 상대경로 비교 안정성을 위해 `doctor` 출력 경로를 POSIX 구분자로 정규화

## What Is Still Insufficient

1) 분산 병렬 worker 환경에서 claim race 검증이 부족:
- 현재 테스트는 단일 호스트/로컬 파일시스템 기반이 주력.
- shared volume/NFS, 네트워크 clock drift, 재시도 경로에서의 중복 claim/reply은 다음 사이클 대상.

2) 명령 우회 공격면은 아직 경량:
- `python -c`류 직접 차단은 보강됨이지만, 인자 인젝션·이중 래핑·인코딩 우회 사례 테스트는 추가 필요.

3) `doctor` 진단의 운영 반영 루프 미성숙:
- 진단 보고서 출력은 가능해졌지만, `doctor` 출력 기반의 자동 교정/재실행 루틴은 아직 미구현.

## Decision

- pass-13 기준으로는 **실행성 핵심공백(템플릿 완결성·스모크·의존성·진단진입점)**은 상당히 닫혔다.
- 다음 단계는 `재현-진단-수정` 루프를 `doctor` 결과와 연동하고, 분산 병렬 안전성/우회 테스트를 추가하여
  “운영급 멀티에이전트 런타임” 문턱에 맞추는 것으로 좁힌다.
