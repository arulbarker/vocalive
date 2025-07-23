import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Create Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const { type, key, provider } = await req.json()

    let result: any = null

    switch (type) {
      case 'api_key':
        const { data: apiData, error: apiError } = await supabase
          .from('api_credentials')
          .select('key_value')
          .eq('key_name', key)
          .eq('is_active', true)
          .single()
        
        if (apiError) throw apiError
        result = apiData?.key_value
        break

      case 'payment_config':
        const { data: paymentData, error: paymentError } = await supabase
          .from('payment_config')
          .select('config_value')
          .eq('provider', provider)
          .eq('config_key', key)
          .eq('is_active', true)
          .single()
        
        if (paymentError) throw paymentError
        result = paymentData?.config_value
        break

      case 'server_config':
        const { data: serverData, error: serverError } = await supabase
          .from('server_config')
          .select('config_value')
          .eq('config_key', key)
          .eq('is_active', true)
          .single()
        
        if (serverError) throw serverError
        result = serverData?.config_value
        break

      case 'google_credentials':
        const { data: googleData, error: googleError } = await supabase
          .from('google_credentials')
          .select('credential_data')
          .eq('credential_type', key)
          .eq('is_active', true)
          .single()
        
        if (googleError) throw googleError
        result = googleData?.credential_data
        break

      default:
        throw new Error(`Unknown config type: ${type}`)
    }

    return new Response(
      JSON.stringify({ 
        status: 'success', 
        data: result 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ 
        status: 'error', 
        message: error.message 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    )
  }
}) 