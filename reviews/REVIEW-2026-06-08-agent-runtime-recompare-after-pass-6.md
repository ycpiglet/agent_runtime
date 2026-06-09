# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-6

## 한 줄 결론

핵심 게이트(템플릿 실행성, 동시 claim, provider 계약, 보안 가드)는 이제 **실행 증거 기반으로 모두 검증 가능한 수준**으로 이동했다.
여전히 다중 워커 운영의 분산적 극단 케이스(실제 병렬 프로세스/IO 경쟁, 장기 재시도 루프)와 모니터링 편의성은 다음 단계에서 보강이 필요하다.

## 기준

- Baseline: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 이전 비교: `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-5.md`
- 실행 근거: `tests/test_template_agent_tools.py`, `tests/test_template_message_queue.py`, `tests/test_template_smoke.py`, `tests/test_provider_import_contract.py`, `src/agent_runtime/templates/project/scripts/agent_tools.py`, `src/agent_runtime/templates/project/scripts/message_queue.py`, `src/agent_runtime/templates/project/scripts/providers/__init__.py`, `pyproject.toml`

## 최신 실행 증빙 (2026-06-08)

- `PYTHONPATH=src python -m pytest tests -q` → `107 passed`
- `PYTHONPATH=src python -m pytest tests/test_template_agent_tools.py tests/test_template_message_queue.py tests/test_provider_import_contract.py -q` → `11 passed`
- `PYTHONPATH=src python -m pytest tests/test_template_smoke.py -q` → `2 passed`
- `PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check` → `findings=0`
- `PYTHONPATH=src python -m agent_runtime.cli publish-check --root . --check` → `findings=0`
- `PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check` → `findings=0`
- `PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --apply` → `applied=187`

## pass-5 대비 pass-6 재평가

| 항목 | pass-5 상태 | pass-6 상태 | 판정 |
|---|---|---|---|
| 템플릿 자체 완결성 | 계속 유지됨 | 유지(더 강화) | 개선 |
| 템플릿 smoke CI | CI 반영되어 있었으나 증명 체계 제한 | 스모크 경로 + dummy 메시지 처리 + `--help` 실행 증거 확보 | 개선 |
| ToolRunner 사전 가드 | 부분/회귀 테스트 미흡 | allowlist + 회귀 테스트(금지 명령, python/py 정책, 경로 탈출) 추가 | 개선 |
| 병렬 claim 안정성 | 설계/연동 시작 | `message_queue` 동시요청 1승자 테스트 + 중복 reply 테스트로 검증 | 개선 |
| 의존성 계약 | 미완료 | Provider lazy import + `extra` 분리 + `agent_runtime[codex|claude|watch|dev]` 제안 반영 + 실패경로 테스트 보강 | 개선 |

## 남은 미비점 (다음 비교에서 재점검 대상)

1. 메시지 claim은 아직 단일 워킹 디렉터리 기준의 파일시스템 원자성 중심 검증이다. 실제 멀티 프로세스/격리된 runtime에서의 lease 충돌·권한상태 전이를 추가한다면 운영 신뢰도가 올라간다.
2. 명령 가드는 정책은 강화되었으나, “허용/금지 분류”를 작업별 프로파일(예: QA용 vs heavy-runner용)로 분리하면 오탐률과 운영 유연성이 개선된다.
3. `tests/test_template_smoke.py`는 현재 clean fixture 기반 단일 워크플로우를 검증한다. 장기 운영을 가정한 `publish-tag-smoke` + `sync` + dummy multi-message 시나리오 연동은 다음 반복에서 연결하는 편이 명확하다.

## 종합 점수(상태 반영 후)

- 템플릿 실행 완성도: `D -> C`
- 설치형 템플릿 CI 증명: `C- -> B-`
- Command/tool security: `D+ -> C-`
- 병렬 claim 안정성: `C -> C+`
- 의존성 계약/옵션 설치: `C -> B-`

## 다음 회차 액션 (우선순위)

1. 멀티 프로세스/멀티 노드에서의 claim lease 회복 경로와 stale reclaim을 통합 테스트에 추가.
2. `run_command`에 프로파일 기반 정책 토글(`ci`, `owner`, `research` 등) + 정책별 문서화.
3. `review` 문서 템플릿을 정해진 스냅샷 양식(`Bottom Line/Signal/Insight/Decision`)으로 정렬해 운영 리뷰를 템플릿화.
