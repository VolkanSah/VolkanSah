import requests
import os
import re

# --- Configuration ---
USERNAME = "VolkanSah"
TOKEN = os.getenv("GITHUB_TOKEN")
README_FILE = "README.md"
CODEY_FILE = ".codey"

if not TOKEN:
    print("❌ GITHUB_TOKEN missing. Check your Action secrets.")
    exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# --- Core Engine: GraphQL Stats ---
def fetch_stats():
    all_repos = []
    has_next, cursor = True, None
    while has_next:
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
            r = requests.post("https://api.github.com/graphql", json={"query": query}, headers=HEADERS)
            data = r.json()["data"]["user"]["repositories"]
            all_repos.extend(data["nodes"])
            has_next = data["pageInfo"]["hasNextPage"]
            cursor = data["pageInfo"]["endCursor"]
        except: break
    return all_repos

# --- Transmission: .codey Parser ---
def parse_codey():
    conf = {"repos": [], "sets": {}}
    if not os.path.exists(CODEY_FILE): return conf
    with open(CODEY_FILE, "r", encoding="utf-8") as f:
        c = f.read()
    
    repos = re.search(r"\[REPO_LIST\](.*?)\[REPO_LIST_END\]", c, re.S)
    if repos:
        conf["repos"] = [l.strip() for l in repos.group(1).splitlines() if l.strip() and not l.strip().startswith("#")]
    
    sets = re.search(r"\[SETTINGS\](.*?)\[SETTINGS_END\]", c, re.S)
    if sets:
        for l in sets.group(1).splitlines():
            if "=" in l:
                k, v = l.split("#")[0].split("=")
                conf["sets"][k.strip()] = int(v.strip())
    return conf

# --- Tuning: Details (Releases & Fixes) ---
def build_tables(config):
    # Link-Fix: Repository-Name ist jetzt der Link
    rel_table = "| Version | Repository | Date | Type |\n| :--- | :--- | :--- | :--- |"
    rel_rows = []
    for repo in config["repos"][:config["sets"].get("RELEASED_REPO_COUNT", 5)]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/releases", headers=HEADERS)
            if r.status_code == 200 and (data := r.json()):
                rel = data[0]
                v, date = rel["tag_name"], rel["published_at"][:10]
                repo_link = f"[{repo}](https://github.com/{USERNAME}/{repo})"
                rel_rows.append(f"| {v} | {repo_link} | {date} | Auto imported |")
        except: continue
    final_rel = rel_table + "\n" + ("\n".join(rel_rows) if rel_rows else "| - | - | - | - |")

    fix_table = "| Date | Message | Repo | Status |\n| :--- | :--- | :--- | :--- |"
    fix_rows = []
    for repo in config["repos"][:config["sets"].get("UPDATE_FIX_REPO_COUNT", 5)]:
        try:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/commits", headers=HEADERS)
            if r.status_code == 200 and (data := r.json()):
                c = data[0]
                msg = c["commit"]["message"].split("\n")[0][:50]
                date, url = c["commit"]["author"]["date"][:10], c["html_url"]
                status = "🩹" if "fix" in msg.lower() else "✅"
                fix_rows.append(f"| {date} | [{msg}]({url}) | {repo} | {status} |")
        except: continue
    final_fix = fix_table + "\n" + ("\n".join(fix_rows) if fix_rows else "| - | - | - | - |")

    return final_rel, final_fix

# --- Injector: Pattern-Logic ---
def update_readme(mapping):
    if not os.path.exists(README_FILE): return
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    for tag, data in mapping.items():
        pattern = rf".*?"
        replacement = f"\n{data}\n"
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# #############################################################
# # DUMMY CLASS FOR EXTENSIONS (Baster-Vorlage)
# #############################################################
# class CodeyExtension:
#     """Template for adding custom data (RPG, Weather, Pet-Status)"""
#     def __init__(self, name):
#         self.name = name
#     def get_data(self):
#         # Your Logic here (API calls, calculations etc.)
#         return "Sample Data or Table"
# #############################################################

if __name__ == "__main__":
    print("🏎️ Shelby V8 starting...")
    
    # 1. Basic Stats
    repos_data = fetch_stats()
    own = [r for r in repos_data if not r["isArchived"] and r["owner"]["login"] == USERNAME]
    arch = [r for r in repos_data if r["isArchived"] and r["owner"]["login"] == USERNAME]
    forks = [r for r in repos_data if r["owner"]["login"] != USERNAME]
    
    s_own, s_arch, s_fork = sum(r["stargazerCount"] for r in own), sum(r["stargazerCount"] for r in arch), sum(r["stargazerCount"] for r in forks)

    stats_md = (f"## 📊 GitHub Stats\n- **Own Public Repositories:** {len(own)}\n"
                f"  - ⭐ Active Stars: {s_own}\n  - 💎 Archived Stars: {s_arch}\n  - 🌟 Total Own Stars: {s_own + s_arch}\n"
                f"- **Forked Public Repositories:** {len(forks)} NOT MY ⭐\n  - ⭐ Active Stars: {s_fork}\n"
                f"- **🎯 Grand Total Stars:** {s_own + s_arch + s_fork}\n\n"
                f"*Last updated automatically via GitHub Actions.*")

    # 2. Advanced Tables
    config = parse_codey()
    rel_table, fix_table = build_tables(config)
    
    # 3. Final Injection Mapping
    readme_map = {
        "STATS": stats_md,
        "LAST_RELEASED": rel_table,
        "LAST_FIX": fix_table,
        # "CUSTOM_MODULE": CodeyExtension("Baster").get_data() # Example
    }
    
    update_readme(readme_map)
    print("🏁 Racing finished. README updated.")
