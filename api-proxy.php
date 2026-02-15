<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// This PHP file will call your local Node.js server
// Upload this to radit.top

$asset = $_GET['asset'] ?? 'USDBDT_otc';
$count = $_GET['count'] ?? 199;
$period = $_GET['period'] ?? 60;

// Option 1: Call external API (if you deploy Node.js elsewhere)
$apiUrl = "https://your-nodejs-api.onrender.com/candles/$asset?count=$count&period=$period";

// Option 2: Use local Python PyQuotex (if you can run Python on hosting)
// exec("python3 get_candles.py $asset $count $period", $output);

// For now, return instruction
echo json_encode([
    'error' => 'Browser WebSocket blocked',
    'solution' => 'Deploy Node.js API to free hosting',
    'options' => [
        '1. Render.com (free)',
        '2. Railway.app (free)', 
        '3. Vercel (free)'
    ],
    'instruction' => 'See DEPLOY.md file'
]);
?>
