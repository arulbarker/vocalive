import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const url = new URL(req.url)
    const returnParam = url.searchParams.get('return')
    const sid = url.searchParams.get('sid')
    const trx_id = url.searchParams.get('trx_id')
    const status = url.searchParams.get('status')
    const tipe = url.searchParams.get('tipe')
    const payment_method = url.searchParams.get('payment_method')

    console.log('Payment completed redirect received:', {
      returnParam,
      sid,
      trx_id,
      status,
      tipe,
      payment_method
    })

    // Create success page HTML
    const successHtml = `
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
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                max-width: 500px;
                width: 90%;
            }
            .success-icon {
                font-size: 80px;
                margin-bottom: 20px;
            }
            h1 {
                margin: 0 0 20px 0;
                font-size: 28px;
                font-weight: 600;
            }
            .message {
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 30px;
                opacity: 0.9;
            }
            .details {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            .detail-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-size: 14px;
            }
            .detail-label {
                opacity: 0.8;
            }
            .detail-value {
                font-weight: 600;
            }
            .button {
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
            }
            .button:hover {
                transform: translateY(-2px);
            }
            .close-button {
                background: linear-gradient(45deg, #f44336, #d32f2f);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Payment Successful!</h1>
            <div class="message">
                Your payment has been processed successfully. Your credits have been added to your wallet.
            </div>
            
            <div class="details">
                <div class="detail-row">
                    <span class="detail-label">Transaction ID:</span>
                    <span class="detail-value">${trx_id || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Session ID:</span>
                    <span class="detail-value">${sid || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">${status || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Payment Method:</span>
                    <span class="detail-value">${payment_method || tipe || 'N/A'}</span>
                </div>
            </div>
            
            <div>
                <a href="#" onclick="window.close()" class="button close-button">Close Window</a>
            </div>
        </div>
        
        <script>
            // Auto close after 5 seconds
            setTimeout(() => {
                window.close();
            }, 5000);
        </script>
    </body>
    </html>
    `

    // Create error page HTML
    const errorHtml = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Cancelled - StreamMate AI</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                max-width: 500px;
                width: 90%;
            }
            .error-icon {
                font-size: 80px;
                margin-bottom: 20px;
            }
            h1 {
                margin: 0 0 20px 0;
                font-size: 28px;
                font-weight: 600;
            }
            .message {
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 30px;
                opacity: 0.9;
            }
            .button {
                background: linear-gradient(45deg, #f44336, #d32f2f);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
            }
            .button:hover {
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">❌</div>
            <h1>Payment Cancelled</h1>
            <div class="message">
                Your payment was cancelled or failed. No charges were made to your account.
            </div>
            
            <div>
                <a href="#" onclick="window.close()" class="button">Close Window</a>
            </div>
        </div>
        
        <script>
            // Auto close after 5 seconds
            setTimeout(() => {
                window.close();
            }, 5000);
        </script>
    </body>
    </html>
    `

    // Return appropriate page based on status
    if (status === 'berhasil' || status === 'success') {
      return new Response(successHtml, {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'text/html' }
      })
    } else {
      return new Response(errorHtml, {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'text/html' }
      })
    }

  } catch (error) {
    console.error('Error processing payment completed:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }), 
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
}) 