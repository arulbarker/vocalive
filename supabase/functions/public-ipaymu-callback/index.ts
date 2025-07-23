// deno-lint-ignore-file
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse form data from iPaymu
    const formData = await req.formData()
    const body = Object.fromEntries(formData.entries())
    
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
      return new Response('OK', { 
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
      })
    }

    // Initialize Supabase client with service role key
    const supabaseUrl = 'https://nivwxqojwljihoybzgkc.supabase.co'
    const supabaseServiceKey = Deno.env.get('SERVICE_ROLE_KEY')!
    
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
      return new Response('OK', { 
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
      })
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
      return new Response('User not found', { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
      })
    }

    // Calculate credits (1:1 ratio with paid amount)
    const paidAmount = parseFloat(paid_off as string) || 0
    const creditsToAdd = Math.floor(paidAmount / 1000) // 1000 IDR = 1 credit

    // Insert or update payment record
    const paymentData = {
      order_id: reference_id,
      user_id: user.id,
      amount: parseFloat(total as string) || 0,
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
      return new Response('Payment processing error', { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
      })
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

    return new Response('OK', { 
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
    })

  } catch (error) {
    console.error('Callback processing error:', error)
    return new Response('Error processing callback', { 
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
    })
  }
}) 