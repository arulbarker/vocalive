import { createClient } from 'jsr:@supabase/supabase-js@^2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const url = new URL(req.url)
    const orderId = url.searchParams.get('order_id')
    const trxId = url.searchParams.get('trx_id')

    if (!orderId) {
      return new Response('Order ID required', {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
      })
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Get payment details
    const { data: payment, error: paymentError } = await supabase
      .from('payments')
      .select('*')
      .eq('order_id', orderId)
      .single()

    if (paymentError || !payment) {
      return new Response('Payment not found', {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
      })
    }

    // Get user details
    const { data: user, error: userError } = await supabase
      .from('user_profiles')
      .select('email, credits')
      .eq('id', payment.user_id)
      .single()

    if (userError || !user) {
      return new Response('User not found', {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
      })
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

    return new Response(html, {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'text/html' }
    })

  } catch (error) {
    console.error('Error:', error)
    return new Response('Internal server error', {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
    })
  }
}) 