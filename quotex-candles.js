const io = require('socket.io-client');

class QuotexCandles {
    constructor(ssid) {
        this.ssid = ssid; // Your session token from browser
        this.socket = null;
        this.candles = {};
    }

    connect() {
        this.socket = io('wss://ws2.qxbroker.com', {
            transports: ['websocket'],
            extraHeaders: {
                'Origin': 'https://qxbroker.com',
                'User-Agent': 'Mozilla/5.0'
            }
        });

        this.socket.on('connect', () => {
            console.log('Connected to Quotex');
            this.authenticate();
        });

        this.socket.on('message', (data) => {
            this.handleMessage(data);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected');
        });
    }

    authenticate() {
        this.socket.emit('authorization', { session: this.ssid, isDemo: 1 });
    }

    getCandles(asset, period, offset = 3600) {
        const payload = {
            asset: asset,
            index: Date.now(),
            time: Math.floor(Date.now() / 1000),
            offset: offset,
            period: period
        };
        this.socket.emit('history/load', payload);
    }

    handleMessage(message) {
        try {
            if (message.index && message.history) {
                // Historical candles received
                this.candles[message.asset] = message.history.map(c => ({
                    time: c[0],
                    open: c[1],
                    close: c[2],
                    high: c[3],
                    low: c[4]
                }));
                console.log(`Candles for ${message.asset}:`, this.candles[message.asset]);
            }
        } catch (e) {
            // Ignore parse errors
        }
    }

    subscribeRealtime(asset, period) {
        this.socket.emit('instruments/update', { asset: asset, period: period });
        this.socket.emit('depth/follow', asset);
    }

    disconnect() {
        if (this.socket) this.socket.disconnect();
    }
}

// Usage
const client = new QuotexCandles('YOUR_SSID_TOKEN_HERE');
client.connect();

setTimeout(() => {
    client.getCandles('EURUSD', 60, 3600); // 1min candles, last hour
}, 2000);
