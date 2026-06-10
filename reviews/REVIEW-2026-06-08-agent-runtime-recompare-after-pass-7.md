# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-7

## Bottom Line

기존 핵심 비판(템플릿 완결성, 설치 후 실행성, 보안 사일로, 병렬 claim, 의존성 분리)은 현재 `pass-6` 기준으로 `pass-5` 대비 5개 항목 모두 실측 증거를 가진 상태로 진전되었고, 공개 배포용 런타임으로서의 실패모드가 줄었다.
남은 리스크는 `1)` 실제 멀티프로세스 격리 환경에서의 lease/권한 상태 전이 검증, `2)` run_command 정책 프로파일 분리, `3)` 리뷰 산출물 템플릿 형식 정합성이다.

## Signal

### 기준 비교

- 기준: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 직전: `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-6.md`
- 실행 증거: `PYTHONPATH=src` 환경에서 `python -m pytest tests -q` → `107 passed`

### pass-6 기준 5개 핵심 항목 재평가 (원래 비판 리뷰 기준)

| 항목 | 비판 당시 상태 | pass-6 상태 | 현재 판정 |
|---|---|---|---|
| 템플릿 self-contained | `agent_orchestrator.py`, `auto_runner.py`, `agent_worker.py`가 외부 의존 누락으로 실패 가능 | `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 등 핵심 파일 추가 및 템플릿 스모크 강화 | 개선 완료 |
| 템플릿 CI 증명 | 패키지 테스트만 통과하고 배포 산출물 smoke 미검증 | `tests/test_template_smoke.py` 추가로 sync/apply 후 핵심 스크립트 실행 + dummy 메시지 처리 검증 | 개선 완료 |
| command sandbox | `python/py` 및 mutable git 허용 경로가 공격면 | allowlist + 회귀 테스트(`python -c`, `py -c`, pip/git 변형 명령 등) 추가 | 개선 완료 |
| 병렬 claim 안정성 | read/check/write 패턴 기반의 race 가능성 | 메시지 lease/marker 기반으로 동일 메시지 단일 claim 테스트, 중복 reply 테스트 통과 | 개선 완료 |
| provider 의존성 계약 | top-level 임포트 시 optional dep 누락으로 실패 가능 | providers lazy import 전환 + extras 제안/구조 정리 + 계약 테스트 추가 | 개선 완료 |

### 현재 미해결 항목

1. 멀티프로세스/격리 환경에서의 실제 동시성 경계: 현재 `message_queue`는 단일 파일시스템 가정에서의 원자성 검증이 충분하지 않음.
2. `run_command` 정책 분할: 현재도 안전 규칙은 강화되어 있으나, 작업 성격별(`qa`, `ci`, `owner`) 모드/프로파일 분리 문서 및 토글이 없음.
3. 리뷰 체계 정합성: 기존 리뷰 산출물이 `Bottom Line/Signal/Insight/Decision` 형식을 일부만 엄격히 따름.

## Insight

현재 변화는 “패키지 자체 점검 통과”에서 “`sync --apply` 후 실제 실행 증거 보유”로 성격이 바뀌었다. 즉, 기존 리스크의 핵심인 공개 배포 가능성 결함이 실사용 경로에서 검출 가능하게 낮아진 게 핵심이다. 남은 리스크는 운영 상에서의 경계 타당성(동시성/프로파일 분리/문서 체계)로, 이는 코드량보다 운영 정책 정합성에서 추가 작업이 필요하다.

## Decision

- 결정: `pass-7` 목표를 `멀티프로세스 claim+stale 회복`과 `run_command 프로파일 가드 분리`를 우선 반영 대상으로 확정.
- 대기: 다음 스냅샷 전까지 `review` 템플릿 정렬 작업(필수 `Bottom Line/Signal/Insight/Decision`)을 수행하고 해당 형식 준수 상태를 evidence로 남김.
