<?php
$asset = $argv[1] ?? 'USDBDT_otc';
$count = (int)($argv[2] ?? 100);
$period = (int)($argv[3] ?? 60);
$email = 'radithasan90@gmail.com';
$password = 'radit01923006192';

function quotexWebSocket($email, $password, $asset, $period, $count) {
    $host = 'ws2.qxbroker.com';
    $port = 443;
    
    $context = stream_context_create([
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
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
    
    $key = base64_encode(random_bytes(16));
    $headers = "GET /socket.io/?EIO=4&transport=websocket HTTP/1.1\r\n";
    $headers .= "Host: {$host}\r\n";
    $headers .= "Upgrade: websocket\r\n";
    $headers .= "Connection: Upgrade\r\n";
    $headers .= "Sec-WebSocket-Key: {$key}\r\n";
    $headers .= "Sec-WebSocket-Version: 13\r\n";
    $headers .= "Origin: https://qxbroker.com\r\n\r\n";
    
    fwrite($socket, $headers);
    
    $response = '';
    while ($line = fgets($socket)) {
        $response .= $line;
        if (trim($line) === '') break;
    }
    
    if (strpos($response, '101') === false) {
        fclose($socket);
        return ['error' => 'WebSocket handshake failed'];
    }
    
    $frame = chr(0x81) . chr(1) . '0';
    fwrite($socket, $frame);
    sleep(1);
    
    $authMsg = '42["auth",{"email":"'.$email.'","password":"'.$password.'"}]';
    $frame = encodeWebSocketFrame($authMsg);
    fwrite($socket, $frame);
    sleep(2);
    
    $candleMsg = '42["candles",{"asset":"'.$asset.'","period":'.$period.',"count":'.$count.'}]';
    $frame = encodeWebSocketFrame($candleMsg);
    fwrite($socket, $frame);
    
    $candles = [];
    $timeout = time() + 10;
    
    while (time() < $timeout) {
        $data = fread($socket, 8192);
        if ($data) {
            $decoded = decodeWebSocketFrame($data);
            if (strpos($decoded, 'candles') !== false) {
                $json = substr($decoded, 2);
                $parsed = json_decode($json, true);
                if (isset($parsed[1])) {
                    $candles = $parsed[1];
                    break;
                }
            }
        }
        usleep(100000);
    }
    
    fclose($socket);
    return $candles;
}

function encodeWebSocketFrame($data) {
    $length = strlen($data);
    $frame = chr(0x81);
    
    if ($length <= 125) {
        $frame .= chr($length);
    } elseif ($length <= 65535) {
        $frame .= chr(126) . pack('n', $length);
    } else {
        $frame .= chr(127) . pack('J', $length);
    }
    
    return $frame . $data;
}

function decodeWebSocketFrame($data) {
    if (strlen($data) < 2) return '';
    $payloadStart = 2;
    $payloadLength = ord($data[1]) & 127;
    
    if ($payloadLength == 126) {
        $payloadStart = 4;
        $payloadLength = unpack('n', substr($data, 2, 2))[1];
    } elseif ($payloadLength == 127) {
        $payloadStart = 10;
        $payloadLength = unpack('J', substr($data, 2, 8))[1];
    }
    
    return substr($data, $payloadStart, $payloadLength);
}

echo "Fetching candles for $asset...\n";
$candles = quotexWebSocket($email, $password, $asset, $period, $count);

if (isset($candles['error'])) {
    echo "Error: " . $candles['error'] . "\n";
} else {
    echo json_encode($candles, JSON_PRETTY_PRINT) . "\n";
}
?>
