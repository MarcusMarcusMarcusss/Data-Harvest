<?php
function getExtractedURLs() {
    try {
        $conn = new PDO('sqlite:mega_scrape.db');
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $query = "SELECT URLString, Location, TimeStamp FROM ExtractedURL";
        $stmt = $conn->query($query);

        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        foreach ($rows as &$row) {
            $row['Risk Level'] = 'Low';
        }
        return $rows;
    } catch (PDOException $e) {
        error_log("Database connection failed: " . $e->getMessage());
        return [];
    }
}

function getCoordinatorInfo($coordinatorID) {
    try {
        $conn = new PDO('sqlite:mega_scrape.db');
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $query = "SELECT CoordinatorName, CoordinatorEmail FROM Coordinator WHERE coordinatorID = :coordinatorID";
        $stmt = $conn->prepare($query);
        $stmt->bindParam(':coordinatorID', $coordinatorID, PDO::PARAM_INT);
        
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($result) {
            return $result;
        } else {
            return [];
        }
    } catch (PDOException $e) {
        error_log("Database connection failed: " . $e->getMessage());
        return [];
    }
}

function getTotalCourses(): int {
    try {
        $db = new PDO('sqlite:mega_scrape.db');
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        return (int) $db->query("SELECT COUNT(*) FROM Unit")->fetchColumn();
    } catch (PDOException $e) {
        error_log("DB error in getTotalCourses: " . $e->getMessage());
        return 0;
    }
}

function getCourses(): array {
    try {
        $db = new PDO('sqlite:mega_scrape.db');
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $stmt = $db->query("SELECT UnitName FROM Unit ORDER BY UnitName");
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    } catch (PDOException $e) {
        error_log("DB error in getCourses: " . $e->getMessage());
        return [];
    }
}

function getCoordinators(): array {
    try {
        $db = new PDO('sqlite:mega_scrape.db');
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $stmt = $db->query("SELECT CoordinatorName FROM Coordinator ORDER BY CoordinatorName");
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    } catch (PDOException $e) {
        error_log("DB error in getCoordinators: " . $e->getMessage());
        return [];
    }
}



function getCoordinatorCourseMap(): array {
    try {
        $db = new PDO('sqlite:mega_scrape.db');
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        // Join Unit and Coordinator to get UnitName and CoordinatorName pairs
        $sql = "SELECT Unit.UnitName, Coordinator.CoordinatorName
                FROM Unit
                LEFT JOIN Coordinator ON Unit.CoordinatorID = Coordinator.CoordinatorID";

        $stmt = $db->query($sql);
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
        error_log($e->getMessage());
        return [];
    }
}



function saveUserSchedule($user_id, $courses, $days, $scan_time, $db) {
    $courses_str = implode(',', $courses);
    $days_str = implode(',', $days);

    // Check if schedule exists
    $stmt = $db->prepare("SELECT COUNT(*) FROM Schedule WHERE user_id = ?");
    $stmt->execute([$user_id]);
    if ($stmt->fetchColumn() > 0) {
        // Update existing
        $stmt = $db->prepare("UPDATE Schedule SET courses = ?, days = ?, scan_time = ? WHERE user_id = ?");
        $stmt->execute([$courses_str, $days_str, $scan_time, $user_id]);
    } else {
        // Insert new
        $stmt = $db->prepare("INSERT INTO Schedule (user_id, courses, days, scan_time) VALUES (?, ?, ?, ?)");
        $stmt->execute([$user_id, $courses_str, $days_str, $scan_time]);
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