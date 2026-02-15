const WebSocket = require('ws');
const https = require('https');

const SSID = 'RgLctoyrYG6bsO6foUOOXuD15vtCfIkxLQiyvCsF';

const ws = new WebSocket('wss://ws2.qxbroker.com/socket.io/?EIO=3&transport=websocket', {
    headers: {
        'Host': 'ws2.qxbroker.com',
        'Origin': 'https://qxbroker.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    rejectUnauthorized: false
});

let authenticated = false;
let waitingForEvent = null;

ws.on('open', () => {
    console.log('✅ Connected!\n');
});

ws.on('message', (data) => {
    const msg = data.toString();
    
    // Handshake
    if (msg.startsWith('0')) {
        ws.send('40');
        setTimeout(() => {
            ws.send(`42["authorization",{"session":"${SSID}","isDemo":1,"tournamentId":0}]`);
        }, 500);
        return;
    }
    
    // Track binary message type
    if (msg.startsWith('451-')) {
        const match = msg.match(/451-\["([^"]+)"/);
        if (match) waitingForEvent = match[1];
        return;
    }
    
    // Binary data
    if (data instanceof Buffer && data[0] === 0x04) {
        try {
            const json = JSON.parse(data.slice(1).toString());
            
            // Candle data from history/load
            if (waitingForEvent === 'history/load' && json.data) {
                // Only process USDBDT_otc data
                if (json.asset !== 'USDBDT_otc') return;
                
                console.log('🎯 USDBDT_otc Candles received!\n');
                console.log('Period:', json.period, 'seconds');
                console.log('Total candles:', json.data.length);
                
                // Get last 199 candles
                const last199 = json.data.slice(-199);
                console.log('\nLast 199 candles:');
                last199.forEach((c, i) => {
                    const time = new Date((c.time || c[0]) * 1000).toLocaleString();
                    const open = c.open || c[1];
                    const close = c.close || c[2];
                    const high = c.high || c[3];
                    const low = c.low || c[4];
                    console.log(`${i+1}. ${time} | O:${open} H:${high} L:${low} C:${close}`);
                });
                process.exit(0);
            }
            
            // Alternative format (tick data)
            if (json.history) {
                // Only process USDBDT_otc
                if (json.asset !== 'USDBDT_otc') return;
                
                console.log('🎯 USDBDT_otc Candles received!\n');
                console.log('Total ticks:', json.history.length);
                
                const candles = {};
                json.history.forEach(tick => {
                    const time = Math.floor(tick[0] / 60) * 60;
                    if (!candles[time]) {
                        candles[time] = { open: tick[1], high: tick[1], low: tick[1], close: tick[1], time: time };
                    } else {
                        candles[time].high = Math.max(candles[time].high, tick[1]);
                        candles[time].low = Math.min(candles[time].low, tick[1]);
                        candles[time].close = tick[1];
                    }
                });
                
                const candleArray = Object.values(candles).sort((a, b) => a.time - b.time);
                
                // Get last 199 candles
                const last199 = candleArray.slice(-199);
                console.log('Last 199 candles:\n');
                last199.forEach((c, i) => {
                    const time = new Date(c.time * 1000).toLocaleString();
                    console.log(`${i+1}. ${time} | O:${c.open} H:${c.high} L:${c.low} C:${c.close}`);
                });
                process.exit(0);
            }
        } catch (e) {}
        return;
    }
    
    // Authenticated
    if (msg.includes('s_authorization') && !authenticated) {
        authenticated = true;
        console.log('✅ Authenticated!\n');
        
        setTimeout(() => {
            const payload = {
                asset: 'USDBDT_otc',
                index: Date.now(),
                time: Math.floor(Date.now() / 1000),
                offset: 199 * 60, // 199 minutes of data
                period: 60
            };
            ws.send(`42["history/load",${JSON.stringify(payload)}]`);
            console.log('📊 Requesting USDBDT_otc candles...\n');
        }, 2000);
    }
});

ws.on('error', (err) => console.log('❌', err.message));
ws.on('close', () => console.log('Connection closed'));

setInterval(() => {
    if (ws.readyState === 1) ws.send('2');
}, 25000);

console.log('🔄 Connecting...\n');
