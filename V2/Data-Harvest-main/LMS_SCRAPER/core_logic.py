import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# Determine Base Directory for Imports/db
LMS_SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(LMS_SCRAPER_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from LMS_SCRAPER.files import (
        extract_all_external_links, extract_potential_file_links,
        extract_url_type_links, extract_page_links, extract_forum_links,
        extract_file_links, extract_external_url, extract_links_from_page,
        extract_forum_discussions, extract_links_from_discussion
    )
    from LMS_SCRAPER.downloader import download_file
except ModuleNotFoundError:
    try:
        from files import (
            extract_all_external_links, extract_potential_file_links,
            extract_url_type_links, extract_page_links, extract_forum_links,
            extract_file_links, extract_external_url, extract_links_from_page,
            extract_forum_discussions, extract_links_from_discussion
        )
        from downloader import download_file
    except ImportError as e2:
        print("Ensure these files are in the LMS_SCRAPER directory.")
        sys.exit(1)

try:
    from DocumentScraper.docx_extractor import extract_urls_from_docx
    from DocumentScraper.pdf_extractor import extract_urls_from_pdf
    from DocumentScraper.pptx_extractor import extract_urls_from_pptx
    from DocumentScraper.excel_extractor import extract_urls_from_excel

except ImportError as e:
    print(f"ERROR in core_logic.py: Could not import document extractor functions: {e}")
    if 'utils' in str(e):
        print("Ensure the extractor files use 'from .utils import ...' (WITH leading dot).")
    sys.exit(1)

try:
    from URLCHECKER.URL_Checker import check_url_virustotal, get_api_delay
except ImportError as e:
    print(f"ERROR in core_logic.py: Could not import VirusTotal functions: {e}")
    print("Ensure URL_Checker.py exists in a 'URLCHECKER' directory relative to the LMS_SCRAPER directory.")
    sys.exit(1)


def get_or_create_content_item(cursor, cache, item_name, item_type, item_path, unit_id=None, local_path=None):
    conn = cursor.connection
    item_id = cache.get(item_path)
    if item_id:
        if local_path:
            try:
                cursor.execute("UPDATE ContentItem SET LocalFilepath = ? WHERE ItemID = ?", (local_path, item_id))
                conn.commit()
            except sqlite3.Error as e:
                print(f"DB Warning: Failed to update LocalFilepath for ItemID {item_id}: {e}")
        return item_id
    try:
        cursor.execute("SELECT ItemID FROM ContentItem WHERE ItemPath = ?", (item_path,))
        result = cursor.fetchone()
        if result:
            item_id = result[0]
            cache[item_path] = item_id
            if local_path:
                try:
                    cursor.execute("UPDATE ContentItem SET LocalFilepath = ? WHERE ItemID = ?", (local_path, item_id))
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"DB Warning: Failed to update LocalFilepath for ItemID {item_id}: {e}")
            return item_id
        else:
            cursor.execute("""
                INSERT INTO ContentItem (UnitID, ItemName, ItemType, ItemPath, LocalFilepath)
                VALUES (?, ?, ?, ?, ?)
            """, (unit_id, item_name, item_type, item_path, local_path))
            item_id = cursor.lastrowid
            conn.commit()
            cache[item_path] = item_id
            return item_id
    except sqlite3.Error as e:
        print(f"DB Error: Failed processing ContentItem for '{item_path}': {e}")
        conn.rollback()
        return None


def insert_extracted_url(cursor, item_id, url_string, location):
    conn = cursor.connection
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    normalized_url = normalize_url_for_db(url_string)
    if not normalized_url:
        return
    if not item_id:
        return
    try:
        cursor.execute("SELECT URLID FROM ExtractedURL WHERE URLString = ?", (normalized_url,))
        existing_url = cursor.fetchone()
        if existing_url:
            return
        cursor.execute("""
            INSERT INTO ExtractedURL (ItemID, URLString, Location, TimeStamp)
            VALUES (?, ?, ?, ?)
        """, (item_id, normalized_url, location, timestamp))
        conn.commit()
    except sqlite3.Error as e:
        print(f"DB Error: Failed checking/inserting ExtractedURL '{normalized_url[:50]}...' for ItemID {item_id}: {e}")
        conn.rollback()


def normalize_url_for_db(url_string):
    if not url_string:
        return None
    url_string = url_string.strip().lower()
    if not url_string.startswith(('http://', 'https://')):
        parts = url_string.split('/', 1)
        if '.' in parts[0]:
            url_string = 'http://' + url_string
        else:
            return url_string
    parsed = urlparse(url_string)
    if parsed.path.endswith('/') and len(parsed.path) > 1:
        normalized_url = url_string.rstrip('/')
    else:
        normalized_url = url_string
    return normalized_url


