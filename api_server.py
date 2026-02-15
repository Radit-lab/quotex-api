from flask import Flask, request, jsonify
import asyncio
from pyquotex.stable_api import Quotex

app = Flask(__name__)

@app.route('/candles', methods=['GET'])
def get_candles():
    email = request.args.get('email', 'radithasan90@gmail.com')
    password = request.args.get('password', 'radit01923006192')
    asset = request.args.get('asset', 'EURUSD_otc')
    period = int(request.args.get('period', 60))
    count = int(request.args.get('count', 100))
    
    async def fetch():
        client = Quotex(email=email, password=password, lang="en")
        await client.connect()
        candles = await client.get_candle(asset, period, count)
        await client.close()
        return candles
    
    candles = asyncio.run(fetch())
    return jsonify(candles)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
