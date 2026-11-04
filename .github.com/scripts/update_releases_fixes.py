#!/usr/bin/env python3
# ##############################################################################
# Project:       .myCodey Profile Engine
# Licensed under: AGPL & ESOL 2.1 (https://github.com/ESOL-License)
# ##############################################################################
"""Fill the 'Released' and 'Last Fixes / Updates' blocks in README.md.

Settings come from .codey ([SETTINGS]); target repos are set below.
Exit code 1 and README untouched if every API call failed or markers are missing.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

USER = "VolkanSah"
TARGET_REPOS = ["Codey"]             # repos to show releases and commits for
CODEY_CONFIG = Path(".codey")
README = Path("README.md")
API = "https://api.github.com"

REL_HEAD = "| Repo | Version | Release | Date |\n|---|---|---|---|"
FIX_HEAD = "| Date | Repo | Commit | Author | Status |\n|---|---|---|---|---|"


def setting(text: str, key: str, default: int) -> int:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\d+)", text, flags=re.M)
    return int(m.group(1)) if m else default


def fetch_json(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "codey-profile-updater"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def as_list(data, what: str) -> list:
    if not isinstance(data, list):         # GitHub sends {"message": ...} on errors
        msg = data.get("message") if isinstance(data, dict) else data
        raise ValueError(f"unexpected API answer for {what}: {msg}")
    return data


def cell(text, limit: int = 80) -> str:
    """Make arbitrary text safe for one markdown table cell / link text."""
    text = " ".join(str(text).split())
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    for a, b in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
                 ("|", "\\|"), ("[", "\\["), ("]", "\\]")):
        text = text.replace(a, b)
    return text


def release_rows(repo: str, n: int) -> list:
    data = as_list(fetch_json(f"{API}/repos/{USER}/{repo}/releases?per_page={n}"), "releases")
    rows = []
    for rel in data[:n]:
        version = rel.get("tag_name") or "-"
        name = rel.get("name") or version
        date = (rel.get("published_at") or "")[:10] or "-"
        url = rel.get("html_url") or f"https://github.com/{USER}/{repo}/releases"
        rows.append(f"| {cell(repo)} | {cell(version)} | [{cell(name)}]({url}) | {date} |")
    return rows


def fix_rows(repo: str, n: int) -> list:
    data = as_list(fetch_json(f"{API}/repos/{USER}/{repo}/commits?per_page={n}"), "commits")
    rows = []
    for c in data[:n]:
        commit = c.get("commit") or {}
        msg = (commit.get("message") or "").split("\n")[0] or "(no message)"
        date = ((commit.get("author") or {}).get("date") or "")[:10] or "-"
        # 'author' is null when the commit email is not linked to an account
        author = (c.get("author") or {}).get("login") or (commit.get("author") or {}).get("name") or "ghost"
        url = c.get("html_url") or f"https://github.com/{USER}/{repo}/commits"
        low = msg.lower()
        status = "⚠" if "wip" in low else ("🩹" if "fix" in low else "✅")
        rows.append(f"| {date} | {cell(repo)} | [{cell(msg)}]({url}) | {cell(author, 30)} | {status} |")
    return rows


def replace_block(text: str, name: str, body: str) -> str:
    start, end = f"<!-- {name}-START -->", f"<!-- {name}-END -->"
    if start not in text or end not in text:
        raise ValueError(f"markers for {name} not found in README.md")
    return re.sub(
        re.escape(start) + r".*?" + re.escape(end),
        lambda _: f"{start}\n\n{body}\n\n{end}",      # lambda: no backslash surprises
        text, count=1, flags=re.S,
    )


def main() -> int:
    cfg = CODEY_CONFIG.read_text(encoding="utf-8") if CODEY_CONFIG.exists() else ""
    rel_per_repo = setting(cfg, "RELEASED", 1)
    rel_repo_cnt = setting(cfg, "RELEASED_REPO_COUNT", 5)
    fix_per_repo = setting(cfg, "UPDATE_FIX", 1)
    fix_repo_cnt = setting(cfg, "UPDATE_FIX_REPO_COUNT", 5)

    rel, fix, ok, failed = [], [], 0, 0
    for repo in TARGET_REPOS[:max(rel_repo_cnt, fix_repo_cnt)]:
        try:
            if repo in TARGET_REPOS[:rel_repo_cnt]:
                rel += release_rows(repo, rel_per_repo)
            if repo in TARGET_REPOS[:fix_repo_cnt]:
                fix += fix_rows(repo, fix_per_repo)
            ok += 1
        except Exception as exc:              # network, rate limit, 404, bad JSON
            failed += 1
            print(f"WARNING: {repo}: {exc}", file=sys.stderr)

    if ok == 0:
        print("ERROR: no repo could be read, README untouched", file=sys.stderr)
        return 1

    empty = "| - | - | - | - |"
    release_md = REL_HEAD + "\n" + ("\n".join(rel) if rel else empty)
    fix_md = FIX_HEAD + "\n" + ("\n".join(fix) if fix else "| - | - | - | - | - |")

    text = README.read_text(encoding="utf-8")
    try:
        new = replace_block(text, "LAST_RELEASED", release_md)
        new = replace_block(new, "LAST_FIX", fix_md)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if new == text:
        print("README unchanged")
        return 0
    README.write_text(new, encoding="utf-8")
    print("README updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
