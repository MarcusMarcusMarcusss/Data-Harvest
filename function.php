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
?>