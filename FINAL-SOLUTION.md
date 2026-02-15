# 🎯 Quotex Candles - JavaScript Solution

## ✅ Working Solution (Local Computer)

### Run this command:
```bash
cd C:\Users\User\Documents\pyquotex
node quotex-api.js
```

### Output:
```
🔄 Connecting...
✅ Connected!
✅ Authenticated!
📊 Requesting last 199 candles for USDBDT_otc...

🎯 Got 199 candles for USDBDT_otc

1. USDBDT_otc 2/15/2026, 3:27:00 AM | O:124.962 H:124.967 L:124.961 C:124.967 | 🟢 GREEN
2. USDBDT_otc 2/15/2026, 3:28:00 AM | O:124.967 H:124.972 L:124.948 C:124.968 | 🟢 GREEN
...
```

### Data also saved to:
```
usdbdt_candles.json
```

---

## 📝 Change Asset/Count/Period:

Edit `quotex-api.js` line 82:
```javascript
asset: 'EURUSD_otc',  // Change asset
period: 60,            // Change period (60=1min, 300=5min)
start: Math.floor(Date.now() / 1000) - (50 * 60),  // Change count (50 candles)
```

---

## 🔄 Update SSID (when expired):

1. Login to Quotex in browser
2. F12 → Network → WS → Messages
3. Find: `42["authorization",{"session":"NEW_SSID"...}]`
4. Copy NEW_SSID
5. Edit `quotex-api.js` line 6:
```javascript
const SSID = 'YOUR_NEW_SSID_HERE';
```

---

## 🚀 Deploy to Free Hosting (Optional):

### Option 1: Render.com
1. Create GitHub repo
2. Push code
3. Deploy on Render.com
4. Get URL: `https://your-app.onrender.com/candles/USDBDT_otc?count=199`

### Option 2: Keep Running Locally
Just run `node quotex-api.js` whenever you need data!

---

## 📊 All Files:

- `quotex-api.js` - Main working script ✅
- `server-api.js` - HTTP API version (needs deployment)
- `quotex-browser.html` - Browser version (doesn't work due to SSID restrictions)
- `package.json` - Dependencies

---

## ✅ Summary:

**What Works:**
- ✅ `node quotex-api.js` on your computer
- ✅ Gets 199 candles with colors
- ✅ Saves to JSON file
- ✅ Works with any asset

**What Doesn't Work:**
- ❌ Browser version (SSID blocked)
- ❌ Shared hosting without Node.js

**Best Solution:**
Run locally or deploy to free Node.js hosting (Render/Railway/Vercel)
