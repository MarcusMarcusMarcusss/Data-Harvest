<?php
try {
    $conn = new PDO('sqlite:mega_scrape.db');
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Connection successful!";
    
    $stmt = $conn->query("SELECT * FROM ExtractedURL");
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    var_dump($rows);
} catch (PDOException $e) {
    echo "Connection failed: " . $e->getMessage();
    echo "<br/>Error Code: " . $e->getCode();
    echo "<br/>Stack Trace: " . $e->getTraceAsString();
}
?>