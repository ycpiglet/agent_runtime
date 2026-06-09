# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-14

## Bottom Line

`pass-13`에서 닫았던 핵심 공백(템플릿 자체 완결성, 템플릿 스모크/의존성, `doctor` 진입점)은 현재 **운영 수준 기준으로 안정적으로 정착**됐다.
지금 남은 갭은 사용자가 말한 “좋은 피드백의 본질”인 **실전 병렬 런타임 신뢰성**(분산 환경 claim/우회 경로)과 **실행 후 교정 루프 자동화**다.

즉, “문서상 아키텍처는 좋아졌다”에서 “운영 중 실패를 자가완화한다”로 가는 마지막 한 단계의 갭이 선명해졌다.

## Signal

- 기준 문서:
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md` (초기 비판 기준)
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-13.md` (이전 재비교)
- 최신 검증(2026-06-08, Windows/Python310):
  - `agent_runtime.cli --help` → `doctor` 서브커맨드 존재
  - `PYTHONPATH=src python -m pytest tests/test_doctor.py tests/test_template_smoke.py tests/test_template_message_queue.py tests/test_template_agent_tools.py -q`
    - `24 passed`
  - `PYTHONPATH=src python -m pytest tests -q`
    - `121 passed`

## 비교 평가 (Baseline vs Now)

| 항목 | 초기 비판 점수/판정 | pass-13 | pass-14(현재) | 상태 |
|---|---|---|---|---|
| 템플릿 자체 완결성 (`orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`) | critical | 해결 | 해결 | ✅ 유지 |
| 템플릿 CI 실제 검증 | critical | 개선됨 | 유지 | ✅ 템플릿 스모크가 테스트/CI에 반영 |
| ToolRunner 보안 경계 | high risk | 부분 해결 | 부분 해결 | ⚠️ 기본 차단은 개선, 고급 우회 패턴 완전 차단은 미완 |
| 메시지 claim 병렬 안전성 | high risk | 부분 해결 | 부분 해결 | ⚠️ 로컬 race/스테일 회복은 있음, 분산 FS 검증 미완 |
| provider 의존성 계약 | medium | 해결 | 해결 | ✅ extras/lazy import 상태 유지 |
| 운영 진단 진입점 (`doctor`) | missing | 해결 | 해결 | ✅ `agent_runtime doctor` 제공, 체크 항목 점증 |
| 누락된 템플릿 문서 참조 (`AUDIT-GATE.md` 등) | weak | 해결 | 해결 | ✅ 템플릿에 문서 파일 추가 |

## What Changed Since Last Recompare (pass-13 → pass-14)

1. **최신 기준 재검증 재확인**
   - `doctor`, 스모크, 메시지 큐, 도구 가드 테스트 모두 통과된 상태를 재확인.
2. **비교 리뷰 산출물 추가**
   - 지금 요청으로 “초기 비판 vs 구현 후”를 다시 텍스트 증적으로 고정.
3. **운영 관점으로 판단 축소 정리**
   - 기존의 “많은 항목을 다 안 된 상태”가 아닌, **남은 미결 포인트를 정확히 2개로 압축**.

## Remaining Gaps (요약)

1. **분산 환경 claim 신뢰도 완성**
   - 현재 큐는 단일/로컬 파일시스템 기준 강건도가 높고 stale recovery 테스트가 있지만,
     NFS/네트워크 볼륨·시간 오차·재시도 경합에서의 일관성은 아직 검증 안 됨.
2. **보안 우회 케이스 확장**
   - `python -c`, `git commit/checkout/restore/stash`, `pip` 등 고위험은 차단되었으나,
     인코딩/쉘 다중단계 조합으로 경유해 우회되는 변형 패턴을 회귀 테스트로 추가해야 함.
3. **진단 결과의 자동 보정 루프 미완**
   - `doctor`는 문제 탐지까지는 되지만, 검사 실패 → 수정안 제안/자동복구까지는 별도 구현이 필요.

## Decision

- 리뷰 관점에서: “초기 비판”이 `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`에 원문 보존되어 있고, 이를 기준으로 현재의 달성도를 `pass-14`에 정량적으로 남김.
- 다음 단계는 위 3개 미결 사항을 순차적으로 처리하면, “공개 배포 자동화 코어”에서 “실전 멀티에이전트 런타임”으로 넘어가는 구간을 닫을 수 있다.
