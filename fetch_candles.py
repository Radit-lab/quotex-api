import asyncio
import sys
import json
from pyquotex.stable_api import Quotex

async def get_candles():
    email = sys.argv[1]
    password = sys.argv[2]
    asset = sys.argv[3]
    period = int(sys.argv[4])
    count = int(sys.argv[5])
    
    client = Quotex(email=email, password=password, lang="en")
    await client.connect()
    candles = await client.get_candle(asset, period, count)
    await client.close()
    
    print(json.dumps(candles, indent=2))

asyncio.run(get_candles())
