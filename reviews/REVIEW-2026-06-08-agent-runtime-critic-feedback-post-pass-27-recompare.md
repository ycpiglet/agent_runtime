# REVIEW-2026-06-08-agent-runtime-critic-feedback-post-pass-27-recompare

## Bottom Line

초기 비판 리뷰를 기준으로 본 `agent_runtime`은 **실행성·안전장치·의존성 계약**에서 가시적으로 개선되었고,
현재는 남은 리스크가 “극한 command 우회”와 “분산 파일시스템/락 타임아웃 정량성”로 줄어든 상태다.

## Signal (초기 비판 vs PASS-27 vs 현재 갱신)

| 항목 | 초기 비판(요약) | PASS-27 기준 상태 | 현재 갱신 상태 | 판정 |
|---|---|---|---|---|
| 템플릿 self-contained 결함 | 핵심 런타임 파일 누락으로 즉시 깨질 수 있음 | `orchestrator_safety_gate`, `pipeline`, `schemas/task.schema.json`, 핵심 가드 문서/claim 스키마 기반 정비 | 템플릿 기본 산출물 존재 확인, 템플릿 smoke에서 실행 + dummy 메시지 처리까지 통과 | ✅ 닫힘 |
| 템플릿 CI 미검증 | 패키지 테스트 통과해도 배포 산출물은 깨질 수 있음 | `tests/test_template_smoke.py` + 워크플로 반영 | `tests/test_template_smoke.py` 포함 5/5 pass 유지, 스크립트 help/worker 처리 경로 검증 | ✅ 닫힘 |
| ToolRunner 샌드박스 | python/python3/pip/git mutate 경로로 우회 가능 | 금지 토큰/명령 확대, 감사로그 강화, 테스트 추가 | `%NN`·here-string 등 추가 우회 패턴 차단 테스트 추가, `doctor`가 denied command의 audit 기록 존재 강제 | 🟡 부분 개선 |
| 멀티워커 claim 병렬성 | read/modify/write로 중복 claim 및 중복 답변 위험 | claim 원자성 강화, 병렬 회귀 확보 | malformed claim 자동회수 + 동시 claim/recover 혼합 경합 테스트로 단일 winner 보장 강화 | ✅ 닫힘 |
| 의존성/의존성 계약 | provider 의존성·lazy import 미흡 | `pyproject` extras 및 provider import 구조 정리 | 템플릿 문맥에서 추가 보강 지속 필요하나, 기본 계약은 실측 테스트로 정합성 가시화됨 | ✅ 닫힘 |

## What Changed Since Previous Recompare

- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
  - command 우회 패턴에 `%XX` 인코딩 탐지와 PowerShell here-string 변형 차단 패턴 추가
- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - 손상된 claim JSON을 즉시 `{}`로 처리해 `claim_message`가 stale로 회수되도록 동작
- `src/agent_runtime/doctor.py`
  - ToolRunner 검증에서 “차단된 명령의 audit 엔트리 존재”까지 의무화
- `tests/test_template_agent_tools.py`, `tests/test_template_message_queue.py`, `tests/test_doctor.py`
  - 우회 벡터 + malformed claim 복구 + audit 무결성 테스트 보강

## Current Verification

- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_message_queue.py tests/test_template_agent_tools.py tests/test_doctor.py -q`
  → `34 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_smoke.py -q`
  → `5 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m agent_runtime.cli publish-check --root . --check`
  → `findings=0`

## Remaining Gap (explicit)

- CMD/PowerShell 고급 우회 문자열 조합(중첩 인코딩, 환경변수 치환 연쇄, 레거시 인코딩/리다이렉션 조합)에 대한 fuzz·property 기반 회귀는 아직 미흡.
- 원격/네트워크 파일시스템에서 `rename`/잠금/lease 경쟁 시나리오에 대한 실증 주입 테스트가 부족.

## Decision

다음 단계는 위 `Remaining Gap` 두 개를 **정량 테스트로 고정**하면 된다.
PASS-27 이후 비교용 기준은 이 문서를 기준으로 다음과 같이 적용한다: 두 남은 항목이 모두 green되어야 “초기 비판 피드백에서 핵심 미해결 항목 0건”으로 판단한다.

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-comparison-record.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-crit-feedback-final-comparison-pass-26.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-27-review-cycle.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `src/agent_runtime/doctor.py`
- `tests/test_template_agent_tools.py`
- `tests/test_template_message_queue.py`
- `tests/test_doctor.py`
- `tests/test_template_smoke.py`
