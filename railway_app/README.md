# StreamMate AI - iPaymu Callback Handler

## 🚀 Railway Deployment

### Setup Railway

1. **Sign Up Railway**
   - Buka: https://railway.app
   - Sign up dengan GitHub

2. **Create New Project**
   - Click "New Project"
   - Pilih "Deploy from GitHub repo"

3. **Connect Repository**
   - Pilih repository Anda
   - Railway akan auto-deploy

4. **Set Environment Variables**
   Di Railway dashboard, set:
   ```
   SUPABASE_URL=https://nivwxqojwljihoybzgkc.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

5. **Get URL**
   Railway akan kasih URL seperti:
   ```
   https://streammate-callback-production.up.railway.app
   ```

### Update iPaymu Dashboard

1. **Login ke iPaymu Dashboard**
2. **Go to Settings > Callback**
3. **Set Callback URL:**
   ```
   https://your-railway-url.railway.app/ipaymu-callback
   ```
4. **Set Return URL:**
   ```
   https://your-railway-url.railway.app/payment-completed
   ```

### Test Callback

```bash
# Test dengan curl
curl -X POST https://your-railway-url.railway.app/ipaymu-callback \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "trx_id=TEST123&reference_id=test@example.com_1234567890&status=berhasil&status_code=1&amount=50000&paid_off=50000"
```

### Features

- ✅ **No Authentication Required**
- ✅ **Handles iPaymu Callbacks**
- ✅ **Updates User Credits**
- ✅ **Idempotency Protection**
- ✅ **Payment Success Page**
- ✅ **Error Handling**

### Free Tier

- **500 hours/month free**
- **Auto-deploy from GitHub**
- **Custom domains**
- **SSL certificates**

## 🎯 Why Railway?

1. **No Auth Issues** - Tidak ada masalah authentication seperti Vercel
2. **Simple Setup** - Setup sangat mudah
3. **Free Tier** - 500 jam gratis cukup untuk callback
4. **Reliable** - Performance bagus dan stabil
5. **Auto-deploy** - Update otomatis dari GitHub 