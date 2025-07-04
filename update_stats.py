import requests
import os
import re

# GitHub Username
username = "VolkanSah"

# Token holen
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ GITHUB_TOKEN nicht gefunden!")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# API Abfragen mit Error Handling
try:
    user_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    
    print("🔍 Hole User-Daten...")
    user_response = requests.get(user_url, headers=headers)
    user_response.raise_for_status()
    user_data = user_response.json()
    
    print("🔍 Hole Repo-Daten...")
    repos_response = requests.get(repos_url, headers=headers)
    repos_response.raise_for_status()
    repos_data = repos_response.json()
    
    # Debug: Typ prüfen
    print(f"📊 Gefundene Repos: {len(repos_data)}")
    
    # Prüfen ob repos_data wirklich eine Liste ist
    if not isinstance(repos_data, list):
        print(f"❌ Fehler: repos_data ist {type(repos_data)}, erwartet: list")
        print(f"Response: {repos_data}")
        exit(1)
    
    # Stats berechnen
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos_data)
    public_repos = user_data.get("public_repos", 0)
    followers = user_data.get("followers", 0)
    
    print(f"⭐ Stars: {total_stars}, 🍴 Forks: {total_forks}, 📁 Repos: {public_repos}, 👥 Followers: {followers}")
    
except requests.exceptions.RequestException as e:
    print(f"❌ API Fehler: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Fehler: {e}")
    exit(1)

# Markdown Inhalt
stats_md = f"""<!-- STATS-START -->
# 📊 GitHub Stats
- **Public Repositories:** {public_repos}
- **Total Stars:** {total_stars}
- **Total Forks:** {total_forks}
- **Followers:** {followers}

*Last updated automatically via GitHub Actions.*
<!-- STATS-END -->"""

# README laden
try:
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()
except FileNotFoundError:
    print("❌ README.md nicht gefunden!")
    exit(1)

# Block ersetzen oder neu einfügen
pattern = r"<!-- STATS-START -->.*?<!-- STATS-END -->"
if re.search(pattern, readme_content, re.DOTALL):
    new_readme = re.sub(pattern, stats_md, readme_content, flags=re.DOTALL)
    print("✅ Stats Bereich in README.md aktualisiert.")
else:
    new_readme = readme_content.strip() + "\n\n" + stats_md
    print("✅ Stats Bereich zu README.md hinzugefügt.")

# Speichern
with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_readme)

print("🎉 Fertig!")
