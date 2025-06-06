<?php
include('function.php');
$rows = getExtractedURLs();
$coordinator = getCoordinatorInfo(1);
?>
<!DOCTYPE html>

<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="style.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>
</head>
<body>
    <div class="header-container">
        <h1>ICT302 Course Link Inspector</h1>
        <button id="downloadBtn" class="title-download-btn" onclick="downloadPage()">Download</button>
    </div>
    <!-- Display Coordinator Information -->
    <div class="coordinator-info">
        <p><strong>Unit Coordinator: </strong><?php echo htmlspecialchars($coordinator['CoordinatorName']); ?></p>
        <p><strong>Email: </strong><a href="mailto:<?php echo htmlspecialchars($coordinator['CoordinatorEmail']); ?>"><?php echo htmlspecialchars($coordinator['CoordinatorEmail']); ?></a></p>
    </div>
    <!-- Table for High, Medium, Broken -->
    <div class="UnitURL-info">
    <table>
        <thead>
            <tr>
                <th class="sortable">Timestamp</th>
                <th class="sortable">Risk Level</th>
                <th class="sortable">Category</th>
                <th class="sortable">Link</th>
                <th class="sortable">From Source</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>2025-04-20 10:33:00</td>
                <td><span class="circle high"></span> High</td>
                <td>Phishing</td>
                <td>
                    <span id="link1">https://KEYtoTheHeart.men</span>
                    <button class="copy-btn" onclick="copyToClipboard('link1', this)">Copy</button>
                </td>
                <td>Lecture Slides week 6</td>
            </tr>
            <tr>
                <td>2025-04-20 10:30:00</td>
                <td><span class="circle medium"></span> Medium</td>
                <td>Expired SSL</td>
                <td>
                    <span id="link2">https://www.telstra.com.eu</span>
                    <button class="copy-btn" onclick="copyToClipboard('link2', this)">Copy</button>
                </td>
                <td>Lecture Slides week 3</td>
            </tr>
            <tr>
                <td>2025-04-20 10:39:00</td>
                <td><span class="circle broken"></span> Broken</td>
                <td>Broken Link</td>
                <td>
                    <span id="link4">https://www.404.org</span>
                    <button class="copy-btn" onclick="copyToClipboard('link4', this)">Copy</button>
                </td>
                <td>Lecture Slides week 3</td>
            </tr>
        </tbody>
    </table>

    <!-- Table for Low Risk -->
    <table>
        <thead>
            <tr>
                <th class="sortable">Timestamp</th>
                <th class="sortable">Risk Level</th>
                <th class="sortable">Link</th>
                <th class="sortable">From Source</th>
            </tr>
        </thead>
        <tbody>
        <?php
            $rowIndex = 1;
            foreach ($rows as $r) {
                $timestamp = $r['TimeStamp'];
                $risk_level = 'Low';
                $link = $r['URLString'];
                $location = $r['Location'];
            ?>
            <tr>
                <td><?php echo $timestamp; ?></td>
                <td><span class="circle <?php echo strtolower($risk_level); ?>"></span> <?php echo $risk_level; ?></td>
                <td>
                    <span id="link<?php echo $timestamp. ':' . $rowIndex; ?>"><?php echo $link; ?></span>
                    <button class="copy-btn" onclick="copyToClipboard('link<?php echo $timestamp. ':' . $rowIndex; ?>', this)">Copy</button>
                </td>
                <td><?php echo $location; ?></td>
            </tr>
            <?php
                $rowIndex++;
            }
            ?>
        </tbody>
    </table>
    </div>

    <!-- Legend -->
    <div class="legend">
        <h3>Security Level Legend</h3>
        <div class="legend-item-Grey">
            <span class="circle broken"></span> 
            Broken Link (Grey) – Link cannot be scanned (e.g., 404 errors).
        </div>
        <div class="legend-item-Green">
            <span class="circle low"></span> 
            Low Risk (Green) – No issues detected, safe resource.
        </div>
        <div class="legend-item-Amber">
            <span class="circle medium"></span> 
            Medium Risk (Amber) – Potential issues flagged (suspicious but not confirmed).
        </div>
        <div class="legend-item-Red">
            <span class="circle high"></span> 
            High Risk (Red) – Confirmed threats (phishing, malware, etc.).
        </div>
    </div>

    <script src="function.js"></script>
</body>
</html>
