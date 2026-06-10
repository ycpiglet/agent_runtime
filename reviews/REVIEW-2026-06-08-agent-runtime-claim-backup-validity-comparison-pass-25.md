# REVIEW-2026-06-08-agent-runtime-claim-backup-validity-comparison-pass-25

## Bottom Line

`message_queue`의 `claim` 소유권 판단에서, 클레임 파일이 사라진 상태에서 frontmatter에 남은 구식 `claim` 정보만으로 영구적으로 active로 보는 오판 가능성을 줄였다.
이 변경으로 **분산 FS/재시작 시 stale frontmatter으로 인한 중복 ownership 판정** 위험을 한 단계 낮췄고, 동시성 테스트가 여전히 단일-winner 성질을 유지한다.

## Signal

| 항목 | 이전 상태 | Pass-25 개선 | 근거 |
|---|---|---|---|
| stale frontmatter fallback | 존재 시 만료 여부 미검증 | `expires_at` 기준으로 만료면 inactive 처리 | `message_queue.py` 변경 + `tests/test_template_message_queue.py::test_has_active_claim_rejects_stale_frontmatter_claim` |
| 병렬 claim 중복 위험 | 일부 환경에서 오래된 claim 메타로 오탐 가능성 | 중복 판정 기준이 active lease 중심으로 강화 | 전체 큐 테스트 통과(11/11) |
| 회귀 커버리지 | 기존 동시성 커버만 존재 | stale frontmatter 전용 회귀 테스트 추가 | 동시성/복구 테스트 + 새 경계 테스트 |

## Current Verification

- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_template_message_queue.py -q`
  → `11 passed`
- `PYTHONPATH=src C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests -q`
  → `134 passed`

## Insight

기존 설계는 claim 파일 손실(크래시/복구 시나리오)에서 frontmatter backup이 살아 있는 경우를 고려했지만, 백업에 TTL이 없어서 장기 stale로 잘못된 active 판정이 가능했다.
이번 패스에서 `has_active_claim`를 claim-file 우선 + frontmatter fallback(단, 미만료)로 정리해 오탐 여지를 줄였다.

## Decision

- 다음 패스 미해결 항목:
  1. 분산/원격 FS에서의 `open(..., 'x')` 동작과 동시성 보장을 별도 테스트 하네스(예: 장애 주입/지연 삽입)로 정량 측정
  2. ToolRunner 플랫폼-우회 시나리오(고급 Windows/Powershell 인코딩 변형) 회귀 테스트를 계속 확대

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-24-critic-feedback-full-comparison.md`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_message_queue.py`
