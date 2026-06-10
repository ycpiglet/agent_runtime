# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9b-critique-alignment

## Bottom Line

초기 비판적 평가(템플릿 완결성·CI 검증·샌드박스·병렬 claim·의존성 계약)를 `pass-9` 결과와 대조해보면, 실행증거 기준으로 **템플릿 완결성/설치 후 스크립트 실행 검증/의존성 계약**은 안정적으로 닫혔다.
남은 큰 간극은 **멀티노드 병렬 실행의 분산 파일시스템 경합 검증**과 **보안 테스트 폭 확대(주입/탈출 시나리오)**다.

## Signal

- 기준:
  - `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
  - `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9.md`
- 현재 실행 증거:
  - `PYTHONPATH=src python -m pytest tests -q` → `112 passed`
  - `Get-Content .github/workflows/test.yml` → template smoke + publish/gate 단계까지 반영
  - `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
    `src/agent_runtime/templates/project/scripts/message_queue.py`
    `tests/test_template_agent_tools.py`
    `tests/test_template_message_queue.py`
    `tests/test_template_smoke.py`에 변경 반영

### 초기 비판 항목 대비 pass-9 현재 상태

| 초기 비판 항목 | 초기 판정 | pass-9 현재 판정 | 근거 |
|---|---|---|---|
| 배포 템플릿 자체 완결성(누락 파일) | 심각 | 해결 | `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json` 상주. `AUDIT-GATE.md`, `SAFETY-GATE.md`, `TEST-STRATEGY.md` 포함되어 템플릿 동작 문맥 정합성 확보. |
| CI가 템플릿 산출물 검증하지 못함 | 심각 | 개선 | `template smoke` 단계가 `agent_orchestrator.py --help`, `agent_worker.py --help`, `auto_runner.py --json`, `check_messages.py` 등으로 확장됨 (`test.yml`, `tests/test_template_smoke.py`). |
| ToolRunner가 샌드박스가 아님 | 고위험 | 부분 해결 | `python -c`, stdin 실행, `pip`, 다수 git mutable 명령이 차단됨. 다만 profile 기반 allowlist 유지 특성상 엄격도는 운영 모드별로 다름. |
| 메시지 claim 경쟁/동시성 | 고위험 | 부분-강화됨 | `message_queue.py` + `claim`/`recover` 경로 + thread/process 경합 테스트 + stale 회복 테스트 추가. 다만 네트워크 공유 FS(분산 worker) 환경은 추가 실험 미비. |
| 의존성 계약 | 중간 | 해결 | `pyproject.toml` extras 분리(`codex/claude/watch/dev`), `providers/__init__.py`에서 선택적 로드 흐름 강화, dummy 모드 동작 확인 테스트 보강. |

## Insight

1. 이번 라운드는 "문서형 리스크"를 "실행 경로 리스크"로 바꾼 점이 크다.
   즉, `orchestrator_safety_gate.py` 누락/스모크 실패 같은 실제 런타임 오류를 실제 테스트 루틴이 직접 잡는다.

2. 명령 실행 정책은 `owner`/`ci`/`research` 분리 자체가 아니라 **모드별 허용면적이 실제로 달라지는지**를 테스트로 증명해 신뢰도를 높였다 (`test_run_command_profile_research_unlocks_more_non_mutating_commands`).

3. 병렬성과 회복성은 `claim` 레이어가 안정화되며 의미 있게 진전되었지만, 현재 검증은 단일 호스트 파일시스템 중심이다. 실제 공개 다중에이전트 배포에서는 NFS/공유볼륨 경합 특성까지 확장해 보는 게 다음 필수 단계다.

## Decision

- 남은 미비 3개를 다음 패치에서 분리한다.
  1) 분산 환경 claim 경합 통합 테스트(공유 드라이브/네트워크 경로, 파일락/시계 역행/재시도 조건 포함).
  2) ToolRunner 보안 스위트 확장: prompt-injection 형식 토큰 패턴, 인용/출력 경로 과다 노출, 경로 탈출·명령조합 공격(예: `python -m pytest` 의도 밖 인자)의 추가 회귀.
  3) 외부 통합성 비교표 갱신: Claude native/subagent, OpenAI/코덱스 하네스, Codex/Claude/Opencode 인터페이스 연동 상태를 실행 지표로 분리.
