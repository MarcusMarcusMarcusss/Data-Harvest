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

    $taskName = "MoodleAutoScrape";
    $pythonExe = "C:/Users/xiema/AppData/Local/Programs/Python/Python310/python.exe"; 
    $pythonScript = "u:/ICT302/Project dev/Code/V4/Data-Harvest-main/LMS_SCRAPER/AutoScan.py";

    $userId = $_SESSION['user_id'];

    $dayMap = [
        "Sunday"    => "SUN",
        "Monday"    => "MON",
        "Tuesday"   => "TUE",
        "Wednesday" => "WED",
        "Thursday"  => "THU",
        "Friday"    => "FRI",
        "Saturday"  => "SAT"
    ];
    $shortDays = array_map(function($day) use ($dayMap) {
        return $dayMap[$day] ?? $day;
    }, $data['days']);
    $daysStr = implode(",", $shortDays);
    $time = $data['time'];
    $argumentas = ["ICT302","ICT303"];
    $jsonArgsss = json_encode($argumentas); 
    $command = "schtasks /Create /TN \"$taskName\" /TR \"\\\"$pythonExe\\\" \\\"$pythonScript\\\" $userId\" /SC WEEKLY /D $daysStr /ST $time /F";
    
    exec($command, $output, $returnCode);

    $debugCmd = "cmd /k \"\"$pythonExe\" \"$pythonScript\" $userId\"";
    exec("start \"\" $debugCmd");

    if ($returnCode !== 0) {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to schedule task', 'details' => $output]);
        exit;
    }
    echo json_encode(['success' => true]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>