# REVIEW-2026-06-09-agent-runtime-recompare-post-pass-114-release-preflight-final.md

## Bottom Line

`release-preflight --check`의 마지막 게이트는 정리된 배포 번들 소스를 통해서만 통과되었고, 현 작업트리(`source=.`) 그대로는 레포 상태/잔재 파일 때문에 `126`개의 blocking finding이 발생한다.

## Signal

| 항목 | 상태 | 근거 |
|---|---|---|
| release-preflight (source=`.`) | blocked | `source-git-repo-exists` 및 `unexpected-source-file`(`reviews/` 등) |
| release-preflight (source=`.tmp/release-bundle`) | pass | `findings=0` |
| host lock | updated | `tests/fixtures/host/agent_runtime.lock.json` write 완료 (`template_digest=sha256:afd83321d1f88d0aeba927cb042a0ea2c433e25d901ab51f675925139cde44be`) |

## Insight

- `release-preflight`는 깔끔한 배포 번들 또는 `.git` 제거된 소스 트리를 전제로 동작하도록 설계되어 있어, 현재 작업 디렉터리의 리뷰/실행 산출물을 그대로 대상 경로로 두면 실패한다.
- 이번 사이클에서 핵심 확인은 `publish-bundle --apply`로 생성한 정적 번들을 기준으로 한 `release-preflight --source .tmp/release-bundle --check`이며, 이 경로는 `sanitize`, `publish-check`, `host-sync-check`, `host-lock`을 포함한 전체 매트릭스를 통과한다.

## Decision

- `PYTHONPATH=src ${PYTHON_EXE} -m agent_runtime.cli publish-bundle --source . --dest .tmp/release-bundle --apply` 수행
- `PYTHONPATH=src ${PYTHON_EXE} -m agent_runtime.cli release-preflight --source .tmp/release-bundle --host-root tests/fixtures/host --remote-url https://github.com/example/agent_runtime.git --tag v0.1.5 --check` 수행
- `PYTHONPATH=src ${PYTHON_EXE} -m agent_runtime.cli lock --root tests/fixtures/host --write` 수행

### Remaining Risk

- 배포 전 최종 검증에서 로컬 source tree를 직접 사용하려면 별도 클린 카피/검증 스테이지가 필요함.
- `.tmp/release-bundle` 재생성 없이 반복 검증 시 예전 산출물이 stale 될 가능성이 있어, 배포 직전 항상 재생성 권장.