def initialize_script(db_name, download_dir, course_url, headers):
    session = requests.Session()
    session.headers.update(headers)
    db_conn = None
    db_cursor = None
    try:
        db_path = os.path.join(LMS_SCRAPER_DIR, db_name)
        db_conn = sqlite3.connect(db_path)
        db_cursor = db_conn.cursor()
    except sqlite3.Error as e:
        print(f"CRITICAL ERROR: Could not connect to database '{db_path}': {e}")
        return None
    course_download_dir = download_dir
    base_download_dir_for_reports = download_dir
    course_name_part = "unknown_course"
    try:
        parent_dir = os.path.dirname(LMS_SCRAPER_DIR)
        base_download_path = os.path.join(parent_dir, download_dir)
        os.makedirs(base_download_path, exist_ok=True)
        course_id_match = re.search(r'id=(\d+)', course_url)
        if course_id_match:
            course_name_part = f"course_{course_id_match.group(1)}"
        course_name_part = re.sub(r'[\\/*?:"<>|]', "_", course_name_part)
        course_download_dir = os.path.join(base_download_path, course_name_part)
        os.makedirs(course_download_dir, exist_ok=True)
    except Exception as e:
        print(f"ERROR: Could not create download directories: {e}. Exiting.")
        if db_conn: db_conn.close()
        return None
    data = {
        "session": session, "db_conn": db_conn, "db_cursor": db_cursor,
        "moodle_item_cache": {}, "potential_files_to_process": {},
        "processed_resource_urls": set(), "course_download_dir": course_download_dir,
        "base_download_dir": base_download_path, "course_name_part": course_name_part,
        "course_url": course_url
    }
    return data


def scrape_course_content(data, base_url, course_url, request_delay, request_timeout, default_unit_id):
    session = data["session"]
    db_cursor = data["db_cursor"]
    moodle_item_cache = data["moodle_item_cache"]
    potential_files_to_process = data["potential_files_to_process"]
    processed_resource_urls = data["processed_resource_urls"]

    try:
        time.sleep(request_delay / 2)
        course_page_res = session.get(course_url, timeout=request_timeout)
        course_page_res.raise_for_status()
        if 'text/html' not in course_page_res.headers.get('Content-Type', ''):
            print(f"Error: Course page ({course_url}) did not return HTML content.")
            return False
        course_soup = BeautifulSoup(course_page_res.text, "html.parser")
        main_div = course_soup.find(attrs={"role": "main"}) or course_soup.find("div",
                                                                                id="region-main") or course_soup.body
        if not main_div:
            print("Error: Could not find main content area or body. Exiting.")
            return False
        processed_resource_urls.add(course_url)
        processed_resource_urls.add(course_page_res.url)
        main_page_source_desc = f"Main Course Page ({course_page_res.url})"
        main_page_item_id = None
        direct_external_links = extract_all_external_links(main_div, course_page_res.url, main_page_source_desc)
        direct_file_links = extract_potential_file_links(main_div, course_page_res.url, main_page_source_desc)
        for link, _ in direct_file_links.items():
            if link not in potential_files_to_process:
                potential_files_to_process[link] = {'source_item_id': None, 'file_item_name': 'Unknown File',
                                                    'file_item_type': 'File'}
        url_resources = extract_url_type_links(main_div, base_url)
        page_resource_links = extract_page_links(main_div, base_url)
        forum_resource_links = extract_forum_links(main_div, base_url)
        file_resource_links = extract_file_links(main_div, base_url)
        for name, file_res_url in file_resource_links:
            abs_file_res_url = urljoin(base_url, file_res_url)
            item_type = 'Folder' if '/folder/' in abs_file_res_url else 'File'
            file_item_id = get_or_create_content_item(
                db_cursor, moodle_item_cache, name, item_type, abs_file_res_url, default_unit_id
            )
            if file_item_id:
                potential_files_to_process[abs_file_res_url] = {'source_item_id': file_item_id, 'file_item_name': name,
                                                                'file_item_type': item_type}
        if url_resources:
            for name, url_res_page_url in url_resources:
                abs_url_res_page_url = urljoin(base_url, url_res_page_url)
                if abs_url_res_page_url in processed_resource_urls: continue
                processed_resource_urls.add(abs_url_res_page_url)
                url_item_id = get_or_create_content_item(db_cursor, moodle_item_cache, name, 'URL',
                                                         abs_url_res_page_url, default_unit_id)
                if not url_item_id: continue
                time.sleep(request_delay)
                target_urls = extract_external_url(abs_url_res_page_url, session)
                if target_urls:
                    for target_url in target_urls:
                        parsed_target = urlparse(target_url)
                        if parsed_target.scheme in ['http',
                                                    'https'] and parsed_target.netloc and parsed_target.netloc != urlparse(
                                base_url).netloc:
                            insert_extracted_url(db_cursor, url_item_id, target_url, abs_url_res_page_url)
        if page_resource_links:
            for page_url in page_resource_links:
                abs_page_url = urljoin(base_url, page_url)
                if abs_page_url in processed_resource_urls: continue
                processed_resource_urls.add(abs_page_url)
                page_item_id = get_or_create_content_item(db_cursor, moodle_item_cache,
                                                          f"Page Resource {abs_page_url.split('id=')[-1]}", 'Page',
                                                          abs_page_url, default_unit_id)
                if not page_item_id: continue
                time.sleep(request_delay)
                ext_links_dict, file_links_dict = extract_links_from_page(abs_page_url, session)
                for link, _ in ext_links_dict.items():
                    insert_extracted_url(db_cursor, page_item_id, link, abs_page_url)
                for link, _ in file_links_dict.items():
                    if link not in potential_files_to_process:
                        potential_files_to_process[link] = {'source_item_id': page_item_id,
                                                            'file_item_name': 'Unknown File', 'file_item_type': 'File'}
        if forum_resource_links:
            for forum_name, forum_url in forum_resource_links:
                abs_forum_url = urljoin(base_url, forum_url)
                if abs_forum_url in processed_resource_urls: continue
                processed_resource_urls.add(abs_forum_url)
                time.sleep(request_delay)
                discussions = extract_forum_discussions(abs_forum_url, session)
                for disc_title, disc_url in discussions:
                    abs_disc_url = urljoin(abs_forum_url, disc_url)
                    if abs_disc_url in processed_resource_urls: continue
                    processed_resource_urls.add(abs_disc_url)
                    disc_item_id = get_or_create_content_item(db_cursor, moodle_item_cache, disc_title, 'Discussion',
                                                              abs_disc_url, default_unit_id)
                    if not disc_item_id: continue
                    time.sleep(request_delay)
                    ext_links_dict, file_links_dict = extract_links_from_discussion(abs_disc_url, session, disc_title)
                    for link, _ in ext_links_dict.items():
                        insert_extracted_url(db_cursor, disc_item_id, link, abs_disc_url)
                    for link, _ in file_links_dict.items():
                        if link not in potential_files_to_process:
                            potential_files_to_process[link] = {'source_item_id': disc_item_id,
                                                                'file_item_name': 'Unknown File',
                                                                'file_item_type': 'File'}
        return True
    except Exception as e:
        print(f"\nAn error occurred during content scraping: {e}")
        traceback.print_exc()
        return False


