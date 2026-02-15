# 🚀 Deploy to Render.com (Free Node.js Hosting)

## Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `quotex-api`
3. Public
4. Create repository

## Step 2: Upload Your Code
```bash
cd c:\Users\User\Documents\pyquotex
git init
git add server-api.js package.json
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/quotex-api.git
git push -u origin main
```

## Step 3: Deploy on Render
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your `quotex-api` repository
5. Settings:
   - Name: `quotex-api`
   - Environment: `Node`
   - Build Command: `npm install`
   - Start Command: `node server-api.js`
6. Click "Create Web Service"

## Step 4: Get Your API URL
After deployment, you'll get:
```
https://quotex-api.onrender.com
```

## Step 5: Use Your API
```
https://quotex-api.onrender.com/candles/USDBDT_otc?count=199&period=60
```

## Update SSID:
```
https://quotex-api.onrender.com/update-ssid/YOUR_NEW_SSID
```

---

## Alternative: Railway.app
1. Go to https://railway.app
2. Login with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select `quotex-api`
5. Done! Get your URL

---

## Then use from radit.top:
Create a PHP proxy on radit.top:

```php
<?php
$url = "https://quotex-api.onrender.com" . $_SERVER['REQUEST_URI'];
$data = file_get_contents($url);
header('Content-Type: application/json');
echo $data;
?>
```

Save as `api.php` on radit.top, then access:
```
https://radit.top/api.php/candles/USDBDT_otc?count=199
```
