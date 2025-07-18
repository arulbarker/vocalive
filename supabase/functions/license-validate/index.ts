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
    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    // Parse request body
    const { email, hardware_id } = await req.json()

    if (!email) {
      return new Response(
        JSON.stringify({ 
          status: 'error', 
          message: 'Email is required' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Get user license data
    const { data: license, error } = await supabaseClient
      .from('licenses')
      .select('*')
      .eq('email', email)
      .single()

    if (error) {
      console.error('License query error:', error)
      return new Response(
        JSON.stringify({ 
          status: 'error', 
          message: 'User license not found' 
        }),
        { 
          status: 404, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Format response data
    const responseData = {
      status: 'success',
      data: {
        email: license.email,
        tier: license.tier,
        credit_balance: parseFloat(license.credit_balance || 0),
        credit_used: parseFloat(license.credit_used || 0),
        is_active: license.is_active,
        is_valid: license.is_active,
        hours_credit: parseFloat(license.credit_balance || 0), // Legacy compatibility
        hours_used: parseFloat(license.credit_used || 0), // Legacy compatibility
        created_at: license.created_at,
        updated_at: license.updated_at
      },
      message: 'License validated successfully',
      timestamp: new Date().toISOString(),
      server_version: '2.0.0-supabase'
    }

    return new Response(
      JSON.stringify(responseData),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('License validation error:', error)
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