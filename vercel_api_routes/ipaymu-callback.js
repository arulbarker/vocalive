import { createClient } from '@supabase/supabase-js'

export default async function handler(req, res) {
  // Handle CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  // Handle preflight request
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    // Parse form data from iPaymu
    const body = req.body
    console.log('iPaymu Callback Data:', body)

    // Extract payment data
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
    } = body

    // Validate payment status
    if (status !== 'berhasil' || status_code !== '1') {
      console.log('Payment not successful:', status, status_code)
      return res.status(200).send('OK')
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
      callback_data: body,
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
} 