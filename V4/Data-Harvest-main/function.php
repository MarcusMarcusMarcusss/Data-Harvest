<?php

// Utility function to get PDO connection if DB exists
function getDBConnection() {
    $dbFilePath = __DIR__ . '/LMS_SCRAPER/mega_scrape.db';
    
    if (!file_exists($dbFilePath)) {
        echo "<script>alert('Scrape database not found at LMS_SCRAPER/mega_scrape.db');</script>";
        return null;
    }

    try {
        $conn = new PDO('sqlite:' . $dbFilePath);
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $conn;
    } catch (PDOException $e) {
        echo "<script>alert('Database connection failed.');</script>";
        return null;
    }
}

function getExtractedURLs() {
    $conn = getDBConnection();
    if (!$conn) return [];

    try {
        $query = "SELECT URLString, Location, TimeStamp FROM ExtractedURL";
        $stmt = $conn->query($query);

        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        foreach ($rows as &$row) {
            $row['Risk Level'] = 'Low';
        }
        return $rows;
    } catch (PDOException $e) {
        echo "<script>alert('Query failed in getExtractedURLs: ' . $e->getMessage());</script>";
        return [];
    }
}

function getCoordinatorInfo($coordinatorID) {
    $conn = getDBConnection();
    if (!$conn) return [];

    try {
        $query = "SELECT CoordinatorName, CoordinatorEmail FROM Coordinator WHERE coordinatorID = :coordinatorID";
        $stmt = $conn->prepare($query);
        $stmt->bindParam(':coordinatorID', $coordinatorID, PDO::PARAM_INT);
        $stmt->execute();

        return $stmt->fetch(PDO::FETCH_ASSOC) ?: [];
    } catch (PDOException $e) {
        echo "<script>alert('Query failed in getCoordinatorInfo: ' . $e->getMessage());</script>";
        return [];
    }
}

function getTotalCourses(): int {
    $conn = getDBConnection();
    if (!$conn) return 0;

    try {
        return (int) $conn->query("SELECT COUNT(*) FROM Unit")->fetchColumn();
    } catch (PDOException $e) {
        echo "<script>alert('Query failed in getTotalCourses: ' . $e->getMessage());</script>";
        return 0;
    }
}

function getCourses(): array {
    $conn = getDBConnection();
    if (!$conn) return [];

    try {
        $stmt = $conn->query("SELECT UnitName FROM Unit ORDER BY UnitName");
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    } catch (PDOException $e) {
        error_log("Query failed in getCourses: " . $e->getMessage());
        return [];
    }
}

function getCoordinators(): array {
    $conn = getDBConnection();
    if (!$conn) return [];

    try {
        $stmt = $conn->query("SELECT CoordinatorName FROM Coordinator ORDER BY CoordinatorName");
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    } catch (PDOException $e) {
        error_log("Query failed in getCoordinators: " . $e->getMessage());
        return [];
    }
}

function getCoordinatorCourseMap(): array {
    $conn = getDBConnection();
    if (!$conn) return [];
    try {
        $sql = "SELECT Unit.UnitName, Coordinator.CoordinatorName
                FROM Unit
                LEFT JOIN Coordinator ON Unit.CoordinatorID = Coordinator.CoordinatorID";
        $stmt = $conn->query($sql);
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

        $map = [];
        foreach ($results as $row) {
            $coordinator = $row['CoordinatorName'] ?? 'Unassigned';
            $unit = $row['UnitName'];

            if (!isset($map[$coordinator])) {
                $map[$coordinator] = [];
            }
            $map[$coordinator][] = $unit;
        }
        return $map;
    } catch (PDOException $e) {
        error_log("Query failed in getCoordinatorCourseMap: " . $e->getMessage());
        return [];
    }
}

function saveUserSchedule($user_id, $courses, $days, $scan_time, $db) {
    $courses_str = implode(',', $courses);
    $days_str = implode(',', $days);

    try {
        $stmt = $db->prepare("SELECT COUNT(*) FROM Schedule WHERE user_id = ?");
        $stmt->execute([$user_id]);

        if ($stmt->fetchColumn() > 0) {
            $stmt = $db->prepare("UPDATE Schedule SET courses = ?, days = ?, scan_time = ? WHERE user_id = ?");
            $stmt->execute([$courses_str, $days_str, $scan_time, $user_id]);
        } else {
            $stmt = $db->prepare("INSERT INTO Schedule (user_id, courses, days, scan_time) VALUES (?, ?, ?, ?)");
            $stmt->execute([$user_id, $courses_str, $days_str, $scan_time]);
        }
    } catch (PDOException $e) {
        error_log("Query failed in saveUserSchedule: " . $e->getMessage());
    }
}

function getUserSchedule($user_id, $db) {
    $stmt = $db->prepare("SELECT courses, days, time FROM Schedule WHERE user_id = ?");
    $stmt->execute([$user_id]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row) {
        return [
            'courses' => json_decode($row['courses'], true),
            'days'    => json_decode($row['days'], true),
            'time'    => $row['time']
        ];
    }
    return null;
}
?>