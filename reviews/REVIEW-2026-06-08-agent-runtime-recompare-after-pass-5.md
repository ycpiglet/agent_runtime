# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-5

## 한 줄 결론

가장 중요한 gap(템플릿 자체 완결성)은 이미 실사용 가능한 수준으로 닫혔다.
반면, **보안 샌드박스의 회귀 방지**와 **병렬 claim 강제성**은 “구현 일부 + 테스트 부재” 상태라 아직 운영 신뢰구간이 완성되지 않았다.

## 기준

- Baseline: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 비교 기준 이력: `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-4.md`
- 실행 근거: `tests/test_template_smoke.py`, `src/agent_runtime/templates/project/scripts/message_queue.py`, `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`, `.github/workflows/test.yml`

## 최신 실행 증빙 (2026-06-08)

- `PYTHONPATH=src python -m pytest tests -q` → `96 passed`
- `PYTHONPATH=src python -m pytest tests/test_template_smoke.py -q` → `2 passed`
- `PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check` → `findings=0`
- `PYTHONPATH=src python -m agent_runtime.cli publish-check --root . --check` → `findings=0`
- `PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check` → `findings=0`
- `PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --apply` → `applied=184`

## pass-4 대비 pass-5 재평가

| 항목 | pass-4 상태 | pass-5 상태 | 판정 |
|---|---|---|---|
| 템플릿 자체 완결성 | 해소됨(핵심 파일 추가) | 계속 유지됨 | 유지(좋음) |
| 템플릿 smoke CI | 부분(구성만 반영) | CI에 반영됨 (`tests/test_template_smoke.py` 실행 단계 추가) | 개선(실행성 증빙 확보) |
| ToolRunner 샌드박스 | 부분 진행(allowlist 강화되었지만 회귀 테스트 미흡) | 동일 | 미완료(고위험 잔여) |
| 병렬 claim 안전성 | 설계 적용(모듈/연동 시작) | `message_queue.py` + `agent_worker/auto_dispatch` 연동은 존재 | 부분 완료(아직 레이스 테스트 미완) |
| 의존성 계약 | 미완료(구조 미변경) | 미완료 | 미완료 |

## 왜 남는가: 변경 후 다시 보이는 공백

1. `providers/agent_tools.py`의 allowlist 자체는 강화되어 있으나, `python/pip/mutable git` 계열이 회귀하지 않는지 보장하는 회귀 테스트가 없다.
2. `message_queue.py`를 활용한 claim flow가 도입되어도 **동시 claim/reply 억제의 결정적 증거 테스트**가 없다.
3. `src/agent_runtime/templates/project/scripts/providers/__init__.py`의 top-level provider import 정책과 `pyproject.toml` extras 정리는 아직 남아 있다.

## 즉시 리뷰 액션(다음 비교를 위해 이번에 꼭 닫아야 할 항목)

1. `test_template_smoke.py`에 `agent_tools.run_command` 허용/차단 회귀 테스트를 추가 (예: `python -c`, `git commit`, `python -m pip`는 차단, `git status`, `python -m pytest tests -q`는 허용).
2. `message_queue`에 대해 병렬 claim/race 테스트를 추가 (동일 메시지 동시 처리 시 1개만 성공, duplicate reply 없음).
3. `providers/__init__.py` lazy import + `pyproject.toml` extras 정리 반영 후 별도 테스트로 clean install + dummy provider 경로 검증.

## 누적 점수(기준 대비)

- 템플릿 실행 완성도: `D → C- → B-`
- 설치형 템플릿 CI 증명: `D+ → C- → B-`
- Command/tool security: `D+ → D+ → D+`
- 병렬 claim 안정성: `C- → C → C`
- 의존성 계약: `C → C → C`
