import sqlite3
DB_PATH = r"mega_scrape.db"

def fix_extractedurl_fk():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    try:
        # Step 1: Rename the old table
        cursor.execute("ALTER TABLE ExtractedURL RENAME TO ExtractedURL_old;")

        # Step 2: Create new ExtractedURL with corrected FK and TimeStamp
        cursor.execute("""
            CREATE TABLE ExtractedURL (
                URLID INTEGER PRIMARY KEY AUTOINCREMENT,
                ItemID INTEGER,
                URLString TEXT,
                Location TEXT,
                TimeStamp TEXT,
                FOREIGN KEY (ItemID) REFERENCES ContentItem(ItemID)
            );
        """)

        # Step 3: Copy data (include TimeStamp)
        cursor.execute("""
            INSERT INTO ExtractedURL (URLID, ItemID, URLString, Location, TimeStamp)
            SELECT URLID, ItemID, URLString, Location, TimeStamp FROM ExtractedURL_old;
        """)

        # Step 4: Drop the old table
        cursor.execute("DROP TABLE ExtractedURL_old;")

        conn.commit()
        print("Foreign key and schema updated successfully.")

    except sqlite3.Error as e:
        print("Error:", e)
        conn.rollback()

    finally:
        conn.close()

fix_extractedurl_fk()












import sys
import sqlite3
import time
import requests
from bs4 import BeautifulSoup
from byPassLogin import prepare_headers,authenticate_moodle,get_pageinfo_html,login_to_moodle
from files_extract import extract_courses,extract_links_from_page,extract_page_links,extract_blanktarget_links,extract_external_url,extract_folder_files,extract_links_from_discussion,extract_forum_discussions,extract_files,extract_folders, extract_url_type_links, extract_forum_links,extract_plain_links
from request import detect_file_type_from_content,download_file
from dataStructure import ContentItemEntry, ExtractedURLEntry, ForumDiscussionEntry, PageLinkEntry, UnitInfoEntry
from database_utils import get_unitid_by_name, insert_ContentItemEntry_files, insert_UnitInfo, insert_extracted_urls, insert_forum_discussions, insert_page_links

#https://moodleprod.murdoch.edu.au/course/index.php?categoryid=202&browse=courses&perpage=all&page=1#
username = "admin"
password = "Password.1"
login_url = "http://localhost/login/index.php"
courses_HTML="http://localhost/course/index.php"
course_url = "http://localhost/course/view.php?id=2"
session = requests.Session()
#edit
authenticate_moodle(session, login_url, username, password)
#cookies
headers=prepare_headers(session)

course_page_html = get_pageinfo_html(courses_HTML,headers)
if course_page_html:
    soup = BeautifulSoup(course_page_html, "html.parser")
    main_div = soup.find("div", id="topofscroll", class_="main-inner")
    if not main_div:
        print("Target div not found.")
        sys.exit()
    course_info = extract_courses(soup)
    course_entries = []
    for course_name, course_url in course_info:
        #print(f"Course Title: {course_name}")
        #print(f"Course URL: {course_url}")
        #print("*" * 35)
        unit_entry = UnitInfoEntry(
        CoordinatorID="1",
        UnitName=course_name,
        SchoolName="school of IT",
        )
        course_entries.append((unit_entry,course_url))
    unit_list = [entry[0] for entry in course_entries]
    insert_UnitInfo(unit_list)

    content_items = []
    for unit_entry, course_url in course_entries:
        unit_id = get_unitid_by_name(unit_entry.UnitName)
        if unit_id:
            content_items.append(ContentItemEntry(
                Unitid=unit_id,
                FileName="Courses Main Page",
                FileType="moodle_course_page",
                URL=course_url,
            ))
        else:
            print(f"UnitID not found for course: {unit_entry.UnitName}")

    insert_ContentItemEntry_files(content_items)

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
    forum_entries = []
    page_entries = []
    file_entries = []
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
                entry = ForumDiscussionEntry(
                    discussionid=1,
                    ForumName=forum_name,
                    DiscussionTitle=title,
                    URL=link,
                    TimeStamp=timestamps
                )
                forum_entries.append(entry)

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
    for link, title in page_links:
        print(f"Page URL: {link}")
        print(f"Page Title: {title}")
        print()

        page_link = extract_links_from_page(link, headers)
        for links in page_link:
            print("In Pages:")
            print(links)
            print()
            entry = PageLinkEntry(
            pageid=1,
            Link=links,
            PageTitle=f"In Pages -> {title}",
            TimeStamp=timestamps
        )
        page_entries.append(entry)




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
            entry = ContentItemEntry(
            Unitid=1, 
            FileName=file_name,
            FileType=file_type,
            URL=file_url)
            file_entries.append(entry)
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

                entry = ContentItemEntry(
                Unitid=1,  
                FileName=f"{folder_name} -> {name}",
                FileType=file_type,
                URL=url)
                file_entries.append(entry)
            else:
                print("Download failed.")
    
    #add to db
    insert_extracted_urls(extractedExternal_urls)
    insert_forum_discussions(forum_entries)
    insert_page_links(page_entries)
    insert_ContentItemEntry_files(file_entries)


else:
    print("Failed to retrieve the page.")