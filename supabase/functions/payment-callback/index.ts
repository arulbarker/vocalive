import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    // Parse callback data from iPaymu
    const callbackData = await req.json()
    
    console.log('Payment callback received:', callbackData)

    // Validate payment status
    const paymentStatus = String(callbackData.status || '').toLowerCase()
    if (paymentStatus !== 'berhasil') {
      console.log('Payment status not successful:', paymentStatus)
      return new Response(
        JSON.stringify({ 
          status: 'success', 
          message: 'Payment status not successful, no action taken' 
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Extract payment data
    const orderId = callbackData.reference_id
    const amountPaid = parseFloat(callbackData.amount || 0)
    
    if (!orderId || !amountPaid) {
      return new Response(
        JSON.stringify({ 
          status: 'error', 
          message: 'Invalid callback data' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Get transaction details from database
    // Note: We need to store transaction details when creating payment
    // For now, we'll extract email from order_id or use a separate lookup
    
    // Extract email from order_id (assuming format: email_timestamp)
    const emailMatch = orderId.match(/^(.+)_\d+$/)
    const email = emailMatch ? emailMatch[1] : null
    
    if (!email) {
      console.error('Cannot extract email from order_id:', orderId)
      return new Response(
        JSON.stringify({ 
          status: 'error', 
          message: 'Cannot determine user email from order ID' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Calculate credits to add (1 IDR = 1 Credit)
    const creditsToAdd = amountPaid

    // Get current user license
    const { data: license, error: licenseError } = await supabaseClient
      .from('licenses')
      .select('*')
      .eq('email', email)
      .single()

    if (licenseError) {
      // Create new license if doesn't exist
      const { error: createError } = await supabaseClient
        .from('licenses')
        .insert({
          email,
          tier: 'basic',
          credit_balance: creditsToAdd,
          credit_used: 0,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })

      if (createError) {
        console.error('Failed to create license:', createError)
        return new Response(
          JSON.stringify({ 
            status: 'error', 
            message: 'Failed to create user license' 
          }),
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }
    } else {
      // Update existing license
      const newBalance = parseFloat(license.credit_balance || 0) + creditsToAdd
      
      const { error: updateError } = await supabaseClient
        .from('licenses')
        .update({
          credit_balance: newBalance,
          is_active: true,
          updated_at: new Date().toISOString()
        })
        .eq('email', email)

      if (updateError) {
        console.error('Failed to update license:', updateError)
        return new Response(
          JSON.stringify({ 
            status: 'error', 
            message: 'Failed to update user credits' 
          }),
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }
    }

    // Record transaction history
    const { error: transactionError } = await supabaseClient
      .from('transaction_history')
      .insert({
        email,
        transaction_type: 'purchase',
        credit_amount: creditsToAdd,
        price: amountPaid,
        order_id: orderId,
        description: `Payment via iPaymu - Order: ${orderId}`,
        created_at: new Date().toISOString()
      })

    if (transactionError) {
      console.error('Failed to record transaction:', transactionError)
      // Don't fail the request, credits were already added
    }

    console.log(`Payment processed successfully: ${email} received ${creditsToAdd} credits`)

    return new Response(
      JSON.stringify({
        status: 'success',
        data: {
          email,
          credits_added: creditsToAdd,
          order_id: orderId,
          amount_paid: amountPaid
        },
        message: 'Payment processed successfully',
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Payment callback error:', error)
    return new Response(
      JSON.stringify({ 
        status: 'error', 
        message: 'Internal server error' 
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
}) 