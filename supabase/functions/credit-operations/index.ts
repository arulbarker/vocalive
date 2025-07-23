// Credit Operations Edge Function
// Handles credit wallet operations for StreamMate AI

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface CreditBalanceRequest {
  email: string
}

interface CreditDeductRequest {
  email: string
  amount: number
  component: string
  description?: string
  session_id?: string
  source_type?: 'wallet' | 'basic' | 'pro'
}

interface CreditTopupRequest {
  email: string
  amount: number
  payment_method: string
  payment_reference: string
  description?: string
}

interface ModePurchaseRequest {
  email: string
  mode_type: 'basic' | 'pro'
  package_price: number
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const { pathname } = new URL(req.url)
    const path = pathname.split('/').pop()

    // Route to appropriate handler
    switch (path) {
      case 'balance':
        return await handleGetBalance(req, supabase)
      
      case 'deduct':
        return await handleDeductCredit(req, supabase)
      
      case 'topup':
        return await handleTopupCredit(req, supabase)
      
      case 'purchase-mode':
        return await handlePurchaseMode(req, supabase)
      
      case 'history':
        return await handleGetHistory(req, supabase)
      
      default:
        return new Response(
          JSON.stringify({ error: 'Invalid endpoint' }),
          { 
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          }
        )
    }
  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

async function handleGetBalance(req: Request, supabase: any) {
  const { email }: CreditBalanceRequest = await req.json()
  
  if (!email) {
    return new Response(
      JSON.stringify({ error: 'Email is required' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  // Get user credit summary
  const { data: summary, error } = await supabase
    .from('user_credit_summary')
    .select('*')
    .eq('email', email)
    .single()

  if (error && error.code !== 'PGRST116') { // PGRST116 = no rows returned
    throw error
  }

  if (!summary) {
    // User doesn't exist, return zero balances
    return new Response(
      JSON.stringify({
        status: 'success',
        data: {
          email,
          wallet_balance: 0,
          basic_credits: 0,
          pro_credits: 0,
          total_balance: 0,
          status: 'no_credit'
        }
      }),
      { 
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  const totalBalance = summary.wallet_balance + summary.basic_credits + summary.pro_credits

  return new Response(
    JSON.stringify({
      status: 'success',
      data: {
        email: summary.email,
        wallet_balance: summary.wallet_balance,
        basic_credits: summary.basic_credits,
        pro_credits: summary.pro_credits,
        total_balance: totalBalance,
        total_topup: summary.total_topup,
        total_spent: summary.total_spent,
        status: totalBalance > 0 ? 'active' : 'no_credit',
        last_updated: summary.last_updated
      }
    }),
    { 
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}

async function handleDeductCredit(req: Request, supabase: any) {
  const request: CreditDeductRequest = await req.json()
  const { email, amount, component, description, session_id, source_type = 'wallet' } = request

  if (!email || !amount || !component) {
    return new Response(
      JSON.stringify({ error: 'Email, amount, and component are required' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  if (amount <= 0) {
    return new Response(
      JSON.stringify({ error: 'Amount must be positive' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  // Get user
  const { data: user, error: userError } = await supabase
    .from('users')
    .select('id')
    .eq('email', email)
    .single()

  if (userError || !user) {
    return new Response(
      JSON.stringify({ error: 'User not found' }),
      { 
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  // Check balance based on source type
  let balanceCheck
  let updateQuery
  
  if (source_type === 'wallet') {
    // Check wallet balance
    const { data: wallet } = await supabase
      .from('wallets')
      .select('id, balance')
      .eq('user_id', user.id)
      .single()

    if (!wallet || wallet.balance < amount) {
      return new Response(
        JSON.stringify({ 
          error: 'Insufficient wallet balance',
          current_balance: wallet?.balance || 0,
          required: amount
        }),
        { 
          status: 402,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Deduct from wallet
    const { error: deductError } = await supabase
      .from('wallets')
      .update({ 
        balance: wallet.balance - amount,
        total_spent: supabase.raw('total_spent + ?', [amount])
      })
      .eq('id', wallet.id)

    if (deductError) throw deductError

    balanceCheck = { balance_before: wallet.balance, balance_after: wallet.balance - amount }
    
  } else {
    // Check mode credits
    const { data: modeCredit } = await supabase
      .from('mode_credits')
      .select('id, credit_balance')
      .eq('user_id', user.id)
      .eq('mode_type', source_type)
      .single()

    if (!modeCredit || modeCredit.credit_balance < amount) {
      return new Response(
        JSON.stringify({ 
          error: `Insufficient ${source_type} credits`,
          current_balance: modeCredit?.credit_balance || 0,
          required: amount
        }),
        { 
          status: 402,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Deduct from mode credits
    const { error: deductError } = await supabase
      .from('mode_credits')
      .update({ 
        credit_balance: modeCredit.credit_balance - amount,
        credit_used: supabase.raw('credit_used + ?', [amount])
      })
      .eq('id', modeCredit.id)

    if (deductError) throw deductError

    balanceCheck = { balance_before: modeCredit.credit_balance, balance_after: modeCredit.credit_balance - amount }
  }

  // Record usage
  const { error: usageError } = await supabase
    .from('credit_usage')
    .insert({
      user_id: user.id,
      source_type,
      credits_used: amount,
      component,
      description,
      session_id,
      metadata: { 
        timestamp: new Date().toISOString(),
        balance_before: balanceCheck.balance_before,
        balance_after: balanceCheck.balance_after
      }
    })

  if (usageError) throw usageError

  return new Response(
    JSON.stringify({
      status: 'success',
      message: 'Credit deducted successfully',
      data: {
        email,
        deducted: amount,
        remaining_credit: balanceCheck.balance_after,
        previous_credit: balanceCheck.balance_before,
        component,
        source_type,
        timestamp: new Date().toISOString()
      }
    }),
    { 
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}

async function handleTopupCredit(req: Request, supabase: any) {
  const request: CreditTopupRequest = await req.json()
  const { email, amount, payment_method, payment_reference, description } = request

  if (!email || !amount || !payment_method || !payment_reference) {
    return new Response(
      JSON.stringify({ error: 'Missing required fields' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  if (amount <= 0) {
    return new Response(
      JSON.stringify({ error: 'Amount must be positive' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  // Call the database function
  const { data, error } = await supabase
    .rpc('add_wallet_credits', {
      p_user_email: email,
      p_amount: amount,
      p_payment_method: payment_method,
      p_payment_reference: payment_reference,
      p_description: description || `Top-up via ${payment_method}`
    })

  if (error) throw error

  return new Response(
    JSON.stringify({
      status: 'success',
      message: 'Credits added successfully',
      data: {
        email,
        amount_added: amount,
        balance_before: data.balance_before,
        balance_after: data.balance_after,
        transaction_id: data.transaction_id
      }
    }),
    { 
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}

async function handlePurchaseMode(req: Request, supabase: any) {
  const request: ModePurchaseRequest = await req.json()
  const { email, mode_type, package_price } = request

  if (!email || !mode_type || !package_price) {
    return new Response(
      JSON.stringify({ error: 'Missing required fields' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  // Define package credits (1 IDR = 1 Credit)
  const packageCredits = {
    'basic': 100000,
    'pro': 250000
  }

  const credits = packageCredits[mode_type]
  if (!credits) {
    return new Response(
      JSON.stringify({ error: 'Invalid mode type' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  // Call the database function
  const { data, error } = await supabase
    .rpc('purchase_mode_credits', {
      p_user_email: email,
      p_mode_type: mode_type,
      p_credits: credits,
      p_price: package_price
    })

  if (error) {
    if (error.message.includes('Insufficient wallet balance')) {
      return new Response(
        JSON.stringify({ 
          status: 'error',
          error: 'Insufficient wallet balance',
          message: 'Please top-up your wallet first'
        }),
        { 
          status: 402,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }
    throw error
  }

  return new Response(
    JSON.stringify({
      status: 'success',
      message: `${mode_type} mode purchased successfully`,
      data: {
        email,
        mode_type,
        credits_purchased: credits,
        price_paid: package_price,
        purchase_id: data.purchase_id
      }
    }),
    { 
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}

async function handleGetHistory(req: Request, supabase: any) {
  const { email, type = 'all', limit = 50 } = await req.json()

  if (!email) {
    return new Response(
      JSON.stringify({ error: 'Email is required' }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  // Get user
  const { data: user } = await supabase
    .from('users')
    .select('id')
    .eq('email', email)
    .single()

  if (!user) {
    return new Response(
      JSON.stringify({ error: 'User not found' }),
      { 
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  let transactions = []
  let usage = []

  if (type === 'all' || type === 'transactions') {
    // Get wallet transactions
    const { data: txData } = await supabase
      .from('wallet_transactions')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(limit)

    transactions = txData || []
  }

  if (type === 'all' || type === 'usage') {
    // Get credit usage
    const { data: usageData } = await supabase
      .from('credit_usage')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(limit)

    usage = usageData || []
  }

  return new Response(
    JSON.stringify({
      status: 'success',
      data: {
        email,
        transactions,
        usage,
        total_transactions: transactions.length,
        total_usage: usage.length
      }
    }),
    { 
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}