def download_discovered_files(data, request_delay, default_unit_id):
    session = data["session"]
    db_cursor = data["db_cursor"]
    moodle_item_cache = data["moodle_item_cache"]
    potential_files_to_process = data["potential_files_to_process"]
    course_download_dir = data["course_download_dir"]
    download_success_count = 0
    download_fail_count = 0
    processed_files_report_data = []
    print("\n--- Starting File Download Phase ---")
    if potential_files_to_process:
        print(f"Attempting to download {len(potential_files_to_process)} potential file(s)...")
        if not os.path.isdir(course_download_dir):
            print(f"ERROR: Download directory '{course_download_dir}' does not exist. Cannot download files.")
            return download_success_count, download_fail_count, processed_files_report_data
        sorted_file_links = sorted(potential_files_to_process.keys())
        for file_link in sorted_file_links:
            file_details = potential_files_to_process[file_link]
            source_item_id_where_found = file_details['source_item_id']
            file_item_name = file_details['file_item_name']
            file_item_type = file_details['file_item_type']
            if not file_link or not urlparse(file_link).scheme in ['http', 'https']:
                print(f"\nSkipping invalid or non-HTTP(S) file link: {file_link}")
                continue
            preferred_name = file_item_name if file_item_name != 'Unknown File' else "downloaded_file"
            result_path = download_file(session, file_link, course_download_dir, fallback_name=preferred_name)
            # print(f"  DEBUG download_file result: {result_path} (Type: {type(result_path)}) for link {file_link}") # Debug
            if result_path:
                download_success_count += 1
                item_name_for_db = os.path.basename(result_path)
                file_item_id = get_or_create_content_item(
                    db_cursor, moodle_item_cache,
                    item_name=item_name_for_db,
                    item_type=file_item_type,
                    item_path=file_link,
                    unit_id=default_unit_id,
                    local_path=result_path
                )
                if file_item_id:
                    processed_files_report_data.append({
                        'moodle_url': file_link,
                        'source_item_id': source_item_id_where_found,
                        'file_item_id': file_item_id,
                        'local_path': result_path
                    })
            else:
                download_fail_count += 1
            time.sleep(request_delay / 2)
    else:
        print("No potential file links were identified for download.")
    return download_success_count, download_fail_count, processed_files_report_data


