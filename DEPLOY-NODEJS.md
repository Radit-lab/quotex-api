# 🚀 Deploy to Node.js Hosting

## 📁 Files to Upload:

1. **server-api.js** ✅
2. **package.json** ✅

That's it! Only 2 files needed.

---

## 📋 Step-by-Step Deployment:

### 1. Upload Files via FTP/cPanel:
```
/your-domain/
├── server-api.js
└── package.json
```

### 2. SSH into your hosting:
```bash
ssh username@your-domain.com
cd /path/to/your/app
```

### 3. Install dependencies:
```bash
npm install
```

### 4. Start the server:
```bash
node server-api.js
```

Or run in background:
```bash
nohup node server-api.js > output.log 2>&1 &
```

### 5. Check if running:
```bash
ps aux | grep node
```

---

## 🌐 Access Your API:

```
http://your-domain.com:3000/candles/USDBDT_otc?count=199&period=60
```

Or if port 3000 is blocked, use port 80/443:

Edit `server-api.js` line 5:
```javascript
const PORT = process.env.PORT || 80;
```

---

## 🔄 Update SSID:

```
http://your-domain.com:3000/update-ssid/YOUR_NEW_SSID
```

---

## 📊 Example Response:

```json
{
  "success": true,
  "asset": "USDBDT_otc",
  "count": 199,
  "period": 60,
  "candles": [
    {
      "index": 1,
      "time": 1771104420,
      "date": "2026-02-15T03:27:00.000Z",
      "open": 124.962,
      "close": 124.967,
      "high": 124.967,
      "low": 124.961,
      "color": "GREEN"
    }
  ]
}
```

---

## ✅ Test Commands:

```bash
# Test locally first
node server-api.js

# Then test API
curl http://localhost:3000/
curl http://localhost:3000/candles/USDBDT_otc?count=10
```

---

## 🔧 Troubleshooting:

**Port already in use:**
```bash
killall node
```

**Permission denied:**
```bash
chmod +x server-api.js
```

**Module not found:**
```bash
npm install express ws
```

---

Ready to deploy! 🚀
