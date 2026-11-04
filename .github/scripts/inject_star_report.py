#!/usr/bin/env python3
"""Fetch CODEY_STAR_REPORT.md from the Codey repo and inject a trimmed version
into README.md between <!-- STAR_REPORT-START --> and <!-- STAR_REPORT-END -->.

Usage:  python3 inject_star_report.py [source-url-or-file]
Exit:   0 = ok (changed or unchanged), 1 = something looked wrong, README untouched.
"""
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_SRC = "https://raw.githubusercontent.com/VolkanSah/Codey/refs/heads/main/CODEY_STAR_REPORT.md"
FULL_URL = "https://github.com/VolkanSah/Codey/blob/main/CODEY_STAR_REPORT.md"
README = Path("README.md")
START, END = "<!-- STAR_REPORT-START -->", "<!-- STAR_REPORT-END -->"
CUT_BEFORE = "<summary>All Own Repos</summary>"   # this block and everything after is dropped


def load(src: str) -> str:
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "codey-profile-updater"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8")
    return Path(src).read_text(encoding="utf-8")


def trim(report: str) -> str:
    if "Codey Gazette" not in report or "real stars" not in report:
        raise ValueError("report does not look like a Codey star report")

    # 1) cut everything from the 'All Own Repos' block on
    idx = report.find(CUT_BEFORE)
    if idx != -1:
        report = report[: report.rfind("<details>", 0, idx)]

    # 2) title: H1 -> bold line, drop the avatar image (profile shows it already)
    report = re.sub(r"^# (.+)$", r"**\1**", report, count=1, flags=re.M)
    report = re.sub(r"^!\[\]\(\s*https://github\.com/[^)]*\.png[^)]*\)\s*$", "", report, flags=re.M)

    # 3) demote H2 to H4 so the profile stays calm
    report = re.sub(r"^## ", "#### ", report, flags=re.M)

    # 4) tidy blank lines / separators at the end, add the link to the full report
    report = re.sub(r"\n{3,}", "\n\n", report).strip()
    report = re.sub(r"(\n---)+$", "", report).strip()
    return f"{report}\n\n[Full report with all repos →]({FULL_URL})"


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    try:
        block = trim(load(src))
    except Exception as exc:          # network error, wrong file, ...
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("ERROR: markers not found in README.md", file=sys.stderr)
        return 1

    new = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: f"{START}\n\n{block}\n\n{END}",
        text,
        count=1,
        flags=re.S,
    )
    if new == text:
        print("README unchanged")
        return 0
    README.write_text(new, encoding="utf-8")
    print("README updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
