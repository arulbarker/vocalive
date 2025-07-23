// Supabase Edge Function: Credit Update
// Path: supabase/functions/credit-update/index.ts

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
    const { 
      email, 
      credits_used, 
      sync_type = 'manual', 
      component = 'client',
      description = '',
      credit_type = 'wallet'
    } = await req.json()

    if (!email || credits_used === undefined) {
      return new Response(
        JSON.stringify({ error: 'Email and credits_used are required' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Get current user data
    const { data: userData, error: userError } = await supabaseClient
      .from('users')
      .select('*')
      .eq('email', email)
      .single()

    if (userError) {
      return new Response(
        JSON.stringify({ error: 'User not found', details: userError }),
        { 
          status: 404, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Check if user has enough credits
    const currentBalance = parseFloat(userData[`${credit_type}_credits`] || 0)
    
    if (currentBalance < credits_used) {
      return new Response(
        JSON.stringify({ 
          error: 'Insufficient credits',
          current_balance: currentBalance,
          requested_amount: credits_used
        }),
        { 
          status: 402, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Calculate new balance
    const newBalance = currentBalance - credits_used

    // Update user credits
    const { error: updateError } = await supabaseClient
      .from('users')
      .update({
        [`${credit_type}_credits`]: newBalance,
        updated_at: new Date().toISOString()
      })
      .eq('email', email)

    if (updateError) {
      return new Response(
        JSON.stringify({ error: 'Failed to update credits', details: updateError }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Log transaction
    const { error: logError } = await supabaseClient
      .from('credit_transactions')
      .insert({
        email: email,
        transaction_type: 'credit_deduct',
        credit_type: credit_type,
        amount: credits_used,
        is_deduction: true,
        component: component,
        description: description || `Sync from client: ${sync_type}`
      })

    if (logError) {
      console.error('Failed to log transaction:', logError)
      // Don't fail the request if logging fails
    }

    return new Response(
      JSON.stringify({
        status: 'success',
        message: 'Credits updated successfully',
        data: {
          email: email,
          credit_type: credit_type,
          credits_used: credits_used,
          previous_balance: currentBalance,
          new_balance: newBalance,
          component: component,
          sync_type: sync_type
        }
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