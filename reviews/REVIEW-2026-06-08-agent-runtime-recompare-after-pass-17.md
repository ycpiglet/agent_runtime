# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-17

## Bottom Line

`PASS-16` 이후 이번 패스에서 추가 개선은 작지만 결정적이었습니다. 템플릿에 실수로 포함되었던 기본 claim 샘플을 제거하고, `sync --apply`로 생성된 호스트가 "사전 시드된 claim 아티팩트"를 남기지 않는지를 CI-level smoke에서 강제했습니다.

초기 비판 리뷰에서 제기한 핵심 5개 항목은 여전히 동일한 우선순위 순서로 재확인됩니다.

## Signal

- 비교 기준:
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-16.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 실행 증거(현재):
  - `python -m pytest tests/test_template_smoke.py -q` → `5 passed`
  - `C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests -q` → `127 passed`

## 비교 재정렬 (Pass-16 → Pass-17)

| 항목 | Pass-16 | Pass-17 | 상태 |
|---|---|---|---|
| 템플릿 self-contained(필수 파일/스키마) | ✅ | ✅ | 유지 개선 |
| 템플릿 런타임 CI 스모크 | ✅ | ✅ | 유지 |
| `ToolRunner` command 경계 | ⚠️ | ⚠️ | 유지(추가 hardening 테스트 필요) |
| 메시지 claim 병렬 안전성 | ✅(로컬 기준) | ✅(로컬 기준) | 유지 |
| 기본 claim 샘플 오염 제거 | ⚠️(포함됨) | ✅(삭제 완료) | **개선됨** |
| 제공자 의존성 계약 및 lazy import | ✅ | ✅ | 유지 |

### 초기 비판 5개 항목 대비 현 상태

1. **템플릿 완결성 (Critical)**: 이미 해결된 상태를 유지.
   - `orchestrator_safety_gate.py`, `pipeline.py`, `task.schema.json`, `message_queue.py` 존재/동작 보장 지속.
2. **템플릿 검증을 CI에 강제 (Critical)**: 유지.
   - sync, 스크립트 help, 더미 메시지 처리, 이제 claim 시드 결함 검출 테스트까지 포함.
3. **ToolRunner 샌드박스 (High)**: 부분 개선됨.
   - 허용/차단 규칙은 유지되나 `파워셸/셸 특이 경로 우회`는 추가 테스트가 필요.
4. **병렬 claim 중복 (High)**: 로컬 병렬 테스트에서 1개 reply만 생성됨 유지.
   - 다만 분산/원격 FS 환경의 rename/락 동작은 미검증.
5. **의존성 계약 (Medium)**: 개선된 상태 유지.
   - `extras`/lazy import는 패스되나 실제 배포 문서의 설치 가이드 정합성 점검 필요.

## Decision

- 이번 `PASS-17`에서는 **작업 후 "변경되지 않은 상태로 배포 가능한 오염"을 제거**했다는 점이 실제 가치가 큽니다(샘플 claim 삭제 + 스모크 제약 추가).
- 다음 패스에서 추가로 정리할 항목은 `PASS-16`에서 남긴 동일 Top-3입니다:
  - 원격 파일시스템에서의 claim 경쟁/스태일 처리 검증
  - command 우회 패턴(셸 특화 escape/우회) 확장 테스트
  - 자동 개선 루프를 evidence-driven로 강화하는 정량 평가 체계
