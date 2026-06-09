# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-16

## Bottom Line

`PASS-15` 이후 현재 상태는, 초기 비판 리뷰의 핵심 리스크 5개(템플릿 완결성/CI 스모크/명령샌드박스/병렬 claim/의존성 계약) 중
네 가지만은 실행 증거로 상당히 정리됐다.

남은 것은 `실전 운영`에서 드러나는 경계 조건(분산 FS claim 충돌, 우회 패턴 완전 차단, 지속적 실증 루프)이다.

## Signal

- 비교 기준:
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-15.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 핵심 실행 증거(현재):
  - `python -m pytest tests/test_template_smoke.py -q` → `4 passed`
  - `python -m pytest tests/test_template_agent_tools.py -q` → `9 passed`
  - `python -m pytest tests/test_template_message_queue.py -q` → `8 passed`
  - `python -m pytest tests/test_doctor.py -q` → `8 passed`
  - `python -m pytest tests -q` → `126 passed`
- 실제 코드 반영:
  - 템플릿 자가완결 파일 추가: `scripts/orchestrator_safety_gate.py`, `scripts/pipeline.py`, `schemas/task.schema.json`, `scripts/message_queue.py`
  - 핵심 워크플로우 hardened: `templates/project/scripts/providers/agent_tools.py`, `agent_worker.py`, `auto_dispatch.py`, `providers/__init__.py`
  - 진단/치유 기능 추가: `src/agent_runtime/doctor.py`, `src/agent_runtime/cli.py`
  - CI 템플릿 검증 포함: `.github/workflows/test.yml`

## 재비교 요약 (Baseline/Pass-15 → Pass-16)

| 항목 | Pass-15 | Pass-16 | 상태 |
|---|---|---|---|
| 템플릿 파일 누락(필수 스크립트/스키마) | 대부분 복구 | 신규 파일 포함으로 정합성 고정 | ✅ |
| `sync --apply` 후 템플릿 실행성 | smoke로 검증됨 | sync 후 core 스크립트 help + 1개/멀티 worker 동작까지 통과 | ✅ |
| CI에서 템플릿 런타임 검증 | smoke 단계 일부 반영 | CI에 `tests/test_template_smoke.py` 별도 단계 추가 | ✅ |
| ToolRunner 정책 경계 | profile 기반 allowlist 도입 | git/python 경계 강화, 토큰/인젝션 패턴 테스트 추가 | ⚠️(기본 경계는 유효, 우회 테스트 확장 필요) |
| 메시지 claim 병렬성 | lease 및 테스트 추가 | 소유자/식별자 검증, stale recover, 멀티스레드·멀티프로세스 claim/race 테스트 | ✅(로컬 기준) |
| provider 의존성 계약 | 부분 정리 | optional extras + lazy import 및 누락시 액션안내 | ✅ |
| 운영 진단/치유 진입점 | 체크만 존재 | `doctor --repair` 추가 (누락 디렉토리 복구 + stale claim 정리) | ✅ |
| 보안/안전 문서 참조 | 누락 이슈 존재 | `agents/...` 가이드 파일 복원, runtime docs 정합성 확보 | ✅ |

## 남은 비교 항목 (다음 패스에서 유지/점검할 미비점)

1. **분산/원격 파일시스템 병행성**
   - 현재 claim 안전성은 로컬 FS 기준 실측에서 강함.
   - NFS/SMB/네트워크 볼륨에서 rename/시간오차가 결합된 claim 시나리오는 아직 증거가 없음.

2. **명령 우회 경로 완전성**
   - `agent_tools.py`는 `& | ; < > \` $, $(), && || \n \r` 등은 차단.
   - 파워셸/셸별 escape 조합은 OS별로 추가 검증이 더 필요.

3. **실행 후 자기개선 루프**
   - 기본 진단/치유는 있음. 그러나 실패 샘플 기반 재학습·재평가 파이프라인은 아직 구조적 제어가 약함.

## Decision

- 비판 포인트의 기록은 `PASS-16`으로 고정했고, “뭐가 개선됐는지/뭐가 미비한지”를 재평가 항목으로 분리해 남김.
- 다음 스텝은 위 3개 미비 항목을 우선순위로 고치면, 초기 리뷰 기준에서 “실행성 중심 멀티 에이전트 런타임” 분류가 현실적으로 가능해짐.
