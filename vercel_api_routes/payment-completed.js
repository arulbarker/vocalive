import { createClient } from '@supabase/supabase-js'

export default async function handler(req, res) {
  // Handle CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  // Handle preflight request
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  try {
    const { order_id, trx_id } = req.query

    if (!order_id) {
      return res.status(400).send('Order ID required')
    }

    // Initialize Supabase client
    const supabaseUrl = process.env.SUPABASE_URL || 'https://nivwxqojwljihoybzgkc.supabase.co'
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    })

    // Get payment details
    const { data: payment, error: paymentError } = await supabase
      .from('payments')
      .select('*')
      .eq('order_id', order_id)
      .single()

    if (paymentError || !payment) {
      return res.status(404).send('Payment not found')
    }

    // Get user details
    const { data: user, error: userError } = await supabase
      .from('user_profiles')
      .select('email, credits')
      .eq('id', payment.user_id)
      .single()

    if (userError || !user) {
      return res.status(404).send('User not found')
    }

    // Create success page HTML
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Success - StreamMate AI</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
            width: 90%;
        }
        .success-icon {
            width: 80px;
            height: 80px;
            background: #4CAF50;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            color: white;
            font-size: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .amount {
            font-size: 24px;
            color: #4CAF50;
            font-weight: bold;
            margin: 20px 0;
        }
        .credits {
            background: #f0f8ff;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .details {
            text-align: left;
            background: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
        }
        .btn {
            background: #4CAF50;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
        }
        .btn:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✓</div>
        <h1>Payment Successful!</h1>
        <p>Thank you for your purchase. Your credits have been added to your account.</p>
        
        <div class="amount">
            Amount: Rp ${payment.paid_amount?.toLocaleString() || '0'}
        </div>
        
        <div class="credits">
            <strong>Credits Added:</strong> ${payment.credits_amount || 0} credits
        </div>
        
        <div class="details">
            <div class="detail-row">
                <span>Order ID:</span>
                <span>${payment.order_id}</span>
            </div>
            <div class="detail-row">
                <span>Transaction ID:</span>
                <span>${payment.transaction_id}</span>
            </div>
            <div class="detail-row">
                <span>Payment Method:</span>
                <span>${payment.payment_method}</span>
            </div>
            <div class="detail-row">
                <span>Date:</span>
                <span>${new Date(payment.paid_at).toLocaleString()}</span>
            </div>
            <div class="detail-row">
                <span>User Email:</span>
                <span>${user.email}</span>
            </div>
            <div class="detail-row">
                <span>Total Credits:</span>
                <span>${user.credits} credits</span>
            </div>
        </div>
        
        <a href="https://streammate-ai.com" class="btn">Back to StreamMate AI</a>
        <a href="mailto:support@streammate-ai.com" class="btn">Contact Support</a>
    </div>
</body>
</html>
    `

    res.setHeader('Content-Type', 'text/html')
    return res.status(200).send(html)

  } catch (error) {
    console.error('Error:', error)
    return res.status(500).send('Internal server error')
  }
} 