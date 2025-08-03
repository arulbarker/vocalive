-- ============================================
-- FINAL FIX FOR SECURE FUNCTIONS
-- ============================================
-- Execute ini untuk fix functions secara final

-- Drop existing functions
DROP FUNCTION IF EXISTS update_user_credits(TEXT, INTEGER, TEXT, TEXT);
DROP FUNCTION IF EXISTS process_payment_callback(TEXT, INTEGER, TEXT, TEXT);

-- Create debug function to check user data
CREATE OR REPLACE FUNCTION debug_user_data(user_email TEXT)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    user_credits INTEGER;
    user_count INTEGER;
BEGIN
    -- Check if user exists
    SELECT COUNT(*) INTO user_count FROM user_profiles WHERE email = user_email;
    
    IF user_count = 0 THEN
        RETURN 'User not found: ' || user_email;
    END IF;
    
    -- Get current credits
    SELECT credits INTO user_credits FROM user_profiles WHERE email = user_email;
    
    RETURN 'User found. Current credits: ' || user_credits;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Error: ' || SQLERRM;
END;
$$;

-- Create fixed update_user_credits function
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
DECLARE
    affected_rows INTEGER;
    current_credits INTEGER;
BEGIN
    -- Check if user exists first
    IF NOT EXISTS (SELECT 1 FROM user_profiles WHERE email = user_email) THEN
        RETURN FALSE;
    END IF;
    
    -- Get current credits
    SELECT credits INTO current_credits FROM user_profiles WHERE email = user_email;
    
    -- Update user credits
    UPDATE user_profiles 
    SET credits = credits + credit_amount
    WHERE email = user_email;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    -- Only insert transaction if user was updated
    IF affected_rows > 0 THEN
        INSERT INTO credit_transactions (
            email, amount, transaction_type, description, created_at
        ) VALUES (
            user_email, credit_amount, transaction_type, description, NOW()
        );
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- Create fixed process_payment_callback function
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
DECLARE
    affected_rows INTEGER;
    current_credits INTEGER;
BEGIN
    -- Only process successful payments
    IF payment_status != 'success' THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user exists
    IF NOT EXISTS (SELECT 1 FROM user_profiles WHERE email = user_email) THEN
        RETURN FALSE;
    END IF;
    
    -- Get current credits
    SELECT credits INTO current_credits FROM user_profiles WHERE email = user_email;
    
    -- Update user credits
    UPDATE user_profiles 
    SET credits = credits + payment_amount
    WHERE email = user_email;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    -- Only insert transaction if user was updated
    IF affected_rows > 0 THEN
        INSERT INTO credit_transactions (
            email, amount, transaction_type, description, created_at
        ) VALUES (
            user_email, payment_amount, 'credit_add', 
            'Payment callback: ' || payment_id, NOW()
        );
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION debug_user_data(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO service_role;

-- Test the functions
SELECT debug_user_data('mursalinasrul@gmail.com') as user_debug;
SELECT 'Functions fixed successfully!' as status; 