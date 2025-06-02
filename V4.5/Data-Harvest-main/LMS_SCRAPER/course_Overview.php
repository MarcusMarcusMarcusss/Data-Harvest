<?php
// --- Configuration ---
error_reporting(E_ALL);
ini_set('display_errors', 1);

$db_file = 'mega_scrape.db'; 
$db_path = __DIR__ . '/' . $db_file;

$page_title = "Overall Course Link Inspector";
$columns = ["Course Name", "Coordinator Name", "Coordinator Email", "Report URL"];
$results = [];
$db_error = null;

// Embed path_php array
$path_php = array(
        [
            'course_id' => '2',
            'course_name' => 'DSSFZ101-Making the Best Dough in the World',
            'report_url' => 'http://localhost:3000/Data-Harvest-main/LMS_SCRAPER/course_inspector_DSSFZ101-Making the Best Dough in the World.php'
        ]
        );


// Connect to DB and collect coordinator info for each course
try {
    $db = new PDO('sqlite:' . $db_path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    foreach ($path_php as $entry) {
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
    }

    $db = null; // close connection
} catch (PDOException $e) {
    $db_error = "Database error: " . $e->getMessage();
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
