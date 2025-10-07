import requests
import os

# GitHub Username
USERNAME = "VolkanSah"

# Token holen
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("❌ GITHUB_TOKEN nicht gefunden! Bitte setzen Sie die Umgebungsvariable.")
    exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# GraphQL-Abfrage
QUERY = """
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

def fetch_github_data():
    """Daten von der GitHub GraphQL API abrufen."""
    try:
        print("🔍 Hole Repository-Daten über GraphQL...")
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": QUERY},
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

def calculate_stats(data):
    """Statistiken basierend auf den GraphQL-Daten berechnen."""
    repositories = data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    if not repositories:
        print("❌ Keine Repositories gefunden oder Daten ungültig.")
        exit(1)

    total_stars = sum(repo.get("stargazerCount", 0) for repo in repositories)
    total_repos = len(repositories)

    print(f"📊 Gefundene Repositories: {total_repos}")
    print(f"⭐ Gesamtanzahl Sterne: {total_stars}")

    return total_repos, total_stars

def update_readme(total_repos, total_stars):
    """Aktualisiere die README.md mit den neuen Statistiken."""
    stats_md = f"""<!-- STATS-START -->
## 📊 GitHub Stats
- **Public Repositories:** {total_repos}
- **Public Total Stars:** {total_stars}

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
    data = fetch_github_data()
    total_repos, total_stars = calculate_stats(data)
    update_readme(total_repos, total_stars)
