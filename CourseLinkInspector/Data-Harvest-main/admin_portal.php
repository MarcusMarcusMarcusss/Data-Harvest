<?php
set_time_limit(0);
session_start();
include('function.php');

$totalUnits = 0;
$courses = [];
$coordinators = [];

if (empty($_SESSION['logged_in'])) {
    header('Location: login_page.php');
    exit;
}
  try {
      $db = new PDO('sqlite:unit_inspector.db');
      $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
      $db->exec('PRAGMA foreign_keys = ON');
  } catch (PDOException $e) {
      die('Database error: ' . $e->getMessage());
  }

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['scan_inline'])) {
    $courses_to_scan = json_decode($_POST['scan_inline'], true);

    if (empty($courses_to_scan)) {
        echo "No courses selected.";
        exit;
    }

    $courseArgString = implode(',', $courses_to_scan);
    $courseArg = escapeshellarg($courseArgString);
    
    $scriptPath = 'LMS_SCRAPER/main.py';

    if (file_exists($scriptPath)) {
        $command = "python " . escapeshellarg($scriptPath) . " " . $courseArg;

        $descriptorspec = array(
           0 => array("pipe", "r"),
           1 => array("pipe", "w"),
           2 => array("pipe", "w")
        );

        $process = proc_open($command, $descriptorspec, $pipes);

        $python_stdout_full = "";
        $python_stderr_full = "";
        $return_value = -1;

        if (is_resource($process)) {
            fclose($pipes[0]);

            $python_stdout_full = stream_get_contents($pipes[1]);
            fclose($pipes[1]);

            $python_stderr_full = stream_get_contents($pipes[2]);
            fclose($pipes[2]);

            $return_value = proc_close($process);

            $final_html_response = "";
            $scan_complete_marker = "<h2>Scan Complete!</h2>";
            $trimmed_stdout = trim($python_stdout_full);

            $scan_complete_pos = strpos($trimmed_stdout, $scan_complete_marker);

            if ($scan_complete_pos !== false) {
                $final_html_response = substr($trimmed_stdout, $scan_complete_pos);
                if (!empty($python_stderr_full) && $return_value != 0) {
                     $error_info = "<h2>Python Script Error Information (stderr):</h2><pre style='color:red;'>" . htmlspecialchars($python_stderr_full) . "</pre>";
                     $final_html_response = $error_info . $final_html_response; 
                }
            } else {
                $final_html_response .= "<p style='font-weight:bold;'>The scan did not complete with the expected report. Displaying available debug information:</p>";
                if (!empty($python_stderr_full)) {
                    $final_html_response .= "<h2>Python Script Error Information (stderr):</h2><pre style='color:red;'>" . htmlspecialchars($python_stderr_full) . "</pre>";
                }
                if (!empty($trimmed_stdout)) { // Show whatever stdout was produced
                    $final_html_response .= "<h2>Python Script Output (stdout):</h2><pre>" . htmlspecialchars($trimmed_stdout) . "</pre>";
                }
                if (empty(trim($python_stderr_full)) && empty($trimmed_stdout)) { // Fallback if both are empty
                     $final_html_response = "<p>Scan process completed, but the Python script produced no output on stdout or stderr. Python exit code: $return_value.</p>";
                }
            }
            
            echo $final_html_response;

        } else {
            echo "<h2>Error: Could not open process to run the scan script.</h2>";
        }
    } else {
        echo "File does not exist: " . htmlspecialchars($scriptPath);
    }
    exit;
}


  #grab from the user its schedule when loading
  $user_id = $_SESSION['user_id'];
  $savedSchedule = getUserSchedule($user_id, $db);
  $scheduleCourses = $savedSchedule['courses'] ?? [];
  $scheduleDays = $savedSchedule['days'] ?? [];
  $scheduleTime = $savedSchedule['time'] ?? '';

  $daysString = !empty($scheduleDays) ? implode(', ', $scheduleDays) : 'No days scheduled';
  $timeString = !empty($scheduleTime) ? date('g:i A', strtotime($scheduleTime)) : 'No time set';
  $upcomingScanText = "$daysString, $timeString";

  $totalUnits = getTotalCourses();
  $courses    = getCourses();
  $coordinators = getCoordinators();
  $coordinatorCourseMap = getCoordinatorCourseMap();
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Course Inspector</title>
  <link rel="stylesheet" href="style.css" />
  <script>
    const savedSchedule = <?php echo json_encode($savedSchedule ?? ['courses'=>[], 'days'=>[], 'time'=>'02:00']); ?>;
  </script>
