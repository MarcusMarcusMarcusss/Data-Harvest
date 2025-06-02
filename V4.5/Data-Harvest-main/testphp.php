<?php
$pythonScript = 'LMS_SCRAPER\discover_course.py';

if (!file_exists($pythonScript)) {
    echo "Error: Python script not found at path: $pythonScript";
    exit;
}

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
?>