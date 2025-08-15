🔐 STREAMMATE AI - SECURE CREDENTIALS SETUP
============================================================

Untuk mengamankan kredensial API Anda di Supabase, ikuti langkah-langkah berikut:

## LANGKAH 1: SETUP TABEL DI SUPABASE DASHBOARD

1. Buka Supabase Dashboard: https://supabase.com/dashboard
2. Login dan pilih project: nivwxqojwljihoybzgkc
3. Klik "SQL Editor" di sidebar kiri
4. Klik "New Query" 
5. Copy dan paste SQL berikut:

```sql
-- Create secure_credentials table
CREATE TABLE IF NOT EXISTS secure_credentials (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    encrypted_value TEXT NOT NULL,
    credential_type VARCHAR(100) DEFAULT 'api_key',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_secure_credentials_key ON secure_credentials(key);
CREATE INDEX IF NOT EXISTS idx_secure_credentials_type ON secure_credentials(credential_type);
CREATE INDEX IF NOT EXISTS idx_secure_credentials_active ON secure_credentials(is_active);

-- Enable Row Level Security
ALTER TABLE secure_credentials ENABLE ROW LEVEL SECURITY;

-- Create policy for service role access
CREATE POLICY IF NOT EXISTS "service_role_all_access" ON secure_credentials
FOR ALL USING (auth.role() = 'service_role');

-- Create policy for authenticated users (optional)
CREATE POLICY IF NOT EXISTS "authenticated_read_own" ON secure_credentials
FOR SELECT USING (auth.uid() = created_by);
```

6. Klik "Run" untuk mengeksekusi SQL
7. Pastikan tidak ada error dan tabel berhasil dibuat

## LANGKAH 2: VERIFIKASI SETUP

Setelah SQL berhasil dijalankan, jalankan command berikut untuk verifikasi:

```bash
python test_supabase_simple.py
```

## LANGKAH 3: MIGRASI KREDENSIAL

Jika verifikasi berhasil, jalankan script migrasi:

```bash
python migrate_credentials_to_supabase.py
```

## KEUNTUNGAN SISTEM INI:

✅ **Keamanan Tingkat Enterprise**: Kredensial dienkripsi dengan AES-256
✅ **Row Level Security**: Akses terbatas hanya untuk service role
✅ **Audit Trail**: Semua akses tercatat dengan timestamp
✅ **Backup Otomatis**: Supabase menyediakan backup otomatis
✅ **Akses Global**: Kredensial dapat diakses dari mana saja
✅ **Sinkronisasi Real-time**: Update langsung tersinkronisasi

## KREDENSIAL YANG AKAN DIAMANKAN:

- Google OAuth Client ID & Secret
- Google Cloud TTS API Key
- Supabase Keys
- Payment Gateway Keys (iPay88, dll)
- Database Connection Strings
- Third-party API Keys

## TROUBLESHOOTING:

Jika ada masalah:
1. Pastikan Supabase project aktif
2. Cek service role key di config/supabase_config.json
3. Pastikan internet connection stabil
4. Cek log error untuk detail masalah

## CONTACT SUPPORT:

Jika butuh bantuan, hubungi tim development dengan menyertakan:
- Error message lengkap
- Screenshot Supabase Dashboard
- Log file dari aplikasi