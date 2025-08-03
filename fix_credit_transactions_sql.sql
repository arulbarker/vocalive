-- ============================================
-- FIX CREDIT TRANSACTIONS TABLE ISSUE
-- ============================================
-- Execute ini untuk fix masalah credit_transactions

-- First, let's check the current table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'credit_transactions';

-- Option 1: Add credit_type column if it doesn't exist
ALTER TABLE credit_transactions 
ADD COLUMN IF NOT EXISTS credit_type TEXT DEFAULT 'general';

-- Option 2: Update existing functions to include credit_type
-- Drop existing functions
DROP FUNCTION IF EXISTS update_user_credits(TEXT, INTEGER, TEXT, TEXT);
DROP FUNCTION IF EXISTS process_payment_callback(TEXT, INTEGER, TEXT, TEXT);

-- Create fixed update_user_credits function with credit_type
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
    max_credits INTEGER := 10000;
BEGIN
    -- Input validation
    IF credit_amount = 0 THEN
        RETURN FALSE;
    END IF;

    IF transaction_type IS NULL OR trim(transaction_type) = '' THEN
        RETURN FALSE;
    END IF;

    -- Check if user exists first
    IF NOT EXISTS (SELECT 1 FROM user_profiles WHERE email = user_email) THEN
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('credit_update', 'User not found: ' || user_email, NOW());
        RETURN FALSE;
    END IF;
    
    -- Get current credits
    SELECT credits INTO current_credits FROM user_profiles WHERE email = user_email;
    
    -- Prevent exceeding maximum credits
    IF current_credits + credit_amount > max_credits THEN
        credit_amount := max_credits - current_credits;
    END IF;
    
    -- Update user credits
    UPDATE user_profiles 
    SET credits = credits + credit_amount
    WHERE email = user_email;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    -- Only insert transaction if user was updated
    IF affected_rows > 0 THEN
        INSERT INTO credit_transactions (
            email, amount, transaction_type, description, credit_type, created_at
        ) VALUES (
            user_email, credit_amount, transaction_type, description, 'credit_update', NOW()
        );
        RETURN TRUE;
    ELSE
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('credit_update', 'Failed to update credits for: ' || user_email, NOW());
        RETURN FALSE;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('credit_update', 'Unexpected error: ' || SQLERRM, NOW());
        RETURN FALSE;
END;
$$;

-- Create fixed process_payment_callback function with credit_type
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
    max_credits INTEGER := 10000;
BEGIN
    -- Validate inputs
    IF payment_amount <= 0 OR payment_status IS NULL OR payment_id IS NULL THEN
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('payment_callback', 'Invalid payment input', NOW());
        RETURN FALSE;
    END IF;

    -- Only process successful payments
    IF payment_status != 'success' THEN
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('payment_callback', 'Non-success payment status: ' || payment_status, NOW());
        RETURN FALSE;
    END IF;
    
    -- Check if user exists
    IF NOT EXISTS (SELECT 1 FROM user_profiles WHERE email = user_email) THEN
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('payment_callback', 'User not found: ' || user_email, NOW());
        RETURN FALSE;
    END IF;
    
    -- Get current credits
    SELECT credits INTO current_credits FROM user_profiles WHERE email = user_email;
    
    -- Prevent exceeding maximum credits
    IF current_credits + payment_amount > max_credits THEN
        payment_amount := max_credits - current_credits;
    END IF;
    
    -- Update user credits
    UPDATE user_profiles 
    SET credits = credits + payment_amount
    WHERE email = user_email;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    -- Only insert transaction if user was updated
    IF affected_rows > 0 THEN
        INSERT INTO credit_transactions (
            email, amount, transaction_type, description, credit_type, created_at
        ) VALUES (
            user_email, payment_amount, 'credit_add', 
            'Payment callback: ' || payment_id, 'payment_callback', NOW()
        );
        RETURN TRUE;
    ELSE
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('payment_callback', 'Failed to update credits for: ' || user_email, NOW());
        RETURN FALSE;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        INSERT INTO error_logs (error_type, error_message, created_at)
        VALUES ('payment_callback', 'Unexpected error: ' || SQLERRM, NOW());
        RETURN FALSE;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO service_role;

-- Test the functions
SELECT 'Functions fixed with credit_type!' as status; 