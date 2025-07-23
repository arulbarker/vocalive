# 🔑 Get Supabase Service Role Key

## Step 1: Login Supabase Dashboard
1. Buka: https://supabase.com
2. Login dengan akun Anda
3. Pilih project: `nivwxqojwljihoybzgkc`

## Step 2: Get Service Role Key
1. Di sidebar kiri, click "Settings"
2. Click "API"
3. Scroll ke bawah ke "Project API keys"
4. Copy "service_role" key (yang panjang)

## Step 3: Set di Render
1. Di Render dashboard
2. Pilih service `streammate-callback`
3. Click "Environment"
4. Add variable:
   ```
   Key: SUPABASE_SERVICE_ROLE_KEY
   Value: [paste service role key]
   ```

## Step 4: Redeploy
1. Click "Manual Deploy"
2. Pilih "Deploy latest commit"
3. Tunggu deployment selesai

## Step 5: Get URL
Setelah deploy selesai, dapat URL seperti:
```
https://streammate-callback.onrender.com
```

## Step 6: Update iPaymu
1. Login iPaymu Dashboard
2. Go to Settings > Callback
3. Set:
   ```
   Callback URL: https://streammate-callback.onrender.com/ipaymu-callback
   Return URL: https://streammate-callback.onrender.com/payment-completed
   ``` 