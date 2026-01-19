<?php
header('Content-Type: application/json; charset=utf-8');
// Simple API to return per-day time series for temperature and wind_speed
// and the latest values for other metrics.

// Configuration - update if your DB credentials differ
$dbHost = '127.0.0.1';
$dbUser = 'weather_php';
$dbPass = 'password';
$dbName = 'database';
$dbPort = 3306;

// Parse date parameter (YYYY-MM-DD), default to today
$date = isset($_GET['date']) ? $_GET['date'] : date('Y-m-d');
if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) {
    http_response_code(400);
    echo json_encode(['error' => 'invalid date format, use YYYY-MM-DD']);
    exit;
}

$from = $date . ' 00:00:00';
$to   = $date . ' 23:59:59';

$mysqli = mysqli_init();
$mysqli->options(MYSQLI_OPT_CONNECT_TIMEOUT, 5);
if (!@$mysqli->real_connect($dbHost, $dbUser, $dbPass, $dbName, $dbPort)) {
    http_response_code(500);
    echo json_encode(['error' => 'db_connect', 'message' => mysqli_connect_error()]);
    exit;
}

// Prepare time series query
$stmt = $mysqli->prepare("SELECT time, temperature, wind_speed FROM weather_data WHERE time BETWEEN ? AND ? ORDER BY time ASC");
if (!$stmt) {
    http_response_code(500);
    echo json_encode(['error' => 'prepare_failed', 'message' => $mysqli->error]);
    exit;
}
$stmt->bind_param('ss', $from, $to);
$stmt->execute();
$res = $stmt->get_result();
$series = [];
while ($row = $res->fetch_assoc()) {
    $series[] = [
        'time' => $row['time'],
        'temperature' => $row['temperature'] !== null ? (float)$row['temperature'] : null,
        'wind_speed' => $row['wind_speed'] !== null ? (float)$row['wind_speed'] : null,
    ];
}
$stmt->close();

// Get latest values for other metrics
$latest = null;
$q = "SELECT time, wind_direction, wind_speed, rainfall, pressure, humidity, altitude, temperature FROM weather_data ORDER BY time DESC LIMIT 1";
if ($r = $mysqli->query($q)) {
    if ($row = $r->fetch_assoc()) {
        $latest = [
            'time' => $row['time'],
            'wind_direction' => $row['wind_direction'],
            'wind_speed' => $row['wind_speed'] !== null ? (float)$row['wind_speed'] : null,
            'rainfall' => $row['rainfall'] !== null ? (float)$row['rainfall'] : null,
            'pressure' => $row['pressure'] !== null ? (float)$row['pressure'] : null,
            'humidity' => $row['humidity'] !== null ? (float)$row['humidity'] : null,
            'altitude' => $row['altitude'] !== null ? (float)$row['altitude'] : null,
            'temperature' => $row['temperature'] !== null ? (float)$row['temperature'] : null,
        ];
    }
    $r->close();
}

$mysqli->close();

echo json_encode(['series' => $series, 'latest' => $latest]);
