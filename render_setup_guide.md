# 🚀 Render Setup Guide - StreamMate AI Callback

## Step 1: Sign Up Render
1. Buka: https://render.com
2. Click "Get Started"
3. Sign up dengan GitHub account
4. Authorize Render untuk akses GitHub

## Step 2: Create New Web Service
1. Di Render dashboard, click "New +"
2. Pilih "Web Service"
3. Connect GitHub repository
4. Pilih repository yang berisi `render_app/`

## Step 3: Configure Service
```
Name: streammate-callback
Environment: Node
Root Directory: render_app
Build Command: npm install
Start Command: npm start
```

## Step 4: Set Environment Variables
Di bagian "Environment Variables", tambahkan:
```
SUPABASE_URL=https://nivwxqojwljihoybzgkc.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Step 5: Deploy
1. Click "Create Web Service"
2. Render akan auto-deploy
3. Tunggu deployment selesai (2-3 menit)
4. Dapat URL seperti: `https://streammate-callback.onrender.com`

## Step 6: Update iPaymu Dashboard
1. Login ke iPaymu Dashboard
2. Go to Settings > Callback
3. Set Callback URL: `https://your-app.onrender.com/ipaymu-callback`
4. Set Return URL: `https://your-app.onrender.com/payment-completed`

## Step 7: Test Callback
```bash
curl -X POST https://your-app.onrender.com/ipaymu-callback \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "trx_id=TEST123&reference_id=test@example.com_1234567890&status=berhasil&status_code=1&amount=50000&paid_off=50000"
```

## Features
- ✅ No authentication required
- ✅ Handles iPaymu callbacks
- ✅ Updates user credits
- ✅ Idempotency protection
- ✅ Payment success page
- ✅ Error handling

## Free Tier
- **750 hours/month free**
- **Auto-deploy from GitHub**
- **Custom domains**
- **SSL certificates**
- **No credit card required** 