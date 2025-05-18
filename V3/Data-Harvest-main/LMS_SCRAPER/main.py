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
        initialize_script,
        scrape_course_content,
        download_discovered_files,
        process_downloaded_content,
        check_url,
        delete_processed_files
    )

except ImportError as e:
    print(f"ERROR: Could not import functions from core_logic.py: {e}")
    sys.exit(1)
try:
    from report_generator import generate_php_report
except ImportError:
    print("Ensure report_generator.py exists in the LMS_SCRAPER directory.")
    sys.exit(1)
BASE_URL = "http://localhost"
LOGIN_URL = f"{BASE_URL}/login/index.php"
COURSE_URL = f"{BASE_URL}/course/view.php?id=2"
USERNAME = "scraper"
PASSWORD = "Scraper123$"
DOWNLOAD_DIR = "moodle_downloads"
DB_NAME = "mega_scrape.db"
PHP_REPORT_FILENAME = "report_checker.php"
DEFAULT_UNIT_ID = 1
DELETE_FILES_AFTER_PROCESSING = True

REQUEST_DELAY = 1.5
REQUEST_TIMEOUT = 25
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}



if __name__ == "__main__":

    script_data = initialize_script(DB_NAME, DOWNLOAD_DIR, COURSE_URL, HEADERS)
    if not script_data or not script_data.get("db_conn"):
        print("Initialization failed. Exiting.")
        sys.exit(1)

    session = script_data["session"]
    db_conn = script_data["db_conn"]

    try:
        logged_in = login_to_moodle(session, LOGIN_URL, USERNAME, PASSWORD)
        if not logged_in:
            print("\nLogin Failed")
            sys.exit(1)

        scraping_successful = scrape_course_content(
            script_data, BASE_URL, COURSE_URL, REQUEST_DELAY, REQUEST_TIMEOUT, DEFAULT_UNIT_ID
        )

        if scraping_successful:
            dl_success, dl_fail, processed_files_data = download_discovered_files(
                script_data, REQUEST_DELAY, DEFAULT_UNIT_ID
            )

            if processed_files_data:
                 process_downloaded_content(script_data, processed_files_data)
            else:
                 if dl_success == 0 and dl_fail == 0:
                     pass
                 else:
                     print("\nNo files were successfully processed.")

            check_url(script_data)

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

        generate_php_report(DB_NAME, PHP_REPORT_FILENAME, COURSE_URL)

