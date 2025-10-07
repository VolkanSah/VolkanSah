import requests
import os
from collections import Counter

# GitHub Username
USERNAME = "VolkanSah"

# GitHub Token
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("❌ GITHUB_TOKEN nicht gefunden! Bitte setzen Sie die Umgebungsvariable.")
    exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# GraphQL-Abfrage für eigene Repos
OWN_REPOS_QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, privacy: PUBLIC, isFork: false) {
      nodes {
        name
        stargazerCount
      }
    }
  }
}
""" % USERNAME

# GraphQL-Abfrage für geforkte Repos
FORKED_REPOS_QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, privacy: PUBLIC, isFork: true) {
      nodes {
        name
        stargazerCount
      }
    }
  }
}
""" % USERNAME

def fetch_github_data(query):
    """Daten von der GitHub GraphQL API abrufen."""
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query},
            headers=HEADERS
        )
        response.raise_for_status()
        data = response.json()

        # Prüfen, ob Fehler in der API-Antwort enthalten sind
        if "errors" in data:
            print(f"❌ API-Fehler: {data['errors']}")
            exit(1)

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API-Fehler: {e}")
        exit(1)

def calculate_stats(data, repo_type):
    """Statistiken für eigene oder geforkte Repos berechnen."""
    repositories = data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    if not repositories:
        print(f"❌ Keine {repo_type} Repositories gefunden oder Daten ungültig.")
        return 0, 0

    total_stars = sum(repo.get("stargazerCount", 0) for repo in repositories)
    total_repos = len(repositories)

    print(f"📊 {repo_type.capitalize()} Repositories: {total_repos}")
    print(f"⭐ {repo_type.capitalize()} Sterne: {total_stars}")

    # Debug: Details zu jedem Repo
    for repo in repositories:
        print(f"  - Repo: {repo['name']}, Stars: {repo.get('stargazerCount', 0)}")

    return total_repos, total_stars

def update_readme(own_repos, own_stars, forked_repos, forked_stars):
    """Aktualisiere die README.md mit den neuen Statistiken."""
    stats_md = f"""<!-- STATS-START -->
## 📊 GitHub Stats
- **Own Public Repositories:** {own_repos}
  - ⭐ Stars: {own_stars}
- **Forked Public Repositories:** {forked_repos}
  - ⭐ Stars: {forked_stars}
- **Total Public Stars:** {own_stars + forked_stars}

*Last updated automatically via GitHub Actions.*
<!-- STATS-END -->"""

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("❌ README.md nicht gefunden!")
        exit(1)

    # Stats-Block ersetzen oder hinzufügen
    import re
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
    # Eigene Repositories abrufen und berechnen
    own_data = fetch_github_data(OWN_REPOS_QUERY)
    own_repos, own_stars = calculate_stats(own_data, "eigene")

    # Geforkte Repositories abrufen und berechnen
    forked_data = fetch_github_data(FORKED_REPOS_QUERY)
    forked_repos, forked_stars = calculate_stats(forked_data, "geforkte")

    # README.md aktualisieren
    update_readme(own_repos, own_stars, forked_repos, forked_stars)
