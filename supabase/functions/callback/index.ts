import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Use service role key to bypass RLS
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    })

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
      buyer_name,
      via,
      channel,
      payment_no,
      va
    } = body

    console.log('Extracted payment info:', {
      trx_id,
      sid,
      reference_id,
      status,
      status_code,
      total,
      paid_at,
      buyer_email,
      buyer_name,
      via,
      channel,
      payment_no,
      va
    })

    // Check if payment is successful
    if (status === 'berhasil' && (status_code == 1 || status_code == '1')) {
      console.log('Payment successful, updating database...')
      
      // Update payment transaction status
      const { error: updateError } = await supabase
        .from('payment_transactions')
        .update({ 
          status: 'completed', 
          paid_at: paid_at, 
          transaction_id: trx_id, 
          session_id: sid,
          payment_method: via,
          payment_channel: channel,
          payment_no: payment_no,
          va_number: va
        })
        .eq('order_id', reference_id)

      if (updateError) {
        console.error('Error updating payment transaction:', updateError)
      } else {
        console.log('Payment transaction updated successfully')
      }

      // Get payment transaction details to determine credits to add
      const { data: transaction, error: getError } = await supabase
        .from('payment_transactions')
        .select('*')
        .eq('order_id', reference_id)
        .single()

      if (getError) {
        console.error('Error getting transaction details:', getError)
      } else if (transaction && buyer_email) {
        console.log('Transaction details:', transaction)
        
        // Add credits to user's wallet using direct SQL to bypass RLS
        const { error: creditError } = await supabase
          .rpc('increment_wallet_balance', {
            user_email: buyer_email,
            amount: parseInt(transaction.credits)
          })

        if (creditError) {
          console.error('Error adding credits:', creditError)
          // Fallback: direct update
          const { error: fallbackError } = await supabase
            .from('users')
            .update({ 
              wallet_balance: supabase.rpc('increment', { 
                row: { wallet_balance: parseInt(transaction.credits) }, 
                amount: parseInt(transaction.credits) 
              })
            })
            .eq('email', buyer_email)
          
          if (fallbackError) {
            console.error('Fallback credit update failed:', fallbackError)
          } else {
            console.log('Credits added successfully to wallet (fallback)')
          }
        } else {
          console.log('Credits added successfully to wallet')
        }

        // Log credit transaction
        const { error: logError } = await supabase
          .from('credit_transactions')
          .insert({
            email: buyer_email,
            credit_type: 'wallet',
            amount: parseInt(transaction.credits),
            component: 'topup',
            description: `Top-up via iPaymu: ${transaction.package}`,
            transaction_id: trx_id,
            payment_method: via,
            payment_channel: channel
          })

        if (logError) {
          console.error('Error logging credit transaction:', logError)
        } else {
          console.log('Credit transaction logged successfully')
        }
      }
      
      return new Response(
        JSON.stringify({ 
          success: true, 
          message: 'Payment processed and credits added',
          credits_added: transaction?.credits || 0
        }), 
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    } else {
      console.log('Payment not successful, updating status to failed')
      
      // Payment not successful
      const { error: updateError } = await supabase
        .from('payment_transactions')
        .update({ status: 'failed' })
        .eq('order_id', reference_id)

      if (updateError) {
        console.error('Error updating failed payment:', updateError)
      }
      
      return new Response(
        JSON.stringify({ 
          success: false, 
          message: 'Payment not successful' 
        }), 
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }
  } catch (error) {
    console.error('Error processing payment callback:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }), 
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
}) 