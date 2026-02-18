import requests
import os
import re

# --- KONFIGURATION (Das Cockpit) ---
USERNAME = "VolkanSah"
TOKEN = os.getenv("GITHUB_TOKEN")
CODEY_FILE = ".codey"
README_FILE = "README.md"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

if not TOKEN:
    print("❌ GITHUB_TOKEN fehlt! Abbruch.")
    exit(1)

# --- PHASE 1: DER MOTOR -
def fetch_stats_graphql():
    """Holt die großen Stats in einem Rutsch - Stabil & Schnell"""
    all_repos = []
    has_next = True
    cursor = None
    
    while has_next:
        query = """
        {
          user(login: "%s") {
            repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER) {
              nodes {
                name, stargazerCount, isArchived, isDisabled, isLocked
                owner { login }
              }
              pageInfo { hasNextPage, endCursor }
            }
          }
        }
        """ % (USERNAME + (f'", after: "{cursor}' if cursor else ""))
        
        try:
            r = requests.post("https://api.github.com/graphql", json={"query": query}, headers=HEADERS)
            r.raise_for_status()
            data = r.json()
            repos = data["data"]["user"]["repositories"]
            all_repos.extend(repos["nodes"])
            has_next = repos["pageInfo"]["hasNextPage"]
            cursor = repos["pageInfo"]["endCursor"]
        except:
            break
    return all_repos

# --- PHASE 2: DAS GETRIEBE (Der .codey Parser) ---
def parse_codey_config():
    """Liest die .codey Datei mechanisch aus - ohne Voodoo"""
    config = {"repos": [], "settings": {}}
    if not os.path.exists(CODEY_FILE): return config

    with open(CODEY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Repos extrahieren
    repo_match = re.search(r"\[REPO_LIST\](.*?)\[REPO_LIST_END\]", content, re.S)
    if repo_match:
        config["repos"] = [l.strip() for l in repo_match.group(1).splitlines() if l.strip() and not l.strip().startswith("#")]

    # Settings extrahieren (PHP-Style: einfach & direkt)
    settings_match = re.search(r"\[SETTINGS\](.*?)\[SETTINGS_END\]", content, re.S)
    if settings_match:
        for line in settings_match.group(1).splitlines():
            if "=" in line:
                key, val = line.split("#")[0].split("=") # Kommentare ignorieren
                config["settings"][key.strip()] = int(val.strip())
    
    return config

# --- PHASE 3: DIE EINSPRITZUNG (Last Fixes & Releases) ---
def get_details(config):
    """Holt nur das, was in den Settings steht - schont das Rate-Limit"""
    release_rows, fix_rows = [], []
    
    # Limits aus Config oder Fallback
    rel_limit = config["settings"].get("RELEASED", 1)
    rel_count = config["settings"].get("RELEASED_REPO_COUNT", 5)
    fix_limit = config["settings"].get("UPDATE_FIX", 1)
    fix_count = config["settings"].get("UPDATE_FIX_REPO_COUNT", 5)

    # Releases holen
    for repo in config["repos"][:rel_count]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/releases", headers=HEADERS)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    for rel in data[:rel_limit]:
                        date = rel.get("published_at", "")[:10]
                        v = rel.get("tag_name", "v?")
                        release_rows.append(f"| {v} | [{repo}]({rel.get('html_url')}) | {date} | Auto |")
        except: pass

    # Fixes (Commits) holen
    for repo in config["repos"][:fix_count]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/commits", headers=HEADERS)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    for c in data[:fix_limit]:
                        msg = c["commit"]["message"].split("\n")[0][:50]
                        date = c["commit"]["author"]["date"][:10]
                        status = "🩹" if "fix" in msg.lower() else "✅"
                        fix_rows.append(f"| {date} | [{msg}]({c.get('html_url')}) | {repo} | {status} |")
        except: pass

    return "\n".join(release_rows), "\n".join(fix_rows)

# --- PHASE 4: DAS FINISH (Update README) ---
def update_readme(stats_md, release_md, fix_md):
    if not os.path.exists(README_FILE): return
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Ersetzungen (Stabil via Regex)
    content = re.sub(r".*?", f"\n{stats_md}\n", content, flags=re.S)
    content = re.sub(r".*?", f"\n{release_md}\n", content, flags=re.S)
    content = re.sub(r".*?", f"\n{fix_md}\n", content, flags=re.S)

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# --- MAIN ---
if __name__ == "__main__":
    print("🏎️ Shelby startet...")
    
    # 1. Große Stats
    raw_data = fetch_stats_graphql()
    active = [r for r in raw_data if not r.get("isArchived")]
    stars = sum(r.get("stargazerCount", 0) for r in active)
    
    stats_md = f"## 📊 Stats\n- Repos: {len(active)}\n- Total Stars: {stars}"
    
    # 2. Config & Details
    config = parse_codey_config()
    rel_md, fix_md = get_details(config)
    
    # 3. Abfahrt
    update_readme(stats_md, rel_md or "| - | - |", fix_md or "| - | - |")
    print("🏁 Ziel erreicht. README ist sauber.")
