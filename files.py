import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def extract_files(main_div, url):
    file_links = []

    for tag in main_div.find_all("a", href=True, class_="aalink stretched-link"):
        span = tag.find("span", class_="instancename")
        if span:
            accesshide = span.find("span", class_="accesshide")
            if accesshide and "File" in accesshide.get_text(strip=True):
                full_text = span.get_text(strip=True)
                file_name = full_text[:-4].strip()

                full_url = urljoin(url, tag["href"])
                file_links.append((file_name, full_url))
    return file_links

def extract_url_type_links(main_div, url):
    found_url_items = []

    for tag in main_div.find_all("a", href=True):
        accesshide = tag.find("span", class_="accesshide")
        if accesshide and accesshide.get_text(strip=True) == "URL":
            instancename_span = tag.find("span", class_="instancename")
            name = instancename_span.get_text(strip=True).replace("URL", "").strip() if instancename_span else "Unknown"
            full_url = urljoin(url, tag["href"])
            found_url_items.append((name, full_url))

    return found_url_items

def extract_external_url(page_url, headers):
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to access the page: {page_url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    main_content = soup.find("div", id="page-content")
    if not main_content:
        print("Main content section not found.")
        return []

    external_links = []
    for tag in main_content.find_all("a", href=True):
        full_url = urljoin(page_url, tag["href"])
        external_links.append(full_url)

    return external_links



def extract_plain_links(main_div, url):

    found_urls = set()
    for tag in main_div.find_all("a", href=True):
        if not tag.has_attr("role") and not tag.has_attr("class"):
            href = tag["href"]
            if "http://localhost/" not in href:
                full_url = urljoin(url, tag["href"])
                found_urls.add(full_url)
    return found_urls

def extract_forum_links(html, url):
    soup = BeautifulSoup(html, "html.parser")
    forum_links = []

    # Find all links that may lead to a forum (by checking for the accesshide Forum span)
    for link in soup.find_all("a", class_="aalink stretched-link"):
        # Check if the span with class 'accesshide' contains the word 'Forum'
        span = link.find("span", class_="accesshide")
        if span and "Forum" in span.get_text(strip=True):
            # It's a forum, extract and return the link and the forum name
            forum_name_tag = link.find("span", class_="instancename")
            
            # Ensure we are only getting the first 'instancename' text
            if forum_name_tag:
                forum_name = forum_name_tag.get_text(strip=True)
                if forum_name.lower().endswith("forum"):
                    forum_name = forum_name[:-5].strip()
                forum_url = urljoin(url, link.get("href"))
                forum_links.append((forum_name, forum_url))
    
    return forum_links

def extract_forum_discussions(forum_url, headers):
    discussions = []

    response = requests.get(forum_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to access the forum: {forum_url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    discussion_table = soup.find("table", class_="table discussion-list generaltable")
    if not discussion_table:
        print("Discussion table not found.")
        return discussions
    
    for tag in discussion_table.find_all("a", class_="w-100 h-100 d-block", href=True):
        discussion_title = tag.get("aria-label", "").strip()
        discussion_url = tag["href"]
        discussions.append((discussion_title, discussion_url))

    return discussions

def extract_links_from_discussion(discussion_url, headers):
    response = requests.get(discussion_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to access the page: {discussion_url}")
        return set()

    soup = BeautifulSoup(response.text, "html.parser")
    post_links = set()

    articles = soup.find_all("article", attrs={"data-region": "post"})
    for article in articles:
        for tag in article.find_all("a", href=True):
            href = tag["href"]
            if "http://localhost/" not in href:
                full_url = urljoin(discussion_url, href)
                post_links.add(full_url)

    return post_links

def extract_folders(main_div, base_url):
    found_folders = []
    for tag in main_div.find_all("a", href=True):
        span = tag.find("span", class_="instancename")
        if span and "Folder" in span.find("span", class_="accesshide").get_text(strip=True):
            folder_url = tag.get("href")
            folder_name = span.get_text(strip=True)
            if len(folder_name) > 6:
                folder_name = folder_name[:-6]  
            if folder_url:
                full_url = urljoin(base_url, folder_url) 
                found_folders.append((folder_name, full_url)) 
    return found_folders


def extract_folder_files(folder_url, headers):
    response = requests.get(folder_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to access the page: {folder_url}")
        return set()

    soup = BeautifulSoup(response.text, "html.parser")

    folder_files = []
    for span in soup.find_all("span", class_="fp-filename"):
        tag = span.find("a", href=True)
        if tag:
            file_url = urljoin(folder_url, tag["href"])
            file_name = tag.get_text(strip=True)
            folder_files.append((file_name, file_url))

    return folder_files