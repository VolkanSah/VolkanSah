import requests
import os

# Hole den Token aus den Umgebungsvariablen
token = os.getenv("GITHUB_TOKEN")
username = "VolkanSah"  # Dein GitHub Username

# Header für die Authentifizierung
headers = {
    "Authorization": f"token {token}"
}

# API-Endpunkte
user_url = f"https://api.github.com/users/{username}"
repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"

# Benutzer-Infos abrufen
user_response = requests.get(user_url, headers=headers)
user_data = user_response.json()

# Repos abrufen
repos_response = requests.get(repos_url, headers=headers)
repos_data = repos_response.json()

# Stats berechnen
total_stars = sum(repo["stargazers_count"] for repo in repos_data)
total_forks = sum(repo["forks_count"] for repo in repos_data)
public_repos = user_data.get("public_repos", 0)
followers = user_data.get("followers", 0)

# Markdown generieren
md_content = f"""
# 📊 GitHub Stats for [{username}](https://github.com/{username})

- **Public Repositories:** {public_repos}
- **Total Stars:** {total_stars}
- **Total Forks:** {total_forks}
- **Followers:** {followers}

_Last updated automatically via [GitHub Actions](https://github.com/features/actions)._
"""

# In stats.md speichern
with open("stats.md", "w", encoding="utf-8") as f:
    f.write(md_content)

print("✅ Stats aktualisiert.")
