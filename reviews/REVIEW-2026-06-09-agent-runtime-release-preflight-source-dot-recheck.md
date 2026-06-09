# REVIEW-2026-06-09-agent-runtime-release-preflight-source-dot-recheck.md

## Bottom Line

`source=.`에서의 `release-preflight --check`는 2026-06-09 재실행 기준 `findings=133`으로 계속 차단되고, `source=.tmp/release-bundle` 기준은 `findings=0`으로 통과입니다.

## Signal

- `release-preflight` 실행
  - `PYTHONPATH=src ${PYTHON_EXE} -m agent_runtime.cli release-preflight --source .tmp/release-bundle --host-root tests/fixtures/host --remote-url https://github.com/example/agent_runtime.git --tag v0.1.5 --check`
    - 결과: `findings=0`
  - `PYTHONPATH=src ${PYTHON_EXE} -m agent_runtime.cli release-preflight --source . --host-root tests/fixtures/host --remote-url https://github.com/example/agent_runtime.git --tag v0.1.5 --check`
    - 결과: `findings=133`

## Insight

- 핵심 차단 원인은 세 가지입니다.
  - `source-git-repo-exists`: 현재 작업 트리가 Git 저장소 루트입니다.
  - `sanitize:absolute-local-path`: `STATUS.md` 내용 내 절대 경로 패턴.
  - `unexpected-source-file`: `reviews/*`, 루트 문서/로그(`stdout.txt`, `stderr.txt`) 등 번들 외부 산출물이 `github-publish-plan` 비교 집합에 들어와 있음.
- `publish-github-plan`이 기대하는 `publish-bundle` 집합 외부 파일을 엄격하게 제한하고 있어, `source=.` 운영 정책을 유지하려면 정합 로직이 분리되어야 합니다.

## Decision

- 다음 세션에서 `P0-1`은 **옵션 B(클린 번들 기반 preflight)** 우선 적용을 제안합니다.
- 구현 전 `P0-2`로 `stdout.txt`/`stderr.txt` 잠금 정리 및 임시 산출물 수거 규칙부터 정렬합니다.