</head>
<body>
  <div class="page-container">
    <div class="side-panel">
      <h2>Admin Panel</h2>
      <ul>
        <li><a href="#" class="nav-link enabled" id="dashboard-link">Dashboard</a></li>
        <li><a href="#" class="nav-link enabled" id="unit-manager-link">Course Manager</a></li>
        <li><a href="#" class="nav-link enabled" id="scan-schedule-link">Scan Schedule</a></li>
      </ul>
      <a href="login_page.php?logout=1" class="logout-btn enabled">
      Logout
    </a>
    </div>

    <div class="main-content">

      <div id="admin-section" style="display: block;">

        <div id="dashboard-section" style="display:block;">
          <div class="header-container">
            <h1>Course Inspector - Dashboard</h1>
          </div>

          <div class="dashboard-container">
            <div class="dashboard-box">
              <h3>Total Units</h3>
              <p><?= htmlspecialchars($totalUnits) ?></p>
            </div>

            <div class="dashboard-box">
              <h3>Courses Managed</h3>
              <p class="courses-managed">
                <?php
                if (!empty($courses)) {
                    echo htmlspecialchars(implode(', ', $courses));
                } else {
                    echo 'No courses found.';
                }
                ?>
              </p>
            </div>

            <div class="dashboard-box">
              <h3>Upcoming Scan</h3>
              <p><?= htmlspecialchars($upcomingScanText) ?></p>
            </div>

            <div class="dashboard-box">
              <h3>Unit Coordinator</h3>
               <p class="courses-managed">
               <?php
                if (!empty($coordinators)) {
                    echo htmlspecialchars(implode(', ', $coordinators));
                } else {
                    echo 'No coordinators found.';
                }
                ?>
                </p>
            </div>
          </div>
        </div>

        <div id="unit-manager-section" style="display: none;">
          <div class="header-container">
            <h1>Course Inspector - Scan Manually</h1>
          </div>
          <div class="dual-container">
            <div class="selector-box">
              <div class="available-courses-text">Available Course</div>
                <input type="text" id="course-search" placeholder="Search course" style="margin-bottom: 10px; width: 100%;" />
                <div class="checkbox-container" id="course-list">
                  <?php if (!empty($courses)): ?>
                    <?php foreach ($courses as $course): ?>
                      <label><input type="checkbox" class="course-checkbox" value="<?= htmlspecialchars($course) ?>" /> <?= htmlspecialchars($course) ?></label>
                    <?php endforeach; ?>
                  <?php else: ?>
                    <p>No courses available.</p>
                  <?php endif; ?>
                </div>
              </div>

              <div class="selector-box">
                <div class="available-courses-text">Unit Coordinator</div>
                  <input type="text" id="coordinator-search" placeholder="Search coordinator" style="margin-bottom: 10px; width: 100%;" />
                <div class="checkbox-container" id="coordinator-list">
                  <?php if (!empty($coordinators)): ?>
                    <?php foreach ($coordinators as $coordinator): ?>
                      <label><input type="checkbox" class="unit_coordinator-checkbox" value="<?= htmlspecialchars($coordinator) ?>" /> <?= htmlspecialchars($coordinator) ?></label>
                    <?php endforeach; ?>
                  <?php else: ?>
                    <p>No coordinators available.</p>
                  <?php endif; ?>
                </div>
              </div>
            </div>
            <div class="header-container">
              <button class="Scan-btn">Scan</button>
            </div>

            <div id="loading-indicator" style="display:none; text-align:center; margin-top:20px;">
                <p>Scanning in progress, please wait...</p>
                <div class="spinner"></div> </div>
            <div id="scan-result-box" style="margin-top: 20px;"></div>

          </div>
        </div>

        <div id="scan-schedule-section" style="display: none;">
          <div class="header-container">
            <h1>Course Inspector - Scan Schedule</h1>
          </div>
            <div class="dual-container">
            <div class="selector-box">
              <div class="available-courses-text">Available Course</div>
              <div class="checkbox-container">
                <?php if (!empty($courses)): ?>
                  <?php foreach ($courses as $course): ?>
                    <label><input type="checkbox" class="course-checkbox" value="<?= htmlspecialchars($course) ?>" /> <?= htmlspecialchars($course) ?></label>
                  <?php endforeach; ?>
                <?php else: ?>
                  <p>No courses available.</p>
                <?php endif; ?>
              </div>
            </div>

            <div class="selector-box">
              <div class="available-courses-text">Unit Coordinator</div>
              <div class="checkbox-container">
                <?php if (!empty($coordinators)): ?>
                  <?php foreach ($coordinators as $coordinator): ?>
                    <label><input type="checkbox" class="unit_coordinator-checkbox" value="<?= htmlspecialchars($coordinator) ?>" /> <?= htmlspecialchars($coordinator) ?></label>
                  <?php endforeach; ?>
                <?php else: ?>
                  <p>No coordinators available.</p>
                <?php endif; ?>
              </div>
            </div>
          </div>

          <div class="scan-settings-box">
            <h3>Automated Scan Schedule</h3>
            <p>Select the days and time to automatically scan the Course(s):</p>

            <div class="day-selector">
              <label><input type="checkbox" value="Monday" /> Monday</label>
              <label><input type="checkbox" value="Tuesday" /> Tuesday</label>
              <label><input type="checkbox" value="Wednesday" /> Wednesday</label>
              <label><input type="checkbox" value="Thursday" /> Thursday</label>
              <label><input type="checkbox" value="Friday" /> Friday</label>
              <label><input type="checkbox" value="Saturday" /> Saturday</label>
              <label><input type="checkbox" value="Sunday" /> Sunday</label>
            </div>

            <div class="time-selector">
              <label for="scan-time">Select Scan Time:</label>
              <select id="scan-time">
                <option value="00:00">00:00 AM</option>
                <option value="02:00">2:00 AM</option>
                <option value="04:00">4:00 AM</option>
                <option value="06:00">6:00 AM</option>
                <option value="08:00">8:00 AM</option>
                <option value="10:00">10:00 AM</option>
                <option value="12:00">12:00 PM</option>
                <option value="14:00">2:00 PM</option>
                <option value="16:00">4:00 PM</option>
                <option value="18:00">6:00 PM</option>
                <option value="20:00">8:00 PM</option>
                <option value="22:00">10:00 PM</option>
              </select>
            </div>
          </div>
          <div class="header-container">
            <button class="Schedule-Save-btn">Save</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>

    document.getElementById('dashboard-link').addEventListener('click', function () {
      document.getElementById('dashboard-section').style.display = 'block';
      document.getElementById('unit-manager-section').style.display = 'none';
      document.getElementById('scan-schedule-section').style.display = 'none';
    });

    document.getElementById('unit-manager-link').addEventListener('click', function () {
      document.getElementById('unit-manager-section').style.display = 'block';
      document.getElementById('scan-schedule-section').style.display = 'none';
      document.getElementById('dashboard-section').style.display = 'none';
    });

    document.getElementById('scan-schedule-link').addEventListener('click', function () {
      document.getElementById('unit-manager-section').style.display = 'none';
      document.getElementById('scan-schedule-section').style.display = 'block';
      document.getElementById('dashboard-section').style.display = 'none';
    });

    const coordinatorCourseMap = <?php echo json_encode($coordinatorCourseMap); ?>;
      document.querySelectorAll('.unit_coordinator-checkbox').forEach(cb => {
        cb.addEventListener('change', function () {
          (coordinatorCourseMap[this.value] || []).forEach(code => {
            const target = this
              .closest('.dual-container')
              .querySelector(`input.course-checkbox[value="${code}"]`);
            if (target) target.checked = this.checked;
          });
        });
      });

    document.querySelector('.Scan-btn').addEventListener('click', function() {
    const checkedCourses = Array.from(document.querySelectorAll('#unit-manager-section .course-checkbox:checked'))
      .map(checkbox => checkbox.value);

      if (checkedCourses.length === 0) {
      alert('Please select at least one course to scan.');
      return;
    }

    const loadingIndicator = document.getElementById('loading-indicator');
    let resultBox = document.querySelector('#unit-manager-section #scan-result-box');
    if (!resultBox) {
        resultBox = document.createElement('div');
        resultBox.id = 'scan-result-box';
        resultBox.style.marginTop = '20px';
        const scanButton = document.querySelector('#unit-manager-section .Scan-btn');
        if (scanButton && scanButton.parentNode) {
            scanButton.parentNode.insertBefore(resultBox, loadingIndicator.nextSibling);
        } else {
            document.querySelector('#unit-manager-section').appendChild(resultBox);
        }
    }
    resultBox.innerHTML = ''; 
    resultBox.style.display = 'none'; 

    loadingIndicator.style.display = 'block'; 

      const formData = new FormData();
      formData.append('scan_inline', JSON.stringify(checkedCourses));


      fetch('admin_portal.php', {
        method: 'POST',
        body: formData
      })
      .then(response => response.text()) 
      .then(result => { 
        loadingIndicator.style.display = 'none'; 

        resultBox.innerHTML = result; 
        resultBox.style.display = 'block'; 
        console.log('Scan Output HTML from Server:', result);
      })
      .catch(error => {
        loadingIndicator.style.display = 'none';
        resultBox.innerHTML = '<strong style="color: red;">An error occurred during the scan request:</strong><pre>' + String(error) + '</pre>';
        resultBox.style.display = 'block';
        console.error('Scan Error:', error);
        alert('An error occurred during the scan: ' + error);
      });

    });

    document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('course-search').addEventListener('input', function () {
        const term = this.value.toLowerCase();
        const labels = document.querySelectorAll('#course-list label');
        labels.forEach(label => {
            const text = label.textContent.toLowerCase();
            label.style.display = text.includes(term) ? '' : 'none';
        });
    });

    document.getElementById('coordinator-search').addEventListener('input', function () {
        const term = this.value.toLowerCase();
        const labels = document.querySelectorAll('#coordinator-list label');
        labels.forEach(label => {
              const text = label.textContent.toLowerCase();
              label.style.display = text.includes(term) ? '' : 'none';
          });
      });
  });


  document.querySelector('.Schedule-Save-btn').addEventListener('click', () => {
    const courses = [...document.querySelectorAll('#scan-schedule-section .course-checkbox:checked')].map(c => c.value);
    const days = [...document.querySelectorAll('#scan-schedule-section .day-selector input:checked')].map(d => d.value);
    const scanTime = document.getElementById('scan-time').value;

    if (courses.length === 0) {
      alert('Please select at least one course to schedule.');
      return;
    }
    if (days.length === 0) {
      alert('Please pick at least one day for the automated scan.');
      return;
    }

    const data = {
      courses: courses,
      days: days,
      time: scanTime
    };

    fetch('save_schedule.php', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
      if(result.success) {
        alert('Schedule saved successfully.');
      } else {
        alert('Failed to save schedule: ' + (result.error || 'Unknown error'));
      }
    })
    .catch(error => {
      alert('Error saving schedule: ' + error.message);
    });
  });

  window.addEventListener('DOMContentLoaded', () => {
    if (typeof savedSchedule !== 'undefined' && savedSchedule.courses) {
        savedSchedule.courses.forEach(course => {
          const checkbox = document.querySelector(`#scan-schedule-section .course-checkbox[value="${course}"]`);
          if (checkbox) checkbox.checked = true;
        });
    }
    if (typeof savedSchedule !== 'undefined' && savedSchedule.days) {
        savedSchedule.days.forEach(day => {
          const dayCheckbox = document.querySelector(`#scan-schedule-section .day-selector input[value="${day}"]`);
          if (dayCheckbox) dayCheckbox.checked = true;
        });
    }
    if (typeof savedSchedule !== 'undefined' && savedSchedule.time) {
        const timeSelect = document.querySelector('#scan-schedule-section #scan-time');
        if (timeSelect) {
          timeSelect.value = savedSchedule.time;
        }
    }
  });


  </script>
</body>
</html>