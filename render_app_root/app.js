const express = require('express')
const { createClient } = require('@supabase/supabase-js')

const app = express()

// Middleware
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*')
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.header('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  next()
})

// Initialize Supabase
const supabaseUrl = process.env.SUPABASE_URL || 'https://nivwxqojwljihoybzgkc.supabase.co'
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

// iPaymu Callback Endpoint
app.post('/ipaymu-callback', async (req, res) => {
  try {
    console.log('iPaymu Callback Data:', req.body)

    const {
      trx_id,
      sid,
      reference_id,
      status,
      status_code,
      sub_total,
      total,
      amount,
      fee,
      paid_off,
      created_at,
      expired_at,
      paid_at,
      settlement_status,
      transaction_status_code,
      is_escrow,
      system_notes,
      via,
      channel,
      payment_no,
      buyer_name,
      buyer_email,
      buyer_phone,
      additional_info,
      url,
      va
    } = req.body

    // Validate payment status
    if (status !== 'berhasil' || status_code !== '1') {
      console.log('Payment not successful:', status, status_code)
      return res.status(200).send('OK')
    }

    // Check if payment already processed (idempotency)
    const { data: existingPayment } = await supabase
      .from('payments')
      .select('id, processed_at')
      .eq('transaction_id', trx_id)
      .single()

    if (existingPayment && existingPayment.processed_at) {
      console.log('Payment already processed:', trx_id)
      return res.status(200).send('OK')
    }

    // Extract user email from reference_id (format: email_timestamp)
    const userEmail = reference_id.split('_')[0]

    // Get user by email
    const { data: user, error: userError } = await supabase
      .from('user_profiles')
      .select('id, credits')
      .eq('email', userEmail)
      .single()

    if (userError || !user) {
      console.error('User not found:', userEmail, userError)
      return res.status(400).send('User not found')
    }

    // Calculate credits (1:1 ratio with paid amount)
    const paidAmount = parseFloat(paid_off) || 0
    const creditsToAdd = Math.floor(paidAmount / 1000) // 1000 IDR = 1 credit

    // Insert or update payment record
    const paymentData = {
      order_id: reference_id,
      user_id: user.id,
      amount: parseFloat(total) || 0,
      status: 'success',
      transaction_id: trx_id,
      payment_method: via,
      paid_amount: paidAmount,
      credits_amount: creditsToAdd,
      paid_at: paid_at,
      processed_at: new Date().toISOString(),
      callback_data: req.body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    const { error: paymentError } = await supabase
      .from('payments')
      .upsert(paymentData, {
        onConflict: 'order_id',
        ignoreDuplicates: false
      })

    if (paymentError) {
      console.error('Payment insert error:', paymentError)
      return res.status(500).send('Payment processing error')
    }

    // Update user credits
    const { error: creditError } = await supabase
      .rpc('add_user_credits', {
        user_id: user.id,
        credits_to_add: creditsToAdd
      })

    if (creditError) {
      console.error('Credit update error:', creditError)
      // Still return OK to iPaymu, but log the error
    }

    console.log(`Payment processed successfully: ${trx_id}, Credits added: ${creditsToAdd}`)

    return res.status(200).send('OK')

  } catch (error) {
    console.error('Callback processing error:', error)
    return res.status(500).send('Error processing callback')
  }
})

// Payment Completed Page
app.get('/payment-completed', async (req, res) => {
  try {
    const { order_id } = req.query

    if (!order_id) {
      return res.status(400).send('Order ID required')
    }

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
})

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() })
})

const PORT = process.env.PORT || 3000
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
}) 