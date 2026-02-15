const express = require('express');
const io = require('socket.io-client');
const app = express();

let socket = null;
let candleCache = {};
let isConnected = false;

// Initialize WebSocket connection
function initSocket(token) {
    const cookies = `remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=${token}; lang=en`;
    
    socket = io('wss://ws.market-qx.trade', {
        transports: ['websocket'],
        extraHeaders: { 
            'Origin': 'https://market-qx.trade',
            'Cookie': cookies
        }
    });

    socket.on('connect', () => {
        isConnected = true;
        socket.emit('tick');
        console.log('Connected to Quotex');
    });

    socket.on('message', (data) => {
        try {
            if (data.index && data.history) {
                candleCache[data.asset] = {
                    timestamp: Date.now(),
                    candles: data.history.map(c => ({
                        time: c[0], open: c[1], close: c[2], high: c[3], low: c[4]
                    }))
                };
            }
        } catch (e) {}
    });

    socket.on('disconnect', () => {
        isConnected = false;
    });
}

// API Endpoints
app.get('/candles/:asset', async (req, res) => {
    const { asset } = req.params;
    const period = parseInt(req.query.period) || 60;
    const offset = parseInt(req.query.offset) || 3600;

    if (!isConnected) {
        return res.status(503).json({ error: 'Not connected to Quotex' });
    }

    socket.emit('history/load', {
        asset: asset,
        index: Date.now(),
        time: Math.floor(Date.now() / 1000),
        offset: offset,
        period: period
    });

    // Wait for data
    setTimeout(() => {
        if (candleCache[asset]) {
            res.json(candleCache[asset]);
        } else {
            res.status(404).json({ error: 'No data received' });
        }
    }, 2000);
});

app.get('/status', (req, res) => {
    res.json({ connected: isConnected });
});

// Start server
const PORT = process.env.PORT || 3000;
const TOKEN = process.env.QUOTEX_TOKEN || 'YOUR_REMEMBER_TOKEN_HERE';

initSocket(TOKEN);

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
