import requests
from bs4 import BeautifulSoup

def get_pageinfo_html(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve page. Status code: {response.status_code}")
        return None
    
def login_to_moodle(session, login_url, username, password):
    # Get login token (Moodle usually uses a hidden token field)
    login_page = session.get(login_url)
    soup = BeautifulSoup(login_page.text, 'html.parser')
    token = soup.find("input", {"name": "logintoken"})
    login_token = token['value'] if token else ''

    payload = {
        'username': username,
        'password': password,
        'logintoken': login_token
    }

    response = session.post(login_url, data=payload)
    return response.ok