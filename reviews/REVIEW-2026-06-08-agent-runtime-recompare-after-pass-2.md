# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2

## 한 줄 결론
이전 비판적 리뷰(`baseline`)에서 최우선 이슈였던 **템플릿 자기완결성**은 해결되었고, 런타임 실행성은 실사용 가능한 수준까지 회복됐다.
다만 질문하신 `실행성`, `보안 샌드박스`, `병렬성`, `CI 검증`의 핵심은 아직 다음 단계로 남아 있다.

## 참조 기준
- 기준점: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- 비교 기준: `reviews/REVIEW-2026-06-08-agent-runtime-after-pass-1.md`
- 이번 재평가: `reviews/REVIEW-2026-06-08-agent-runtime-post-pass-2.md`

## 이번 점검 근거(실측)
- `PYTHONPATH=src pytest tests -q` → 94 passed
- `python -m agent_runtime.cli sanitize --root . --check` → findings=0
- `python -m agent_runtime.cli publish-check --root . --check` → findings=0
- `python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check` → findings=0 / 선택 파일 182개
- `agent_runtime sync --root <clean host> --apply` → updates 156, conflicts 0
- sync된 host에서 스크립트 실행:
  - `scripts/agent_orchestrator.py --help`
  - `scripts/agent_worker.py --help`
  - `scripts/auto_runner.py --help`
  - `scripts/check_messages.py` (OK: 0 error, 0 warning)

## 항목별 비교

| 항목 | baseline(비판적 리뷰) | pass-2 현재 | 상태 |
|---|---|---|---|
| 템플릿 자기완결성 | 핵심 의존 누락(`orchestrator_safety_gate.py`, `pipeline.py`, `task.schema.json`, 문서 누락) | 누락 파일 추가 (`orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, 게이트/테스트 문서) | **해결됨** |
| 템플릿 실행 증명 | sync 후 실행 검증 없음 | clean sync + core 엔트리포인트 help/sanity 확인 완료 | **부분 해결(기능 단독 실행) / 지속적 CI화 미완료** |
| publish/sanitize 게이트 | 통과 상태였으나 template 실제 실패와 분리됨 | 여전히 통과 유지 | **유지** |
| ToolRunner 보안 가드 | python/py + mutable git 허용으로 임의 실행 우회 가능 | 개선 없음 | **미해결 (고위험)**
| 병렬 claim/race | read-modify-write 기반으로 중복 claim 가능성 높음 | 개선 없음 | **미해결 (고위험)** |
| provider 의존성 계약 | optional contract 모호, lazy import 미흡 | 개선 없음 | **미해결 (중위험)** |
| CI 산출물 증명 | package 테스트만 확인, host 산출물 미검증 | package 테스트만으로 동일 | **미해결 (중위험)** |

## 점수 업데이트(변경분만)
- Public release hygiene: B+ → B+
- Template execution completeness: D → **B-**
- Runtime distributed artifact proof: 낮음(미흡) → **낮음(미흡)**
- Command/tool security: D+ → D+
- Parallel message execution: C- → C-
- Provider dependency contract: C → C

## 남은 차이점 정리(다음 사이클에서 꼭 닫을 항목)
1. 템플릿 산출물을 대상으로 한 CI smoke job 정식화
   - clean host 생성 → sync --apply → `agent_orchestrator.py`/`agent_worker.py`/`auto_runner.py`/`check_messages.py` 실행
2. `providers/agent_tools.py`의 command allowlist 강화
   - `python -c`, `pip`, 임의 스크립트 실행 차단
   - mutable git (`commit/checkout/restore/stash`) 차단
3. 메시지 claim atomic lease 도입 (중복 claim/race 테스트 추가)
4. provider extras/lazy import 정리 (dummy 경로는 기본 설치에서 즉시 동작, live provider는 명시적 안내)

## 사용 방법(리뷰 재사용)
다음 번에는 baseline ↔ pass-3(또는 pass-N) 대비로 아래 두 문서를 함께 보자.
- `REVIEW-2026-06-08-agent-runtime-baseline.md`
- `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2.md`
