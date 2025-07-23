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

// Environment detection
const isSandbox = process.env.IPAYMU_API_KEY?.includes('SANDBOX') || false

// Health check endpoint
app.get('/healthz', (req, res) => {
  res.status(200).json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    environment: isSandbox ? 'sandbox' : 'production'
  })
})

// iPaymu Callback Endpoint
app.post('/ipaymu-callback', async (req, res) => {
  try {
    console.log('iPaymu Callback Data:', req.body)
    console.log('Environment:', isSandbox ? 'SANDBOX' : 'PRODUCTION')

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
    const creditsToAdd = Math.floor(parseFloat(amount))

    // Update user credits
    const { error: updateError } = await supabase
      .from('user_profiles')
      .update({ 
        credits: user.credits + creditsToAdd,
        updated_at: new Date().toISOString()
      })
      .eq('id', user.id)

    if (updateError) {
      console.error('Error updating user credits:', updateError)
      return res.status(500).send('Error updating credits')
    }

    // Save payment record
    const { error: paymentError } = await supabase
      .from('payments')
      .insert({
        transaction_id: trx_id,
        user_id: user.id,
        amount: parseFloat(amount),
        credits_added: creditsToAdd,
        payment_method: via || channel,
        status: 'completed',
        processed_at: new Date().toISOString(),
        payment_data: req.body,
        environment: isSandbox ? 'sandbox' : 'production'
      })

    if (paymentError) {
      console.error('Error saving payment:', paymentError)
      return res.status(500).send('Error saving payment')
    }

    console.log(`Payment processed successfully: ${trx_id}, Credits added: ${creditsToAdd}, Environment: ${isSandbox ? 'SANDBOX' : 'PRODUCTION'}`)
    res.status(200).send('OK')

  } catch (error) {
    console.error('Callback processing error:', error)
    res.status(500).send('Internal server error')
  }
})

// Payment completion page
app.get('/payment-completed', (req, res) => {
  const { status, trx_id } = req.query
  
  if (status === 'berhasil') {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Payment Successful</title>
        <style>
          body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
          .success { color: #28a745; font-size: 24px; }
          .details { margin: 20px 0; }
          .environment { background: #ffc107; color: #000; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
      </head>
      <body>
        <div class="success">✅ Payment Successful!</div>
        <div class="environment">${isSandbox ? '🧪 SANDBOX MODE' : '🚀 PRODUCTION MODE'}</div>
        <div class="details">
          <p>Your credits have been added to your account.</p>
          <p>Transaction ID: ${trx_id}</p>
        </div>
        <p>You can now close this window and return to StreamMate AI.</p>
      </body>
      </html>
    `)
  } else {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Payment Failed</title>
        <style>
          body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
          .error { color: #dc3545; font-size: 24px; }
        </style>
      </head>
      <body>
        <div class="error">❌ Payment Failed</div>
        <p>Please try again or contact support.</p>
      </body>
      </html>
    `)
  }
})

const PORT = process.env.PORT || 3000
app.listen(PORT, () => {
  console.log(`Callback server running on port ${PORT}`)
  console.log(`Environment: ${isSandbox ? 'SANDBOX' : 'PRODUCTION'}`)
}) 