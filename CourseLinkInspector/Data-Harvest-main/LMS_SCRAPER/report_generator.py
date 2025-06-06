import os
from pathlib import Path
import html
import sqlite3
import sys # Import sys

def generate_php_report(db_filename, report_filename, course_url, Course_name, unit_id):
    print(f"\nGenerating report file: {report_filename}", file=sys.stderr)
    localhost_port = 8888 
    base_url = f"http://localhost:{localhost_port}"

    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root_dir = script_dir.parent

    sql_query = """
                SELECT
                    ar.AnalysisTimestamp,
                    ar.RiskLevel,
                    ar.DomainCreationDate, -- Added DomainCreationDate
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

    safe_course_url = html.escape(course_url, quote=True)
    escaped_db_filename = html.escape(db_filename)

    lms_scraper_dir_for_saving = project_root_dir / "LMS_SCRAPER"
    os.makedirs(lms_scraper_dir_for_saving, exist_ok=True)
    actual_save_path = lms_scraper_dir_for_saving / report_filename

    php_template = f"""<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$db_file = '{escaped_db_filename}';
$db_path = __DIR__ . '/' . $db_file; 

$page_title = "Unit Course Link Inspector";
$unit_id = {unit_id};
$course_url = "{safe_course_url}";
$columns = ["Timestamp", "Risk Level", "Link", "Domain Creation Date", "Type", "Source Location"]; // Added "Domain Creation Date"
$results = [];
$db_error = null;

$sql = <<<SQL
{sql_query}
SQL;


