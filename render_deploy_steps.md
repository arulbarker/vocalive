# 🚀 Render Deployment Steps

## Setelah Set Environment Variables

### Step 1: Redeploy Service
1. Di Render dashboard, pilih service `streammate-callback`
2. Click "Manual Deploy"
3. Pilih "Deploy latest commit"
4. Tunggu deployment selesai (2-3 menit)

### Step 2: Get URL
Setelah deploy selesai, dapat URL seperti:
```
https://streammate-callback.onrender.com
```

### Step 3: Test Callback
```bash
curl -X POST https://streammate-callback.onrender.com/ipaymu-callback \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "trx_id=TEST123&reference_id=test@example.com_1234567890&status=berhasil&status_code=1&amount=50000&paid_off=50000"
```

### Step 4: Update iPaymu Dashboard
1. Login ke iPaymu Dashboard
2. Go to Settings > Callback
3. Set Callback URL: `https://streammate-callback.onrender.com/ipaymu-callback`
4. Set Return URL: `https://streammate-callback.onrender.com/payment-completed`

### Step 5: Test Payment Flow
1. Buat payment baru di aplikasi
2. Lakukan pembayaran di iPaymu
3. Verifikasi callback diterima
4. Cek credits bertambah di database

## Troubleshooting

### Jika Deployment Gagal:
1. Check logs di Render dashboard
2. Pastikan environment variables benar
3. Pastikan service role key valid

### Jika Callback Tidak Berfungsi:
1. Test dengan curl command
2. Check logs di Render dashboard
3. Verifikasi URL di iPaymu dashboard 