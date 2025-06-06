import sys
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, urljoin
import os
import re
import sqlite3
from datetime import datetime
import traceback


LMS_SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(LMS_SCRAPER_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)


try:

    from LMS_SCRAPER.files import (
        extract_all_external_links, extract_potential_file_links,extract_courses,
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
        print(f"ERROR in core_logic.py: Could not import from files.py or downloader.py: {e2}")
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
    from URLCHECKER.URL_Checker import check_url_virustotal, get_api_delay, \
        get_domain_creation_date 
except ImportError as e:
    print(f"ERROR in core_logic.py: Could not import VirusTotal/Domain functions: {e}")
    print("Ensure URL_Checker.py exists in a 'URLCHECKER' directory and has necessary functions.")
    sys.exit(1)

def get_or_create_content_item(cursor, cache, item_name, item_type, item_path, unit_id=None, local_path=None,
                               file_hash=None):  # Function to get ItemID from DB, create if it doesnt exist
    conn = cursor.connection
    item_id = cache.get(item_path)
    updated_fields = []
    update_values = []

    if local_path:
        updated_fields.append("LocalFilepath = ?")
        update_values.append(local_path)
    if file_hash:
        updated_fields.append("FileHash = ?")  # Use FileHash
        update_values.append(file_hash)

    if item_id:
        if updated_fields:
            sql = f"UPDATE ContentItem SET {', '.join(updated_fields)} WHERE ItemID = ?"
            update_values.append(item_id)
            try:
                cursor.execute(sql, tuple(update_values))
                conn.commit()
            except sqlite3.Error as e:
                print(f"DB Warning: Failed to update ContentItem for ItemID {item_id}: {e}")
        return item_id
    try:
        cursor.execute("SELECT ItemID FROM ContentItem WHERE ItemPath = ?", (item_path,))
        result = cursor.fetchone()
        if result:
            item_id = result[0]
            cache[item_path] = item_id
            if updated_fields:
                sql = f"UPDATE ContentItem SET {', '.join(updated_fields)} WHERE ItemID = ?"
                update_values.append(item_id)
                try:
                    cursor.execute(sql, tuple(update_values))
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"DB Warning: Failed to update ContentItem for ItemID {item_id}: {e}")
            return item_id
        else:
            # Include FileHash in INSERT
            cursor.execute("""
                INSERT INTO ContentItem (UnitID, ItemName, ItemType, ItemPath, LocalFilepath, FileHash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (unit_id, item_name, item_type, item_path, local_path, file_hash))
            item_id = cursor.lastrowid
            conn.commit()
            cache[item_path] = item_id
            return item_id
    except sqlite3.Error as e:
        print(f"DB Error: Failed processing ContentItem for '{item_path}': {e}")
        conn.rollback()
        return None



def insert_unit_info(cursor,coordinator_id,unit_name,school_name):
    #function to insert record into unit table
    conn = cursor.connection
    try:
        cursor.execute("SELECT 1 FROM Unit WHERE UnitName = ?", (unit_name,))
        existing_url = cursor.fetchone()
        if existing_url:
            return
        cursor.execute("""
            INSERT INTO Unit (CoordinatorID, UnitName, SchoolName)
            VALUES (?, ?, ?)
        """, (coordinator_id, unit_name, school_name))
        conn.commit()

    except sqlite3.Error as e:
        print(f"DB Error: failed inserting Unit for unit name {unit_name}: {e}")
        conn.rollback()

def get_unit_id_by_name(cursor,unit_name):
    conn = cursor.connection
    try:
        cursor.execute("SELECT UnitID FROM Unit WHERE UnitName = ?", (unit_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"DB Error: failed fetching UnitID for '{unit_name}': {e}")
        return None

def insert_extracted_url(cursor, item_id, url_string, location):
    conn = cursor.connection
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    normalized_url = normalize_url_for_db(url_string)
    if not normalized_url or not item_id:
        return

    try:
        # Check if the exact combination already exists
        cursor.execute("""
            SELECT 1 FROM ExtractedURL
            WHERE URLString = ? AND ItemID = ?
        """, (normalized_url, item_id))
        exists = cursor.fetchone()

        if exists:
            return

        # Insert new entry even if same URL used for different ItemID
        cursor.execute("""
            INSERT INTO ExtractedURL (ItemID, URLString, Location, TimeStamp)
            VALUES (?, ?, ?, ?)
        """, (item_id, normalized_url, location, timestamp))
        conn.commit()

    except sqlite3.IntegrityError as e:
        #print(f"Integrity Error: Possibly due to a UNIQUE constraint on URLString: {e}")
        conn.rollback()
    except sqlite3.Error as e:
        #print(f"DB Error: Failed inserting ExtractedURL '{normalized_url[:50]}...' for ItemID {item_id}: {e}")
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
    #Sets up session, DB connection, directories, and initial variables.
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




def scrape_avaliable_course(data, avaliable_course_URL, request_delay, request_timeout):
    # add/create the unit column and add to rows
    # return the unit id and unit name

    session = data["session"]
    db_cursor = data["db_cursor"]
    moodle_item_cache = data["moodle_item_cache"]
    scraped_units = []
    unit_coordinator_id=1
    try:
            time.sleep(request_delay / 2)
            course_page_res = session.get(avaliable_course_URL, timeout=request_timeout)
            course_page_res.raise_for_status()
            if 'text/html' not in course_page_res.headers.get('Content-Type', ''):
                print(f"Error: Course page ({avaliable_course_URL}) did not return HTML content.")
                return False
            course_soup = BeautifulSoup(course_page_res.text, "html.parser")
            main_div = course_soup.find(attrs={"role": "main"}) or course_soup.find("div", id="region-main") or course_soup.body
            if not main_div:
                print("Error: Could not find main content area or body. Exiting.")
                return False
            Course_extract = extract_courses(main_div)
            for name, url in Course_extract:
                insert_unit_info(db_cursor,unit_coordinator_id, name,"School of IT")
                unitid=get_unit_id_by_name(db_cursor,name)
                file_item_id = get_or_create_content_item(
                db_cursor, moodle_item_cache, name,  'Course Page: '+name, url,unitid)
                scraped_units.append({
                    "unit_name": "Found Course: "+name,
                })
            return scraped_units
    except Exception as e:
        print(f"\nAn error occurred during avaliable course scraping: {e}")
        traceback.print_exc()
        return False




def scrape_course_content(data, base_url, course_url, request_delay, request_timeout, default_unit_id,Content_item_ID):
    # helpers, caches, and state
    session = data["session"]
    db_cursor = data["db_cursor"]
    moodle_item_cache = data["moodle_item_cache"]
    potential_files_to_process = data["potential_files_to_process"]
    processed_resource_urls = data["processed_resource_urls"]

    try:
        # fetch the course page
        time.sleep(request_delay / 2)
        course_page_res = session.get(course_url, timeout=request_timeout)
        course_page_res.raise_for_status()
        if 'text/html' not in course_page_res.headers.get('Content-Type', ''):
            print(f"Error: Course page ({course_url}) did not return HTML content.")
            return False
        
        # parse HTML and locate the main content container
        course_soup = BeautifulSoup(course_page_res.text, "html.parser")
        main_div = course_soup.find(attrs={"role": "main"}) or course_soup.find("div", id="region-main") or course_soup.body
        if not main_div:
            print("Error: Could not find main content area or body. Exiting.")
            return False
        # course URL
        processed_resource_urls.add(course_url)
        processed_resource_urls.add(course_page_res.url)
        main_page_source_desc = f"Main Course Page ({course_page_res.url})"

        # external links found directly on the course page
        direct_external_links = extract_all_external_links(main_div, course_page_res.url, main_page_source_desc)
        for link, _ in direct_external_links.items():
            insert_extracted_url(db_cursor, Content_item_ID, link, course_page_res.url)

        # file links directly visible on the course page
        direct_file_links = extract_potential_file_links(main_div, course_page_res.url, main_page_source_desc)
        for link, _ in direct_file_links.items():
            if link not in potential_files_to_process:
                potential_files_to_process[link] = {'source_item_id': None, 'file_item_name': 'Unknown File',
                                                    'file_item_type': 'File'}
        # lists of all resources
        url_resources = extract_url_type_links(main_div, base_url) # type of resource defined as "URL Link" resource in moodle (users are able to just post a link under a content by specifiying as a URL)
        page_resource_links = extract_page_links(main_div, base_url) 
        forum_resource_links = extract_forum_links(main_div, base_url)
        file_resource_links = extract_file_links(main_div, base_url,session)
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
                abs_url_res_page_url = urljoin(base_url, url_res_page_url) # skips if already processed
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
                abs_page_url = urljoin(base_url, page_url) # constructing absolute url
                if abs_page_url in processed_resource_urls: continue
                processed_resource_urls.add(abs_page_url)
                page_item_id = get_or_create_content_item(db_cursor, moodle_item_cache,
                                                          f"Page Resource {abs_page_url.split('id=')[-1]}", 'Page',
                                                          abs_page_url, default_unit_id) #retrivies item location for item table for the page 
                if not page_item_id: continue
                time.sleep(request_delay)
                ext_links_dict, file_links_dict = extract_links_from_page(abs_page_url, session) # visits the page and extracts links in it
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
                discussions = extract_forum_discussions(abs_forum_url, session) # calls a function to extract discussin board link and their titles
                for disc_title, disc_url in discussions:
                    abs_disc_url = urljoin(abs_forum_url, disc_url)
                    if abs_disc_url in processed_resource_urls: continue
                    processed_resource_urls.add(abs_disc_url)
                    disc_item_id = get_or_create_content_item(db_cursor, moodle_item_cache, disc_title, 'Discussion',
                                                              abs_disc_url, default_unit_id) # populates the content item table for discssion
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
    #download files discovered during scraping
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


            download_result = download_file(session, file_link, course_download_dir, fallback_name=preferred_name)

            if download_result and download_result.get('local_path'):
                download_success_count += 1
                local_path = download_result['local_path']
                file_hash = download_result.get('file_hash')  
                item_name_for_db = os.path.basename(local_path)

                file_item_id = get_or_create_content_item(
                    db_cursor, moodle_item_cache,
                    item_name=item_name_for_db,
                    item_type=file_item_type,
                    item_path=file_link,
                    unit_id=default_unit_id,
                    local_path=local_path,
                    file_hash=file_hash  
                )
                if file_item_id:
                    processed_files_report_data.append({
                        'moodle_url': file_link,
                        'source_item_id': source_item_id_where_found,
                        'file_item_id': file_item_id,
                        'local_path': local_path,
                        'file_hash': file_hash  
                    })
            else:
                download_fail_count += 1
            time.sleep(request_delay / 2)
    else:
        print("No potential file links were identified for download.")
    return download_success_count, download_fail_count, processed_files_report_data


def process_downloaded_content(data, processed_files_data):
    #Iterates through successfully downloaded files, extracts URLs from their content,
    #and inserts them into the database.

    db_cursor = data["db_cursor"]
    urls_found_in_docs = 0
    docs_processed_count = 0
    docs_failed_count = 0
    if not processed_files_data:
        print("No downloaded files were processed successfully to analyze.")
        return
    print("\nStarting Document Content Processing")
    print(f"Analyzing content of {len(processed_files_data)} downloaded file(s)...")
    for file_info in processed_files_data:
        local_path = file_info['local_path']
        file_item_id = file_info['file_item_id']
        moodle_url = file_info['moodle_url']
        if not os.path.exists(local_path):
            print(f"WARNING: File path not found, skipping analysis: {local_path}")
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
            print(f"  -> ERROR during content extraction for {local_path}: {e}")
            docs_failed_count += 1
    print("\nDocument Content Processing Finished")
    print(f"  Documents Analyzed: {docs_processed_count}")
    print(f"  URLs Found in Documents: {urls_found_in_docs}")
    print(f"  Documents Failed/Skipped: {docs_failed_count}")


def check_url(data,unit_id):

    #Queries database for ALL URLs, checks them via VirusTotal, gets domain registration date,
    #and UPSERTS results into AnalysisReport table.

    db_cursor = data["db_cursor"]
    db_conn = data["db_conn"]
    api_delay = get_api_delay()

    print("\nStarting URL Analysis (VirusTotal & Domain Age)")
    urls_to_check = []
    try:
        query = """
            SELECT e.URLID, e.URLString
            FROM ExtractedURL e
            JOIN ContentItem c ON e.ItemID = c.ItemID
            WHERE c.UnitID = ?
        """
        db_cursor.execute(query, (unit_id,))
        urls_to_check = db_cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB Error querying URLs: {e}")
        return

    if not urls_to_check:
        print("No URLs found in the database to analyze.")
        return

    print(f"Found {len(urls_to_check)} URLs to check/re-check.")
    analysis_success_count = 0
    analysis_fail_count = 0
    analysis_skipped_count = 0

    for index, (url_id, url_string) in enumerate(urls_to_check):
        if index > 0:
            time.sleep(api_delay)  # Delay for VirusTotal

        print(f"\nAnalyzing URL {index + 1}/{len(urls_to_check)} (URLID: {url_id}): {url_string}")

        # 1. Get VirusTotal Report
        vt_report = check_url_virustotal(url_string)
        vt_status = vt_report.get('status', 'error')
        vt_message = vt_report.get('message', 'No details')
        risk_level_category = "Error"
        reputation_source = "VirusTotal"
        analysis_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if vt_status == 'ok':
            stats = vt_report.get('stats', {})
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            if malicious > 0:
                risk_level_category = "Red"
            else:
                risk_level_category = "Green"
            print(f"  VT Result: Category={risk_level_category} (M:{malicious}, S:{suspicious})")
            analysis_success_count += 1
        elif vt_status == 'not_found':
            #check_url_reachability sending session
            is_reachable = check_url_reachability(url_string)
            if not is_reachable:
                print("  Status Check: URL is unreachable or broken.")
                risk_level_category = "Broken Link"
            else:
                risk_level_category = "Not Found"
            print(f"  VT Result: {vt_message}")

            analysis_skipped_count += 1
        else:  # vt_status == 'error'
            risk_level_category = "VT Error"  # More specific error type
            print(f"  VT Result: {vt_status} - {vt_message}")
            analysis_fail_count += 1
            if 'Rate limit exceeded' in vt_message or 'Authentication failed' in vt_message:
                print("Stopping analysis due to VirusTotal API error.")
                break

        # 2. Get Domain Creation Date
        domain_creation_date = get_domain_creation_date(url_string)  # Call new function
        if domain_creation_date:
            print(f"  Domain Creation Date: {domain_creation_date}")
        else:
            print(f"  Domain Creation Date: Not found or error.")
            domain_creation_date = None  # Ensure it's None for DB if not found

        #UPSERT into AnalysisReport table
        try:
            db_cursor.execute("SELECT ResultID FROM AnalysisReport WHERE URLID = ?", (url_id,))
            existing_report = db_cursor.fetchone()

            if existing_report:
                db_cursor.execute("""
                    UPDATE AnalysisReport
                    SET RiskLevel = ?, ReputationSource = ?, AnalysisTimestamp = ?, DomainCreationDate = ?
                    WHERE URLID = ?
                """, (risk_level_category, reputation_source, analysis_timestamp, domain_creation_date, url_id))
            else:
                db_cursor.execute("""
                    INSERT INTO AnalysisReport (URLID, RiskLevel, ReputationSource, AnalysisTimestamp, DomainCreationDate)
                    VALUES (?, ?, ?, ?, ?)
                """, (url_id, risk_level_category, reputation_source, analysis_timestamp, domain_creation_date))
            db_conn.commit()
        except sqlite3.Error as e:
            print(f"  DB Error inserting/updating analysis report for URLID {url_id}: {e}")
            db_conn.rollback()
            if vt_status != 'error':
                analysis_fail_count += 1
                if analysis_success_count > 0: analysis_success_count -= 1

    print("\n Analysis Finished")
    print(f" Successfully Analyzed/Updated: {analysis_success_count}")
    print(f" Not Found / Skipped by VT: {analysis_skipped_count}")


def check_url_reachability(url):
    try:
        with requests.Session() as session:
            response = session.head(url, allow_redirects=True, timeout=5)
            if response.status_code < 400:
                return True
            else:
                return False
    except requests.RequestException:
        return False

def delete_processed_files(processed_files_data): #delets files after processing
    if not processed_files_data:
        return

    for file_info in processed_files_data:
        local_path = file_info.get('local_path')

        if not local_path:
            # If local_path is missing in the data, cannot delete
            continue

        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

def get_CoursePage_Urls(db_path, unit_name): 
    query = """
        SELECT 
            u.UnitID,
            u.CoordinatorID,
            c.ItemID,
            c.ItemPath
        FROM 
            Unit u
        JOIN 
            ContentItem c ON u.UnitID = c.UnitID
        WHERE 
            u.UnitName = ?
            AND c.ItemName = ?
            AND c.ItemType = ?;
    """

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(query, (unit_name, unit_name, f"Course Page: {unit_name}"))
        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        print(f"CRITICAL ERROR: Could not connect to database '{db_path}': {e}")
        return []

    finally:
        if conn:
            conn.close()

def delete_unit_content(unit_id, db_path='mega_scrape.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Find ItemIDs to delete (except course page items)
        cursor.execute("""
            SELECT ItemID FROM ContentItem
            WHERE UnitID = ? AND ItemType NOT LIKE 'Course Page:%'
        """, (unit_id,))
        item_ids = [row[0] for row in cursor.fetchall()]

        if item_ids:
            cursor.executemany(
                "DELETE FROM ExtractedURL WHERE ItemID = ?",
                [(item_id,) for item_id in item_ids]
            )
            print(f"Deleted {cursor.rowcount} rows from ExtractedURL.")

            cursor.executemany(
                "DELETE FROM ContentItem WHERE ItemID = ?",
                [(item_id,) for item_id in item_ids]
            )
            print(f"Deleted {cursor.rowcount} rows from ContentItem.")
        else:
            print(f"No deletable content items found for UnitID {unit_id}.")

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")