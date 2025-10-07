# GitHub Stats Auto-Update v2 (Workflow clean by Batman 🦇)
import requests
import os
import re
from collections import Counter

# Optional für schönere Tabellen
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

username = "VolkanSah"
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ GITHUB_TOKEN nicht gefunden!")
    exit(1)
headers = {"Authorization": f"Bearer {token}"}

try:
    # --- User Data ---
    user_url = f"https://api.github.com/users/{username}"
    user_response = requests.get(user_url, headers=headers)
    user_response.raise_for_status()
    user_data = user_response.json()

    followers = user_data.get("followers", 0)
    following = user_data.get("following", 0)

    # --- Repo Data ---
    repos_data = []
    page = 1
    while True:
        repos_url_page = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        repos_response = requests.get(repos_url_page, headers=headers)
        repos_response.raise_for_status()
        page_data = repos_response.json()
        if not page_data:
            break
        repos_data.extend(page_data)
        page += 1

    # --- Stats ---
    own_public_repos = [r for r in repos_data if not r.get("fork", False)]
    forked_public_repos = [r for r in repos_data if r.get("fork", False)]

    own_total_stars = sum(r.get("stargazers_count", 0) for r in own_public_repos)
    own_total_forks = sum(r.get("forks_count", 0) for r in own_public_repos)
    own_public_repo_count = len(own_public_repos)

    forked_total_stars = sum(r.get("stargazers_count", 0) for r in forked_public_repos)
    forked_total_forks = sum(r.get("forks_count", 0) for r in forked_public_repos)
    forked_public_repo_count = len(forked_public_repos)

    own_languages = Counter(r.get("language") or "Unknown" for r in own_public_repos)
    forked_languages = Counter(r.get("language") or "Unknown" for r in forked_public_repos)

    total_open_issues = sum(r.get("open_issues_count", 0) for r in repos_data)

    # --- CLI Output ---
    if TABULATE_AVAILABLE:
        table = [
            ["Own Public Repos", own_public_repo_count, own_total_stars, own_total_forks],
            ["Forked Public Repos", forked_public_repo_count, forked_total_stars, forked_total_forks],
        ]
        print(tabulate(table, headers=["Category", "Repos", "Stars", "Forks"], tablefmt="fancy_grid"))
    else:
        print(f"📂 Own: {own_public_repo_count} repos, ⭐ {own_total_stars}, 🍴 {own_total_forks}")
        print(f"📂 Forked: {forked_public_repo_count} repos, ⭐ {forked_total_stars}, 🍴 {forked_total_forks}")

    print(f"👥 Followers: {followers}, 🫂 Following: {following}")
    print(f"🐛 Open Issues (total): {total_open_issues}")
    print(f"🧠 Own Languages: {own_languages}")
    print(f"🧩 Forked Languages: {forked_languages}")

except requests.exceptions.RequestException as e:
    print(f"❌ API Error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# --- Markdown Output ---
def format_languages(lang_counter):
    return "\n".join(f"- {lang}: {count}" for lang, count in lang_counter.items())

stats_md = f"""<!-- STATS-START -->
### 📊 GitHub Stats
- **Own Public Repositories:** {own_public_repo_count}
  - ⭐ Stars: {own_total_stars}
  - 🍴 Forks: {own_total_forks}
- **Forked Public Repositories:** {forked_public_repo_count}
  - ⭐ Stars: {forked_total_stars}
  - 🍴 Forks: {forked_total_forks}
- **Followers:** {followers}
- **Following:** {following}
- **🐛 Open Issues (total):** {total_open_issues}

### 🧠 Languages (Own)
{format_languages(own_languages)}

### 🧩 Languages (Forked)
{format_languages(forked_languages)}

*Last updated automatically via GitHub Actions.*
<!-- STATS-END -->
"""

# --- README Update ---
try:
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()
except FileNotFoundError:
    print("❌ README.md nicht gefunden!")
    exit(1)

pattern = r"<!-- STATS-START -->.*?<!-- STATS-END -->"
if re.search(pattern, readme_content, re.DOTALL):
    new_readme = re.sub(pattern, stats_md, readme_content, flags=re.DOTALL)
    print("✅ Stats section updated in README.md.")
else:
    new_readme = readme_content.strip() + "\n\n" + stats_md
    print("✅ Stats section added to README.md.")

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_readme)

print("🎉 Done! Auto-update completed successfully.")
