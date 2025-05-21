from bs4 import BeautifulSoup


def login_to_moodle(session, login_url, username, password):
    login_page_res = session.get(login_url, timeout=15)
    login_page_res.raise_for_status()
    soup = BeautifulSoup(login_page_res.text, 'html.parser')

    print(f"\nAttempting Login")
    # Find login token
    logintoken_input = soup.find('input', {'name': 'logintoken'})
    if not logintoken_input:
        login_form = soup.find('form', id='login')
        if login_form:
            logintoken = ''
        else:
            print("ERROR: Login form not found either. Cannot proceed with login.")
            return False
    else:
        logintoken = logintoken_input.get('value', '')

    payload = {
        'anchor': '',
        'logintoken': logintoken,
        'username': username,
        'password': password,
        'rememberusername': 1,
    }

    login_res = session.post(login_url, data=payload, timeout=20)
    login_res.raise_for_status()

    # Check for Login Success
    final_soup = BeautifulSoup(login_res.text, 'html.parser')
    user_menu = final_soup.find('div', id='usermenu')
    user_name_element = final_soup.find('span', class_='usertext')

    if user_menu or user_name_element:
        print("Login Successful")
        return True  # Login successful

    logout_link = final_soup.find('a', href=lambda href: href and 'logout.php' in href)
    if logout_link:
        print("Login Successful")
        return True
