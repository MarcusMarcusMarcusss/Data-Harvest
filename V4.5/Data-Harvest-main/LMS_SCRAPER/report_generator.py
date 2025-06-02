import os
from pathlib import Path
import html
import sqlite3
import sys

def generate_php_report(db_filename, report_filename, course_url,Course_name,unit_id):
    print(f"\nGenerating report file: {report_filename}")
    localhost_port = 3000
    base_url = f"http://localhost:{localhost_port}"
    sql_query = """
                SELECT
                    ar.AnalysisTimestamp,
                    ar.RiskLevel,
                    eu.URLString,
                    ci.ItemType,
                    eu.Location,
                    c.CoordinatorName,
                    c.CoordinatorEmail
                FROM
                    AnalysisReport ar
                JOIN
                    ExtractedURL eu ON ar.URLID = eu.URLID
                JOIN
                    ContentItem ci ON eu.ItemID = ci.ItemID
                JOIN
                    Unit u ON ci.UnitID = u.UnitID
                JOIN
                    Coordinator c ON u.CoordinatorID = c.CoordinatorID
                WHERE
                    ci.UnitID = :unit_id
                ORDER BY
                    ar.AnalysisTimestamp DESC,
                    ci.ItemType,
                    eu.URLString;
                    """.strip()

    # Escape the course URL for safe embedding in PHP/HTML
    safe_course_url = html.escape(course_url, quote=True)

    php_template = f"""<?php
// --- Configuration ---
error_reporting(E_ALL);
ini_set('display_errors', 1);

$db_file = '{db_filename}'; // Database filename relative to this PHP script
$db_path = __DIR__ . '/' . $db_file; // Assumes DB is in the same directory as PHP script
$page_title = "{Course_name} Course Link Inspector";
$unit_id = {unit_id};
$course_url = "{safe_course_url}"; // Embed course URL safely
$columns = ["Timestamp", "Risk Level", "Link", "Source Type", "Source Location"];
$results = [];
$db_error = null;

// Define SQL query using Heredoc syntax
$sql = <<<SQL
{sql_query}
SQL;

// --- Database Connection and Query ---
if (!file_exists($db_path)) {{
    $db_error = "Database file not found: " . htmlspecialchars($db_path);
}} else {{
    try {{
        // Use PDO for database access
        $db = new PDO('sqlite:' . $db_path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

        // Prepare and execute the SQL query using the $sql variable
        $stmt = $db->prepare($sql);
        $stmt->execute([':unit_id' => $unit_id]);
        $results = $stmt->fetchAll();

    }} catch (PDOException $e) {{
        $db_error = "Database Error: " . $e->getMessage();
    }} finally {{
        // Close connection
        $db = null;
    }}
}}

function getRiskClass($risk_level) {{
    $level = strtolower($risk_level ?? '');
    if ($level === 'red') {{
        return 'risk-red';
    }} elseif ($level === 'broken link') {{
        return 'risk-Grey';
    }} elseif ($level === 'green') {{
        return 'risk-green';
    }} else {{
        return 'risk-unknown'; // For 'Not Found', 'Error', or NULL
    }}
}}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <script src="search-toggle.js"></script>
    <script src="download_pdf.js"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>
    <title><?php echo htmlspecialchars($page_title); ?></title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }}
        h1 {{ color: #555; border-bottom: 2px solid #ccc; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background-color: #fff; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; vertical-align: top; }}
        th {{ background-color: #e9e9e9; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        td a {{ color: #0066cc; text-decoration: none; word-break: break-all; }}
        td a:hover {{ text-decoration: underline; }}
        .risk-red {{ color: #d9534f; font-weight: bold; }}
        .risk-Grey {{ color: gray; }}
        .risk-green {{ color: #5cb85c; }}
        .risk-unknown {{color:rgb(56, 133, 206); }}
        .error-message {{ color: red; font-weight: bold; border: 1px solid red; padding: 10px; background-color: #fdd; margin-bottom: 20px; }}
        .no-results {{ color: #555; font-style: italic; }}
        .info {{ margin-bottom: 15px; font-size: 0.9em; color: #444; }}
        .legend {{
        margin-top: 40px;
        text-align: left;
        width: 60%;
        margin-left: auto;
        margin-right: auto;
        }}
        .legend h3 {{
            margin-bottom: 10px;
        }}
        .legend-item {{
            margin-bottom: 8px;
        }}
        .circle {{
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
        }}
        .low {{
            background-color: green;
        }}
        .high {{
            background-color: red; 
        }}
        .broken{{
            background-color: gray; 
        }}
        .unknown {{
            background-color: #5b9bd5; 
        }}
        .th-content {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .sort-icon {{
            width: 20px;
            height: 20px;
            margin-left: 8px;
            opacity: 0.7;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <h1><?php echo htmlspecialchars($page_title); ?></h1>
    <button id="download-btn" style="margin-top: 3px; padding: 5px 12px; font-size: 1em; cursor: pointer;">
            Download PDF
    </button>
    <p class="info">Report for Moodle Course: <?php echo $course_url; ?>
    <?php if (!empty($results)): ?>
    <?php 
        
            $coordinatorName = htmlspecialchars($results[0]['CoordinatorName'] ?? 'N/A');
            $coordinatorEmail = htmlspecialchars($results[0]['CoordinatorEmail'] ?? 'N/A');
        ?>
        <p class="info" id="coordinator-info">
            Coordinator: <?php echo $coordinatorName; ?><br>
            Email: <a href="mailto:<?php echo $coordinatorEmail; ?>"><?php echo $coordinatorEmail; ?></a>
        </p>
    <?php endif; ?>
    <?php if ($db_error): ?>
        <p class="error-message"><?php echo htmlspecialchars($db_error); ?></p>
    <?php elseif (empty($results)): ?>
        <p class="no-results">No analysis results found in the database.</p>
    <?php else: ?>
        <input type="text" id="table-search-input" style="display:none; margin-top:10px; width: 100%; padding: 8px;" placeholder="Search table...">
        <table>
            <thead>
                <tr>
                    <?php foreach ($columns as $col): ?>
                        <th>
                            <div class="th-content">
                                <span class="header-text"><?php echo htmlspecialchars($col); ?></span>
                                <img src="sort.png" alt="Sort" class="sort-icon" data-column="<?php echo htmlspecialchars($col); ?>">
                            </div>
                        </th>
                    <?php endforeach; ?>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($results as $row): ?>
                <tr>
                    <td><?php echo htmlspecialchars($row['AnalysisTimestamp'] ?? 'N/A'); ?></td>
                    <?php $risk_level = $row['RiskLevel'] ?? 'Unknown'; ?>
                    <td class="<?php echo getRiskClass($risk_level); ?>"><?php echo htmlspecialchars($risk_level); ?></td>
                    <td>
                        <?php
                            $url = $row['URLString'] ?? '#';
                            $display_url = htmlspecialchars($url, ENT_QUOTES, 'UTF-8');
                            // Make the displayed URL shorter if it's very long
                            $short_display_url = (strlen($display_url) > 80) ? substr($display_url, 0, 77) . '...' : $display_url;
                            // Escaped PHP variables inside echo string
                            echo "<a href='{{$display_url}}' target='_blank' rel='noopener noreferrer' title='{{$display_url}}'>{{$short_display_url}}</a>";
                        ?>
                    </td>
                    <td><?php echo htmlspecialchars($row['ItemType'] ?? 'N/A'); ?></td>
                    <td><?php echo htmlspecialchars($row['Location'] ?? 'N/A'); ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php endif; ?>
    
        <div class="legend">
        <h3>Security Level Legend</h3>
        <div class="legend-item">
        <span class="circle broken"></span>
        Broken Link (Grey) – Link cannot be scanned (e.g., 404 errors or inaccessible URLs).
        </div>
        <div class="legend-item">
            <span class="circle unknown"></span>
            Not Found (Blue) – URL was not found or could not be scanned by VirusTotal.
        </div>

        <div class="legend-item">
            <span class="circle low"></span>
            Low Risk (Green) – No issues detected by VirusTotal; URL is considered safe.
        </div>

        <div class="legend-item">
            <span class="circle high"></span>
            High Risk (Red) – At least one malware checker in VirusTotal found an issue with this URL.
        </div>
    </div>
</body>
</html>
<script>
document.getElementById('download-btn').addEventListener('click', downloadPage);
</script>
"""
    try:
        script_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        report_path = script_dir / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(php_template)
        full_url = f"{base_url}/Data-Harvest-main/LMS_SCRAPER/{report_filename}"
        print(f"PHP report generated successfully: {report_path}")
        print(f"Access via web browser {full_url}")
        return full_url
    except IOError as e:
        print(f"\nERROR: Could not write PHP report file '{report_filename}': {e}")
    except Exception as e:
         print(f"\nERROR: An unexpected error occurred generating PHP report: {e}")





    print(f"\n Generating report file: {report_filename}")
    localhost_port = 3000
    base_url = f"http://localhost:{localhost_port}"
    sql_query = """
            SELECT
                c.CoordinatorName,
                c.CoordinatorEmail
            FROM
                Unit u
            JOIN
                Coordinator c ON u.CoordinatorID = c.CoordinatorID
            WHERE
                u.UnitID = :unit_id
            LIMIT 1;
        """.strip()

    php_template = f"""<?php
// --- Configuration ---
error_reporting(E_ALL);
ini_set('display_errors', 1);

$db_file = '{db_filename}'; // Database filename relative to this PHP script
$db_path = __DIR__ . '/' . $db_file; // Assumes DB is in the same directory as PHP script
$page_title = "Course Link Inspector - Overview";
$columns = ["Course Name", "Coordinator Name", "Coordinator Email", "Inspects Detail"];
$results = [];
$db_error = null;

// Define SQL query using Heredoc syntax
$sql = <<<SQL
{sql_query}
SQL;

// --- Database Connection and Query ---
if (!file_exists($db_path)) {{
    $db_error = "Database file not found: " . htmlspecialchars($db_path);
}} else {{
    try {{
        // Use PDO for database access
        $db = new PDO('sqlite:' . $db_path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

        // Prepare and execute the SQL query using the $sql variable
        $stmt = $db->prepare($sql);
        $stmt->execute([':unit_id' => $unit_id]);
        $results = $stmt->fetchAll();

    }} catch (PDOException $e) {{
        $db_error = "Database Error: " . $e->getMessage();
    }} finally {{
        // Close connection
        $db = null;
    }}
}}


?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo htmlspecialchars($page_title); ?></title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }}
        h1 {{ color: #555; border-bottom: 2px solid #ccc; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background-color: #fff; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; vertical-align: top; }}
        th {{ background-color: #e9e9e9; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        td a {{ color: #0066cc; text-decoration: none; word-break: break-all; }}
        td a:hover {{ text-decoration: underline; }}
        .risk-red {{ color: #d9534f; font-weight: bold; }}
        .risk-amber {{ color: #f0ad4e; font-weight: bold; }}
        .risk-green {{ color: #5cb85c; }}
        .risk-unknown {{color:rgb(56, 133, 206); }}
        .error-message {{ color: red; font-weight: bold; border: 1px solid red; padding: 10px; background-color: #fdd; margin-bottom: 20px; }}
        .no-results {{ color: #555; font-style: italic; }}
        .info {{ margin-bottom: 15px; font-size: 0.9em; color: #444; }}
        .legend {{
        margin-top: 40px;
        text-align: left;
        width: 60%;
        margin-left: auto;
        margin-right: auto;
        }}
        .legend h3 {{
            margin-bottom: 10px;
        }}
        .legend-item {{
            margin-bottom: 8px;
        }}
        .circle {{
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
        }}
        .low {{
            background-color: green;
        }}
        .high {{
            background-color: red; 
        }}
        .broken{{
            background-color: gray; 
        }}
        .unknown {{
            background-color: #5b9bd5; 
        }}
    </style>
</head>
<body>
    <h1><?php echo htmlspecialchars($page_title); ?></h1>
    <?php if (!empty($results)): ?>
    <?php 
        
            $coordinatorName = htmlspecialchars($results[0]['CoordinatorName'] ?? 'N/A');
            $coordinatorEmail = htmlspecialchars($results[0]['CoordinatorEmail'] ?? 'N/A');
        ?>
        <p class="info">
            Coordinator: <?php echo $coordinatorName; ?><br>
            Email: <a href="mailto:<?php echo $coordinatorEmail; ?>"><?php echo $coordinatorEmail; ?></a>
        </p>
    <?php endif; ?>
    <?php if ($db_error): ?>
        <p class="error-message"><?php echo htmlspecialchars($db_error); ?></p>
    <?php elseif (empty($results)): ?>
        <p class="no-results">No analysis results found in the database.</p>
    <?php else: ?>
        <table>
            <thead>
                <tr>
                    <?php foreach ($columns as $col): ?>
                        <th><?php echo htmlspecialchars($col); ?></th>
                    <?php endforeach; ?>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($results as $row): ?>
                <tr>
                    <td><?php echo htmlspecialchars($row['AnalysisTimestamp'] ?? 'N/A'); ?></td>
                    <?php $risk_level = $row['RiskLevel'] ?? 'Unknown'; ?>
                    <td class="<?php echo getRiskClass($risk_level); ?>"><?php echo htmlspecialchars($risk_level); ?></td>
                    <td>
                        <?php
                            $url = $row['URLString'] ?? '#';
                            $display_url = htmlspecialchars($url, ENT_QUOTES, 'UTF-8');
                            // Make the displayed URL shorter if it's very long
                            $short_display_url = (strlen($display_url) > 80) ? substr($display_url, 0, 77) . '...' : $display_url;
                            // Escaped PHP variables inside echo string
                            echo "<a href='{{$display_url}}' target='_blank' rel='noopener noreferrer' title='{{$display_url}}'>{{$short_display_url}}</a>";
                        ?>
                    </td>
                    <td><?php echo htmlspecialchars($row['ItemType'] ?? 'N/A'); ?></td>
                    <td><?php echo htmlspecialchars($row['Location'] ?? 'N/A'); ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php endif; ?>
    

</body>
</html>
"""
    try:
        script_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        report_path = script_dir / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(php_template)
        full_url = f"{base_url}/Data-Harvest-main/LMS_SCRAPER/{report_filename}"
        print(f"PHP report generated successfully: {report_path}")
        print(f"Access via web browser {full_url}")
        return full_url,
    except IOError as e:
        print(f"\nERROR: Could not write PHP report file '{report_filename}': {e}")
    except Exception as e:
         print(f"\nERROR: An unexpected error occurred generating PHP report: {e}")









