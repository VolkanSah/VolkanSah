# Public GitHub Stats by Volkan S. Kücükbudak
# https://github.com/VolkanSah/
import os
import re
import requests

# GitHub Username
USERNAME = "VolkanSah"

# Token holen
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("❌ GITHUB_TOKEN nicht gefunden! Bitte setzen Sie die Umgebungsvariable.")
    exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# API-Endpunkte
USER_URL = f"https://api.github.com/users/{USERNAME}"
REPOS_URL = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"

def fetch_github_data():
    """Daten von der GitHub-API abrufen."""
    try:
        # Benutzer-Daten abrufen
        print("🔍 Hole Benutzer-Daten...")
        user_response = requests.get(USER_URL, headers=HEADERS)
        user_response.raise_for_status()
        user_data = user_response.json()

        # Repository-Daten abrufen
        print("🔍 Hole Repository-Daten...")
        repos_response = requests.get(REPOS_URL, headers=HEADERS)
        repos_response.raise_for_status()
        repos_data = repos_response.json()

        # Debug: Anzahl der Repositories überprüfen
        print(f"📊 Gefundene Repositories: {len(repos_data)}")

        # Prüfen, ob die Daten korrekt formatiert sind
        if not isinstance(repos_data, list):
            print(f"❌ Fehler: Repositories-Daten sind {type(repos_data)}, erwartet: list")
            print(f"Antwort: {repos_data}")
            exit(1)

        return user_data, repos_data

    except requests.exceptions.RequestException as e:
        print(f"❌ API-Fehler: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Fehler: {e}")
        exit(1)

def calculate_stats(user_data, repos_data):
    """Statistiken berechnen."""
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos_data)
    public_repos = user_data.get("public_repos", 0)
    followers = user_data.get("followers", 0)

    print(f"⭐ Stars: {total_stars}, 🍴 Forks: {total_forks}, 📁 Repos: {public_repos}, 👥 Followers: {followers}")
    return total_stars, total_forks, public_repos, followers

def update_readme(total_stars, total_forks, public_repos, followers):
    """Markdown-Inhalt aktualisieren."""
    stats_md = f"""<!-- STATS-START -->
## 📊 Public GitHub Stats
- **Public Repositories:** {public_repos}
- **Public Total Stars:** {total_stars}
- **Public Total Forks:** {total_forks}
- **Public Followers:** {followers}

*Last updated automatically via GitHub Actions.*
<!-- STATS-END -->"""

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("❌ README.md nicht gefunden!")
        exit(1)

    # Stats-Block ersetzen oder hinzufügen
    pattern = r"<!-- STATS-START -->.*?<!-- STATS-END -->"
    if re.search(pattern, readme_content, re.DOTALL):
        new_readme = re.sub(pattern, stats_md, readme_content, flags=re.DOTALL)
        print("✅ Stats-Bereich in README.md aktualisiert.")
    else:
        new_readme = readme_content.strip() + "\n\n" + stats_md
        print("✅ Stats-Bereich zu README.md hinzugefügt.")

    # Änderungen speichern
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

    print("🎉 Fertig! Die README.md wurde erfolgreich aktualisiert.")

if __name__ == "__main__":
    user_data, repos_data = fetch_github_data()
    total_stars, total_forks, public_repos, followers = calculate_stats(user_data, repos_data)
    update_readme(total_stars, total_forks, public_repos, followers)
