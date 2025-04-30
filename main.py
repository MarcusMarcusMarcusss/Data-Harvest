import sys
import sqlite3
import time
import requests
from bs4 import BeautifulSoup
from byPassLogin import get_pageinfo_html,login_to_moodle
from files import extract_links_from_page,extract_page_links,extract_blanktarget_links,extract_external_url,extract_folder_files,extract_links_from_discussion,extract_forum_discussions,extract_files,extract_folders, extract_url_type_links, extract_forum_links,extract_plain_links
from request import detect_file_type_from_content,download_file
from dataStructure import ExtractedURLEntry



username = "admin"
password = "Password.1"
login_url = "http://localhost/login/index.php"
course_url = "http://localhost/course/view.php?id=2"

file_URL="http://localhost/mod/resource/view.php?id=5"
file_name="The_PDF"
session = requests.Session()
if login_to_moodle(session, login_url, username, password):
    print("success")
    # Now, download the file using the session
    #download_file(session, file_URL, file_name)
else:
    print("Login failed.")


#-----------------------cookie
cookie_string = '; '.join([f"{cookie.name}={cookie.value}" for cookie in session.cookies])
# Headers to bypass login (or use session if you prefer,
# the actual LMS does have a auth security checker and this is the only way to bypass it)
headers = {
    "Cookie": cookie_string,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
print("\nUpdated Headers with Live Cookies:")
for k, v in headers.items():
    print(f"{k}: {v}")


html  = get_pageinfo_html(course_url,headers)
if html:
    soup = BeautifulSoup(html, "html.parser")
    #print(html)
    # Find the specific section we need
    main_div = soup.find("div", id="topofscroll", class_="main-inner")
    if not main_div:
        print("Target div not found.")
        sys.exit()
    timestamps = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # Extract files and URLs
    found_files = extract_files(main_div, course_url)
    url_links = extract_url_type_links(main_div, course_url)
    forum_links = extract_forum_links(html, course_url)
    plain_links = extract_plain_links(main_div, course_url)
    blanktarget_links = extract_blanktarget_links(main_div, course_url)
    found_Folders = extract_folders(main_div, course_url)
    page_links = extract_page_links(main_div, course_url)
    extractedExternal_urls = []

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
                print()

    else:
        print("No Forums found.")
        print()

    print("Plain links Section(no role/class):")
    for link in plain_links:
        print(link)
        print()
        entry = ExtractedURLEntry(
        itemid=1,
        URLString=link,
        Location="Directly on course page, text section.",
        TimeStamp=timestamps
        )
        extractedExternal_urls.append(entry)

    print("_blanktarget links Section(no role):")
    for blanktarget_link in blanktarget_links:
        print(blanktarget_link)
        print()
        entry = ExtractedURLEntry(
        itemid=1,
        URLString=blanktarget_link,
        Location="Directly on course page, text section.",
        TimeStamp=timestamps
        )
        extractedExternal_urls.append(entry)

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
    print("Extracted URLs Section List:")
    for file_name, file_url in found_files:
        print(f"File name: {file_name}")
        print(f"URL: {file_url}")
        print()
        downloaded_file_name = download_file(session, file_url)
        if downloaded_file_name:
            filenamedetail, timestamp =downloaded_file_name
            print(f"\nDownloaded file: {filenamedetail} at {timestamp}")

            file_type = detect_file_type_from_content(filenamedetail)
            print(f"\nDetected file type: {file_type}")
            print("-" * 40)
        else:
            print("Download failed.")
        
    
    print("Found Folders:")
    for folder_name, folder_url in found_Folders:
        print(f"Folder name: {folder_name}")
        print(f"URL: {folder_url}")
        print()
        folder_files = extract_folder_files(folder_url, headers)
        for name, url in folder_files:
            print(f"File name: {name}")
            print(f"URL: {url}")
            download_folder= download_file(session, url,save_directory=folder_name)
            if download_folder:
                filenamedetail, timestamp =download_folder
                print(f"\nDownloaded file: {filenamedetail} at {timestamp}")

                file_type = detect_file_type_from_content(filenamedetail)
                print(f"\nDetected file type: {file_type}")
                print("-" * 40)
            else:
                print("Download failed.")

        conn = sqlite3.connect('mega_scrape.db')
        cursor = conn.cursor()        
        for entry in extractedExternal_urls:
            cursor.execute('''
                SELECT 1 FROM ExtractedURL
                WHERE itemid = ? AND URLString = ? AND Location = ?
            ''', (entry.itemid, entry.URLString, entry.Location))

            exists = cursor.fetchone()

            if not exists:
                cursor.execute('''
                    INSERT INTO ExtractedURL (itemid, URLString, Location, TimeStamp)
                    VALUES (?, ?, ?, ?)
                ''', (entry.itemid, entry.URLString, entry.Location, entry.TimeStamp))
            else:
                print(f"Skipping duplicate: {entry.URLString}")

        conn.commit()
        conn.close()
 
else:
    print("Failed to retrieve the page.")