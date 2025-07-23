-- Drop existing payments table if exists
DROP TABLE IF EXISTS payments;

-- Create payments table with correct structure
CREATE TABLE payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES user_profiles(id),
    amount DECIMAL(10,2) NOT NULL,
    credits_added INTEGER NOT NULL,
    payment_method VARCHAR(100),
    status VARCHAR(50) DEFAULT 'completed',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    payment_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_payments_transaction_id ON payments(transaction_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);

-- Test insert
INSERT INTO payments (transaction_id, user_id, amount, credits_added, payment_method, status)
VALUES (
    'TEST123456789',
    (SELECT id FROM user_profiles WHERE email = 'mursalinasrul@gmail.com'),
    10000.00,
    10000,
    'bca',
    'completed'
) ON CONFLICT (transaction_id) DO NOTHING;

-- Show table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'payments'; 