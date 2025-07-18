import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    const { email, credits_used, sync_type, component, description } = await req.json()

    if (!email || !credits_used) {
      return new Response(
        JSON.stringify({ 
          status: 'error', 
          message: 'Email and credits_used are required' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Get current license
    const { data: license, error: licenseError } = await supabaseClient
      .from('licenses')
      .select('*')
      .eq('email', email)
      .single()

    if (licenseError) {
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

    const currentBalance = parseFloat(license.credit_balance || 0)
    const creditsToDeduct = parseFloat(credits_used)

    // Check if sufficient balance
    if (currentBalance < creditsToDeduct) {
      return new Response(
        JSON.stringify({ 
          status: 'error', 
          message: 'Insufficient credit balance' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Update license with new balance
    const newBalance = currentBalance - creditsToDeduct
    const newUsed = parseFloat(license.credit_used || 0) + creditsToDeduct

    const { error: updateError } = await supabaseClient
      .from('licenses')
      .update({
        credit_balance: newBalance,
        credit_used: newUsed,
        updated_at: new Date().toISOString()
      })
      .eq('email', email)

    if (updateError) {
      console.error('Credit update error:', updateError)
      return new Response(
        JSON.stringify({ 
          status: 'error', 
          message: 'Failed to update credits' 
        }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Log usage history
    const { error: historyError } = await supabaseClient
      .from('credit_usage_history')
      .insert({
        email,
        credit_deducted: creditsToDeduct,
        component: component || 'client_usage_sync',
        description: description || `Sync from client: ${sync_type}`,
        created_at: new Date().toISOString()
      })

    if (historyError) {
      console.error('Usage history error:', historyError)
      // Don't fail the request, just log the error
    }

    return new Response(
      JSON.stringify({
        status: 'success',
        data: {
          email,
          credits_deducted: creditsToDeduct,
          new_balance: newBalance,
          total_used: newUsed
        },
        message: 'Credits updated successfully',
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Credit update error:', error)
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