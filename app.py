from flask import Flask, jsonify, request
from pyquotex.stable_api import Quotex
import asyncio

app = Flask(__name__)

# আপনার Quotex credentials
EMAIL = "radithasan90@gmail.com"
PASSWORD = "radit01923006192"

async def get_candles(asset, period, count):
    client = Quotex(email=EMAIL, password=PASSWORD, lang="en")
    check, reason = await client.connect()
    
    if not check:
        return {"error": f"Connection failed: {reason}"}
    
    candles = await client.get_candle(asset, period, count)
    await client.close()
    
    result = []
    for candle in candles:
        result.append({
            "time": candle["time"],
            "open": candle["open"],
            "close": candle["close"],
            "high": candle["high"],
            "low": candle["low"],
            "color": "GREEN" if candle["close"] > candle["open"] else "RED"
        })
    
    return result

@app.route('/candles/<asset>')
def candles(asset):
    count = int(request.args.get('count', 199))
    period = int(request.args.get('period', 60))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(get_candles(asset, period, count))
    loop.close()
    
    return jsonify(data)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "example": "/candles/USDBDT_otc?count=199&period=60"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
