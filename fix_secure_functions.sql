-- ============================================
-- FIX SECURE FUNCTIONS
-- ============================================

-- Drop existing functions first
DROP FUNCTION IF EXISTS update_user_credits(TEXT, INTEGER, TEXT, TEXT);
DROP FUNCTION IF EXISTS process_payment_callback(TEXT, INTEGER, TEXT, TEXT);

-- Recreate update_user_credits function with proper error handling
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
    current_credits INTEGER;
BEGIN
    -- Get current credits
    SELECT credits INTO current_credits 
    FROM user_profiles 
    WHERE email = user_email;
    
    -- Check if user exists
    IF current_credits IS NULL THEN
        RAISE EXCEPTION 'User not found: %', user_email;
    END IF;
    
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
        RAISE LOG 'Error in update_user_credits: %', SQLERRM;
        RETURN FALSE;
END;
$$;

-- Recreate process_payment_callback function with proper error handling
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
    current_credits INTEGER;
BEGIN
    -- Only process successful payments
    IF payment_status = 'success' THEN
        -- Get current credits
        SELECT credits INTO current_credits 
        FROM user_profiles 
        WHERE email = user_email;
        
        -- Check if user exists
        IF current_credits IS NULL THEN
            RAISE EXCEPTION 'User not found: %', user_email;
        END IF;
        
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
        RAISE LOG 'Error in process_payment_callback: %', SQLERRM;
        RETURN FALSE;
END;
$$;

-- Grant permissions again
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO service_role;

-- Test the functions
SELECT 'Functions recreated successfully!' as status; 