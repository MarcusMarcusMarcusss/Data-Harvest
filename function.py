
import time
from bs4 import BeautifulSoup
from byPassLogin import get_pageinfo_html
from files_extract import extract_courses, extract_folder_resources,extract_links_from_page,extract_page_links,extract_blanktarget_links,extract_folder_files,extract_links_from_discussion,extract_forum_discussions,extract_files, extract_url_type_links, extract_forum_links,extract_plain_links
from request import detect_file_type_from_content,download_file
from dataStructure import ContentItemEntry, ExtractedURLEntry, ForumDiscussionEntry, PageLinkEntry, UnitInfoEntry
from database_utils import get_unitid_by_name, insert_ContentItemEntry_files, insert_UnitInfo, insert_extracted_urls, insert_forum_discussions, insert_page_links

def process_courses(course_html, headers):
    soup = BeautifulSoup(course_html, "html.parser")
    main_div = soup.find("div", id="topofscroll", class_="main-inner")
    if not main_div:
        print("Course div not found.")
        return []

    course_info = extract_courses(soup)
    course_entries = []
    for course_name, course_url in course_info:
        unit_entry = UnitInfoEntry(
            CoordinatorID="1",
            UnitName=course_name,
            SchoolName="school of IT",
        )
        course_entries.append((unit_entry, course_url))
    
    insert_UnitInfo([entry[0] for entry in course_entries])
    insert_ContentItemEntry_files([
        ContentItemEntry(
            Unitid=get_unitid_by_name(entry[0].UnitName),
            FileName="Courses Main Page",
            FileType="moodle_course_page",
            URL=entry[1]
        )
        for entry in course_entries
    ])
    return course_entries


def extract_course_content(unit_name,course_url, headers, session):
    html = get_pageinfo_html(course_url, headers)
    if not html:
        print("Failed to retrieve the course page.")
        return

    soup = BeautifulSoup(html, "html.parser")
    main_div = soup.find("div", id="topofscroll", class_="main-inner")
    if not main_div:
        print("Main content div not found.")
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    unit_id = get_unitid_by_name(unit_name)
    extracted_urls = []
    forum_entries = []
    page_entries = []
    file_entries = []

    # Scraper the page
    extract_forums(soup, headers, timestamp, forum_entries,unit_id)
    extract_plain_and_blanktarget_links(soup, timestamp, extracted_urls,unit_id)
    extract_pages_and_links(soup, headers, timestamp, page_entries,unit_id)
    extract_direct_files(soup, course_url, session, timestamp, file_entries,unit_id)
    extract_folders(soup, headers, session, timestamp, file_entries,unit_id)

    # Insert to database
    insert_extracted_urls(extracted_urls)
    insert_forum_discussions(forum_entries)
    insert_page_links(page_entries)
    insert_ContentItemEntry_files(file_entries)


def extract_forums(soup, headers, timestamp, forum_entries,unit_id):
    forum_links = extract_forum_links(str(soup), "")
    if not forum_links:
        print("No forums found.")
        return
    for forum_name, forum_url in forum_links:
        discussions = extract_forum_discussions(forum_url, headers)
        for title, discussion_url in discussions:
            post_links = extract_links_from_discussion(discussion_url, headers)
            for link in post_links:
                entry = ForumDiscussionEntry(
                    discussionid=unit_id,
                    ForumName=forum_name,
                    DiscussionTitle=title,
                    URL=link,
                    TimeStamp=timestamp
                )
                forum_entries.append(entry)

def extract_url_links(soup, timestamp, extracted_urls,unit_id):
    url_links = extract_url_type_links(soup, "")
    for name, link in url_links:
        entry = ExtractedURLEntry(
            itemid=unit_id,
            URLString=link,
            Location=f"Moodle URL resource: {name}",
            TimeStamp=timestamp
        )
        extracted_urls.append(entry)


def extract_plain_and_blanktarget_links(soup, timestamp, extracted_urls,unit_id):
    plain_links = extract_plain_links(soup, "")
    blanktarget_links = extract_blanktarget_links(soup, "")

    for link in plain_links | blanktarget_links:
        entry = ExtractedURLEntry(
            itemid=unit_id,
            URLString=link,
            Location="Directly on course page, text section.",
            TimeStamp=timestamp
        )
        extracted_urls.append(entry)

def extract_pages_and_links(soup, headers, timestamp, page_entries,unit_id):
    page_links = extract_page_links(soup, "")
    for page_url, page_title in page_links:
        internal_links = extract_links_from_page(page_url, headers)
        for link in internal_links:
            entry = PageLinkEntry(
                pageid=unit_id,
                Link=link,
                PageTitle=f"In Pages -> {page_title}",
                TimeStamp=timestamp
            )
            page_entries.append(entry)

def extract_direct_files(soup, course_url, session, timestamp, file_entries,unit_id):
    files = extract_files(soup, course_url)
    for file_name, file_url in files:
        result = download_file(session, file_url)
        if result:
            downloaded_filename, download_time = result
            file_type = detect_file_type_from_content(downloaded_filename)
            entry = ContentItemEntry(
                Unitid=unit_id,
                FileName=file_name,
                FileType=file_type,
                URL=file_url
            )
            file_entries.append(entry)
        else:
            print(f"Failed to download file: {file_name}")


def extract_folders(soup, headers, session, timestamp, file_entries,unit_id):
    folders = extract_folder_resources(soup, "")
    for folder_name, folder_url in folders:
        folder_files = extract_folder_files(folder_url, headers)
        for name, url in folder_files:
            result = download_file(session, url, save_directory=folder_name)
            if result:
                downloaded_filename, download_time = result
                file_type = detect_file_type_from_content(downloaded_filename)
                entry = ContentItemEntry(
                    Unitid=unit_id,
                    FileName=f"{folder_name} -> {name}",
                    FileType=file_type,
                    URL=url
                )
                file_entries.append(entry)
            else:
                print(f"Failed to download file: {name} in folder {folder_name}")