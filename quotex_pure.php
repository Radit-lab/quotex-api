<?php
// Pure PHP Quotex Candle Fetcher
$asset = $argv[1] ?? 'EURUSD_otc';
$count = (int)($argv[2] ?? 100);
$period = (int)($argv[3] ?? 60);
$email = 'radithasan90@gmail.com';
$password = 'radit01923006192';

function connectQuotex($email, $password, $asset, $period, $count) {
    $host = 'ws2.qxbroker.com';
    $port = 443;
    $path = '/socket.io/?EIO=3&transport=websocket';
    
    // Create SSL socket
    $context = stream_context_create([
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false,
            'allow_self_signed' => true
        ]
    ]);
    
    $socket = @stream_socket_client(
        "ssl://{$host}:{$port}",
        $errno, $errstr, 30,
        STREAM_CLIENT_CONNECT,
        $context
    );
    
    if (!$socket) {
        return ['error' => "Connection failed: $errstr ($errno)"];
    }
    
    stream_set_blocking($socket, false);
    
    // WebSocket handshake
    $key = base64_encode(openssl_random_pseudo_bytes(16));
    $accept = base64_encode(sha1($key . '258EAFA5-E914-47DA-95CA-C5AB0DC85B11', true));
    
    $request = "GET {$path} HTTP/1.1\r\n";
    $request .= "Host: {$host}\r\n";
    $request .= "Upgrade: websocket\r\n";
    $request .= "Connection: Upgrade\r\n";
    $request .= "Sec-WebSocket-Key: {$key}\r\n";
    $request .= "Sec-WebSocket-Version: 13\r\n";
    $request .= "Origin: https://qxbroker.com\r\n";
    $request .= "User-Agent: Mozilla/5.0\r\n\r\n";
    
    fwrite($socket, $request);
    
    // Read handshake response
    sleep(1);
    $response = '';
    while ($data = fread($socket, 1024)) {
        $response .= $data;
        if (strpos($response, "\r\n\r\n") !== false) break;
    }
    
    if (strpos($response, '101 Switching Protocols') === false) {
        fclose($socket);
        return ['error' => 'Handshake failed'];
    }
    
    // Wait for Socket.IO connection
    sleep(1);
    $buffer = '';
    while ($data = fread($socket, 8192)) {
        $buffer .= $data;
        if (strlen($buffer) > 0) break;
    }
    
    // Send Socket.IO probe
    sendFrame($socket, '2probe');
    sleep(1);
    
    // Upgrade to websocket
    sendFrame($socket, '5');
    sleep(1);
    
    // Authenticate
    $authPayload = json_encode([
        'email' => $email,
        'password' => $password
    ]);
    sendFrame($socket, '42["authorize",' . $authPayload . ']');
    sleep(2);
    
    // Clear buffer
    while (fread($socket, 8192)) {}
    
    // Request candles
    $candlePayload = json_encode([
        'asset' => $asset,
        'period' => $period,
        'count' => $count
    ]);
    sendFrame($socket, '42["candles",' . $candlePayload . ']');
    
    // Read candle response
    $candles = [];
    $timeout = time() + 15;
    $buffer = '';
    
    while (time() < $timeout) {
        $data = fread($socket, 8192);
        if ($data) {
            $decoded = decodeFrame($data);
            if ($decoded) {
                $buffer .= $decoded;
                
                // Check if we have candle data
                if (strpos($buffer, 'candles') !== false || strpos($buffer, '"data"') !== false) {
                    // Try to extract JSON
                    if (preg_match('/42\["candles",(.+)\]/', $buffer, $matches)) {
                        $candles = json_decode($matches[1], true);
                        break;
                    } elseif (preg_match('/\{.+"data":.+\}/', $buffer, $matches)) {
                        $result = json_decode($matches[0], true);
                        if (isset($result['data'])) {
                            $candles = $result['data'];
                            break;
                        }
                    }
                }
            }
        }
        usleep(200000);
    }
    
    fclose($socket);
    
    if (empty($candles)) {
        return ['error' => 'No candle data received'];
    }
    
    return $candles;
}

function sendFrame($socket, $data) {
    $length = strlen($data);
    $header = chr(0x81); // Text frame, FIN bit set
    
    if ($length <= 125) {
        $header .= chr($length | 0x80); // Masked
    } elseif ($length <= 65535) {
        $header .= chr(126 | 0x80) . pack('n', $length);
    } else {
        $header .= chr(127 | 0x80) . pack('J', $length);
    }
    
    // Masking key
    $mask = openssl_random_pseudo_bytes(4);
    $header .= $mask;
    
    // Mask data
    $masked = '';
    for ($i = 0; $i < $length; $i++) {
        $masked .= $data[$i] ^ $mask[$i % 4];
    }
    
    fwrite($socket, $header . $masked);
}

function decodeFrame($data) {
    if (strlen($data) < 2) return '';
    
    $byte1 = ord($data[0]);
    $byte2 = ord($data[1]);
    
    $payloadLength = $byte2 & 127;
    $maskStart = 2;
    
    if ($payloadLength == 126) {
        $maskStart = 4;
        $payloadLength = unpack('n', substr($data, 2, 2))[1];
    } elseif ($payloadLength == 127) {
        $maskStart = 10;
        $payloadLength = unpack('J', substr($data, 2, 8))[1];
    }
    
    if (strlen($data) < $maskStart + $payloadLength) {
        return '';
    }
    
    return substr($data, $maskStart, $payloadLength);
}

echo "Connecting to Quotex...\n";
echo "Fetching $count candles for $asset (period: {$period}s)\n\n";

$result = connectQuotex($email, $password, $asset, $period, $count);

if (isset($result['error'])) {
    echo "Error: " . $result['error'] . "\n";
    echo "\nNote: PHP WebSocket support is limited. Consider using:\n";
    echo "1. Python version (recommended)\n";
    echo "2. Node.js version\n";
    echo "3. PHP with Ratchet library\n";
} else {
    echo json_encode($result, JSON_PRETTY_PRINT) . "\n";
}
?>
