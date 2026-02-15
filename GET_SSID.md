# How to Get Your SSID Token

## Method 1: From Browser DevTools

1. Login to Quotex at https://qxbroker.com
2. Press F12 to open DevTools
3. Go to **Network** tab
4. Filter by **WS** (WebSocket)
5. Click on the WebSocket connection
6. Go to **Messages** tab
7. Look for a message like: `42["authorization",{"session":"YOUR_SSID_HERE",...}]`
8. Copy the SSID value

## Method 2: From Python PyQuotex

Run this Python script:

```python
from pyquotex.stable_api import Quotex
import asyncio

async def get_ssid():
    client = Quotex(email="your_email", password="your_password")
    await client.connect()
    print(f"SSID: {client.session_data.get('token')}")
    await client.close()

asyncio.run(get_ssid())
```

## Method 3: From Browser Console

1. Login to Quotex
2. Press F12 → Console
3. Paste this code:

```javascript
// Check localStorage
console.log('Token:', localStorage.getItem('token'));

// Or check all storage
for(let i=0; i<localStorage.length; i++) {
    let key = localStorage.key(i);
    console.log(key, ':', localStorage.getItem(key));
}
```

## Then Update test.js

Replace `YOUR_SSID_HERE` with your actual SSID token.
