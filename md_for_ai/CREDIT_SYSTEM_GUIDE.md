# StreamMate AI - Credit System Guide

## 🔄 Sistem Kredit Baru (Updated)

Kami telah memisahkan sistem pembelian menjadi **dua tahap terpisah** untuk memberikan kontrol yang lebih baik kepada pengguna:

---

## 📋 Alur Pembelian Baru

### 1️⃣ **Top-up Kredit** (Credit Wallet Tab)
**Tujuan**: Membeli kredit dengan uang asli

- Buka tab **💰 Credit Wallet**
- Pilih paket top-up yang sesuai:
  - **💎 Starter Pack**: Rp 50,000 → 120,000 kredit
  - **🚀 Regular Pack**: Rp 100,000 → 300,000 kredit ⭐ POPULAR
  - **⭐ Premium Pack**: Rp 200,000 → 750,000 kredit  
  - **🏆 Enterprise Pack**: Rp 500,000 → 2,000,000 kredit
- Klik **💳 Top-up Credits**
- Bayar dengan uang asli (Rupiah)

### 2️⃣ **Beli Paket Fitur** (Subscription Tab)
**Tujuan**: Menggunakan kredit untuk membeli akses fitur

- Buka tab **📦 Subscription**
- Pilih paket yang diinginkan:
  - **🚀 Basic Package**: 100,000 kredit
  - **🛍️ CoHost Seller**: 300,000 kredit
- Klik **💳 Buy with Credits**
- Kredit akan terpotong, fitur langsung aktif

---

## 🔐 Sistem Keamanan

### ✅ Fitur HANYA Aktif Setelah Dibeli
- **Basic features** (Cohost, Overlay, dll) → Hanya aktif setelah beli Basic Package
- **CoHost Seller features** → Hanya aktif setelah beli CoHost Seller Package
- **Memiliki kredit saja TIDAK mengaktifkan fitur**

### 🛡️ Perlindungan Kredit
- Kredit tidak terpotong saat top-up
- Kredit hanya terpotong saat beli paket fitur
- Sistem validasi mencegah duplikasi pembelian

---

## 📊 Status & Validasi

### Check Status Pembelian:
```python
python test_credit_wallet.py
```

### File Konfigurasi:
- `config/subscription_status.json` → Status paket yang dibeli
- Credit wallet database → Saldo kredit

---

## 🎯 Keuntungan Sistem Baru

1. **Kontrol Penuh**: User dapat top-up dulu, beli paket belakangan
2. **Fleksibilitas**: Kredit bisa digunakan untuk berbagai paket
3. **Keamanan**: Fitur tidak aktif tanpa pembelian yang valid
4. **Transparansi**: Jelas mana yang top-up, mana yang beli fitur

---

## 🚀 Contoh Skenario

### Skenario 1: User Baru
1. Top-up **Regular Pack** (Rp 100,000 → 300,000 kredit)
2. Beli **Basic Package** (300,000 - 100,000 = 200,000 sisa)
3. Nanti bisa beli **CoHost Seller** (butuh 100,000 kredit lagi)

### Skenario 2: User Existing
1. Sudah punya 140,000 kredit
2. Cukup untuk **Basic Package** ✅
3. Perlu top-up lagi untuk **CoHost Seller** ❌

---

## 🔧 Developer Notes

### UI Changes:
- **Credit Wallet Tab**: Label "Top-up Credits" bukan "Purchase Package"
- **Subscription Tab**: Label "Buy with Credits" + harga dalam kredit
- **Main Window**: Features locked sampai package dibeli

### Backend Changes:
- Paket validation di `main_window.py`
- Credit deduction di subscription purchase
- Package status tracking di `subscription_status.json`

---

## ❓ FAQ

**Q: Apakah kredit yang sudah dibeli hilang?**  
A: Tidak, kredit tetap ada dan bisa digunakan untuk beli paket.

**Q: Bisa refund kredit tidak?**  
A: Kredit tidak bisa di-refund, tapi bisa digunakan untuk paket lain.

**Q: Fitur Basic tidak muncul padahal sudah ada kredit?**  
A: Kredit saja tidak cukup, harus beli Basic Package dulu.

**Q: CoHost Seller butuh Basic Package juga?**  
A: Tidak, CoHost Seller sudah include semua fitur Basic.

---

**✅ Sistem ini memastikan user mendapat value yang jelas untuk setiap pembelian!** 