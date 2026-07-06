#!/usr/bin/env python3
"""Scribe 압축 필요 여부 advisory (read-only, source of truth 아님).

STATUS.md 의 `## 현재 한 줄 요약` 섹션 핫 항목 수를 세어 압축 트리거 상태를 보고한다.
설계 근거: agents/scribe/SKILL.md §Invocation Triggers (AUDIT-2026-05-31-012).

임계 (SKILL.md 와 일치):
  <= 12  ok          압축 불요
  13-15  due         압축 권장(다음 사이클/거버넌스)
  > 15   overdue     압축 필수(스킵 불가), 최신 10 hot 유지하고 나머지 아카이브

사용:
  python scripts/scribe_due.py            # 사람용 출력
  python scripts/scribe_due.py --quiet    # 상태 한 줄 + 종료코드(0=ok, 0=due/overdue도 0; advisory라 fail 안 함)
"""
import re
import sys
from pathlib import Path

try:  # Windows 콘솔(cp949)에서도 UTF-8 출력 (em-dash/화살표 등)
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
STATUS_CANDIDATES = [
    ROOT / "agents" / "lead_engineer" / "STATUS.md",
    ROOT / "STATUS.md",
]
HOT_KEEP = 10
DUE_AT = 13
OVERDUE_AT = 16  # > 15


def count_hot_entries(text: str) -> int:
    lines = text.split("\n")
    in_section = False
    count = 0
    for ln in lines:
        if ln.startswith("## "):
            in_section = ln.strip() == "## 현재 한 줄 요약"
            continue
        if in_section and re.match(r"^- ", ln):
            count += 1
    return count


def classify(n: int) -> str:
    if n >= OVERDUE_AT:
        return "overdue"
    if n >= DUE_AT:
        return "due"
    return "ok"


def status_path() -> Path | None:
    for path in STATUS_CANDIDATES:
        if path.is_file():
            return path
    return None


def main() -> int:
    quiet = "--quiet" in sys.argv
    status = status_path()
    if status is None:
        candidates = ", ".join(str(path) for path in STATUS_CANDIDATES)
        print(f"scribe_due: STATUS 없음 — checked {candidates}")
        return 0
    n = count_hot_entries(status.read_text(encoding="utf-8"))
    state = classify(n)
    msg = {
        "ok": f"ok — 핫 항목 {n}개 (<= 12), 압축 불요",
        "due": f"due — 핫 항목 {n}개 (13~15), 압축 권장: 다음 사이클/거버넌스에서 archive (최신 {HOT_KEEP} hot 유지)",
        "overdue": f"overdue — 핫 항목 {n}개 (> 15), 압축 필수: 가장 오래된 항목부터 아카이브, 최신 {HOT_KEEP} hot 유지",
    }[state]
    print(f"[scribe_due] {msg}")
    if not quiet and state != "ok":
        print("  → Scribe Cleanup(archive) 절차: agents/scribe/SKILL.md §Invocation Triggers / Compression Policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
