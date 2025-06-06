<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$db_file = 'mega_scrape.db';
$db_path = __DIR__ . '/' . $db_file;

$page_title = "Overall Course Link Inspector - Overview";
$columns = ["Course Name", "Coordinator Name", "Coordinator Email", "Inspect Details"];
$results = [];
$db_error = null;

$path_php = array(
        [
            'course_id' => '12',
            'course_name' => 'Computer Security',
            'report_url' => 'http://localhost:8888/LMS_SCRAPER/course_inspector_Computer_Security.php'
        ]
        );

if (!file_exists($db_path)) {
    $db_error = "Database file not found: " . htmlspecialchars($db_path);
} else {
    try {
        $db = new PDO('sqlite:' . $db_path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

        foreach ($path_php as $entry) {
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
        }
        $db = null; 
    } catch (PDOException $e) {
        $db_error = "Database error: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title><?php echo htmlspecialchars($page_title); ?></title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        h1 { color: #555; border-bottom: 2px solid #ccc; padding-bottom: 10px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; background-color: #fff; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }
        th, td { border: 1px solid #ddd; padding: 10px 12px; text-align: left; vertical-align: top; }
        th { background-color: #e9e9e9; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        td a { color: #0066cc; text-decoration: none; word-break: break-word; }
        td a:hover { text-decoration: underline; }
        .error-message { color: red; font-weight: bold; border: 1px solid red; padding: 10px; background-color: #fdd; margin-bottom: 20px; }
        .no-results { color: #555; font-style: italic; }
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
