<?php
include('function.php');
try {
    $db = new PDO('sqlite:mega_scrape.db');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $tablesStmt = $db->query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'");
    $tables = $tablesStmt->fetchAll(PDO::FETCH_COLUMN);

    foreach ($tables as $table) {
        echo "<h2>Table: " . htmlspecialchars($table) . "</h2>";

        $columnsStmt = $db->query("PRAGMA table_info($table)");
        $columns = $columnsStmt->fetchAll(PDO::FETCH_ASSOC);

        $uniqueCols = [];
        $indexesStmt = $db->query("PRAGMA index_list($table)");
        $indexes = $indexesStmt->fetchAll(PDO::FETCH_ASSOC);

        foreach ($indexes as $index) {
            if ($index['unique']) {
                $indexName = $index['name'];
                $indexInfoStmt = $db->query("PRAGMA index_info($indexName)");
                $indexCols = $indexInfoStmt->fetchAll(PDO::FETCH_ASSOC);
                foreach ($indexCols as $ic) {
                    $uniqueCols[$ic['name']] = true;
                }
            }
        }

        if ($columns) {
            echo "<table border='1' cellpadding='5' cellspacing='0'>";
            echo "<thead><tr>";
            echo "<th>Column Name</th><th>Primary Key</th><th>Unique</th>";
            echo "</tr></thead><tbody>";

            foreach ($columns as $col) {
                $isPK = $col['pk'] ? 'Yes' : 'No';
                $isUnique = isset($uniqueCols[$col['name']]) ? 'Yes' : 'No';

                if ($isPK === 'Yes') {
                    $isUnique = 'Yes';
                }
                echo "<tr>";
                echo "<td>" . htmlspecialchars($col['name']) . "</td>";
                echo "<td style='text-align:center;'>" . $isPK . "</td>";
                echo "<td style='text-align:center;'>" . $isUnique . "</td>";
                echo "</tr>";
            }

            echo "</tbody></table><br>";
        } else {
            echo "<p>No columns found for table " . htmlspecialchars($table) . ".</p>";
        }
    }
} catch (PDOException $e) {
    echo "<p>DB Error: " . htmlspecialchars($e->getMessage()) . "</p>";
}


$totalCourses = getTotalCourses();
$courses = getCourses();
$coordinators = getCoordinators();

print_r([
    'total_courses' => $totalCourses,
    'courses' => $courses,
    'coordinators' => $coordinators
]);

?>
