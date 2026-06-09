# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9

## Bottom Line

`pass-9`에서는 `pass-8`의 미해결 항목 중 **1) research 프로파일의 실물 분리**와 **3) 다중 메시지/재시도 경로 검증**을 실행 증거로 해결했습니다.
현재 남은 리스크는 `agent_worker` 내부에서 노드/드라이브 분산 환경의 claim 회복 메커니즘(네트워크 FS 특성) 검증만 남아 있습니다.

## Signal

- 기준:
  - 직전: `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-8.md`
- 실행 증거:
  - `C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_template_smoke.py -q`
    → `15 passed`
  - `C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests -q`
    → `112 passed`

### pass-8 → pass-9 비교

| 항목 | pass-8 판정 | pass-9 판정 | 근거 |
|---|---|---|---|
| ToolRunner 프로파일 구분 | owner/ci/research 구분 개념은 있었으나 research가 ci와 실질 동일 | 연구모드(`research`)가 실제로 `agent_worker.py --help`, `auto_runner.py --help` 를 허용하고 `ci`는 차단 | `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`, `tests/test_template_agent_tools.py` |
| 다중 메시지/재시도 경합 증거 | 멀티프로세스 claim 1승자만 검증, 메시지 1건 처리 위주 | 스모크에서 3개 메시지 일괄 처리 + stale claim 자동 회복 확인 + 회신 1:1 매핑 확인 | `tests/test_template_smoke.py` |
| Claim 복구 운용성 | 단위 테스트에 recovery API 검증 | 스모크에서 stale claim 파일이 있는 상태에서도 worker가 실제 처리 복구 후 종료되는 흐름 검증 | `tests/test_template_smoke.py` |
| 리뷰 형식 정합성 | pass-8 형식 준수 | pass-9 형식 준수 | `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9.md` |

## Insight

우선순위가 모호했던 “연구 모드”는 `ci` 대비 실제 명령 허용 차이로 명확해졌고,
스모크도 1건 처리에서 다중 처리 + 회복 경로까지 확장되어 운영형 동시성/중단 후복구 감각이 강화됐습니다.

이번 변경의 핵심은 `run_command` 정책을 “문서상 구분”에서 “실행 경로 검증 가능 구분”으로 바꾼 것입니다.

## Decision

- 결정: `pass-9`에서 목표한 실행 순서 우선 항목 1/3은 완료로 간주.
- 잔여 항목:
  1) 다중 노드/네트워크 공유 파일시스템(claim 경합)을 가정한 통합 테스트 추가
  2) `run_command` 정책 표를 사용자 문서(`README` 또는 템플릿 문서)와 동기화해 운영자가 모드별 허용 집합을 즉시 확인 가능하게 개선
  3) 다중 메시지 처리 후 재시도 실패(처리 중 예외) 케이스를 이벤트/claim 상태 관측 지표로 분리 기록
