# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-22-critic-feedback-continuation

## Bottom Line

초기 비판 리뷰(`user_action`)에서 제시된 핵심 결함 5개는 이 작업 세트에서
실질적으로 대부분 해소되어, 현재는 **템플릿 완결성 + 템플릿 smoke CI +
메시지 claim 정합성 + 의존성 계약 + ToolRunner 강화**가 운영 가능한 상태로
수렴했다.
남은 큰 리스크는 **보안 경계(플랫폼 특화 셸 우회)와 분산/원격 FS에서의
claim 정합성 정량 입증**뿐이다.

현재 상태는 “공개 배포 가능한 자동화 코어”에서 “실사용형 멀티에이전트 런타임”으로 가는 마지막 1~2단계 구간으로 볼 수 있다.

## Signal

| 항목 (초기 비판 리뷰 기준) | Baseline | PASS-21 상태 | PASS-22 재평가 |
|---|---|---|---|
| 템플릿 자체 완결성 | Critical(누락 파일 다수) | ✅ Closed | ✅ 유지 |
| 템플릿 실행 smoke CI | Critical(미검증) | ✅ Closed | ✅ 유지 |
| ToolRunner sandbox | High(임의 실행 통로) | ⚠️ 일부 완화 | ✅ 부분 완화 유지(추가 남음 존재) |
| 병렬 claim 안전성 | High(중복 claim/reply) | ✅ 크게 개선 | ✅ 유지(동일) |
| 의존성 계약 | Medium(클린 설치 불안정) | ✅ Closed | ✅ 유지 |

### 현재 검증 근거(2026-06-08)

- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q`
  → `132 passed`
- `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_smoke.py -q`
  → `5 passed`
- CI 설정(`.github/workflows/test.yml`)에 템플릿 smoke 단계가 추가됨( `tests/test_template_smoke.py` )
- `tests/test_template_agent_tools.py`, `tests/test_template_message_queue.py`,
  `tests/test_template_smoke.py`에서 각각 임계 보안/병렬성/엔드-투-엔드 시나리오를 직접 검증

## Insight

1. 초기 리뷰의 “좋은 설계가 실행 경로에서 깨지는 문제”는 해소됐다.
   `agent_orchestrator.py`, `agent_worker.py`, `auto_runner.py`, `check_messages.py`
   실행 경로가 템플릿 내부에서 자립적으로 동작한다.
2. 메시지 claim은 단일 호스트 FS 기준에서 **중복 답변을 실질적으로 막는 수준**으로 정착했고, stale 회수/소유자 검증도 테스트로 고정됐다.
3. ToolRunner는 `ci/owner/research` 프로파일과 allowlist 기반으로 강해졌고,
   금지/허용 차이를 명시적으로 감사(`command_audit`)하게 되어 운영 가시성이 생겼다.
4. 지금 남은 미비점은 “원칙을 다 더한 수준”이 아니라 “실전 환경 변주 대응”이 남은 단계다.
   즉, 규칙 자체는 좋아졌고, 정책-프로토콜 매핑의 정밀화가 다음 우선순위다.

## Decision

### 이번 재평가에서 `pass-21` 대비 유지/개선

- `providers/agent_tools.py`
  - `ToolRunner`의 프로파일 기반 정책 적용 유지, 금지 패턴 확대
  - `python -c`, `py -c`, `python -`, 임의 파이프/리디렉션 토큰 차단
  - `command_audit`(허용/차단 로그)와 bounded audit ring 유지
- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - claim/ownership/claim marker 기반 경쟁 제어 및 stale recovery 동작 유지
  - reply path에서 소유자 불일치 시 답변 불가 처리 유지
- 템플릿 산출물/CI
  - 누락된 핵심 파일 존재성 보완( `orchestrator_safety_gate.py`, `pipeline.py`,
    `schemas/task.schema.json` 및 역할별 참조 문서)
  - CI에서 `sync --apply` + 스크립트 help + dummy 메시지 처리 smoke를 실행
- provider/import 계약
  - lazy import 기반 provider 팩토리화 유지
  - `get_provider("dummy")`가 선택적 의존성 미설치 상태에서 동작, live provider는
    사용자 액션 필요 메시지로 가이드

### 새롭게 재정리된 미비점 (다음 비교 대상)

- **R1. 플랫폼/셸 특화 우회 경로 완전성**
  - 현재 테스트는 일반적인 우회 패턴은 막지만, PowerShell/CMD 환경 특유 인용/환경치환/
    `%COMSPEC%`/`!var!` 류 같은 변형 입력은 증거 기반 정량화 필요.
- **R2. 분산/원격 FS 정합성**
  - 현재 claim 검증은 원칙적으로 로컬 FS 위주의 동시성 증거가 강함.
  - NFS/SMB/네트워크 FS에서의 atomic create + stale 회수 동작은 별도 회귀 테스트가 필요.
- **R3. 운영 정책 문서와 감사 로그의 1:1 정합성**
  - `owner/research` 허용 확장 시 로그 항목과 조직 정책(승인/의무 감사 항목) 간의
    완전 매핑이 문서/자동 점검으로 남아야 함.
- **R4. 현재 산출물에 대한 sanitize 노이즈**
  - `reviews/*.md`에 로컬 절대 경로가 남아 `sanitize --check`에서 발견됨.
    공개 산출물에서 review 파일이 포함될 수 있다면 민감정보 패턴 제거/패턴 허용 필요.

## Re-score (Baseline 대비 현재)

| Area | 현재 |
|---|---|
| Public release hygiene | B+ |
| Sync/update safety | B+ |
| Template execution completeness | B- |
| Real multi-agent parallelism | B- |
| Security / command sandbox | C- |
| Collaboration/governance design | B |
| Self-improvement loop | C- |

## 참고

- `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-21-critic-feedback-comparison.md`
- `IMPLEMENTATION_PLAN.md`
