# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2.5

## 한 줄 결론
이전 치명적 지적(템플릿 자기완결성 실패, CI 증명 부재, command sandbox 취약, 병렬 claim 취약, 의존성 계약 불명확)은 일부는 해소되었고, 일부는 다음 단계로 남았다.
`agent_runtime`은 **배포 후 실행 가능한 핵심 런타임 골격**은 갖췄으나, "강한 멀티에이전트 운영체제" 기준으로는 보안/동시성/유지보수 자동증명 항목이 미완이다.

## 기준 문서
- 원본 비판 리뷰: `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md`
- Pass-2 구현 반영: `reviews/REVIEW-2026-06-08-agent-runtime-post-pass-2.md`
- 본 재평가 결과(현재 워크트리): `tests/test_template_smoke.py` 기준

## 이번 재평가 근거
- `PYTHONPATH=src pytest tests -q` → 94 passed
- `python -m agent_runtime.cli sanitize --root . --check` → findings=0
- `python -m agent_runtime.cli publish-check --root . --check` → findings=0
- `python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check` → findings=0
- `python -m agent_runtime.cli sync --root <clean host> --apply` → updates 156, conflicts 0
- 동기식 실행성 smoke:
  - `scripts/agent_orchestrator.py --help`
  - `scripts/agent_worker.py --help`
  - `scripts/auto_runner.py --help`
  - `scripts/check_messages.py`
  - `scripts/agent_worker.py --role qa --provider dummy --once --quiet` (메시지 1건 처리)

## 항목 비교(원본 비판 리뷰 대비)

| 항목 | 원본 상태 | pass-2 이후 | 평가 |
|---|---|---|---|
| 템플릿 자기완결성 | 심각: `orchestrator_safety_gate.py`, `pipeline.py`, `task.schema.json`, 게이트 문서 누락 | 3개 핵심 파일 + 게이트 문서 추가 완료 | **해결** |
| 템플릿 산출물 실행 검증 | sync 산출물 미실행(패키지 테스트와 분리됨) | sync+entrypoint 실행 + 더미 메시지 1건 처리까지 자동화(테스트로 증명) | **부분 해결** (로컬 테스트는 통과, CI 연동은 미완) |
| ToolRunner command sandbox | 고위험: `python/py`, mutable git 허용 | 변경 없음 | **미해결(고위험)** |
| 병렬 claim 안정성 | 중복 claim/race 가능 | 변경 없음 | **미해결(고위험)** |
| provider 의존성 계약 | optional 계약/ lazy import 미흡 | 변경 없음 | **미해결(중요)** |
| CI에서 installed template 검증 | 패키지 테스트만 있음 | 로컬 smoke 테스트만 존재(워크플로 연동 미완) | **미해결(중요)** |

## 점수 반영(실무 비교)
- Public release hygiene: B+ → B+ (유지)
- Template execution completeness: D → B- (크게 개선)
- Installed-template CI proof: 낮음 → 중간 미흡(테스트 추가는 있었으나 CI 미연동)
- Command/tool security: D+ → D+ (동일)
- Parallel claim safety: C- → C- (동일)
- Provider dependency contract: C → C (동일)

## 남은 공백(다음 비교 주기용)
1. `.github/workflows/test.yml`에 `tests/test_template_smoke.py` 포함을 확정해, GitHub CI가 clean host 기반 sync → entrypoint 실행 → 더미 메시지 처리까지 실패 즉시 실패로 반영하도록 고정.
2. `src/agent_runtime/templates/project/scripts/providers/agent_tools.py` 명령 정책 잠금:
   - `python -c`, `python -m`, `pip`, 임의 스크립트 실행 금지
   - `git commit/checkout/restore/stash` 등 write 계열 기본차단
   - 허용 커맨드 profile 테스트 추가
3. 메시지 claim 동시성 제어(atomic claim lease + stale 회수 + 중복 reply 방지) 구현 + 동시성 테스트.
4. provider 의존성 분리(`extras` + lazy import), dummy-provider만 있는 환경의 install 안정성 확보.

## 메모 (원문 비판 리뷰 보존)
요청하신 이전 비판 포인트(템플릿 실패, CI blind spot, 샌드박스 회피, 병렬 claim race, 의존성 계약)를 위 표에 모두 유지했고, 재평가마다 "해결/미해결" 상태를 추적하도록 영속화했다.
