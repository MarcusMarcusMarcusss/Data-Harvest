import requests

def get_pageinfo_html(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve page. Status code: {response.status_code}")
        return None