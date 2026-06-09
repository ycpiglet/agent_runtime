# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-3

## 한 줄 결론
이전 비판 리뷰(리뷰-베이스라인)가 지적한 치명 이슈 중 **템플릿 핵심 누락은 해소된 상태**이며,
템플릿 런타임이 깨끗한 호스트에서 실행되는지에 대한 증거도 생겼다.
다만 **CI 반영, 보안 샌드박스 경화, 병렬 claim 동시성, 의존성 계약**은 아직 미완이다.

## 기준 문서
- 기준: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 이전 비교: `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2.md`

## 최신 증빙 (2026-06-08)
- `python -m pytest tests/test_template_smoke.py -q` → `2 passed`
- `python -m agent_runtime.cli sanitize --root . --check` → `findings=0`
- `python -m agent_runtime.cli publish-check --root . --check` → `findings=0`
- `python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check` → `findings=0`
- `python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --apply` → `applied=184`
- `PYTHONPATH=src pytest tests -q`(전체 테스트) → template 내부 테스트 수집 실패 4건:
  - `scripts` 패키지 import 경로 가정 실패 (`test_agent_runtime_migration_inventory`, `test_check_repo_structure`, `test_claude_cli_probe`, `test_generate_script_index`)

## 항목별 재평가 (baseline 대비)

| 항목 | baseline | pass-3 현재 | 상태 |
|---|---|---|---|
| 템플릿 자기완결성 | 심각: 핵심 파일/문서 누락 | `orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, `AUDIT-GATE.md`, `SAFETY-GATE.md`, `TEST-STRATEGY.md` 추가 및 존재 검증 | **해결됨** |
| 템플릿 스모크 증명 | 없음 (패키지 테스트만) | `tests/test_template_smoke.py` 추가, sync 후 핵심 스크립트 `--help` 실행 및 더미 메시지 1건 처리 검증 (`2 passed`) | **해결(로컬 only)** |
| CI에서 템플릿 검증 | 미흡 | GitHub workflow에 스모크 테스트 step 미연동 | **미완료(높음)** |
| ToolRunner 샌드박스 | `python`/mutable git 허용, `git add/commit/checkout/restore/stash` 위험 | `providers/agent_tools.py`에는 아직 완전 잠금 미반영 (허용 명령군 유지) | **미해결(고위험)** |
| 메시지 claim 동시성 | read/modify/write 경쟁창 | `message_queue.py` 추가로 lease 기반 설계(독립 모듈) 준비 | **미완(부분진행)** |
| worker/dispatch claim 적용 | 기존 open->claimed 단순 전환 | `agent_worker.py`/`auto_dispatch.py`는 기존 방식 유지, `message_queue` 연동 미적용 | **미완료(핵심 미해결)** |
| 의존성 계약 | base deps 공백, top-level optional import 위험 | `pyproject.toml` 추가 조치 없음 | **미해결** |
| 전체 패키지/배포 게이트 | 좋음 | 동일 | **유지** |

## 점수 업데이트

| 영역 | baseline | pass-2 | pass-3 |
|---|---:|---:|---:|
| 공개 릴리스 위생 | B+ | B+ | B+ |
| 템플릿 실행 완성도 | D | B- | **C-** |
| 설치형 템플릿 CI 증명 | 낮음 | 미흡 | **미흡** |
| ToolRunner 보안 | D+ | D+ | D+ |
| 병렬 claim 안정성 | C- | C- | C (메시지 큐 시도 반영) |
| 의존성 계약 | C | C | C |

## 다음 비교 주기까지 미비한 4개
1. `.github/workflows/test.yml`에 `tests/test_template_smoke.py`를 CI step으로 고정
2. `providers/agent_tools.py`에서 `python -c/-`, `pip`, mutable git(`commit/checkout/restore/stash/....`)를 강제 차단하고 프로파일 allowlist만 통과
3. `agent_worker.py` / `auto_dispatch.py`의 claim/mark flow를 `message_queue.py` lease 방식으로 대체
4. `pyproject.toml` extras + providers lazy import (`dummy` 기본 동작은 clean env에서도 동작)

## 비교 평가 포인트(중요)
- 이번 단계는 **실행성의 증거 확보**가 유의미하게 개선된 상태다.
- 그러나 핵심 운영 안정성(보안/동시성/의존성)은 문서와 모듈 추가만으로 끝난 게 아니라, 실제 런타임 경로 연결이 필요하다.
- 따라서 이번 비교에서는 "기초는 단단해짐", "핵심 운영 하드닝은 아직 전면 미적용"이 가장 정확한 정리다.
