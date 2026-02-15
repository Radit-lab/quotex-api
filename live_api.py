import os
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import time as time_module
import json
import uvicorn
from pyquotex.stable_api import Quotex
from pyquotex.config import credentials
from datetime import datetime, timezone, timedelta

app = FastAPI(title="PyQuotex Live API")
client = None

TIMEFRAMES = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H2": 7200,
    "H4": 14400,
    "D1": 86400
}

SIGNAL_WINDOW_START = 50
SIGNAL_WINDOW_END = 55

# Bangladesh timezone (UTC+6)
BD_TZ = timezone(timedelta(hours=6))


async def get_client():
    global client
    if client is None:
        email, password = credentials()
        client = Quotex(email=email, password=password, lang="pt")
        await client.connect()
    return client


async def wait_for_signal_window(period: int = 60):
    while True:
        current_time = time_module.time()
        seconds_into_candle = int(current_time % period)
        
        if SIGNAL_WINDOW_START <= seconds_into_candle <= SIGNAL_WINDOW_END:
            return
        
        if seconds_into_candle < SIGNAL_WINDOW_START:
            wait_time = SIGNAL_WINDOW_START - seconds_into_candle
            await asyncio.sleep(wait_time)
        else:
            wait_time = period - seconds_into_candle + SIGNAL_WINDOW_START
            await asyncio.sleep(wait_time)


async def is_in_signal_window(period: int = 60) -> bool:
    current_time = time_module.time()
    seconds_into_candle = int(current_time % period)
    return SIGNAL_WINDOW_START <= seconds_into_candle <= SIGNAL_WINDOW_END


async def get_running_candle_analysis(asset: str, period: int = 60):
    try:
        c = await get_client()
        asset_name, asset_data = await c.get_available_asset(asset, force_open=True)
        
        if not asset_data or not asset_data[2]:
            return None
        
        candles = await c.get_candle(asset_name, period, 50)
        if not candles or len(candles) < 2:
            return None
        
        running_candle = candles[-1]
        prev_candle = candles[-2]
        
        o, h, l, c = running_candle['open'], running_candle['high'], running_candle['low'], running_candle['close']
        body = abs(c - o)
        total_range = h - l
        midpoint = (h + l) / 2
        
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        
        is_bullish = c > o
        is_bearish = c < o
        
        body_strength = body / total_range if total_range > 0 else 0
        
        call_confirmed = (
            is_bullish and
            c > midpoint and
            upper_wick < body * 1.5 and
            body_strength > 0.4
        )
        
        put_confirmed = (
            is_bearish and
            c < midpoint and
            lower_wick < body * 1.5 and
            body_strength > 0.4
        )
        
        is_indecision = upper_wick > body and lower_wick > body
        
        prev_range = prev_candle['high'] - prev_candle['low']
        has_momentum = total_range >= prev_range * 0.5
        
        return {
            "asset": asset_name,
            "running_candle": running_candle,
            "is_bullish": is_bullish,
            "is_bearish": is_bearish,
            "call_confirmed": call_confirmed,
            "put_confirmed": put_confirmed,
            "is_indecision": is_indecision,
            "has_momentum": has_momentum,
            "body_strength": body_strength,
            "seconds_into_candle": int(time_module.time() % period)
        }
        
    except Exception as e:
        return None


