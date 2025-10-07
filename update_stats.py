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
    """Holt ALLE Repos mit Pagination"""
    all_repos = []
    has_next = True
    cursor = None
    
    while has_next:
        query = """
        {
          user(login: "%s") {
            repositories(first: 100, privacy: PUBLIC, isFork: %s%s) {
              nodes {
                name
                stargazerCount
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
    """Berechnet Stats"""
    total_stars = sum(repo.get("stargazerCount", 0) for repo in repos)
    total_repos = len(repos)
    
    print(f"\n📊 {repo_type.capitalize()} Repositories: {total_repos}")
    print(f"⭐ {repo_type.capitalize()} Sterne: {total_stars}")
    
    # Top 5 Repos mit meisten Stars
    top_repos = sorted(repos, key=lambda x: x.get("stargazerCount", 0), reverse=True)[:5]
    print(f"\n🏆 Top 5 {repo_type} Repos:")
    for repo in top_repos:
        print(f"  - {repo['name']}: {repo.get('stargazerCount', 0)} ⭐")
    
    return total_repos, total_stars

def update_readme(own_repos, own_stars, forked_repos, forked_stars):
    """Aktualisiert die README"""
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
    own_repos, own_stars = calculate_stats(own_repos_data, "eigene")
    
    print("\n🔍 Hole geforkte Repositories...")
    forked_repos_data = fetch_all_repos(True)
    forked_repos, forked_stars = calculate_stats(forked_repos_data, "geforkte")
    
    print(f"\n📈 GESAMT:")
    print(f"  Repos: {own_repos + forked_repos}")
    print(f"  Stars: {own_stars + forked_stars}")
    
    update_readme(own_repos, own_stars, forked_repos, forked_stars)
