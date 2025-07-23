#!/bin/bash

# StreamMate AI - Supabase Edge Functions Deployment Script

echo "🚀 Deploying StreamMate AI Edge Functions to Supabase..."

# Set Supabase project details
PROJECT_ID="nivwxqojwljihoybzgkc"
SUPABASE_URL="https://nivwxqojwljihoybzgkc.supabase.co"

# Check if supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install it first:"
    echo "npm install -g supabase"
    exit 1
fi

# Login to Supabase (if not already logged in)
echo "🔐 Checking Supabase login status..."
supabase status --project-ref $PROJECT_ID > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️ Not logged in to Supabase. Please run:"
    echo "supabase login"
    exit 1
fi

echo "✅ Logged in to Supabase"

# Deploy Edge Functions
echo "📦 Deploying Edge Functions..."

# Deploy license-validate function
echo "🔧 Deploying license-validate function..."
supabase functions deploy license-validate --project-ref $PROJECT_ID
if [ $? -eq 0 ]; then
    echo "✅ license-validate deployed successfully"
else
    echo "❌ Failed to deploy license-validate"
    exit 1
fi

# Deploy credit-update function
echo "🔧 Deploying credit-update function..."
supabase functions deploy credit-update --project-ref $PROJECT_ID
if [ $? -eq 0 ]; then
    echo "✅ credit-update deployed successfully"
else
    echo "❌ Failed to deploy credit-update"
    exit 1
fi

# Deploy config-get function
echo "🔧 Deploying config-get function..."
supabase functions deploy config-get --project-ref $PROJECT_ID
if [ $? -eq 0 ]; then
    echo "✅ config-get deployed successfully"
else
    echo "❌ Failed to deploy config-get"
    exit 1
fi

echo ""
echo "🎉 All Edge Functions deployed successfully!"
echo ""
echo "📋 Deployed Functions:"
echo "  • license-validate: https://$PROJECT_ID.supabase.co/functions/v1/license-validate"
echo "  • credit-update: https://$PROJECT_ID.supabase.co/functions/v1/credit-update"
echo "  • config-get: https://$PROJECT_ID.supabase.co/functions/v1/config-get"
echo ""
echo "🔧 Next Steps:"
echo "1. Run the configuration migration script"
echo "2. Update application to use Supabase config"
echo "3. Test all functionality"
echo "4. Remove VPS dependencies" 