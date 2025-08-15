import { createClient } from 'jsr:@supabase/supabase-js@^2'

function parseForm(body: string): Record<string, string> {
  return Object.fromEntries(
    body.split('&').map((pair) => {
      const [k, v] = pair.split('=')
      return [decodeURIComponent(k), decodeURIComponent(v || '')]
    })
  )
}

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    })
  }

  if (req.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405 })
  }

  const contentType = req.headers.get('content-type') || ''
  let form: Record<string, string> = {}
  if (contentType.includes('application/x-www-form-urlencoded')) {
    const body = await req.text()
    form = parseForm(body)
  } else {
    return new Response('Unsupported Content-Type', { status: 415 })
  }

  // Extract fields
  const { trx_id, status, status_code, reference_id, paid_off } = form
  if (!trx_id || !status || !status_code || !reference_id || !paid_off) {
    return new Response('Missing required fields', { status: 400 })
  }

  // Only process successful payments
  if (status !== 'berhasil' || status_code !== '1') {
    return new Response('Payment not successful', { status: 200 })
  }

  // Parse user email from reference_id (format: email_timestamp)
  const email = reference_id.split('_')[0]
  if (!email) {
    return new Response('Invalid reference_id', { status: 400 })
  }

  // Supabase client with service role for DB writes
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Idempotency: check if trx_id already exists
  const { data: existing, error: checkError } = await supabase
    .from('payments')
    .select('id')
    .eq('trx_id', trx_id)
    .maybeSingle()
  if (checkError) {
    return new Response('Database error', { status: 500 })
  }
  if (existing) {
    return new Response('Already processed', { status: 200 })
  }

  // Insert payment record
  const { error: insertError } = await supabase.from('payments').insert({
    trx_id,
    status,
    status_code,
    reference_id,
    paid_off: Number(paid_off),
  })
  if (insertError) {
    return new Response('Failed to record payment', { status: 500 })
  }

  // Call add_user_credits(email, paid_off)
  const { error: funcError } = await supabase.rpc('add_user_credits', {
    user_email: email,
    amount: Number(paid_off),
  })
  if (funcError) {
    return new Response('Failed to add credits', { status: 500 })
  }

  return new Response('OK', {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'text/plain',
    },
  })
})