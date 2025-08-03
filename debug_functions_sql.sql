-- ============================================
-- DEBUG FUNCTIONS SQL
-- ============================================
-- Execute ini untuk debug functions

-- Drop existing functions
DROP FUNCTION IF EXISTS update_user_credits(TEXT, INTEGER, TEXT, TEXT);
DROP FUNCTION IF EXISTS process_payment_callback(TEXT, INTEGER, TEXT, TEXT);

-- Create simple test function
CREATE OR REPLACE FUNCTION test_simple()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN 'Test successful!';
END;
$$;

-- Create debug function
CREATE OR REPLACE FUNCTION debug_function()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    user_count INTEGER;
BEGIN
    -- Check if user exists
    SELECT COUNT(*) INTO user_count FROM user_profiles WHERE email = 'mursalinasrul@gmail.com';
    
    IF user_count > 0 THEN
        RETURN 'User exists: ' || user_count;
    ELSE
        RETURN 'User not found';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Error: ' || SQLERRM;
END;
$$;

-- Create simple update_user_credits function
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
BEGIN
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

-- Create simple process_payment_callback function
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
BEGIN
    -- Only process successful payments
    IF payment_status = 'success' THEN
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
    END IF;
    
    RETURN FALSE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION test_simple() TO service_role;
GRANT EXECUTE ON FUNCTION debug_function() TO service_role;
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO service_role;

-- Test the functions
SELECT test_simple() as test_result;
SELECT debug_function() as debug_result;
SELECT 'Functions created successfully!' as status; 