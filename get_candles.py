import asyncio
import sys
import json
from pyquotex.stable_api import Quotex

async def get_candles(email, password, asset, count, period):
    client = Quotex(email=email, password=password, lang="en")
    await client.connect()
    candles = await client.get_candle(asset, period, count)
    await client.close()
    return candles

if __name__ == "__main__":
    email = sys.argv[1]
    password = sys.argv[2]
    asset = sys.argv[3]
    count = int(sys.argv[4])
    period = int(sys.argv[5])
    
    result = asyncio.run(get_candles(email, password, asset, count, period))
    print(json.dumps(result))