def generate_Overall_php_report(db_filename, report_filename, path_php):
    print(f"\nGenerating report file: {report_filename}")
    php_array_entries = []
    for entry in path_php:
        course_id = entry.get("course_ID", "")
        course_name = entry.get("course_name", "")
        report_url = entry.get("course_php_URL", "")
        # Attempt to extract unit_id (you can adjust this logic as needed)
        unit_id = course_name.split("_")[-1] if "_" in course_name else course_name
        php_array_entries.append(f"""
        [
            'course_id' => '{course_id}',
            'course_name' => '{course_name}',
            'report_url' => '{report_url}'
        ]
        """)

    php_path_php_array = "array(" + ",".join(php_array_entries) + ")"

    php_template = f"""<?php
// --- Configuration ---
error_reporting(E_ALL);
ini_set('display_errors', 1);

$db_file = '{db_filename}'; 
$db_path = __DIR__ . '/' . $db_file;

$page_title = "Overall Course Link Inspector";
$columns = ["Course Name", "Coordinator Name", "Coordinator Email", "Report URL"];
$results = [];
$db_error = null;

// Embed path_php array
$path_php = {php_path_php_array};


// Connect to DB and collect coordinator info for each course
try {{
    $db = new PDO('sqlite:' . $db_path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    foreach ($path_php as $entry) {{
        $unit_id = $entry['course_id']; 
        $course_name = $entry['course_name'];
        $report_url = $entry['report_url'];

        $stmt = $db->prepare("
            SELECT c.CoordinatorName, c.CoordinatorEmail
            FROM Unit u
            JOIN Coordinator c ON u.CoordinatorID = c.CoordinatorID
            WHERE u.UnitID = :unit_id
            LIMIT 1
        ");
        $stmt->execute([':unit_id' => $unit_id]);
        $row = $stmt->fetch();

        $results[] = [
            'course_name' => $course_name,
            'coordinator_name' => $row['CoordinatorName'] ?? 'N/A',
            'coordinator_email' => $row['CoordinatorEmail'] ?? 'N/A',
            'report_url' => $report_url,
        ];
        echo "<!-- Debug: unit_id = $unit_id | course_name = $course_name -->";
    }}

    $db = null; // close connection
}} catch (PDOException $e) {{
    $db_error = "Database error: " . $e->getMessage();
}}







?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title><?php echo htmlspecialchars($page_title); ?></title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }}
        h1 {{ color: #555; border-bottom: 2px solid #ccc; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background-color: #fff; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; vertical-align: top; }}
        th {{ background-color: #e9e9e9; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        td a {{ color: #0066cc; text-decoration: none; word-break: break-word; }}
        td a:hover {{ text-decoration: underline; }}
        .error-message {{ color: red; font-weight: bold; border: 1px solid red; padding: 10px; background-color: #fdd; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1><?php echo htmlspecialchars($page_title); ?></h1>
    <?php if ($db_error): ?>
        <p class="error-message"><?php echo htmlspecialchars($db_error); ?></p>
    <?php elseif (empty($path_php)): ?>
        <p>No courses found to display.</p>
    <?php else: ?>
        <table>
            <thead>
                <tr>
                    <?php foreach ($columns as $col): ?>
                    <th><?php echo htmlspecialchars($col); ?></th>
                    <?php endforeach; ?>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($results as $entry): ?>
                <tr>
                    <td><?php echo htmlspecialchars($entry['course_name']); ?></td>
                    <td><?php echo htmlspecialchars($entry['coordinator_name']); ?></td>
                    <td><a href="mailto:<?php echo htmlspecialchars($entry['coordinator_email']); ?>"><?php echo htmlspecialchars($entry['coordinator_email']); ?></a></td>
                    <td><a href="<?php echo htmlspecialchars($entry['report_url']); ?>" target="_blank" rel="noopener noreferrer">View Report</a></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php endif; ?>
</body>
</html>
<script>
document.getElementById('download-btn').addEventListener('click', downloadPage);
</script>
"""

    try:
        script_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        report_path = script_dir / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(php_template)
        base_url = "http://localhost:3000"
        full_url = f"{base_url}/Data-Harvest-main/LMS_SCRAPER/{report_filename}"
        print(f"PHP report generated successfully: {report_path}")
        print(f"Access via web browser {full_url}")
        return full_url
    except IOError as e:
        print(f"\nERROR: Could not write PHP report file '{report_filename}': {e}")
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred generating PHP report: {e}")