if (!file_exists($db_path)) {{
    $db_error = "Database file not found: " . htmlspecialchars($db_path);
}} else {{
    try {{
        $db = new PDO('sqlite:' . $db_path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

        $stmt = $db->prepare($sql);
        $stmt->execute([':unit_id' => $unit_id]);
        $results = $stmt->fetchAll();

    }} catch (PDOException $e) {{
        $db_error = "Database Error: " . $e->getMessage();
    }} finally {{
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
        return 'risk-unknown'; 
    }}
}}

function getRiskDisplayText($risk_level_from_db) {{
    $level = strtolower($risk_level_from_db ?? '');
    if ($level === 'red') {{
        return 'High Risk';
    }} elseif ($level === 'green') {{
        return 'Low Risk';
    }} elseif ($level === 'broken link') {{
        return 'Broken Link';
    }} elseif ($level === 'not found' || $level === 'vt error') {{
        return 'Not Found/Error';
    }} else {{
        return htmlspecialchars($risk_level_from_db);
    }}
}}

function getCircleClass($risk_level_from_db) {{
    $level = strtolower($risk_level_from_db ?? '');
    if ($level === 'red') {{
        return 'red';
    }} elseif ($level === 'green') {{
        return 'green';
    }} elseif ($level === 'broken link') {{
        return 'broken';
    }} elseif ($level === 'not found' || $level === 'vt error') {{
        return 'unknown';
    }} else {{
        return 'unknown';
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
        th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; vertical-align: top; word-break: break-word; }} /* Added word-break */
        th {{ background-color: #e9e9e9; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        
        .url-text {{ 
            color: #0066cc; 
            text-decoration: none;
            /* word-break: break-all; /* Moved to general td */
            display: inline-block; 
            margin-right: 8px; 
        }}

        .risk-red {{ color: #d9534f; font-weight: bold; }}
        .risk-Grey {{ color: gray; }}
        .risk-green {{ color: #5cb85c; }}
        .risk-unknown {{color:rgb(56, 133, 206); }}
        
        .error-message {{ color: red; font-weight: bold; border: 1px solid red; padding: 10px; background-color: #fdd; margin-bottom: 20px; }}
        .no-results {{ color: #555; font-style: italic; }}
        .info {{ margin-bottom: 15px; font-size: 0.9em; color: #444; }}
        .legend {{ margin-top: 40px; text-align: left; width: 60%; margin-left: auto; margin-right: auto; }}
        .legend h3 {{ margin-bottom: 10px; }}
        .legend-item {{ margin-bottom: 8px; }}
        .circle {{ display: inline-block; width: 15px; height: 15px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }}
        .circle.green {{ background-color: #5cb85c; }}
        .circle.red {{ background-color: #d9534f; }}
        .circle.broken {{ background-color: gray; }}
        .circle.unknown {{ background-color: #5b9bd5; }}

        .th-content {{ display: flex; align-items: center; justify-content: space-between; }}
        .sort-icon {{ width: 20px; height: 20px; margin-left: 8px; opacity: 0.7; cursor: pointer; }}

        .copy-url-btn {{
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 5px 10px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}
        .copy-url-btn:hover {{
            background-color: #45a049;
        }}
        .copy-url-btn.copied {{
            background-color: #007bff;
        }}
    </style>
</head>
<body>
    <h1><?php echo htmlspecialchars($page_title); ?></h1>
    <button id="download-btn" style="margin-top: 3px; padding: 5px 12px; font-size: 1em; cursor: pointer;">
            Download PDF
    </button>
    <p class="info">Report for Moodle Course: <a href="<?php echo $course_url; ?>" target="_blank" rel="noopener noreferrer"><?php echo $course_url; ?></a></p>
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
        <p class="no-results">No analysis results found in the database for this course.</p>
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
                <?php foreach ($results as $index => $row): ?>
                <tr>
                    <td><?php echo htmlspecialchars($row['AnalysisTimestamp'] ?? 'N/A'); ?></td>
                    <?php $risk_level_from_db = $row['RiskLevel'] ?? 'Unknown'; ?>
                    <td class="<?php echo getRiskClass($risk_level_from_db); ?>">
                        <span class="circle <?php echo getCircleClass($risk_level_from_db); ?>"></span>
                        <?php echo htmlspecialchars(getRiskDisplayText($risk_level_from_db)); ?>
                    </td>
                    <td>
                        <?php
                            $url = $row['URLString'] ?? '#';
                            $display_url_full = htmlspecialchars($url, ENT_QUOTES, 'UTF-8');
                            $short_display_url = (strlen($display_url_full) > 60) ? substr($display_url_full, 0, 57) . '...' : $display_url_full;
                            $url_span_id = "url_to_copy_" . $index; 
                        ?>
                        <span class="url-text" id="<?php echo $url_span_id; ?>" title="<?php echo $display_url_full; ?>"><?php echo $short_display_url; ?></span>
                        <button class="copy-url-btn" onclick="copyToClipboard('<?php echo $display_url_full; ?>', this)">Copy</button>
                    </td>
                    <td><?php echo htmlspecialchars($row['DomainCreationDate'] ?? 'N/A'); ?></td>
                    <td><?php echo htmlspecialchars($row['ItemType'] ?? 'N/A'); ?></td>
                    <td><?php echo htmlspecialchars($row['Location'] ?? 'N/A'); ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php endif; ?>

    <div class="legend">
        <h3>Security Level Legend</h3>
        <div class="legend-item"><span class="circle broken"></span>Broken Link (Grey) – Link cannot be scanned (e.g., 404 errors or inaccessible URLs).</div>
        <div class="legend-item"><span class="circle unknown"></span>Not Found/Error (Blue) – URL not found in VirusTotal, or a VT API error occurred.</div>
        <div class="legend-item"><span class="circle green"></span>Low Risk (Green) – No issues detected by VirusTotal; URL is considered safe.</div>
        <div class="legend-item"><span class="circle red"></span>High Risk (Red) – At least one malware checker in VirusTotal found an issue with this URL.</div>
    </div>
</body>
</html>
<script>
    if(document.getElementById('download-btn')) {{
        document.getElementById('download-btn').addEventListener('click', downloadPage);
    }}

    function copyToClipboard(textToCopy, buttonElement) {{
        const tempTextArea = document.createElement('textarea');
        tempTextArea.value = textToCopy;
        document.body.appendChild(tempTextArea);
        tempTextArea.select();
        tempTextArea.setSelectionRange(0, 99999); 
        try {{
            document.execCommand('copy'); 
            if (buttonElement) {{
                const originalText = buttonElement.innerText;
                buttonElement.innerText = 'Copied!';
                buttonElement.classList.add('copied');
                setTimeout(() => {{
                    buttonElement.innerText = originalText;
                    buttonElement.classList.remove('copied');
                }}, 1500);
            }}
        }} catch (err) {{
            console.error('Failed to copy text: ', err);
            if (buttonElement) {{
                 buttonElement.innerText = 'Failed!';
                 setTimeout(() => {{ buttonElement.innerText = 'Copy'; }}, 1500);
            }}
        }}
        document.body.removeChild(tempTextArea);
    }}
</script>
"""
    try:
        with open(actual_save_path, "w", encoding="utf-8") as f:
            f.write(php_template)
        
        full_url = f"{base_url}/LMS_SCRAPER/{report_filename}"

        print(f"PHP report generated successfully: {actual_save_path}", file=sys.stderr)
        print(f"Access via web browser {full_url}", file=sys.stderr)
        return full_url
    except IOError as e:
        print(f"\nERROR: Could not write PHP report file '{report_filename}' to '{actual_save_path}': {e}", file=sys.stderr)
    except Exception as e:
         print(f"\nERROR: An unexpected error occurred generating PHP report: {e}", file=sys.stderr)
    return None


def generate_Overall_php_report(db_filename, report_filename, path_php):
    print(f"\nGenerating overall report file: {report_filename}", file=sys.stderr)
    localhost_port = 8888 
    base_url = f"http://localhost:{localhost_port}"

    script_dir = Path(os.path.dirname(os.path.abspath(__file__))) 
    project_root_dir = script_dir.parent 
    lms_scraper_dir_for_saving = project_root_dir / "LMS_SCRAPER"
    os.makedirs(lms_scraper_dir_for_saving, exist_ok=True)
    actual_save_path = lms_scraper_dir_for_saving / report_filename
    
    escaped_db_filename = html.escape(db_filename)

    php_array_entries = []
    for entry in path_php:
        course_id = html.escape(str(entry.get("course_ID", "")))
        course_name = html.escape(entry.get("course_name", ""))
        
        individual_report_filename = Path(entry.get("course_php_URL", "")).name 
        report_url_for_individual = f"{base_url}/LMS_SCRAPER/{individual_report_filename}"

        php_array_entries.append(f"""
        [
            'course_id' => '{course_id}',
            'course_name' => '{course_name}',
            'report_url' => '{html.escape(report_url_for_individual)}'
        ]
        """)

    php_path_php_array = "array(" + ",".join(php_array_entries) + ")"

    php_template = f"""<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$db_file = '{escaped_db_filename}';
$db_path = __DIR__ . '/' . $db_file;

$page_title = "Overall Course Link Inspector - Overview";
$columns = ["Course Name", "Coordinator Name", "Coordinator Email", "Inspect Details"];
$results = [];
$db_error = null;

$path_php = {php_path_php_array};

if (!file_exists($db_path)) {{
    $db_error = "Database file not found: " . htmlspecialchars($db_path);
}} else {{
    try {{
        $db = new PDO('sqlite:' . $db_path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

        foreach ($path_php as $entry) {{
            $unit_id_param = $entry['course_id'];
            $course_name_display = $entry['course_name'];
            $report_url_display = $entry['report_url'];

            $stmt = $db->prepare("
                SELECT c.CoordinatorName, c.CoordinatorEmail
                FROM Unit u
                JOIN Coordinator c ON u.CoordinatorID = c.CoordinatorID
                WHERE u.UnitID = :unit_id
                LIMIT 1
            ");
            $stmt->execute([':unit_id' => $unit_id_param]);
            $row = $stmt->fetch();

            $results[] = [
                'course_name' => $course_name_display,
                'coordinator_name' => $row['CoordinatorName'] ?? 'N/A',
                'coordinator_email' => $row['CoordinatorEmail'] ?? 'N/A',
                'report_url' => $report_url_display,
            ];
        }}
        $db = null; 
    }} catch (PDOException $e) {{
        $db_error = "Database error: " . $e->getMessage();
    }}
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
        .no-results {{ color: #555; font-style: italic; }}
    </style>
</head>
<body>
    <h1><?php echo htmlspecialchars($page_title); ?></h1>
    <?php if ($db_error): ?>
        <p class="error-message"><?php echo htmlspecialchars($db_error); ?></p>
    <?php elseif (empty($results)): ?>
        <p class="no-results">No course reports found to display in the overview.</p>
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
"""

    try:
        with open(actual_save_path, "w", encoding="utf-8") as f:
            f.write(php_template)

        full_url = f"{base_url}/LMS_SCRAPER/{report_filename}"

        print(f"PHP overall report generated successfully: {actual_save_path}", file=sys.stderr)
        print(f"Access via web browser {full_url}", file=sys.stderr)
        return full_url
    except IOError as e:
        print(f"\nERROR: Could not write PHP overall report file '{report_filename}' to '{actual_save_path}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred generating PHP overall report: {e}", file=sys.stderr)
    return None
