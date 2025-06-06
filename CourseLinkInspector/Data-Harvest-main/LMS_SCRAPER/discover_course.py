import sys
import sqlite3
import time
import traceback
import os
import json
try:
    from auth import login_to_moodle
except ImportError:
    print("ERROR: Could not import 'login_to_moodle' from auth.py.")
    sys.exit(1)

try:
    from core_logic import (
        initialize_script,
        scrape_avaliable_course,
    )
except ImportError as e:
    print(f"ERROR: Could not import functions from core_logic.py: {e}")
    sys.exit(1)
#define variables
REQUEST_DELAY = 0.5
REQUEST_TIMEOUT = 25
USERNAME = "Admin"
PASSWORD = "Password.1"
BASE_URL = "http://localhost"
LOGIN_URL = f"{BASE_URL}/login/index.php"
COURSE_AVALIABLE_COURSES= f"{BASE_URL}/course/index.php"
DB_NAME = "mega_scrape.db"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}
DOWNLOAD_DIR = "moodle_downloads"

#state

script_data = initialize_script(DB_NAME, DOWNLOAD_DIR, COURSE_AVALIABLE_COURSES, HEADERS)
if not script_data or not script_data.get("db_conn"):
        print("Initialization failed. Exiting.")
        sys.exit(1)

session = script_data["session"]
db_conn = script_data["db_conn"]

try:
    #login pass
    logged_in = login_to_moodle(session, LOGIN_URL, USERNAME, PASSWORD)
    if not logged_in:
        sys.exit(1)

    # scraping
    scraped_units = scrape_avaliable_course(script_data,COURSE_AVALIABLE_COURSES,REQUEST_DELAY, REQUEST_TIMEOUT)
    # return data to PHP via stdout
    print(scraped_units)
    print(json.dumps(scraped_units))  # to stdout
    print("Database connection closed.", file=sys.stderr)  # to stderr


except Exception as e:
        print(f"\n CRITICAL UNEXPECTED ERROR in main execution: {e}")
        traceback.print_exc()

if db_conn:
    try:
        db_conn.close()
    except sqlite3.Error as e:
        print(f"Error closing database connection: {e}")
