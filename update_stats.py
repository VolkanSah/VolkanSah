import requests
import os
import re

USERNAME = "VolkanSah"
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("❌ GITHUB_TOKEN nicht gefunden!")
    exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def fetch_all_repos(is_fork):
    """Holt ALLE Repos mit Pagination + erweiterten Infos"""
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
                owner {
                  login
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """ % (USERNAME, str(is_fork).lower(), f', after: "{cursor}"' if cursor else '')
        
        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query},
                headers=HEADERS
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                print(f"❌ API-Fehler: {data['errors']}")
                exit(1)
            
            repos = data["data"]["user"]["repositories"]
            all_repos.extend(repos["nodes"])
            
            page_info = repos["pageInfo"]
            has_next = page_info["hasNextPage"]
            cursor = page_info["endCursor"]
            
            print(f"  📦 {len(repos['nodes'])} Repos geholt (Gesamt: {len(all_repos)})")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API-Fehler: {e}")
            exit(1)
    
    return all_repos

def calculate_stats(repos, repo_type):
    """Berechnet Stats mit Filter"""
    # Filter: Nur aktive, nicht-archivierte Repos
    active_repos = [
        r for r in repos 
        if not r.get("isArchived", False) 
        and not r.get("isDisabled", False)
        and not r.get("isLocked", False)
        and r.get("owner", {}).get("login") == USERNAME
    ]
    
    # Archivierte Repos separat
    archived_repos = [
        r for r in repos 
        if (r.get("isArchived", False) or r.get("isDisabled", False) or r.get("isLocked", False))
        and r.get("owner", {}).get("login") == USERNAME
    ]
    
    archived = len(archived_repos)
    archived_stars = sum(repo.get("stargazerCount", 0) for repo in archived_repos)
    
    total_stars = sum(repo.get("stargazerCount", 0) for repo in active_repos)
    total_repos = len(active_repos)
    
    print(f"\n📊 {repo_type.capitalize()} Repositories:")
    print(f"  ✅ Aktiv: {total_repos}")
    if archived > 0:
        print(f"  🗄️  Archiviert/Deaktiviert: {archived} (mit {archived_stars} ⭐)")
    print(f"⭐ {repo_type.capitalize()} Sterne:")
    print(f"  Aktiv: {total_stars}")
    if archived_stars > 0:
        print(f"  Archiv: {archived_stars} 💎")
    print(f"  Gesamt: {total_stars + archived_stars}")
    
    # Top 10 mit meisten Stars + Statuscheck
    print(f"\n🏆 Top 10 {repo_type} Repos:")
    top_repos = sorted(active_repos, key=lambda x: x.get("stargazerCount", 0), reverse=True)[:10]
    for i, repo in enumerate(top_repos, 1):
        status = ""
        if repo.get("isArchived"):
            status = " [ARCHIVIERT]"
        elif repo.get("isDisabled"):
            status = " [DEAKTIVIERT]"
        print(f"  {i:2}. {repo['name']:40} {repo.get('stargazerCount', 0):4} ⭐{status}")
    
    # Detaillierte Liste ALLER Repos mit Stars (zum manuellen Nachprüfen)
    print(f"\n📋 Alle {repo_type} Repos mit Stars:")
    repos_with_stars = sorted(
        [r for r in active_repos if r.get("stargazerCount", 0) > 0],
        key=lambda x: x.get("stargazerCount", 0),
        reverse=True
    )
    for repo in repos_with_stars:
        print(f"  - {repo['name']:40} {repo.get('stargazerCount', 0):4} ⭐")
    
    print(f"\n  Repos mit 0 Stars: {total_repos - len(repos_with_stars)}")
    
    return total_repos, total_stars, archived

def update_readme(own_repos, own_stars, forked_repos, forked_stars):
    """Aktualisiert die README"""
    stats_md = f"""<!-- STATS-START -->
## 📊 GitHub Stats (Active Repos Only)
- **Own Public Repositories:** {own_repos}
  - ⭐ Stars: {own_stars}
- **Forked Public Repositories:** {forked_repos}
  - ⭐ Stars: {forked_stars}
- **Total Public Stars:** {own_stars + forked_stars}

*Last updated automatically via GitHub Actions. Excludes archived/disabled repositories.*
<!-- STATS-END -->"""
    
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("❌ README.md nicht gefunden!")
        exit(1)
    
    pattern = r"<!-- STATS-START -->.*?<!-- STATS-END -->"
    if re.search(pattern, readme_content, re.DOTALL):
        new_readme = re.sub(pattern, stats_md, readme_content, flags=re.DOTALL)
        print("\n✅ Stats-Bereich aktualisiert.")
    else:
        new_readme = readme_content.strip() + "\n\n" + stats_md
        print("\n✅ Stats-Bereich hinzugefügt.")
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)
    
    print("🎉 Fertig!")

if __name__ == "__main__":
    print("🔍 Hole eigene Repositories...")
    own_repos_data = fetch_all_repos(False)
    own_repos, own_stars, own_archived = calculate_stats(own_repos_data, "eigene")
    
    print("\n" + "="*80)
    print("🔍 Hole geforkte Repositories...")
    forked_repos_data = fetch_all_repos(True)
    forked_repos, forked_stars, forked_archived = calculate_stats(forked_repos_data, "geforkte")
    
    print("\n" + "="*80)
    print(f"📈 GESAMT (NUR AKTIVE):")
    print(f"  Repos: {own_repos + forked_repos}")
    print(f"  Stars: {own_stars + forked_stars}")
    print(f"\n🗄️  Gesamt archiviert/deaktiviert: {own_archived + forked_archived}")
    
    # Manuelle Verifikation
    print("\n" + "="*80)
    print("🔍 MANUELLE VERIFIKATION:")
    print("Gehe zu: https://github.com/VolkanSah?tab=repositories")
    print("Zähle manuell die öffentlichen Repos und vergleiche!")
    
    update_readme(own_repos, own_stars, forked_repos, forked_stars)
