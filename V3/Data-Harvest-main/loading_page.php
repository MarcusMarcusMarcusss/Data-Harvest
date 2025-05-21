<?php
session_start();

if (!isset($_SESSION['logged_in'])) {
    header('Location: login_page.php');
    exit;
}
$pythonScript = 'LMS_SCRAPER\discover_course.py';

if (!file_exists($pythonScript)) {
    echo "Error: Python script not found at path: $pythonScript";
    exit;
}

header("Refresh: 2; url=admin_portal.php");

?>


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Loading...</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding-top: 100px;
            background-color: #f0f0f0;
        }
        .spinner {
            margin: 20px auto;
            border: 6px solid #f3f3f3;
            border-top: 6px solid #3498db;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0%   { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .message {
            margin-top: 20px;
            font-size: 18px;
            color: #333;
        }
    </style>
</head>
<body>
<?php if (!file_exists($pythonScript)): ?>
    <script>
        alert("Scraping script 'discover_course.py' is missing inside 'LMS_SCRAPER'.");
        window.location.href = 'admin_portal.php';
    </script>
<?php else: ?>
    <div class="spinner"></div>
    <div class="message">Loading available courses... Please wait.</div>

    <?php
    ob_flush();
    flush();

    $command = escapeshellcmd("python $pythonScript");
    $output = shell_exec($command);
    $lines = explode("\n", trim($output));
    $json = end($lines);
    $data = json_decode($json, true);

    if ($output === null) {
        echo "Error: Python script failed to run or produced no output.";
        exit;
    }else{
        print_r($data);
    }

    sleep(1);
    exit;
    ?>
<?php endif; ?>
</body>
</html>