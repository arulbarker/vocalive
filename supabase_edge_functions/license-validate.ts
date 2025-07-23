// Supabase Edge Function: License Validation
// Path: supabase/functions/license-validate/index.ts

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
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    )

    // Parse request body
    const { email, hardware_id } = await req.json()

    if (!email) {
      return new Response(
        JSON.stringify({ error: 'Email is required' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Get user data from database
    const { data: userData, error: userError } = await supabaseClient
      .from('users')
      .select('*')
      .eq('email', email)
      .single()

    if (userError && userError.code !== 'PGRST116') {
      return new Response(
        JSON.stringify({ error: 'Database error', details: userError }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // If user doesn't exist, create new user
    if (!userData) {
      const { data: newUser, error: createError } = await supabaseClient
        .from('users')
        .insert({
          email: email,
          name: email.split('@')[0],
          wallet_balance: 0,
          basic_credits: 0,
          pro_credits: 0
        })
        .select()
        .single()

      if (createError) {
        return new Response(
          JSON.stringify({ error: 'Failed to create user', details: createError }),
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify({
          is_valid: false,
          tier: 'none',
          message: 'New user created',
          source: 'supabase_edge',
          hours_credit: 0.0,
          wallet_balance: 0,
          basic_credits: 0,
          pro_credits: 0
        }),
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Determine tier based on credits
    const wallet_balance = parseFloat(userData.wallet_balance || 0)
    const basic_credits = parseFloat(userData.basic_credits || 0)
    const pro_credits = parseFloat(userData.pro_credits || 0)

    let tier = 'none'
    let available_credits = 0

    if (pro_credits > 0) {
      tier = 'pro'
      available_credits = pro_credits
    } else if (basic_credits > 0) {
      tier = 'basic'
      available_credits = basic_credits
    }

    return new Response(
      JSON.stringify({
        is_valid: available_credits > 0,
        tier: tier,
        message: 'License validated via Supabase Edge Function',
        source: 'supabase_edge',
        hours_credit: available_credits,
        wallet_balance: wallet_balance,
        basic_credits: basic_credits,
        pro_credits: pro_credits
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
}) 