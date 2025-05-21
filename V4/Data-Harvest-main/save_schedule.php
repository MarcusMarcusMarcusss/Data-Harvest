<?php
session_start();
if (empty($_SESSION['user_id'])) {
    http_response_code(401);
    echo json_encode(['error' => 'Not logged in']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);
if (empty($data['courses']) || empty($data['days']) || empty($data['time'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing data']);
    exit;
}

try {
    $db = new PDO('sqlite:unit_inspector.db');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $stmt = $db->prepare(
        "INSERT INTO Schedule (user_id, courses, days, time)
         VALUES (:user_id, :courses, :days, :time)
         ON CONFLICT(user_id) DO UPDATE SET
           courses = :courses,
           days = :days,
           time = :time"
    );

    $stmt->execute([
        ':user_id' => $_SESSION['user_id'],
        ':courses' => json_encode($data['courses']),
        ':days'    => json_encode($data['days']),
        ':time'    => $data['time']
    ]);

    echo json_encode(['success' => true]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>
