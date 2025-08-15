# 🚀 VERCEL DEPLOYMENT GUIDE - IPAYMU CALLBACK

## **📋 PREREQUISITES**

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

## **🗂️ PROJECT STRUCTURE**

```
vercel-api-routes/
├── api/
│   ├── ipaymu-callback.js
│   └── payment-completed.js
├── package.json
└── vercel.json
```

## **📦 SETUP PROJECT**

### 1. Create package.json
```json
{
  "name": "streammate-ipaymu-callback",
  "version": "1.0.0",
  "description": "iPaymu callback handler for StreamMate AI",
  "main": "index.js",
  "scripts": {
    "dev": "vercel dev",
    "deploy": "vercel --prod"
  },
  "dependencies": {
    "@supabase/supabase-js": "^2.38.0"
  },
  "devDependencies": {
    "vercel": "^32.0.0"
  }
}
```

### 2. Create vercel.json
```json
{
  "functions": {
    "api/ipaymu-callback.js": {
      "maxDuration": 30
    },
    "api/payment-completed.js": {
      "maxDuration": 30
    }
  },
  "env": {
    "SUPABASE_URL": "https://nivwxqojwljihoybzgkc.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "your_service_role_key_here"
  }
}
```

## **🔧 DEPLOYMENT STEPS**

### Step 1: Initialize Project
```bash
# Create project directory
mkdir vercel-ipaymu-callback
cd vercel-ipaymu-callback

# Initialize npm
npm init -y

# Install dependencies
npm install @supabase/supabase-js
npm install -D vercel
```

### Step 2: Create API Routes
1. Buat folder `api/`
2. Copy file `ipaymu-callback.js` dan `payment-completed.js` ke folder `api/`

### Step 3: Set Environment Variables
```bash
# Set environment variables
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_ROLE_KEY
```

### Step 4: Deploy to Vercel
```bash
# Deploy to production
vercel --prod
```

## **🔗 UPDATE IPAYMU CONFIGURATION**

### Callback URLs:
- **Callback URL:** `https://your-app.vercel.app/api/ipaymu-callback`
- **Return URL:** `https://your-app.vercel.app/api/payment-completed`

## **🧪 TESTING**

### 1. Test Callback Function
```bash
curl -X POST https://your-app.vercel.app/api/ipaymu-callback \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "trx_id=12345&status=berhasil&status_code=1&reference_id=test@email.com_1234567890&paid_off=50000"
```

### 2. Test Payment Completed Page
```bash
curl https://your-app.vercel.app/api/payment-completed?order_id=test@email.com_1234567890
```

## **📊 MONITORING**

### 1. Vercel Dashboard
- Buka: https://vercel.com/dashboard
- Pilih project Anda
- Monitor function logs dan performance

### 2. Function Logs
```bash
# View function logs
vercel logs your-app.vercel.app
```

## **✅ ADVANTAGES OF VERCEL**

1. **✅ No Authorization Issues** - Tidak ada requirement authorization header
2. **✅ Global CDN** - Performance optimal worldwide
3. **✅ Automatic Scaling** - Handle traffic spikes
4. **✅ Easy Deployment** - Git integration
5. **✅ Free Tier** - Generous limits
6. **✅ Real-time Logs** - Easy debugging

## **🔧 TROUBLESHOOTING**

### Common Issues:

1. **Environment Variables Not Set**
   - Solution: Set via Vercel dashboard or CLI
   - Check: `vercel env ls`

2. **Function Timeout**
   - Solution: Increase maxDuration in vercel.json
   - Default: 10 seconds

3. **CORS Issues**
   - Solution: Check CORS headers in function
   - Test with OPTIONS request

4. **Database Connection Error**
   - Solution: Verify Supabase credentials
   - Check: Environment variables

## **📈 PERFORMANCE OPTIMIZATION**

### 1. Cold Start Reduction
```javascript
// Use connection pooling
const supabase = createClient(url, key, {
  auth: { autoRefreshToken: false, persistSession: false }
})
```

### 2. Error Handling
```javascript
// Always return 200 to iPaymu
try {
  // Process payment
} catch (error) {
  console.error('Error:', error)
  return res.status(200).send('OK') // Important!
}
```

## **🎯 NEXT STEPS**

1. **Deploy to Vercel** - Follow deployment steps
2. **Update iPaymu URLs** - Set callback URLs
3. **Test with real payment** - Verify end-to-end flow
4. **Monitor logs** - Check for any issues
5. **Scale if needed** - Upgrade plan if required

## **📞 SUPPORT**

- **Vercel Docs:** https://vercel.com/docs
- **Supabase Docs:** https://supabase.com/docs
- **iPaymu Docs:** https://ipaymu.com/docs 