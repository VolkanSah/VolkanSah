import requests
import os
import re

# GitHub Username
username = "VolkanSah"

# Token holen
token = os.getenv("GIT_TOKEN")
headers = {"Authorization": f"token {token}"}

# API Abfragen
user_url = f"https://api.github.com/users/{username}"
repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"

user_data = requests.get(user_url, headers=headers).json()
repos_data = requests.get(repos_url, headers=headers).json()

# Stats berechnen
total_stars = sum(repo["stargazers_count"] for repo in repos_data)
total_forks = sum(repo["forks_count"] for repo in repos_data)
public_repos = user_data.get("public_repos", 0)
followers = user_data.get("followers", 0)

# Markdown Inhalt
stats_md = f"""
<!-- STATS-START -->
# 📊 GitHub Stats

- **Public Repositories:** {public_repos}
- **Total Stars:** {total_stars}
- **Total Forks:** {total_forks}
- **Followers:** {followers}

_Last updated automatically via GitHub Actions._
<!-- STATS-END -->
"""

# README laden
with open("README.md", "r", encoding="utf-8") as f:
    readme_content = f.read()

# Block ersetzen oder neu einfügen
pattern = r"<!-- STATS-START -->(.|\n)*?<!-- STATS-END -->"
if re.search(pattern, readme_content):
    new_readme = re.sub(pattern, stats_md.strip(), readme_content, flags=re.DOTALL)
else:
    new_readme = readme_content.strip() + "\n\n" + stats_md

# Speichern
with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_readme)

print("✅ Stats Bereich in README.md aktualisiert.")
