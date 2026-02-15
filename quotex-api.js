const WebSocket = require('ws');
const fs = require('fs');

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

ws.on('open', () => console.log('✅ Connected!\n'));

ws.on('message', (data) => {
    const msg = data.toString();
    
    if (msg.startsWith('0')) {
        ws.send('40');
        setTimeout(() => {
            ws.send(`42["authorization",{"session":"${SSID}","isDemo":1,"tournamentId":0}]`);
        }, 500);
        return;
    }
    
    if (msg.startsWith('451-')) {
        const match = msg.match(/451-\["([^"]+)"/);
        if (match) waitingForEvent = match[1];
        return;
    }
    
    if (data instanceof Buffer && data[0] === 0x04) {
        try {
            const json = JSON.parse(data.slice(1).toString());
            
            // history/list/v2 response
            if (waitingForEvent === 'history/list/v2' && json.candles) {
                if (json.asset !== 'USDBDT_otc') return;
                
                console.log('Sample candle:', json.candles[0]);
                
                const result = json.candles.slice(-199).map((c, i) => {
                    const isGreen = c[2] > c[1];
                    const isRed = c[2] < c[1];
                    const color = isGreen ? '🟢 GREEN' : isRed ? '🔴 RED' : '⚪ DOJI';
                    return {
                        index: i + 1,
                        time: c[0],
                        date: new Date(c[0] * 1000).toLocaleString(),
                        open: c[1],
                        close: c[2],
                        high: c[3],
                        low: c[4],
                        color: color
                    };
                });
                
                console.log(`\n🎯 Got ${result.length} candles for USDBDT_otc\n`);
                result.forEach(c => {
                    console.log(`${c.index}. USDBDT_otc ${c.date} | O:${c.open} H:${c.high} L:${c.low} C:${c.close} | ${c.color}`);
                });
                
                fs.writeFileSync('usdbdt_candles.json', JSON.stringify(result, null, 2));
                console.log('\n✅ Saved to usdbdt_candles.json');
                process.exit(0);
            }
        } catch (e) {}
        return;
    }
    
    if (msg.includes('s_authorization') && !authenticated) {
        authenticated = true;
        console.log('✅ Authenticated!\n');
        
        setTimeout(() => {
            ws.send(`42["history/list/v2",${JSON.stringify({
                asset: 'USDBDT_otc',
                period: 60,
                start: Math.floor(Date.now() / 1000) - (199 * 60),
                end: Math.floor(Date.now() / 1000)
            })}]`);
            console.log('📊 Requesting last 199 candles for USDBDT_otc...\n');
        }, 2000);
    }
});

ws.on('error', (err) => console.log('❌', err.message));
ws.on('close', () => console.log('Connection closed'));

setInterval(() => { if (ws.readyState === 1) ws.send('2'); }, 25000);

console.log('🔄 Connecting...\n');
