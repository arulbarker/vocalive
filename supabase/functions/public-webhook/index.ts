import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

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
    
    console.log('Public webhook received:', body)

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
      console.log('Payment successful, processing...')
      
      // For now, just return success response
      // Database operations will be handled by the main application
      
      return new Response(
        JSON.stringify({ 
          success: true, 
          message: 'Payment processed successfully',
          transaction_id: trx_id,
          reference_id: reference_id,
          buyer_email: buyer_email,
          amount: total
        }), 
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    } else {
      console.log('Payment not successful')
      
      return new Response(
        JSON.stringify({ 
          success: false, 
          message: 'Payment not successful',
          status: status,
          status_code: status_code
        }), 
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }
  } catch (error) {
    console.error('Error processing public webhook:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }), 
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
}) 