import requests
import os
import re
import sys

# --- Configuration ---
USERNAME = "VolkanSah"
TOKEN = os.getenv("GITHUB_TOKEN")
README_FILE = "README.md"
CODEY_FILE = ".codey"

if not TOKEN:
    print("❌ ERROR: GITHUB_TOKEN is not set.")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def fetch_stats():
    """GraphQL collector with loop protection and timeout."""
    all_repos = []
    has_next, cursor = True, None
    max_pages = 15  # Safety break to prevent endless loops
    current_page = 0
    
    print(f"📡 Requesting Profile Data for: {USERNAME}")
    
    while has_next and current_page < max_pages:
        current_page += 1
        cursor_str = f', after: "{cursor}"' if cursor else ""
        query = """
        {
          user(login: "%s") {
            repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER %s) {
              nodes {
                name, stargazerCount, isArchived, isDisabled, isLocked
                owner { login }
              }
              pageInfo { hasNextPage, endCursor }
            }
          }
        }
        """ % (USERNAME, cursor_str)
        
        try:
            # 25s timeout to stay ahead of GitHub Action's cancelation
            r = requests.post("https://api.github.com/graphql", json={"query": query}, headers=HEADERS, timeout=25)
            r.raise_for_status()
            res = r.json()
            
            if "errors" in res:
                print(f"❌ GraphQL API Error: {res['errors']}")
                break
                
            repo_data = res.get("data", {}).get("user", {}).get("repositories", {})
            nodes = repo_data.get("nodes", [])
            all_repos.extend(nodes)
            
            print(f"  📦 Page {current_page}: Received {len(nodes)} repositories.")
            
            has_next = repo_data.get("pageInfo", {}).get("hasNextPage", False)
            cursor = repo_data.get("pageInfo", {}).get("endCursor", None)
            
            if not nodes and has_next:
                break
                
        except Exception as e:
            print(f"❌ Connection interrupted: {e}")
            break
            
    return all_repos

def parse_codey_config():
    """Parses .codey for repository lists and execution limits."""
    conf = {"repos": [], "sets": {}}
    if not os.path.exists(CODEY_FILE):
        return conf
    
    with open(CODEY_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    repo_m = re.search(r"\[REPO_LIST\](.*?)\[REPO_LIST_END\]", content, re.S)
    if repo_m:
        conf["repos"] = [l.strip() for l in repo_m.group(1).splitlines() if l.strip() and not l.strip().startswith("#")]
    
    set_m = re.search(r"\[SETTINGS\](.*?)\[SETTINGS_END\]", content, re.S)
    if set_m:
        for l in set_m.group(1).splitlines():
            if "=" in l:
                k, v = l.split("#")[0].split("=")
                try: conf["sets"][k.strip()] = int(v.strip())
                except: pass
    return conf

def build_data_tables(config):
    """Builds the tables for Releases and Commits."""
    rel_limit = config["sets"].get("RELEASED_REPO_COUNT", 5)
    fix_limit = config["sets"].get("UPDATE_FIX_REPO_COUNT", 5)

    # Releases
    rel_rows = []
    for repo in config["repos"][:rel_limit]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/releases", headers=HEADERS, timeout=15)
            if r.status_code == 200 and r.json():
                rel = r.json()[0]
                v, date = rel["tag_name"], rel["published_at"][:10]
                rel_rows.append(f"| {v} | [{repo}](https://github.com/{USERNAME}/{repo}) | {date} | Auto |")
        except: continue
    
    rel_t = "| Version | Repository | Date | Type |\n| :--- | :--- | :--- | :--- |\n"
    rel_t += "\n".join(rel_rows) if rel_rows else "| - | - | - | - |"

    # Fixes (Last Commits)
    fix_rows = []
    for repo in config["repos"][:fix_limit]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/commits", headers=HEADERS, timeout=15)
            if r.status_code == 200 and r.json():
                c = r.json()[0]
                msg = c["commit"]["message"].split("\n")[0][:50]
                date = c["commit"]["author"]["date"][:10]
                status = "🩹" if "fix" in msg.lower() else "✅"
                fix_rows.append(f"| {date} | [{msg}]({c['html_url']}) | {repo} | {status} |")
        except: continue
        
    fix_t = "| Date | Message | Repo | Status |\n| :--- | :--- | :--- | :--- |\n"
    fix_t += "\n".join(fix_rows) if fix_rows else "| - | - | - | - |"
    
    return rel_t, fix_t

def update_readme_io(mapping):
    """Surgical README update using pattern matching."""
    if not os.path.exists(README_FILE): return
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    for tag, data in mapping.items():
        pattern = rf".*?"
        if re.search(pattern, content, re.S):
            content = re.sub(pattern, f"\n{data}\n", content, flags=re.S)
            
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    print("🚀 .codey Profile Update Sequence started...")
    repos = fetch_stats()
    
    if not repos:
        print("❌ No data available. Aborting.")
        sys.exit(1)

    # Filter and calculate Stats
    own = [r for r in repos if not r["isArchived"] and r["owner"]["login"] == USERNAME]
    arch = [r for r in repos if r["isArchived"] and r["owner"]["login"] == USERNAME]
    forks = [r for r in repos if r["owner"]["login"] != USERNAME]
    
    s_own = sum(r["stargazerCount"] for r in own)
    s_arch = sum(r["stargazerCount"] for r in arch)
    s_fork = sum(r["stargazerCount"] for r in forks)

    stats_md = (f"## 📊 GitHub Stats\n- **Own Repos:** {len(own)}\n"
                f"  - ⭐ Active: {s_own}\n  - 💎 Archived: {s_arch}\n"
                f"- **Forks:** {len(forks)}\n"
                f"- **🎯 Grand Total Stars:** {s_own + s_arch + s_fork}")

    # Build Tables and Update
    config = parse_codey_config()
    rel_table, fix_table = build_data_tables(config)
    
    update_readme_io({
        "STATS": stats_md,
        "LAST_RELEASED": rel_table,
        "LAST_FIX": fix_table
    })
    print("🏁 Update finished successfully.")
