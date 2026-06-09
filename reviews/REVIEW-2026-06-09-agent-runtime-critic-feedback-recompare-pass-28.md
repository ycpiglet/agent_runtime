# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-28

## Bottom Line

초기 비판 리뷰(템플릿 완결성·템플릿 검증·보안 샌드박스·병렬 claim·의존성 정합성)를 기준으로 비교한 결과,
`PASS-28`에서 **템플릿 실행성/CI 게이트/의존성 측면은 실질적 개선이 확인**되었고,
**우회 방어의 극단 벡터**와 **분산 파일시스템 기반 race-safe 검증의 정량성**만이 남은 주요 미결 항목이다.

## Original Critic Priority Snapshot (from prior review)

- 즉시 수정 필요: 1) 템플릿 self-contained 보강, 2) 템플릿 smoke CI, 3) ToolRunner command 샌드박스 정비, 4) 병렬 claim 재검증.
- 보강 권장: 5) provider 의존성 분리 + lazy import.

## Signal: Initial Critic vs CURRENT (PASS-28)

| 항목 | 초기 비판 상태 | PASS-28 현재 상태 | 근거 |
|---|---|---|---|
| 템플릿 self-contained | 누락 파일(`orchestrator_safety_gate`, `pipeline`, `task.schema`)로 동작 실패 가능 | 템플릿 산출물 정합성 보완 후 core 스크립트 의존성 확보 | 템플릿 파일/스키마 정비 증거 + smoke 경로 |
| 템플릿 CI 누락 | 패키지 테스트만 통과, 동기화 산출물은 미검증 | 템플릿 sync 후 핵심 스크립트 실행/흐름을 검증하는 테스트 체인 존재 | `tests/test_template_smoke.py`와 기존 smoke 연동 |
| ToolRunner sandbox | `python/py`, `git mutable`, 인코딩 우회로 임의 실행 우려 | 단일·중첩 인코딩 금지 토큰 탐지 강화, 우회 회귀 테스트 추가, audit 기반 차단 증거 보강 | `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`, `tests/test_template_agent_tools.py`, `tests/test_doctor.py` |
| 병렬 claim 정합성 | read-modify-write에 의한 중복 claim/reply 위험 | 핵심 경합 시나리오에서 단일 winner 보장 강화 | `src/agent_runtime/templates/project/scripts/message_queue.py`, `tests/test_template_message_queue.py` |
| 의존성 계약 | `pyproject` 선언 불일치, import-time 크래시 가능성 | 선택형 extras + provider import 게이트 정리 방향은 정합성 확보 단계 진입 | `pyproject.toml`, provider lazy/selection 라우팅 |

## What changed since last comparison

- `ToolRunner`의 forbidden-token 검사 로직을 다단계 URL 디코드 후보 집합 기반으로 변경해 다중 인코딩 우회 탐지력을 높임.
- 우회 회귀 테스트 추가 (`multistep_decoding_bypass`): 중첩 `%` 인코딩, 제어문자/분기 조합 등 탐지 케이스 고정.
- REVIEW 사이클 문서화:
  - `reviews/REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-post-pass-27-recompare.md`

## Current Verification Snapshot

- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_template_agent_tools.py -q` → `14 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_template_message_queue.py tests/test_doctor.py tests/test_template_smoke.py -q` → `26 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests -q` → `138 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m agent_runtime.cli sanitize --root . --check` → `findings=0`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m agent_runtime.cli publish-check --root . --check` → `findings=0`

## Remaining gaps (recompare result)

- `R1` 극한 command 우회 벡터: 멀티엔진(CMD/PowerShell) 고급 조합, 환경변수/리다이렉션/인코딩 연쇄의 완전 수치화가 추가로 필요.
- `R2` 분산/원격 FS claim 강건성: stale lease 회수, rename 충돌, 네트워크 지연 하에서의 deterministic 실패 모드 검증이 추가로 필요.

## Decision

- 다음 단계에서 리스크는 `R1`, `R2` 두 항목으로 고정한다.
- 이후 `REVIEW-...` 문서는 매 패스마다 **동일 5개 항목**(템플릿 완결성·템플릿 CI·샌드박스·claim 정합성·의존성 계약)로 재채점한다.

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-comparison-record.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-post-pass-27-recompare.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_agent_tools.py`
- `tests/test_template_message_queue.py`
