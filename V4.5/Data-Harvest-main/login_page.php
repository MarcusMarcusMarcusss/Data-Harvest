<?php
session_start();


$error = '';

try {
    $db = new PDO('sqlite:unit_inspector.db');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec('PRAGMA foreign_keys = ON');
} catch (PDOException $e) {
    die('Database error: ' . $e->getMessage());
}

if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: ' . strtok($_SERVER['REQUEST_URI'], '?'));
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $user = trim($_POST['username'] ?? '');
    $pass = trim($_POST['password'] ?? '');

    $stmt = $db->prepare(
        "SELECT user_id, password, user_type
         FROM Login
         WHERE username = :u"
    );
    $stmt->execute([':u' => $user]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);


    if ($row && $pass === $row['password']) {
        $_SESSION['logged_in'] = true;
        $_SESSION['user_id']  = $row['user_id'];
        $_SESSION['user_type'] = $row['user_type'];
        header('Location: loading_page.php');
        exit;
    }
    $error = 'Invalid username or password.';
}

if (!empty($_SESSION['logged_in'])) {
    header('Location:admin_portal.php');
    exit;
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Unit Inspector Login Page</title>
<link rel="stylesheet" href="style.css" />
</head>
<body class="login-page-background">
  <div class="login-section" id="login-section">
    <h2>Welcome to Unit Inspector</h2>
    <p>Please login to access the admin portal<p>
    <?php if ($error): ?>
      <div class="error"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>
    <form method="POST" action="">
      <input type="text" name="username" placeholder="Username" required autofocus />
      <input type="password" name="password" placeholder="Password" required />
      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html>
