import sys
import sqlite3
import time
import requests
from bs4 import BeautifulSoup
from byPassLogin import prepare_headers,authenticate_moodle,get_pageinfo_html,login_to_moodle
from function import extract_course_content, process_courses

#https://moodleprod.murdoch.edu.au/course/index.php?categoryid=202&browse=courses&perpage=all&page=1#
username = "admin"
password = "Password.1"
login_url = "http://localhost/login/index.php"
courses_HTML="http://localhost/course/index.php"
session = requests.Session()
#edit
authenticate_moodle(session, login_url, username, password)
#cookies
headers=prepare_headers(session)

course_page_html = get_pageinfo_html(courses_HTML,headers)
course_entries = process_courses(course_page_html, headers)

for unit_entry, url in course_entries:
        extract_course_content(unit_entry.UnitName,url, headers, session)