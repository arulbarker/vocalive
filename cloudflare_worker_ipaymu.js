// Cloudflare Worker untuk iPaymu Callback
// Deploy ke Cloudflare Workers (gratis)

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Handle CORS
  if (request.method === 'OPTIONS') {
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
      }
    })
  }

  try {
    // Parse form data
    const formData = await request.formData()
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
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'text/plain'
        }
      })
    }

    // Initialize Supabase client
    const supabaseUrl = 'https://nivwxqojwljihoybzgkc.supabase.co'
    const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMjE5NzI5NSwiZXhwIjoyMDQ3NzczMjk1fQ.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8'

    // Check if payment already processed
    const checkResponse = await fetch(`${supabaseUrl}/rest/v1/payments?transaction_id=eq.${trx_id}&select=id,processed_at`, {
      headers: {
        'apikey': supabaseServiceKey,
        'Authorization': `Bearer ${supabaseServiceKey}`,
        'Content-Type': 'application/json'
      }
    })

    const existingPayments = await checkResponse.json()
    
    if (existingPayments.length > 0 && existingPayments[0].processed_at) {
      console.log('Payment already processed:', trx_id)
      return new Response('OK', {
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'text/plain'
        }
      })
    }

    // Extract user email
    const userEmail = reference_id.split('_')[0]

    // Get user by email
    const userResponse = await fetch(`${supabaseUrl}/rest/v1/user_profiles?email=eq.${userEmail}&select=id,credits`, {
      headers: {
        'apikey': supabaseServiceKey,
        'Authorization': `Bearer ${supabaseServiceKey}`,
        'Content-Type': 'application/json'
      }
    })

    const users = await userResponse.json()
    
    if (users.length === 0) {
      console.error('User not found:', userEmail)
      return new Response('User not found', {
        status: 400,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'text/plain'
        }
      })
    }

    const user = users[0]

    // Calculate credits
    const paidAmount = parseFloat(paid_off) || 0
    const creditsToAdd = Math.floor(paidAmount / 1000)

    // Insert payment record
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

    const insertResponse = await fetch(`${supabaseUrl}/rest/v1/payments`, {
      method: 'POST',
      headers: {
        'apikey': supabaseServiceKey,
        'Authorization': `Bearer ${supabaseServiceKey}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
      },
      body: JSON.stringify(paymentData)
    })

    if (!insertResponse.ok) {
      console.error('Payment insert error:', await insertResponse.text())
      return new Response('Payment processing error', {
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'text/plain'
        }
      })
    }

    // Update user credits
    const newCredits = (user.credits || 0) + creditsToAdd
    const updateResponse = await fetch(`${supabaseUrl}/rest/v1/user_profiles?id=eq.${user.id}`, {
      method: 'PATCH',
      headers: {
        'apikey': supabaseServiceKey,
        'Authorization': `Bearer ${supabaseServiceKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ credits: newCredits })
    })

    if (!updateResponse.ok) {
      console.error('Credit update error:', await updateResponse.text())
    }

    console.log(`Payment processed successfully: ${trx_id}, Credits added: ${creditsToAdd}`)

    return new Response('OK', {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'text/plain'
      }
    })

  } catch (error) {
    console.error('Callback processing error:', error)
    return new Response('Error processing callback', {
      status: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'text/plain'
      }
    })
  }
} 