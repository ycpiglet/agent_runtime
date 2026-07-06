# 개발 환경 온보딩 — 다른 PC / 클라우드에서 동일하게 작업하기

> 이 저장소의 작업 환경을 새 머신(또는 클라우드)에서 재현하는 정본 가이드.
> 행동 계약은 `AGENTS.md`, 현황은 `STATUS.md`, Claude Code 요약은 `CLAUDE.md` 참조.

## Bottom Line — 3커맨드 셋업

```sh
git clone https://github.com/ycpiglet/agent_runtime.git && cd agent_runtime
pip install -e .
python scripts/bootstrap_dev_env.py --apply   # 배선 점검 + hooksPath 자동 수리
```

이후 `gh auth login`(최초 1회)과 SSH 키 등록만 하면 이 PC와 동일하게 작업할 수 있다.

## 1. 사전 요구사항

| 도구 | 용도 | 비고 |
|---|---|---|
| git | 소스/훅 체인 | 필수 |
| Python ≥ 3.10 | 패키지·게이트·테스트 | CI는 3.10/3.11/3.12 매트릭스 |
| GitHub CLI (`gh`) | 이슈/PR/릴리스 자동화 | `gh auth login` 필요 |
| SSH 키 (GitHub 등록) | push 전송 | 아래 §3 — 릴리스 작업에 사실상 필수 |

## 2. 셋업 절차 (왜 각 단계가 필요한가)

1. **`pip install -e .` (editable 설치)** — src 레이아웃 패키지라 editable이 아니면
   site-packages의 옛 빌드가 import되어 "코드 고쳤는데 반영 안 됨" 사고가 난다
   (2026-06-11 실사례).
2. **`git config core.hooksPath .githooks`** — 게이트 체인·evidence INDEX·호스트 락
   재생성이 pre-commit 훅으로 돈다. 미설정 시 로컬 커밋이 게이트를 전부 건너뛰고
   **CI에서만 터진다** (2026-07-06 실사례: PR #267/#268 각 1회 red).
3. **`python scripts/bootstrap_dev_env.py --apply`** — 위 두 가지 + push 전송 +
   gh 인증을 한 번에 점검한다. `--apply --ssh-push`를 주면 push URL도 SSH로 전환.

## 3. GitHub 인증 — push는 SSH를 권장

- `gh auth login` 후 이슈/PR 작업은 HTTPS로도 충분하다.
- 단, **HTTPS OAuth 토큰에는 보통 `workflow` 스코프가 없어**
  `.github/workflows/**`를 건드리는 커밋의 push가 거부된다. 릴리스 버전 cascade가
  `test.yml`을 bump하므로 **릴리스 작업에는 SSH push가 사실상 필수**
  (2026-07-06 v0.6.0 발행 실사례):

```sh
ssh -T git@github.com                       # "Hi <계정>!" 이면 인증 OK
git remote set-url --push origin git@github.com:ycpiglet/agent_runtime.git
# fetch는 https 유지 가능 — push만 SSH로 분리하는 구성이 검증됨
```

## 4. 클라우드에서 작업하기

- **GitHub Codespaces**: 저장소에 `.devcontainer/devcontainer.json`이 있어
  Codespace를 열면 Python 3.12 + gh CLI + editable 설치 + hooksPath까지 자동
  구성된다. 브라우저만 있으면 어느 기기에서든 동일 환경.
- **Claude Code 웹/원격 세션**(claude.ai/code): git 저장소만 연결하면 동작.
  로컬 자동 메모리는 따라오지 않으므로 §6 참조.

## 5. 자주 쓰는 커맨드 크립시트

| 상황 | 커맨드 |
|---|---|
| 전체 게이트 수동 실행 | `python scripts/owner_governance_gate.py` |
| 신규 `reviews/*` 문서 추가 후 | `python scripts/evidence_index_generator.py --write` |
| 템플릿(`src/agent_runtime/templates/**`) 변경 후 | `python scripts/regen_host_lock_if_needed.py --write` |
| 태스크 closeout 후 | `python scripts/work_item_classifier.py --write && python scripts/backlog_board.py --write` |
| 릴리스 버전 일괄 bump | `python scripts/release_version_cascade.py --write X.Y.Z` (12 refs; `--check`로 검증) |
| self-eval 스냅샷/델타 | `python scripts/self_eval_harness.py --report / --gate` |
| 버전 윈도 지표 | `PYTHONPATH=src python scripts/self_eval_metrics.py --from vA --to vB` |
| 테스트 | `python -m pytest -q` (전체), 파일 단위 권장 |

- PR은 CI green이면 `auto-merge.yml`이 ~1분 내 자동 머지한다. 머지 후 main CI는
  auto-merge의 workflow_dispatch 체인으로 돈다.
- 릴리스: patch는 cadence가 자동, minor/major는 Owner 승인 이슈(`[release-auto] …`)
  경유 — 절차는 `STATUS.md` 2026-07-06 항목과 이슈 #241 이력 참조.

## 6. Claude Code로 작업할 때 (머신 간 이식성)

- `CLAUDE.md`(리포 커밋됨)가 세션마다 자동 로드된다 — 핵심 운영 지식은 여기와
  본 문서에 커밋돼 있어 **어느 머신에서든 동일하게 주입**된다.
- 반면 다음은 **머신-로컬**이라 새 PC에 자동으로 따라오지 않는다:
  - 자동 메모리(`~/.claude/projects/<프로젝트-경로>/memory/`) — 이식 필요 시
    해당 폴더를 복사하면 되지만, 정본 지식은 리포 문서로 승격하는 것이 원칙
  - `.remember/` 세션 히스토리(untracked), `.claude/settings.local.json`(로컬 권한/env)
  - 사용자 레벨 플러그인/스킬(`~/.claude/`)
- 새 PC에서 첫 세션을 열면: 이 문서 §2 셋업 → `CLAUDE.md`/`AGENTS.md`/`STATUS.md`가
  컨텍스트를 복원한다.
