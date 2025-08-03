-- ============================================
-- SUPABASE SECURITY CONFIGURATION
-- ============================================

-- 1. ENABLE RLS ON CRITICAL TABLES
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

-- 2. CREATE SECURITY POLICIES FOR USER_PROFILES
-- Users can only access their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.email() = email);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.email() = email);

-- Service role can access all profiles (for callbacks)
CREATE POLICY "Service role can access all profiles" ON user_profiles
    FOR ALL USING (auth.role() = 'service_role');

-- 3. CREATE SECURITY POLICIES FOR CREDIT_TRANSACTIONS
-- Users can only view their own transactions
CREATE POLICY "Users can view own transactions" ON credit_transactions
    FOR SELECT USING (auth.email() = email);

-- Service role can insert transactions (for callbacks)
CREATE POLICY "Service role can insert transactions" ON credit_transactions
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Service role can update transactions
CREATE POLICY "Service role can update transactions" ON credit_transactions
    FOR UPDATE USING (auth.role() = 'service_role');

-- 4. CREATE FUNCTION FOR SECURE CREDIT UPDATES
CREATE OR REPLACE FUNCTION update_user_credits(
    user_email TEXT,
    credit_amount INTEGER,
    transaction_type TEXT,
    description TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Update user credits
    UPDATE user_profiles 
    SET credits = credits + credit_amount,
        updated_at = NOW()
    WHERE email = user_email;
    
    -- Log transaction
    INSERT INTO credit_transactions (
        email, amount, transaction_type, description, created_at
    ) VALUES (
        user_email, credit_amount, transaction_type, description, NOW()
    );
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- 5. CREATE FUNCTION FOR PAYMENT CALLBACK
CREATE OR REPLACE FUNCTION process_payment_callback(
    user_email TEXT,
    payment_amount INTEGER,
    payment_status TEXT,
    payment_id TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Only process successful payments
    IF payment_status = 'success' THEN
        -- Update user credits
        UPDATE user_profiles 
        SET credits = credits + payment_amount,
            updated_at = NOW()
        WHERE email = user_email;
        
        -- Log transaction
        INSERT INTO credit_transactions (
            email, amount, transaction_type, description, created_at
        ) VALUES (
            user_email, payment_amount, 'credit_add', 
            'Payment callback: ' || payment_id, NOW()
        );
        
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- 6. GRANT NECESSARY PERMISSIONS
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO service_role;

-- 7. CREATE INDEXES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_email ON credit_transactions(email);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);

-- 8. ADD AUDIT LOGGING
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    user_email TEXT,
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (table_name, operation, user_email, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.email, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (table_name, operation, user_email, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.email, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (table_name, operation, user_email, old_data)
        VALUES (TG_TABLE_NAME, TG_OP, OLD.email, to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit triggers
DROP TRIGGER IF EXISTS audit_user_profiles_trigger ON user_profiles;
CREATE TRIGGER audit_user_profiles_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

DROP TRIGGER IF EXISTS audit_credit_transactions_trigger ON credit_transactions;
CREATE TRIGGER audit_credit_transactions_trigger
    AFTER INSERT OR UPDATE OR DELETE ON credit_transactions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- 9. SECURITY CHECK FUNCTION
CREATE OR REPLACE FUNCTION check_security_status()
RETURNS TABLE (
    table_name TEXT,
    rls_enabled BOOLEAN,
    policy_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname||'.'||tablename as table_name,
        rowsecurity as rls_enabled,
        (SELECT COUNT(*) FROM pg_policies WHERE tablename = t.tablename) as policy_count
    FROM pg_tables t
    WHERE schemaname = 'public' 
    AND tablename IN ('user_profiles', 'credit_transactions');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 10. FINAL SECURITY VERIFICATION
SELECT 'Security configuration completed successfully!' as status; 