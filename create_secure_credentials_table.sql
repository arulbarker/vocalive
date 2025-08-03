-- ============================================
-- SECURE CREDENTIALS STORAGE SYSTEM
-- Tabel untuk menyimpan kredensial penting secara aman di Supabase
-- ============================================

-- 1. Buat tabel untuk menyimpan kredensial terenkripsi
CREATE TABLE IF NOT EXISTS secure_credentials (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    credential_key VARCHAR(100) UNIQUE NOT NULL,
    encrypted_value TEXT NOT NULL,
    credential_type VARCHAR(50) NOT NULL, -- 'api_key', 'oauth', 'database', 'payment'
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system'
);

-- 2. Buat index untuk performa
CREATE INDEX IF NOT EXISTS idx_secure_credentials_key ON secure_credentials(credential_key);
CREATE INDEX IF NOT EXISTS idx_secure_credentials_type ON secure_credentials(credential_type);
CREATE INDEX IF NOT EXISTS idx_secure_credentials_active ON secure_credentials(is_active);

-- 3. Enable RLS (Row Level Security)
ALTER TABLE secure_credentials ENABLE ROW LEVEL SECURITY;

-- 4. Buat policy untuk akses (hanya service role yang bisa akses)
CREATE POLICY "Service role can access credentials" ON secure_credentials
    FOR ALL USING (auth.role() = 'service_role');

-- 5. Fungsi untuk enkripsi/dekripsi (menggunakan built-in pgcrypto)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 6. Fungsi untuk menyimpan kredensial terenkripsi
CREATE OR REPLACE FUNCTION store_secure_credential(
    p_key VARCHAR(100),
    p_value TEXT,
    p_type VARCHAR(50),
    p_description TEXT DEFAULT NULL,
    p_encryption_key TEXT DEFAULT 'StreamMateAI_SecureKey_2024'
)
RETURNS JSON AS $$
DECLARE
    encrypted_val TEXT;
    result JSON;
BEGIN
    -- Enkripsi nilai menggunakan AES
    encrypted_val := encode(
        encrypt(p_value::bytea, p_encryption_key::bytea, 'aes'),
        'base64'
    );
    
    -- Insert atau update kredensial
    INSERT INTO secure_credentials (credential_key, encrypted_value, credential_type, description)
    VALUES (p_key, encrypted_val, p_type, p_description)
    ON CONFLICT (credential_key) 
    DO UPDATE SET 
        encrypted_value = EXCLUDED.encrypted_value,
        credential_type = EXCLUDED.credential_type,
        description = EXCLUDED.description,
        updated_at = NOW();
    
    result := json_build_object(
        'status', 'success',
        'message', 'Credential stored securely',
        'key', p_key,
        'type', p_type
    );
    
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        result := json_build_object(
            'status', 'error',
            'message', SQLERRM,
            'key', p_key
        );
        RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Fungsi untuk mengambil kredensial terenkripsi
CREATE OR REPLACE FUNCTION get_secure_credential(
    p_key VARCHAR(100),
    p_encryption_key TEXT DEFAULT 'StreamMateAI_SecureKey_2024'
)
RETURNS JSON AS $$
DECLARE
    encrypted_val TEXT;
    decrypted_val TEXT;
    cred_type VARCHAR(50);
    result JSON;
BEGIN
    -- Ambil kredensial terenkripsi
    SELECT encrypted_value, credential_type 
    INTO encrypted_val, cred_type
    FROM secure_credentials 
    WHERE credential_key = p_key AND is_active = true;
    
    IF encrypted_val IS NULL THEN
        result := json_build_object(
            'status', 'error',
            'message', 'Credential not found',
            'key', p_key
        );
        RETURN result;
    END IF;
    
    -- Dekripsi nilai
    decrypted_val := convert_from(
        decrypt(decode(encrypted_val, 'base64'), p_encryption_key::bytea, 'aes'),
        'UTF8'
    );
    
    result := json_build_object(
        'status', 'success',
        'key', p_key,
        'value', decrypted_val,
        'type', cred_type
    );
    
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        result := json_build_object(
            'status', 'error',
            'message', SQLERRM,
            'key', p_key
        );
        RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 8. Fungsi untuk mendapatkan semua kredensial (tanpa nilai, hanya metadata)
CREATE OR REPLACE FUNCTION list_secure_credentials()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_agg(
        json_build_object(
            'key', credential_key,
            'type', credential_type,
            'description', description,
            'is_active', is_active,
            'created_at', created_at,
            'updated_at', updated_at
        )
    )
    INTO result
    FROM secure_credentials
    WHERE is_active = true
    ORDER BY credential_type, credential_key;
    
    RETURN json_build_object(
        'status', 'success',
        'data', COALESCE(result, '[]'::json)
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'status', 'error',
            'message', SQLERRM
        );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 9. Fungsi untuk menghapus kredensial (soft delete)
CREATE OR REPLACE FUNCTION delete_secure_credential(p_key VARCHAR(100))
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    UPDATE secure_credentials 
    SET is_active = false, updated_at = NOW()
    WHERE credential_key = p_key;
    
    IF FOUND THEN
        result := json_build_object(
            'status', 'success',
            'message', 'Credential deactivated',
            'key', p_key
        );
    ELSE
        result := json_build_object(
            'status', 'error',
            'message', 'Credential not found',
            'key', p_key
        );
    END IF;
    
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        result := json_build_object(
            'status', 'error',
            'message', SQLERRM,
            'key', p_key
        );
        RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 10. Grant permissions
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON TABLE secure_credentials TO service_role;
GRANT EXECUTE ON FUNCTION store_secure_credential TO service_role;
GRANT EXECUTE ON FUNCTION get_secure_credential TO service_role;
GRANT EXECUTE ON FUNCTION list_secure_credentials TO service_role;
GRANT EXECUTE ON FUNCTION delete_secure_credential TO service_role;

-- 11. Contoh data awal (opsional)
-- INSERT INTO secure_credentials (credential_key, encrypted_value, credential_type, description)
-- VALUES ('EXAMPLE_API_KEY', 'encrypted_value_here', 'api_key', 'Example API key for testing');

COMMENT ON TABLE secure_credentials IS 'Secure storage for encrypted credentials and API keys';
COMMENT ON FUNCTION store_secure_credential IS 'Store encrypted credential securely';
COMMENT ON FUNCTION get_secure_credential IS 'Retrieve and decrypt credential';
COMMENT ON FUNCTION list_secure_credentials IS 'List all credential metadata (without values)';
COMMENT ON FUNCTION delete_secure_credential IS 'Soft delete credential';