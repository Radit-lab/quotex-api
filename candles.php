<?php
$asset = $argv[1] ?? 'EURUSD_otc';
$count = (int)($argv[2] ?? 100);
$period = (int)($argv[3] ?? 60);
$email = 'radithasan90@gmail.com';
$password = 'radit01923006192';

echo "Fetching candles for $asset...\n";

$pythonScript = __DIR__ . '/app.py';
$command = "python \"$pythonScript\" get_candles $email $password $asset $period $count";

exec($command, $output, $returnCode);

if ($returnCode === 0) {
    $result = implode("\n", $output);
    echo $result . "\n";
} else {
    echo "Error: Failed to fetch candles\n";
    echo "Make sure Python and PyQuotex are installed\n";
}
?>
