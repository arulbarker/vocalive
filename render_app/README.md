# StreamMate AI - iPaymu Callback Handler

## 🚀 Render Deployment

### Quick Setup

1. **Sign Up Render**
   - Buka: https://render.com
   - Sign up dengan GitHub

2. **Create Web Service**
   - Click "New +" > "Web Service"
   - Connect GitHub repository
   - Root Directory: `render_app`

3. **Configure Service**
   ```
   Name: streammate-callback
   Environment: Node
   Build Command: npm install
   Start Command: npm start
   ```

4. **Set Environment Variables**
   ```
   SUPABASE_URL=https://nivwxqojwljihoybzgkc.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait 2-3 minutes for deployment
   - Get URL: `https://your-app.onrender.com`

### Update iPaymu Dashboard

1. **Login iPaymu Dashboard**
2. **Go to Settings > Callback**
3. **Set URLs:**
   ```
   Callback URL: https://your-app.onrender.com/ipaymu-callback
   Return URL: https://your-app.onrender.com/payment-completed
   ```

### Test Callback

```bash
curl -X POST https://your-app.onrender.com/ipaymu-callback \
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

- **750 hours/month free**
- **Auto-deploy from GitHub**
- **Custom domains**
- **SSL certificates**
- **No credit card required** 