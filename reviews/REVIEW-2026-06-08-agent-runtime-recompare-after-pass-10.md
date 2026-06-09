# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-10

## Bottom Line

`pass-9`~`pass-9b`에서 정리한 핵심 이슈(템플릿 완결성, CI, 보안 가드, claim 동시성, 의존성 계약)는 **실행 증거 기준으로 절반 이상 진전**했지만,
현 시점에서는 **실제로 배포 가능한 멀티에이전트 런타임**으로 불릴 만큼은 아직 완전히 닫히지 않았다.

`agent_orchestrator.py / agent_worker.py / auto_runner.py / check_messages.py` 실행 스모크, 더미 메시지 처리, stale claim 복구는 안정적으로 확인되며,
운영 모드별 명령 허용도는 pass-by-pass로 개선되었다.
다만 분산 파일시스템 경합, 복합 명령 주입 방어, 네이티브 플랫폼 통합-관측 루프는 아직 후속 단계다.

## Signal

- 비교 기준:
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9b-critique-alignment.md`
- 최신 실행 증거:
  - `PYTHONPATH=src python -m pytest tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_template_smoke.py -q` → `19 passed`
  - `PYTHONPATH=src python -m pytest tests -q` → `116 passed`
  - `tests/test_template_smoke.py`에서 템플릿 sync 후 핵심 스크립트 help/json 실행 및 더미 메시지 처리 통과
  - 템플릿 파일군에 `schemas/task.schema.json`, `orchestrator_safety_gate.py`, `pipeline.py`, 감사/안전 문서군 반영됨

### 핵심 항목 비교 (초기 비판 → pass-9b → pass-10)

| 항목 | 초기 비판(요약) | pass-9 / pass-9b 판정 | pass-10 판정 | 근거 |
|---|---|---|---|---|
| 배포 템플릿 자체 완결성 | critical | 해결 | 해결 | `schemas/task.schema.json`, `orchestrator_safety_gate.py`, `pipeline.py` 및 누락 문서 반영. `template smoke`에서 스크립트 실행 통과. |
| CI가 템플릿 산출물 검증 못함 | critical | 개선 | 개선 | 워크플로우에 템플릿 스모크 단계 반영, sync 후 `--help`, `--json`, 더미 메시지 처리 검증. |
| ToolRunner가 샌드박스가 아님 | high | 부분 개선 | 부분 개선 | `python -c`, `python <<`/`py -c`, `pip`, `git commit/checkout/restore/stash` 경로가 정책 차단됨. 다만 쉘 인젝션 조합/우회(복합 토큰 조합)은 추가 hardening 대상. |
| 병렬 claim/동시성 안전성 | high | 부분 강화 | 부분 강화 | 멀티스레드/멀티프로세스 단일-host claim 1승자 검증, stale recover/중복 reply 차단 테스트 완료. 하지만 NFS/네트워크 공유 FS의 lease 경합 검증은 미완. |
| 의존성 계약 | medium | 해결 | 해결 | `pyproject.toml` extras 분리 및 provider lazy load/테스트 보강. 누락 optional dep로 인한 template import 실패 위험이 크게 완화됨. |

## What Changed Since Last Review

- `provider` 런타임에서 명령 정책을 프로파일별로 분기(`owner`/`ci`/`research`)하고, 결과를 허용/차단 집합 형태로 명시 출력.
- 메시지 큐 claim 경합을 `threading.Barrier` 및 `multiprocessing.Process` 시나리오로 검증했고, stale claim 복구·응답 mismatch 차단을 명시 테스트로 정착.
- CI 템플릿 스모크를 `test_template_smoke.py`에서 `agent_orchestrator.py --help`, `agent_worker.py --help`, `auto_runner.py --json`, `check_messages.py`로 확장.
- `test_template_agent_tools.py`에서 경로 탈출, 금지 토큰 주입 패턴, 프로파일별 허용 차이, 오너/ci 정책 차이를 재검증.

## Remaining Gaps (재평가 대상)

1. 분산 실행 환경(공유 볼륨/원격 FS)에서의 atomic claim/recover 경합이 아직 실제 통합 테스트로 검증되지 않음.
2. `run_command`은 현재 token-level denylist 중심이므로, 쉘 조합 우회/인코딩 우회/경로 인코딩 변형 등 고급 주입 시나리오를 더 확장해야 함.
3. 멀티에이전트 운영 비교점수(Claude/Codex/OpenCode/subagent 통합) 대비는 문서/코드 정렬은 되었으나, 실제 메트릭 기반 점검 루프는 미흡.

## Decision for Product Direction

- `pass-10`에서 즉시 달성한 상태는 **“베이스 배포 템플릿 실행 경로가 실제로 살아나는 수준”**까지는 충분.
- 다음 라운드에서만 멀티에이전트 실전 런타임으로 분류 가능:
  1) 분산 claim/락 통합 테스트 추가 (네트워크 FS 포함)
  2) `run_command` command-injection hardening 강화 (인자 파싱/인코딩 우회/우회 조합 패턴)
  3) 실행 상태/결과의 운영 메트릭(성능·오류율·재시도율) 루프 반영
