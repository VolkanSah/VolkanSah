import requests
import os
import re

USERNAME = "VolkanSah"
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("❌ GITHUB_TOKEN nicht gefunden!")
    exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}
CODEY_FILE = ".codey"

# ------------------- Helper functions -------------------
def fetch_all_repos(is_fork):
    all_repos = []
    has_next = True
    cursor = None
    while has_next:
        query = """
        {
          user(login: "%s") {
            repositories(first: 100, privacy: PUBLIC, isFork: %s, ownerAffiliations: OWNER%s) {
              nodes {
                name
                stargazerCount
                isArchived
                isDisabled
                isLocked
                owner { login }
              }
              pageInfo { hasNextPage endCursor }
            }
          }
        }
        """ % (USERNAME, str(is_fork).lower(), f', after: "{cursor}"' if cursor else '')
        try:
            r = requests.post("https://api.github.com/graphql", json={"query": query}, headers=HEADERS)
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                print(f"❌ API-Fehler: {data['errors']}")
                exit(1)
            repos = data["data"]["user"]["repositories"]
            all_repos.extend(repos["nodes"])
            page_info = repos["pageInfo"]
            has_next = page_info["hasNextPage"]
            cursor = page_info["endCursor"]
        except requests.exceptions.RequestException as e:
            print(f"❌ API-Fehler: {e}")
            exit(1)
    return all_repos

def calculate_stats(repos, repo_type):
    active_repos = [r for r in repos if not r.get("isArchived", False) and not r.get("isDisabled", False) and not r.get("isLocked", False) and r.get("owner", {}).get("login")==USERNAME]
    archived_repos = [r for r in repos if (r.get("isArchived", False) or r.get("isDisabled", False) or r.get("isLocked", False)) and r.get("owner", {}).get("login")==USERNAME]
    active_count, active_stars = len(active_repos), sum(r.get("stargazerCount",0) for r in active_repos)
    archived_count, archived_stars = len(archived_repos), sum(r.get("stargazerCount",0) for r in archived_repos)
    return active_count, active_stars, archived_count, archived_stars

def read_codey_repos():
    repos = []
    try:
        with open(CODEY_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            in_list = False
            for line in content.splitlines():
                if "[REPO_LIST]" in line: in_list=True; continue
                if "[REPO_LIST_END]" in line: break
                if in_list:
                    line=line.strip()
                    if line and not line.startswith("#"): repos.append(line)
    except FileNotFoundError:
        print(f"❌ {CODEY_FILE} nicht gefunden!")
    return repos

def generate_details_blocks(repos, release_limit=1, release_repo_count=5, fix_limit=1, fix_repo_count=5):
    release_rows, fix_rows = [], []
    check_repos = repos[:max(release_repo_count, fix_repo_count)]
    for repo in check_repos[:release_repo_count]:
        r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/releases", headers=HEADERS)
        releases = r.json()[:release_limit]
        for rel in releases:
            version = rel.get("tag_name","-")
            name = rel.get("name") or version
            date = (rel.get("published_at") or "")[:10]
            link = rel.get("html_url")
            release_rows.append(f"| {version} | [{name}]({link}) | {date} | Auto imported |")
    for repo in check_repos[:fix_repo_count]:
        r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo}/commits", headers=HEADERS)
        commits = r.json()[:fix_limit]
        for c in commits:
            msg = c["commit"]["message"].split("\n")[0]
            date = c["commit"]["author"]["date"][:10]
            author = c.get("author", {}).get("login","ghost")
            status="✅"
            low=msg.lower()
            if "wip" in low: status="⚠"
            elif "fix" in low: status="🩹"
            link = c.get("html_url")
            fix_rows.append(f"| {date} | [{msg}]({link}) | {author} | {status} |")
    release_md = "\n".join(release_rows) if release_rows else "| - | - | - | - |"
    fix_md = "\n".join(fix_rows) if fix_rows else "| - | - | - | - |"
    return release_md, fix_md

def update_readme_stats(own_repos, own_stars, own_archived_stars, forked_repos, forked_stars, forked_archived_stars):
    stats_md = f"""<!-- STATS-START -->
## 📊 GitHub Stats
- **Own Public Repositories:** {own_repos}
  - ⭐ Active Stars: {own_stars}
  - 💎 Archived Stars: {own_archived_stars}
  - 🌟 Total Own Stars: {own_stars + own_archived_stars}
- **Forked Public Repositories:** {forked_repos} NOT MY ⭐
  - ⭐ Active Stars: {forked_stars}
  - 💎 Archived Stars: {forked_archived_stars}
  - 🌟 Total Fork Stars: {forked_stars + forked_archived_stars}
- **🎯 FAKE Total Stars:** {own_stars + own_archived_stars + forked_stars + forked_archived_stars}
- ** See Codey RPG system for better stats**
*Fake STATS updated automatically via GitHub Actions!*
<!-- STATS-END -->"""
    with open("README.md", "r", encoding="utf-8") as f:
        content=f.read()
    content=re.sub(r"<!-- STATS-START -->.*?<!-- STATS-END -->", stats_md, content, flags=re.S)
    with open("README.md","w",encoding="utf-8") as f: f.write(content)

def update_readme_details(release_md, fix_md):
    with open("README.md", "r", encoding="utf-8") as f:
        content=f.read()
    content=re.sub(r"<!-- LAST_RELEASED-START -->.*?<!-- LAST_RELEASED-END -->", f"<!-- LAST_RELEASED-START -->\n{release_md}\n<!-- LAST_RELEASED-END -->", content, flags=re.S)
    content=re.sub(r"<!-- LAST_FIX-START -->.*?<!-- LAST_FIX-END -->", f"<!-- LAST_FIX-START -->\n{fix_md}\n<!-- LAST_FIX-END -->", content, flags=re.S)
    with open("README.md","w",encoding="utf-8") as f: f.write(content)
    print("✅ README Details updated (Releases & Fixes)")

# ------------------- Main -------------------
if __name__=="__main__":
    print("🔍 Hole eigene Repositories...")
    own_data=fetch_all_repos(False)
    own_repos, own_stars, own_archived, own_archived_stars=calculate_stats(own_data,"eigene")
    print("🔍 Hole geforkte Repositories...")
    fork_data=fetch_all_repos(True)
    forked_repos, forked_stars, forked_archived, forked_archived_stars=calculate_stats(fork_data,"geforkte")
    update_readme_stats(own_repos, own_stars, own_archived_stars, forked_repos, forked_stars, forked_archived_stars)

    print("🔍 Erstelle Details-Blöcke...")
    codey_repos=read_codey_repos()
    release_md, fix_md=generate_details_blocks(codey_repos)
    update_readme_details(release_md, fix_md)

    print("🎉 Alle Updates abgeschlossen!")
