import asyncio
import sys
import json
from pyquotex.stable_api import Quotex

async def main():
    email = sys.argv[1] if len(sys.argv) > 1 else "radithasan90@gmail.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "radit01923006192"
    asset = sys.argv[3] if len(sys.argv) > 3 else "EURUSD_otc"
    period = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    count = int(sys.argv[5]) if len(sys.argv) > 5 else 100
    
    client = Quotex(email=email, password=password, lang="en")
    await client.connect()
    candles = await client.get_candle(asset, period, count)
    await client.close()
    
    print(json.dumps(candles))

if __name__ == "__main__":
    asyncio.run(main())
