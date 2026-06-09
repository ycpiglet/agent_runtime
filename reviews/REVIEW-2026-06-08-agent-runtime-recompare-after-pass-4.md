# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-4

## 한 줄 결론

이전 비판 리뷰(`reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`) 기준으로
핵심 위험은 크게 줄었고, 실사용 증거(템플릿 smoke + 더미 메시지 처리)는 확보됐다.
다만 **실제 보안 샌드박스 완결/동시성 완전 강제/의존성 lazy import**는 아직 작업 잔여가 있다.

## 기준 문서

- 원본 비판 리뷰(상세 근거): `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 지난 재평가: `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-3.md`
- 최신 근거 코드/테스트: `tests/test_template_smoke.py`, `src/agent_runtime/templates/project/scripts/agent_worker.py`, `src/agent_runtime/templates/project/scripts/auto_dispatch.py`, `src/agent_runtime/templates/project/scripts/message_queue.py`, `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`, `.github/workflows/test.yml`

## 최신 실행 증빙

- `PYTHONPATH=src python -m pytest tests -q` → `96 passed`
- `python -m pytest tests/test_template_smoke.py -q` → `2 passed`
- `python -m agent_runtime.cli sanitize --root . --check` → `findings=0`
- `python -m agent_runtime.cli publish-check --root . --check` → `findings=0`
- `.tmp/public-source`가 비어있지 않아 `publish-bundle --check`는 실패했으나, 원인 자체는 상태 정합성(목표 디렉터리 사전 정리 필요)이며, 기능 회귀 자체는 아님.

## 이전 비판 항목 대비 진행상태

| 항목 | Baseline 상태 | pass-4 현재 | 근거 |
|---|---|---|---|
| 템플릿 자체 완결성 | 누락 파일로 실행 실패 위험 | **해결** | `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, `AUDIT-GATE.md`, `SAFETY-GATE.md`, `TEST-STRATEGY.md` 추가 |
| CI 내 Host 템플릿 실행 증명 | 패키지 테스트만 되고 런타임 증빙 없음 | **개선(부분 완료)** | `.github/workflows/test.yml`에 `tests/test_template_smoke.py` 단계 추가, smoke 테스트에서 `sync` + `--help` + 더미 메시지 처리 검증 통과 |
| ToolRunner 보안 샌드박스 | `python/py`, mutable git 허용 | **부분 진행** | `providers/agent_tools.py`에서 명령 allowlist 강화: `python -m pytest`, `scripts/check_agent_docs.py`, `scripts/check_messages.py`, `scripts/agent_orchestrator.py status --json`만 허용. `python -c`, `git add/commit/restore/...` 등 차단. 다만 회귀 테스트 부재로 장기 안정성은 미검증 |
| 동시성 claim 안정성 | read-modify-write race | **부분 진행** | `message_queue.py` 도입 + `agent_worker.py`/`auto_dispatch.py`가 lease 기반 함수로 전환. 실제 동시 실행 경합 테스트는 추가 필요 |
| 병렬 워커 소유권 강제 | 역할 미전파 | **개선** | `claim/mark` 경로가 `role`을 전달하도록 변경되어 ownership mismatch 방지 경향 강화 |
| 의존성 계약 | optional deps/top-level import 문제 | **미완료** | `pyproject.toml`은 아직 기존 상태, `providers/__init__.py`는 여전히 eager import |

## 남은 차이점(즉시 재작업 우선순위)

1. **ToolRunner 정책 테스트 보강**
   - `python -c`, `git commit`, `git restore`, `git checkout`, 임의 `py -m pip install` 등 명령이 `run_command`에서 확실히 거부되는지 단위 테스트 추가.
2. **claim 레이스 고정성 테스트**
   - 같은 메시지 동시 claim 시 1건만 처리되는 동시성 테스트 추가.
3. **의존성 분리/지연 로드**
   - `providers/__init__.py`의 live provider top-level import 제거 + `pyproject.toml` extras (`codex`, `claude`, `watch`, `dev`) 반영.
4. **리뷰/운영 문서 업데이트**
   - 이번 pass에서 진행한 변경이 `IMPLEMENTATION_PLAN.md`와 상태 문서에 반영되었는지 체크(기록 일치성).

## 작업 후 비교용 1줄 점수(현 버전)

- 템플릿 실행성: **B → A-** (실행 증빙 확보됨)
- 배포형 CI 증명: **D+ → B-** (단계 추가됨, 전체 파이프라인 안정성 점검 필요)
- 샌드박스 보안: **D → C-** (정책 강화는 됐으나 테스트 증빙 부재)
- 병렬 claim: **C- → C- (부분 개선)** (구조 추가, 레이스-테스트 미흡)
- 의존성 계약: **C → C** (변화 없음)
