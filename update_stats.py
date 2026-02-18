import requests
import os
import re
import sys

# --- Config ---
USERNAME = "VolkanSah"
TOKEN = os.getenv("GITHUB_TOKEN")
README_FILE = "README.md"
CODEY_FILE = ".codey"

if not TOKEN:
    print("❌ No Token")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def fetch_stats():
    all_repos = []
    cursor = None
    print("📡 Fetching...")
    
    for _ in range(10):  # Hard limit 10 pages
        cursor_str = f', after: "{cursor}"' if cursor else ""
        query = """
        {
          user(login: "%s") {
            repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER %s) {
              nodes {
                name, stargazerCount, isArchived
                owner { login }
              }
              pageInfo { hasNextPage, endCursor }
            }
          }
        }
        """ % (USERNAME, cursor_str)
        
        try:
            r = requests.post("https://api.github.com/graphql", json={"query": query}, headers=HEADERS, timeout=15)
            data = r.json().get("data", {}).get("user", {}).get("repositories", {})
            nodes = data.get("nodes", [])
            if not nodes: break
            
            all_repos.extend(nodes)
            print(f"✅ +{len(nodes)} repos")
            
            if not data.get("pageInfo", {}).get("hasNextPage"): break
            cursor = data.get("pageInfo", {}).get("endCursor")
        except:
            break
    return all_repos

def parse_codey():
    conf = {"repos": [], "sets": {}}
    if not os.path.exists(CODEY_FILE): return conf
    with open(CODEY_FILE, "r", encoding="utf-8") as f:
        c = f.read()
    
    # Quick Regex extraction
    repos = re.findall(r"^([^#\s\[].*)$", re.search(r"\[REPO_LIST\](.*?)\[REPO_LIST_END\]", c, re.S).group(1), re.M)
    conf["repos"] = [r.strip() for r in repos if r.strip()]
    
    sets = re.search(r"\[SETTINGS\](.*?)\[SETTINGS_END\]", c, re.S)
    if sets:
        for l in sets.group(1).splitlines():
            if "=" in l:
                k, v = l.split("#")[0].split("=")
                try: conf["sets"][k.strip()] = int(v.strip())
                except: pass
    return conf

def build_tables(config):
    rel_rows, fix_rows = [], []
    # Releases
    for repo in config["repos"][:config["sets"].get("RELEASED_REPO_COUNT", 5)]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/releases", headers=HEADERS, timeout=10).json()
            if r and isinstance(r, list):
                rel = r[0]
                rel_rows.append(f"| {rel['tag_name']} | [{repo}](https://github.com/{USERNAME}/{repo}) | {rel['published_at'][:10]} | Auto |")
        except: continue
    # Commits
    for repo in config["repos"][:config["sets"].get("UPDATE_FIX_REPO_COUNT", 5)]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/commits", headers=HEADERS, timeout=10).json()
            if r and isinstance(r, list):
                c = r[0]
                status = "🩹" if "fix" in c['commit']['message'].lower() else "✅"
                fix_rows.append(f"| {c['commit']['author']['date'][:10]} | [{c['commit']['message'][:50]}]({c['html_url']}) | {repo} | {status} |")
        except: continue

    rt = "| Version | Repository | Date | Type |\n| :--- | :--- | :--- | :--- |\n" + ("\n".join(rel_rows) if rel_rows else "| - | - | - | - |")
    ft = "| Date | Message | Repo | Status |\n| :--- | :--- | :--- | :--- |\n" + ("\n".join(fix_rows) if fix_rows else "| - | - | - | - |")
    return rt, ft

if __name__ == "__main__":
    repos = fetch_stats()
    if not repos: sys.exit(0)
    
    own = [r for r in repos if not r["isArchived"] and r["owner"]["login"] == USERNAME]
    arch = [r for r in repos if r["isArchived"] and r["owner"]["login"] == USERNAME]
    s_own, s_arch = sum(r["stargazerCount"] for r in own), sum(r["stargazerCount"] for r in arch)

    stats_md = f"## 📊 Stats\n- **Repos:** {len(own)}\n  - ⭐ Active: {s_own}\n  - 💎 Archived: {s_arch}\n- **🎯 Total:** {s_own + s_arch}"

    cfg = parse_codey()
    rt, ft = build_tables(cfg)
    
    with open(README_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Precision Injection
    for tag, data in {"STATS": stats_md, "LAST_RELEASED": rt, "LAST_FIX": ft}.items():
        text = re.sub(rf".*?", f"\n{data}\n", text, flags=re.S)
    
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print("🏁 Done")
