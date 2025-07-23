# 🔧 SOLUSI LENGKAP MASALAH AUTHORIZATION EDGE FUNCTIONS

## **🎯 ROOT CAUSE ANALYSIS**

### **Masalah Utama:**
```
Error: 401 "Missing authorization header"
```

### **Mengapa Terjadi:**
1. **Supabase Edge Functions** secara default memerlukan authorization header
2. **iPaymu** sebagai external service tidak bisa mengirim custom header
3. **Architecture mismatch** antara external dan internal security model

## **🚀 SOLUSI IMPLEMENTASI**

### **1. Edge Function dengan Service Role Key**

```typescript
// supabase/functions/ipaymu-callback/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse form data dari iPaymu
    const formData = await req.formData()
    const body = Object.fromEntries(formData.entries())
    
    // Validasi payment status
    if (body.status !== 'berhasil' || body.status_code !== '1') {
      return new Response('OK', { status: 200, headers: corsHeaders })
    }

    // Gunakan service role key untuk bypass authorization
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Process payment dan update credits
    // ... rest of implementation

    return new Response('OK', { status: 200, headers: corsHeaders })
  } catch (error) {
    console.error('Error:', error)
    return new Response('Error', { status: 500, headers: corsHeaders })
  }
})
```

### **2. Database Schema**

```sql
-- Table payments
CREATE TABLE IF NOT EXISTS payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id TEXT UNIQUE NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  amount DECIMAL(10,2) NOT NULL,
  status TEXT DEFAULT 'pending',
  transaction_id TEXT,
  payment_method TEXT,
  paid_amount DECIMAL(10,2),
  credits_amount INTEGER DEFAULT 0,
  paid_at TIMESTAMP,
  processed_at TIMESTAMP,
  callback_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Function untuk update credits
CREATE OR REPLACE FUNCTION add_user_credits(user_id UUID, credits_to_add INTEGER)
RETURNS VOID AS $$
BEGIN
  UPDATE user_profiles 
  SET credits = COALESCE(credits, 0) + credits_to_add
  WHERE id = user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- RLS Policy untuk service role
CREATE POLICY "Service role can manage payments" ON payments
  FOR ALL USING (auth.role() = 'service_role');
```

### **3. Environment Variables**

```bash
# Set environment variables
supabase secrets set SUPABASE_URL=https://nivwxqojwljihoybzgkc.supabase.co
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

## **🔧 DEPLOYMENT STEPS**

### **Step 1: Deploy Edge Function**
```bash
# Deploy function
supabase functions deploy ipaymu-callback

# Set environment variables
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_key_here
```

### **Step 2: Apply Database Schema**
```bash
# Apply schema
supabase db push
```

### **Step 3: Update iPaymu Callback URL**
```
https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-callback
```

## **🧪 TESTING**

### **Test Script:**
```python
import requests

# Test successful payment
payment_data = {
    "trx_id": "172797",
    "status": "berhasil",
    "status_code": "1",
    "reference_id": "test@email.com_1234567890",
    "paid_off": "50000"
}

response = requests.post(
    "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-callback",
    data=payment_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

## **🔍 TROUBLESHOOTING**

### **Common Issues:**

1. **401 Authorization Error**
   - ✅ **Solution:** Gunakan service role key
   - ✅ **Check:** Environment variables set correctly

2. **Database Connection Error**
   - ✅ **Solution:** Verify SUPABASE_URL and service role key
   - ✅ **Check:** Database schema applied

3. **CORS Error**
   - ✅ **Solution:** Function includes proper CORS headers
   - ✅ **Check:** OPTIONS request handled

4. **Payment Not Processed**
   - ✅ **Check:** Payment status is 'berhasil' and status_code is '1'
   - ✅ **Check:** User exists in database
   - ✅ **Check:** Function logs for errors

## **📊 MONITORING**

### **Check Function Logs:**
```bash
supabase functions logs ipaymu-callback --follow
```

### **Monitor Database:**
```sql
-- Check recent payments
SELECT * FROM payments ORDER BY created_at DESC LIMIT 10;

-- Check user credits
SELECT email, credits FROM user_profiles WHERE credits > 0;
```

## **✅ VERIFICATION CHECKLIST**

- [ ] Edge function deployed successfully
- [ ] Environment variables set correctly
- [ ] Database schema applied
- [ ] CORS headers working
- [ ] Payment processing works
- [ ] Credits added to user account
- [ ] Idempotency prevents double processing
- [ ] Error handling works properly

## **🚀 ALTERNATIVE SOLUTIONS**

Jika masih ada masalah dengan Edge Functions:

1. **Cloudflare Workers** - External service yang tidak require auth
2. **Vercel API Routes** - Similar to Edge Functions but different auth model
3. **Local Webhook Server** - Flask/FastAPI server untuk handle callback
4. **Netlify Functions** - Serverless dengan auth yang lebih flexible

**RECOMMENDATION:** Gunakan Edge Function dengan service role key - ini adalah solusi yang paling clean dan terintegrasi dengan Supabase. 