@app.get("/analyze/{asset}")
async def analyze_running_candle(asset: str, timeframe: str = "M1"):
    try:
        period = TIMEFRAMES.get(timeframe.upper(), 60)
        in_window = await is_in_signal_window(period)
        
        if not in_window:
            return {
                "status": "waiting",
                "message": "Not in signal window (50-55 seconds)",
                "seconds_into_candle": int(time_module.time() % period)
            }
        
        analysis = await get_running_candle_analysis(asset, period)
        
        if not analysis:
            return JSONResponse({"error": "Analysis failed"}, status_code=500)
        
        return {
            "status": "ready",
            "analysis": analysis,
            "signal_window": f"{SIGNAL_WINDOW_START}-{SIGNAL_WINDOW_END}s"
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/")
async def root():
    return {"status": "PyQuotex Live API", "version": "1.0", "endpoints": {
        "stream": "/stream/{asset}?timeframe=M1",
        "candle": "/candle/{asset}?timeframe=M1",
        "analyze": "/analyze/{asset}?timeframe=M1"
    }}


@app.get("/stream/{asset}")
async def stream_candle(asset: str, timeframe: str = "M1"):
    period = TIMEFRAMES.get(timeframe.upper(), 60)
    
    async def generate():
        try:
            c = await get_client()
            asset_name, asset_data = await c.get_available_asset(asset, force_open=True)
            
            if not asset_data or not asset_data[2]:
                yield f"data: {json.dumps({'error': f'Asset {asset} is closed'})}\n\n"
                return
            
            await c.start_realtime_price(asset_name, period)
            
            while True:
                candle_price_data = await c.get_realtime_price(asset_name)
                
                if candle_price_data:
                    latest_data = candle_price_data[-1]
                    timestamp = latest_data['time']
                    price = latest_data['price']
                    bd_time = datetime.fromtimestamp(timestamp, tz=BD_TZ)
                    formatted_time = bd_time.strftime('%H:%M:%S')
                    
                    data = {
                        "asset": asset_name,
                        "timeframe": timeframe.upper(),
                        "timestamp": timestamp,
                        "time": formatted_time,
                        "time_bd": bd_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                        "price": price
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                
                await asyncio.sleep(0.5)
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/candle/{asset}")
async def get_live_candle(asset: str, timeframe: str = "M1", wait_near_close: bool = False):
    try:
        period = TIMEFRAMES.get(timeframe.upper(), 60)
        
        c = await get_client()
        asset_name, asset_data = await c.get_available_asset(asset, force_open=True)
        
        if not asset_data or not asset_data[2]:
            return JSONResponse({"error": f"Asset {asset} is closed"}, status_code=400)
        
        await c.start_realtime_price(asset_name, period)
        
        if wait_near_close:
            await wait_for_signal_window(period)
        
        candle_price_data = await c.get_realtime_price(asset_name)
        
        if candle_price_data:
            latest_data = candle_price_data[-1]
            timestamp = latest_data['time']
            price = latest_data['price']
            bd_time = datetime.fromtimestamp(timestamp, tz=BD_TZ)
            formatted_time = bd_time.strftime('%H:%M:%S')
            
            current_time = time_module.time()
            seconds_into_candle = int(current_time % period)
            
            return {
                "asset": asset_name,
                "timeframe": timeframe.upper(),
                "timestamp": timestamp,
                "time": formatted_time,
                "time_bd": bd_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "price": price,
                "seconds_into_candle": seconds_into_candle,
                "is_near_close": seconds_into_candle >= SIGNAL_WINDOW_START
            }
        
        return JSONResponse({"error": "No data available"}, status_code=404)
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.websocket("/ws/{asset}")
async def websocket_stream(websocket: WebSocket, asset: str, timeframe: str = "M1"):
    await websocket.accept()
    
    try:
        period = TIMEFRAMES.get(timeframe.upper(), 60)
        
        c = await get_client()
        asset_name, asset_data = await c.get_available_asset(asset, force_open=True)
        
        if not asset_data or not asset_data[2]:
            await websocket.send_json({"error": f"Asset {asset} is closed"})
            await websocket.close()
            return
        
        await c.start_realtime_price(asset_name, period)
        
        while True:
            candle_price_data = await c.get_realtime_price(asset_name)
            
            if candle_price_data:
                latest_data = candle_price_data[-1]
                timestamp = latest_data['time']
                price = latest_data['price']
                bd_time = datetime.fromtimestamp(timestamp, tz=BD_TZ)
                formatted_time = bd_time.strftime('%H:%M:%S')
                
                await websocket.send_json({
                    "asset": asset_name,
                    "timeframe": timeframe.upper(),
                    "timestamp": timestamp,
                    "time": formatted_time,
                    "time_bd": bd_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "price": price
                })
            
            await asyncio.sleep(0.1)
            
    except:
        pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
