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
    // Use service role key for DB access
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Parse body as form-urlencoded or JSON
    const contentType = req.headers.get('content-type') || ''
    let body: any = {}
    if (contentType.includes('application/x-www-form-urlencoded')) {
      const form = await req.formData()
      for (const [key, value] of form.entries()) {
        body[key] = value
      }
    } else {
      body = await req.json()
    }
    console.log('Payment callback received:', body)

    // Extract payment information
    const {
      trx_id,
      sid,
      reference_id,
      status,
      status_code,
      total,
      paid_at,
      buyer_email,
      buyer_name
    } = body

    // Check if payment was successful
    if (status === 'berhasil' && (status_code == 1 || status_code == '1')) {
      // Update payment transaction status
      await supabase
        .from('payment_transactions')
        .update({
          status: 'completed',
          paid_at: paid_at,
          transaction_id: trx_id,
          session_id: sid
        })
        .eq('order_id', reference_id)

      // Get payment transaction details to determine credits to add
      const { data: transaction } = await supabase
        .from('payment_transactions')
        .select('*')
        .eq('order_id', reference_id)
        .single()

      if (transaction && buyer_email) {
        // Add credits to user's wallet
        await supabase
          .from('users')
          .update({
            wallet_balance: supabase.rpc('increment', { 
              row: { wallet_balance: parseInt(transaction.credits) },
              amount: parseInt(transaction.credits)
            })
          })
          .eq('email', buyer_email)

        // Log credit transaction
        await supabase
          .from('credit_transactions')
          .insert({
            email: buyer_email,
            credit_type: 'wallet',
            amount: parseInt(transaction.credits),
            component: 'topup',
            description: `Top-up via iPaymu: ${transaction.package}`,
            transaction_id: trx_id
          })
      }

      return new Response(
        JSON.stringify({ success: true, message: 'Payment processed and credits added' }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    } else {
      // Payment not successful
      await supabase
        .from('payment_transactions')
        .update({ status: 'failed' })
        .eq('order_id', reference_id)
      return new Response(
        JSON.stringify({ success: false, message: 'Payment not successful' }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
  } catch (error) {
    console.error('Error processing payment callback:', error)
    // Always return 200 OK to iPaymu
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 