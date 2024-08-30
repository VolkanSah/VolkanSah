import os
import requests
from bs4 import BeautifulSoup
from github import Github
import html2text

# GitHub Authentifizierung
GITHUB_TOKEN = os.environ.get('GH_TOKEN')
REPO_NAME = 'VolkanSah/VolkanSah'
PAGE_URL = 'https://volkansah.github.io/test_jelly/'  # URL Ihrer HTML-Seite oder Angular-App

def get_page_content(url):
    response = requests.get(url)
    return response.text

def html_to_markdown(html_content):
    h = html2text.HTML2Text()
    h.body_width = 0  # Keine Zeilenumbrüche
    return h.handle(html_content)

def update_readme(content):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    try:
        readme = repo.get_contents("README.md")
        current_content = readme.decoded_content.decode()
        
        # Aktualisieren Sie den Inhalt zwischen den Markierungen
        start_marker = "<!-- START_AUTOMATED_SECTION -->"
        end_marker = "<!-- END_AUTOMATED_SECTION -->"
        
        start_index = current_content.find(start_marker)
        end_index = current_content.find(end_marker)
        
        if start_index != -1 and end_index != -1:
            new_content = (
                current_content[:start_index + len(start_marker)] +
                "\n" + content + "\n" +
                current_content[end_index:]
            )
            
            repo.update_file(
                path="README.md",
                message="Automatisches Update der README.md",
                content=new_content,
                sha=readme.sha
            )
            print("README.md erfolgreich aktualisiert.")
        else:
            print("Markierungen in README.md nicht gefunden.")
    
    except Exception as e:
        print(f"Fehler beim Aktualisieren der README.md: {str(e)}")

if __name__ == "__main__":
    html_content = get_page_content(PAGE_URL)
    markdown_content = html_to_markdown(html_content)
    update_readme(markdown_content)
