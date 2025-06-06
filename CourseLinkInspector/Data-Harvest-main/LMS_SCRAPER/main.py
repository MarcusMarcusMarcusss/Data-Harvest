import json
import sys
import sqlite3
import time
import traceback
import os

try:
    from auth import login_to_moodle
except ImportError:
    print("ERROR: Could not import 'login_to_moodle' from auth.py.", file=sys.stderr)
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
    print(f"ERROR: Could not import functions from core_logic.py: {e}", file=sys.stderr)
    sys.exit(1)
try:
    from report_generator import generate_php_report,generate_Overall_php_report
except ImportError:
    # No changes here
    print("Ensure report_generator.py exists in the LMS_SCRAPER directory.", file=sys.stderr)
    sys.exit(1)
BASE_URL = "http://localhost"
LOGIN_URL = f"{BASE_URL}/login/index.php"
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
    path_php=[] # This will store individual course report URLs
    final_report_summary = {
        "individual_reports": [],
        "overall_report_url": ""
    }

    if len(sys.argv) > 1:

        raw_input = sys.argv[1].strip("[] ").strip()


        courses = [c.strip() for c in raw_input.split(',')]


        for course in courses:
            items = get_CoursePage_Urls(db_path, course)
            if items:
                for row in items:
                    script_data = initialize_script(DB_NAME, DOWNLOAD_DIR, row[3], HEADERS)
                    if not script_data or not script_data.get("db_conn"):
                        print("Initialization failed. Exiting.", file=sys.stderr)
                        sys.exit(1)
                    session = script_data["session"]
                    db_conn = script_data["db_conn"]
                    try:
                        #login pass
                        logged_in = login_to_moodle(session, LOGIN_URL, USERNAME, PASSWORD)
                        if not logged_in:
                            print("\nLogin Failed", file=sys.stderr)
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
                                pass # No files to download or process
                            else:
                                print("\nNo files were successfully processed.", file=sys.stderr)
                        check_url(script_data,row[0])

                    except Exception as e:
                        print(f"\nCRITICAL UNEXPECTED ERROR in main execution: {e}", file=sys.stderr)
                        traceback.print_exc(file=sys.stderr)
                    finally:
                        if db_conn:
                            try:
                                db_conn.close()
                            except sqlite3.Error as e:
                                print(f"Error closing database connection: {e}", file=sys.stderr)
                        if DELETE_FILES_AFTER_PROCESSING:
                            if processed_files_data:
                                delete_processed_files(processed_files_data)
                        else:
                            print("\nSkipping deletion of processed files as per configuration.", file=sys.stderr)

                        course_inspector_filename = "course_inspector_" + course.replace(" ", "_").replace("/", "_").replace("\\", "_") + ".php" # Sanitize filename for URL and path
                        report_url = generate_php_report(DB_NAME, course_inspector_filename,row[3],course,row[0])
                        if report_url:
                            final_report_summary["individual_reports"].append({
                                "course_name": course,
                                "report_url": report_url
                            })
                            # Add to path_php for overall report generation, ensuring no duplicates
                            path_entry = {
                                "course_ID": row[0], # Assuming row[0] is the course_id
                                "course_name": course,
                                "course_php_URL": report_url
                            }
                            if path_entry not in path_php:
                                path_php.append(path_entry)


                overall_report_url = generate_Overall_php_report(DB_NAME, "course_Overview.php", path_php) # overall report filename is fixed to course_Overview.php
                if overall_report_url:
                    final_report_summary["overall_report_url"] = overall_report_url
            else:
                print("No courses found or query failed for the given input.", file=sys.stderr)
    else:
        print("No arguments received for main.py.", file=sys.stderr)

    html_output_parts = []
    if not final_report_summary["individual_reports"] and not final_report_summary["overall_report_url"]:
        html_output_parts.append("<p>Scan completed, but no specific reports were generated. Check debug information if available.</p>")
    else:
        html_output_parts.append("<h2>Scan Complete!</h2>")
        html_output_parts.append("<p>Here are your reports:</p><ul>")
        for report_item in final_report_summary.get("individual_reports", []):
            html_output_parts.append(f"<li><a href=\"{report_item['report_url']}\" target=\"_blank\" rel=\"noopener noreferrer\">{report_item['course_name']} Report</a></li>")
        if final_report_summary.get("overall_report_url"):
            html_output_parts.append(f"<li><a href=\"{final_report_summary['overall_report_url']}\" target=\"_blank\" rel=\"noopener noreferrer\">Overall Course Overview Report</a></li>")
        html_output_parts.append("</ul>")

    print("".join(html_output_parts)) 
    sys.exit(0)