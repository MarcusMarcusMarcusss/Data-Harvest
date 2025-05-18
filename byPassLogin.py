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
    # Get login token
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

def authenticate_moodle(session, login_url, username, password):
    if login_to_moodle(session, login_url, username, password):
        print("Login successful.")
        return True
    print("Login failed.")
    return False

#-----------------------cookie
def prepare_headers(session):
    cookie_string = '; '.join([f"{cookie.name}={cookie.value}" for cookie in session.cookies])
    return {
        # Headers to bypass login (or use session if you prefer,
# the actual LMS does have a auth security checker and this is the only way to bypass it)
        "Cookie": cookie_string,
        "User-Agent": "Mozilla/5.0 ..."
    }

