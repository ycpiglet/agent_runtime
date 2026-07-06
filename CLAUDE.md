# CLAUDE.md — agent_runtime 세션 필수 컨텍스트

- **언어**: 사용자 대화는 한국어 기본(`AGENTS.md` Owner-Facing Language Contract).
  작업 보고는 `Bottom Line → Signal → Insight → Decision` 포맷.
- **정본 문서**: 행동 계약 `AGENTS.md` · 환경 셋업 `docs/DEV-ENVIRONMENT.md` ·
  현황 `STATUS.md` · 백로그 `BACKLOG-BOARD.md`.

## 환경 배선 (새 머신이면 가장 먼저)

```sh
pip install -e .                                # src 레이아웃 — editable 필수
python scripts/bootstrap_dev_env.py --apply     # hooksPath 등 일괄 점검/수리
```

- `core.hooksPath`가 `.githooks`가 아니면 게이트/락 재생성이 로컬에서 안 돌고
  **CI에서만 터진다**. bootstrap이 자동 수리한다.
- push는 SSH 권장: HTTPS OAuth 토큰은 `workflow` 스코프가 없어
  `.github/workflows/**` 변경 push가 거부된다(릴리스 cascade가 `test.yml`을 bump).

## 커밋 전 자주 잊는 재생성물 (CI red의 단골 원인)

| 변경 | 필수 재생성 |
|---|---|
| 신규 `reviews/*` 문서 | `python scripts/evidence_index_generator.py --write` |
| 템플릿 미러(`src/agent_runtime/templates/**`) | `python scripts/regen_host_lock_if_needed.py --write` |
| 태스크 closeout(status=done) | `work_item_classifier.py --write` + `backlog_board.py --write` |

## 운영 사실

- PR은 CI green 시 `auto-merge.yml`이 ~1분 내 자동 머지 — "머지 전 수정" 창이
  없으므로 문제 발견 시 fix-forward(새 PR)가 경로다.
- 릴리스: patch는 cadence 자동, minor/major는 Owner 승인 이슈 경유.
  발행 절차: `release_version_cascade.py --write X.Y.Z` → PR → 머지 →
  annotated tag(머지 커밋) → `gh release create` (v0.5.0/v0.6.0 검증 패턴).
- 병렬 PR이 생성 파일(INDEX/보드/락)을 공유하면 충돌한다 — 충돌 시 hand-merge
  대신 origin/main 채택 후 `--write` 재생성.
