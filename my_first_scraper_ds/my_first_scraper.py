import requests
from bs4 import BeautifulSoup   
import pandas as pd

def request_github_trending(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response  
    else:
        raise Exception(f"Failed: \nStatus code: {response.status_code}")


def extract(page):
    if isinstance(page, requests.Response):
        page = page.text

    soup = BeautifulSoup(page, 'html.parser')
    repositories = soup.find_all('article', class_='Box-row')
    return repositories

def transform(html_repos):
    dev = []
    repo_names = []
    nbr_stars = []

    for repo in html_repos:
        dev_repo_name = repo.find('h1', class_='h3 lh-condensed').get_text(strip=True)
        developer, repository_name = [part.strip() for part in dev_repo_name.split('/', 1)]
        stars = repo.find('a', class_='Link--muted d-inline-block mr-3').get_text(strip=True)

        dev.append(developer)
        repo_names.append(repository_name)
        nbr_stars.append(stars)

    repo_df = pd.DataFrame({'developer': dev, 'repository_name': repo_names, 'nbr_stars': nbr_stars})

    return repo_df.to_dict("records")


def format(repositories_data):
    if isinstance(repositories_data, list):
        repositories_data = pd.DataFrame(repositories_data)
        
    output_df = repositories_data[['developer', 'repository_name', 'nbr_stars']].copy()
    output_df.columns = ['Developer', 'Repository Name', 'Number of Stars']
    
    csv_string = output_df.to_csv(index=False, line_terminator='\n')
    
    return csv_string


if __name__ == "__main__":
    url = 'https://storage.googleapis.com/qwasar-public/track-ds/trending_14_06_2022'
    page = request_github_trending(url).text
    html_repositories = extract(page)
    df_repos = transform(html_repositories)
    top25_repos = df_repos.head(25)

    output_csv = format(top25_repos)
    print(output_csv)