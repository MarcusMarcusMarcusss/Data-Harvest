def get_unit_content_items(db_path, unit_name):
    query = """
        SELECT 
            ar.RiskLevel,
        FROM 
            AnalysisReport ar
            ExtractedURL eu 
            ON ar.URLID = eu.URLID
        JOIN ContentItem ci 
            ON eu.ItemID = ci.ItemID
        
        WHERE ci.UnitID = ?
    """

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query, (unit_name,))
        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        print(f"CRITICAL ERROR: Could not connect to database '{db_path}': {e}")
        return []

    finally:
        if conn:
            conn.close()
import sys
import sqlite3
DB_NAME = "LMS_SCRAPER\mega_scrape.db"


if len(sys.argv) > 1:
    raw_input = sys.argv[1]
    print("Raw input:", raw_input)
    
    courses = [c.strip() for c in raw_input.split(',')]
    print("Parsed courses:", courses)

    for course in courses:
        print(f"\nFetching data for course: {course}")
        items = get_unit_content_items(DB_NAME, course)
        if items:
            for row in items:
                print(f"UnitID: {row[0]}, CoordinatorID: {row[1]}, ItemID: {row[2]}, ItemPath: {row[3]}")
        else:
            print("No results found or query failed.")
else:
    print("No arguments received.")