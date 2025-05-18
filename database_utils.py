#database_utils.py
import sqlite3
import os
from typing import List
from dataStructure import UnitInfoEntry,CoordinatorEntry,ExtractedURLEntry,ContentItemEntry,FolderFileEntry,ForumDiscussionEntry,PageLinkEntry

DB_PATH = r"mega_scrape.db"

def is_valid_db_path(db_path: str) -> bool:
    return os.path.isfile(db_path)

#if not is_valid_db_path(DB_PATH):
#    print(f"Database file not found at: {DB_PATH}")
#else:
#   print("Database path is valid.")

def insert_UnitInfo(courseUrlEntries: List[UnitInfoEntry], db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for entry in courseUrlEntries:
        cursor.execute('''
            SELECT 1 FROM Unit
            WHERE UnitName = ?
        ''', (entry.UnitName,))

        exists = cursor.fetchone()
        if not exists:
            cursor.execute('''
                INSERT INTO Unit (CoordinatorID, UnitName,SchoolName)
                VALUES (?, ?, ?)
            ''', (entry.CoordinatorID,entry.UnitName,entry.SchoolName))
        else:
            print(f"Skipping duplicate: {entry.UnitName}")
    conn.commit()
    conn.close()
#example_Unit_entries = [UnitInfoEntry(CoordinatorID=1,UnitName= "ICT302",SchoolName="school of IT",)]
#insert_UnitInfo(example_Unit_entries)

def get_unitid_by_name(unit_name: str, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT UnitID FROM Unit WHERE UnitName = ?", (unit_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_unitid_by_itempath(unit_name: str, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT UnitID FROM Unit WHERE UnitName = ?", (unit_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def insert_extracted_urls(urlEntries: List[ExtractedURLEntry], db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for entry in urlEntries:
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

def insert_ContentItemEntry_files(file_entries: List[ContentItemEntry], db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for entry in file_entries:
            cursor.execute('''SELECT 1 FROM ContentItem WHERE UnitID = ? AND ItemPath = ?''',
                           (entry.Unitid, entry.URL))

            if not cursor.fetchone():
                cursor.execute('''INSERT INTO ContentItem (UnitID, ItemName, ItemType, ItemPath)
                                  VALUES (?, ?, ?, ?)''',
                               (entry.Unitid, entry.FileName, entry.FileType, entry.URL))
            else:
                print(f"Skipping duplicate ContentItem: {entry.URL}")
        conn.commit()
    finally:
        conn.close()

#example_file_entries = [ContentItemEntry(Unitid=1, FileName="The audio Book", URL="https://www.audio.pptx", FileType="pptx")]
#insert_ContentItemEntry_files(example_file_entries)

def insert_forum_discussions(entries: List[ForumDiscussionEntry], db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for entry in entries:
            location = f"{entry.ForumName}->{entry.DiscussionTitle}"

            cursor.execute('''SELECT 1 FROM ExtractedURL WHERE itemid = ? AND URLString = ? AND Location = ?''',
                           (entry.discussionid, entry.URL,location))

            if not cursor.fetchone():                
                cursor.execute('''INSERT INTO ExtractedURL (itemid, URLString, Location, TimeStamp)
                                  VALUES (?, ?, ?, ?)''',
                               (entry.discussionid, entry.URL, location, entry.TimeStamp))
            else:
                print(f"Skipping duplicate URL: {entry.URL}")
        conn.commit()
    finally:
        conn.close()


def insert_folder_files(entries: List[FolderFileEntry], db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for entry in entries:
            location = f"{entry.FolderName}->{entry.FileName}"
            cursor.execute('''SELECT 1 FROM ExtractedURL WHERE itemid = ? AND URLString = ? AND Location = ?''',
                           (entry.fileid, entry.URL,location))

            if not cursor.fetchone():
                cursor.execute('''INSERT INTO ExtractedURL (itemid, URLString, Location, TimeStamp)
                                  VALUES (?, ?, ?, ?)''',
                               (entry.fileid, entry.URL, location, entry.TimeStamp))
            else:
                print(f"Skipping duplicate URL: {entry.URL}")
        conn.commit()
    finally:
        conn.close()


def insert_page_links(entries: List[PageLinkEntry], db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for entry in entries:
            cursor.execute('''SELECT 1 FROM ExtractedURL WHERE itemid = ? AND URLString = ? AND Location = ?''',
                           (entry.pageid, entry.Link,entry.PageTitle))

            if not cursor.fetchone():
                cursor.execute('''INSERT INTO ExtractedURL (itemid, URLString, Location, TimeStamp)
                                  VALUES (?, ?, ?, ?)''',
                               (entry.pageid, entry.Link, entry.PageTitle, entry.TimeStamp))
            else:
                print(f"Skipping duplicate URL: {entry.Link}")
        conn.commit()
    finally:
        conn.close()

def insert_coordinator_info(entries: List[CoordinatorEntry], db_path: str = DB_PATH): 
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for entry in entries:
            cursor.execute('''SELECT 1 FROM Coordinator WHERE CoordinatorEmail = ?''', (entry.Email,))
            
            if not cursor.fetchone():
                cursor.execute('''INSERT INTO Coordinator (CoordinatorName, CoordinatorEmail) 
                                  VALUES (?, ?)''', (entry.Name, entry.Email))
            else:
                print(f"Skipping duplicate coordinator: {entry.Name}")
        conn.commit()
    finally:
        conn.close()

##add_coordinators = [CoordinatorEntry(Name="Mark Asblo", Email="Mark.Asblo@murdoch.edu", Department="School of Media&Music"),CoordinatorEntry(Name="Garen Smart", Email="Garen.Smart@murdoch.edu", Department="School of Media&Music")]
##insert_coordinator_info(add_coordinators)