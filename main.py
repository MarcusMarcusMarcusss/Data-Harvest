import sys
from bs4 import BeautifulSoup
from byPassLogin import get_pageinfo_html
from files import extract_links_from_page,extract_page_links,extract_blanktarget_links,extract_external_url,extract_folder_files,extract_links_from_discussion,extract_forum_discussions,extract_files,extract_folders, extract_url_type_links, extract_forum_links,extract_plain_links

# Headers to bypass login (or use session if you prefer,
# the actual LMS does have a auth security checker and this is the only way to bypass it)
headers = {
    "Cookie": 'MoodleSession=ldapkd213vvai42jqhtcc9vtiv; MOODLEID1_=sodium%3Afvas8yoLIwfnMwPG2YunTW7hcQI%2FHlkyDjWy0m3v7cXzxUyTWbtZtbCbRm1m',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

url = "http://localhost/course/view.php?id=2"
html  = get_pageinfo_html(url, headers)

if html:
    soup = BeautifulSoup(html, "html.parser")
    #print(html)
    # Find the specific section we need
    main_div = soup.find("div", id="topofscroll", class_="main-inner")
    if not main_div:
        print("Target div not found.")
        sys.exit()


    # Extract files and URLs
    found_files = extract_files(main_div, url)
    url_links = extract_url_type_links(main_div, url)
    forum_links = extract_forum_links(html, url)
    plain_links = extract_plain_links(main_div, url)
    blanktarget_links = extract_blanktarget_links(main_div, url)
    found_Folders = extract_folders(main_div, url)
    page_links = extract_page_links(main_div, url)

    if forum_links:
        for forum_name, forum_url in forum_links:

            print(f"Forum name:  {forum_name}")
            print(f"URL: {forum_url}")
            print()
            forum_discussions = extract_forum_discussions(forum_url, headers)

            print("Forum Discussions:")
            for title, url in forum_discussions:
                print(f"Discussion Name: {title}")
                print(f"URL: {url}")
                print()
                
            forum_Post = extract_links_from_discussion(url, headers)
            
            for link in forum_Post:
                print(f"Discussion Name: {title}")
                print(f"Found Link: {link}")

    else:
        print("No Forums found.")

    print()

    print("Extracted URLs Section List:")
    for name, url in url_links:
        print(f"Name: {name}")
        print(f"URL: {url}")
        
        external_link = extract_external_url(url, headers)
        for ext_url in external_link:
            print(f"External URLs: {ext_url}")
            print()


    print("Plain links Section(no role/class):")
    for link in plain_links:
        print(link)
        print()

    print("_blanktarget links Section(no role):")
    for blanktarget_link in blanktarget_links:
        print(blanktarget_link)
        print()

    print("Page Links:")
    for link in page_links:
        print(link)
        print()

        page_link = extract_links_from_page(link, headers)
        for link in page_link:
            print("In Pages:")
            print(link)
            print()

    # Display the file names and URLs
    for file_name, file_url in found_files:
        print(f"File name: {file_name}")
        print(f"URL: {file_url}")
        print()
    
    print("Found Folders:")
    for folder_name, folder_url in found_Folders:
        print(f"Folder name: {folder_name}")
        print(f"URL: {folder_url}")
        print()
        folder_files = extract_folder_files(folder_url, headers)
        for name, url in folder_files:
            print(f"File name: {name}")
            print(f"URL: {url}")
 
else:
    print("Failed to retrieve the page.")