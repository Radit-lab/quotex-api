<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// This PHP calls your local Node.js server
// You need to expose it using ngrok or similar

$asset = $_GET['asset'] ?? 'USDBDT_otc';
$count = $_GET['count'] ?? 199;
$period = $_GET['period'] ?? 60;

// Option 1: Call local server via ngrok
$nodeServerUrl = "http://YOUR_NGROK_URL/candles/$asset?count=$count&period=$period";

// Option 2: Call deployed server (Render/Railway)
// $nodeServerUrl = "https://your-app.onrender.com/candles/$asset?count=$count&period=$period";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $nodeServerUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode === 200) {
    echo $response;
} else {
    echo json_encode([
        'error' => 'Failed to fetch candles',
        'instructions' => [
            '1. Run: node server-api.js (on your computer)',
            '2. Run: ngrok http 3000',
            '3. Update $nodeServerUrl in this PHP file with ngrok URL',
            '4. Or deploy to Render.com and use that URL'
        ]
    ]);
}
?>
