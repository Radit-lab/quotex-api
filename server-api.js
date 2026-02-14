const express = require('express');
const WebSocket = require('ws');

const app = express();
const PORT = process.env.PORT || 3000;

let SSID = 'RgLctoyrYG6bsO6foUOOXuD15vtCfIkxLQiyvCsF';

// Get candles endpoint
app.get('/candles/:asset', async (req, res) => {
    const { asset } = req.params;
    const count = parseInt(req.query.count) || 199;
    const period = parseInt(req.query.period) || 60;
    
    try {
        const candles = await fetchCandles(asset, count, period);
        res.json({
            success: true,
            asset: asset,
            count: candles.length,
            period: period,
            candles: candles
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Update SSID endpoint
app.get('/update-ssid/:newSsid', (req, res) => {
    SSID = req.params.newSsid;
    res.json({ success: true, message: 'SSID updated' });
});

// Health check
app.get('/', (req, res) => {
    res.json({
        status: 'running',
        endpoints: {
            candles: '/candles/:asset?count=199&period=60',
            updateSsid: '/update-ssid/:newSsid'
        },
        example: '/candles/USDBDT_otc?count=199&period=60'
    });
});

function fetchCandles(asset, count, period) {
    return new Promise((resolve, reject) => {
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
        const timeout = setTimeout(() => {
            ws.close();
            reject(new Error('Timeout'));
        }, 15000);

        ws.on('open', () => {});

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

                    if (waitingForEvent === 'history/list/v2' && json.candles) {
                        if (json.asset !== asset) return;

                        const result = json.candles.slice(-count).map((c, i) => {
                            const isGreen = c[2] > c[1];
                            const isRed = c[2] < c[1];
                            const color = isGreen ? 'GREEN' : isRed ? 'RED' : 'DOJI';
                            return {
                                index: i + 1,
                                time: c[0],
                                date: new Date(c[0] * 1000).toISOString(),
                                open: c[1],
                                close: c[2],
                                high: c[3],
                                low: c[4],
                                color: color
                            };
                        });

                        clearTimeout(timeout);
                        ws.close();
                        resolve(result);
                    }
                } catch (e) {}
                return;
            }

            if (msg.includes('s_authorization') && !authenticated) {
                authenticated = true;
                setTimeout(() => {
                    ws.send(`42["history/list/v2",${JSON.stringify({
                        asset: asset,
                        period: period,
                        start: Math.floor(Date.now() / 1000) - (count * period),
                        end: Math.floor(Date.now() / 1000)
                    })}]`);
                }, 2000);
            }
        });

        ws.on('error', (err) => {
            clearTimeout(timeout);
            reject(err);
        });
    });
}

app.listen(PORT, () => {
    console.log(`🚀 Quotex API Server running on port ${PORT}`);
    console.log(`📊 Example: http://localhost:${PORT}/candles/USDBDT_otc?count=199&period=60`);
});
