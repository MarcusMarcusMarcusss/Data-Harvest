import json
import sys
import sqlite3
import time
import traceback
import os

try:
    from auth import login_to_moodle
except ImportError:
    print("ERROR: Could not import 'login_to_moodle' from auth.py.")
    sys.exit(1)
try:
    from core_logic import (
        initialize_script,get_CoursePage_Urls,
        scrape_course_content,
        download_discovered_files,
        process_downloaded_content,
        check_url,
        delete_processed_files,delete_unit_content
    )
except ImportError as e:
    print(f"ERROR: Could not import functions from core_logic.py: {e}")
    sys.exit(1)
try:
    from report_generator import generate_php_report,generate_Overall_php_report
except ImportError:
    print("Ensure report_generator.py exists in the LMS_SCRAPER directory.")
    sys.exit(1)
BASE_URL = "http://localhost"
LOGIN_URL = f"{BASE_URL}/login/index.php"
#https://moodleprod.murdoch.edu.au/course/index.php?categoryid=202&browse=courses&perpage=all&page=1#
COURSE_All_COURSE= f"{BASE_URL}/course/index.php"
COURSE_URL = f"{BASE_URL}/course/view.php?id=2"
USERNAME = "Admin"
PASSWORD = "Password.1"
DOWNLOAD_DIR = "moodle_downloads"
DB_NAME = "mega_scrape.db"
PHP_REPORT_FILENAME = "report_checker.php"
DEFAULT_UNIT_ID = 1
DELETE_FILES_AFTER_PROCESSING = True
LMS_SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(LMS_SCRAPER_DIR, DB_NAME)
REQUEST_DELAY = 1.5
REQUEST_TIMEOUT = 25
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}



if __name__ == "__main__":

    courses_to_scan = []
    path_php=[]
    if len(sys.argv) > 1:
        
        raw_input = sys.argv[1].strip("[] ").strip()
        print("Raw input:", raw_input)
        
        courses = [c.strip() for c in raw_input.split(',')]
        print("Parsed courses:", courses)

        for course in courses:
            print(f"\nFetching data for course: {course}")
            items = get_CoursePage_Urls(db_path, course)
            if items:
                for row in items:
                    #print(f"UnitID: {row[0]}, CoordinatorID: {row[1]}, ItemID: {row[2]}, ItemPath: {row[3]}")
                    script_data = initialize_script(DB_NAME, DOWNLOAD_DIR, row[3], HEADERS)
                    if not script_data or not script_data.get("db_conn"):
                        print("Initialization failed. Exiting.")
                        sys.exit(1)
                    session = script_data["session"]
                    db_conn = script_data["db_conn"]
                    try:
                        #login pass
                        logged_in = login_to_moodle(session, LOGIN_URL, USERNAME, PASSWORD)
                        if not logged_in:
                            print("\nLogin Failed")
                            sys.exit(1)
                        #Remove existing data associate with the unit to ensure new entry can be stored and old entry is removed
                        delete_unit_content(row[0],db_path)
                        # grabing course content
                        scraping_successful = scrape_course_content(
                            script_data, BASE_URL, row[3], REQUEST_DELAY, REQUEST_TIMEOUT, row[0],row[2]
                        )
                        if scraping_successful:
                            dl_success, dl_fail, processed_files_data = download_discovered_files(
                            script_data, REQUEST_DELAY, row[0])

                        if processed_files_data:
                            process_downloaded_content(script_data, processed_files_data)
                        else:
                            if dl_success == 0 and dl_fail == 0:
                                pass
                            else:
                                print("\nNo files were successfully processed.")
                        check_url(script_data,row[0])

                        print("\nDownload Summary")
                        print(f"Successfully downloaded: {dl_success}")
                        if dl_success > 0 :
                            print(f"Downloaded files saved under: {script_data['course_download_dir']}")
                        else:
                            print("\nAborting after error during content scraping.")

                    except Exception as e:
                        print(f"\nCRITICAL UNEXPECTED ERROR in main execution: {e}")
                        traceback.print_exc()
                    finally:
                        if db_conn:
                            try:
                                db_conn.close()
                                print("\nDatabase connection closed.")
                            except sqlite3.Error as e:
                                print(f"Error closing database connection: {e}")             
                        if DELETE_FILES_AFTER_PROCESSING:
                            if processed_files_data:
                                delete_processed_files(processed_files_data)
                        else:
                            print("\nSkipping deletion of processed files as per configuration.")
                        
                        course_inspector = "course_inspector_" + course + ".php"
                        report_url = generate_php_report(DB_NAME, course_inspector,row[3],course,row[0],)
                        path_php.append({
                            "course_ID": row[0],
                            "course_name": course,
                            "course_php_URL": report_url
                        })
                        print("\n=== PHP Report Summary ===")
                        for entry in path_php:
                            print(f"Course: {entry['course_name']} | Report URL: {entry['course_php_URL']}")
                course_Overview = "course_Overview.php"
                generate_Overall_php_report(DB_NAME, course_Overview,path_php)

            else:
                print("No results found or query failed.")
    else:
        print("No arguments received.")