def process_downloaded_content(data, processed_files_data):
    db_cursor = data["db_cursor"]
    urls_found_in_docs = 0
    docs_processed_count = 0
    docs_failed_count = 0

    if not processed_files_data:
        print("No downloaded files were processed successfully to analyze.")
        return
    print("\nStarting Document Parsing")
    for file_info in processed_files_data:
        local_path = file_info['local_path']
        file_item_id = file_info['file_item_id']
        moodle_url = file_info['moodle_url']
        if not os.path.exists(local_path):
            print(f"File path not found, skipping analysis: {local_path}")
            docs_failed_count += 1
            continue
        _, extension = os.path.splitext(local_path)
        extension = extension.lower()
        extracted_urls = []
        try:
            if extension == '.pdf':
                extracted_urls = extract_urls_from_pdf(local_path)
            elif extension == '.docx':
                extracted_urls = extract_urls_from_docx(local_path)
            elif extension == '.xlsx':
                extracted_urls = extract_urls_from_excel(local_path)
            elif extension == '.pptx':
                extracted_urls = extract_urls_from_pptx(local_path)
            else:
                continue
            docs_processed_count += 1
            if extracted_urls:
                urls_found_in_docs += len(extracted_urls)
                for url in extracted_urls:
                    insert_extracted_url(db_cursor, file_item_id, url, moodle_url)
        except Exception as e:
            print(f"ERROR during content extraction for {local_path}: {e}")
            docs_failed_count += 1
    print("\nDocument Content Parsing Finished")
    print(f"Documents Analyzed: {docs_processed_count}")
    print(f"URLs Found in Documents: {urls_found_in_docs}")


def check_url(data):
    db_cursor = data["db_cursor"]
    db_conn = data["db_conn"]
    api_delay = get_api_delay()

    print("\nChecking URLs in DB")
    urls_to_check = []
    try:
        db_cursor.execute("SELECT URLID, URLString FROM ExtractedURL")
        urls_to_check = db_cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB Error querying URLs: {e}")
        return

    if not urls_to_check:
        print("No URLs found in the database to analyze.")
        return

    print(f"Found {len(urls_to_check)} URLs to check.")
    analysis_success_count = 0
    analysis_fail_count = 0
    analysis_skipped_count = 0

    for index, (url_id, url_string) in enumerate(urls_to_check):
        if index > 0:
            time.sleep(api_delay)

        report = check_url_virustotal(url_string)

        status = report.get('status', 'error')
        message = report.get('message', 'No details')
        risk_level_category = "Error"
        reputation_source = "VirusTotal"
        analysis_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if status == 'ok':
            stats = report.get('stats', {})
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            if malicious > 0:
                risk_level_category = "Red"
            elif suspicious > 0:
                risk_level_category = "Amber"
            else:
                risk_level_category = "Green"
            analysis_success_count += 1
        elif status == 'not_found':
            risk_level_category = "Not Found"
            analysis_skipped_count += 1
        else:  # status == 'error'
            risk_level_category = "Error"
            analysis_fail_count += 1
            if 'Rate limit exceeded' in message or 'Authentication failed' in message:
                print("Stopping analysis due to API error.")  # Keep critical error
                break

        try:
            db_cursor.execute("SELECT ResultID FROM AnalysisReport WHERE URLID = ?", (url_id,))
            existing_report = db_cursor.fetchone()

            if existing_report:
                db_cursor.execute("""
                    UPDATE AnalysisReport
                    SET RiskLevel = ?, ReputationSource = ?, AnalysisTimestamp = ?
                    WHERE URLID = ?
                """, (risk_level_category, reputation_source, analysis_timestamp, url_id))
            else:
                db_cursor.execute("""
                    INSERT INTO AnalysisReport (URLID, RiskLevel, ReputationSource, AnalysisTimestamp)
                    VALUES (?, ?, ?, ?)
                """, (url_id, risk_level_category, reputation_source, analysis_timestamp))

            db_conn.commit()
        except sqlite3.Error as e:
            print(f"  DB Error inserting/updating analysis report for URLID {url_id}: {e}")  # Keep DB error
            db_conn.rollback()
            if status != 'error':
                analysis_fail_count += 1
                if analysis_success_count > 0: analysis_success_count -= 1
        # ---

    print("\nURL Check Completed")
    print(f"Successfully Analyzed: {analysis_success_count}")
    print(f"Not Found by VT: {analysis_skipped_count}")

