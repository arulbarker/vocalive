# 🚀 StreamMate AI - Supabase Migration Guide

## 📋 OVERVIEW

This guide provides step-by-step instructions for migrating StreamMate AI from VPS backend to Supabase. The migration includes:

- ✅ Complete database migration to Supabase PostgreSQL
- ✅ Credit system with wallet, basic mode, and pro mode credits
- ✅ Payment processing via Supabase
- ✅ User authentication and session management
- ✅ Demo mode tracking
- ✅ Transaction history and logging

## 🎯 MIGRATION STEPS

### Step 1: Supabase Project Setup

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create new project: `streammate-ai`
   - Note down your project URL and API keys

2. **Update Configuration**
   - Update `config/supabase_config.json` with your credentials:
   ```json
   {
     "url": "https://your-project.supabase.co",
     "anon_key": "your-anon-key",
     "service_role_key": "your-service-role-key",
     "project_id": "your-project-id"
   }
   ```

### Step 2: Database Schema Setup

1. **Run SQL Schema**
   - Copy the contents of `supabase_schema.sql`
   - Go to Supabase Dashboard → SQL Editor
   - Paste and execute the schema

2. **Verify Tables Created**
   - Check that all tables are created:
     - `users`
     - `credit_transactions`
     - `payment_transactions`
     - `demo_usage`
     - `session_tracking`
     - `package_subscriptions`

### Step 3: Update Application Code

1. **Supabase Client Updated** ✅
   - `modules_client/supabase_client.py` - Complete rewrite
   - All methods updated for new credit system

2. **UI Components Updated** ✅
   - `ui/subscription_tab.py` - Updated for Supabase
   - `ui/main_window.py` - Updated for Supabase

3. **Configuration Updated** ✅
   - `config/supabase_config.json` - Updated with correct credentials

### Step 4: Test Migration

1. **Test Credit System**
   ```python
   from modules_client.supabase_client import SupabaseClient
   
   supabase = SupabaseClient()
   
   # Test user creation
   result = supabase.create_user("test@example.com", "Test User")
   print(result)
   
   # Test credit balance
   balance = supabase.get_credit_balance("test@example.com")
   print(balance)
   
   # Test adding credits
   add_result = supabase.add_credits("test@example.com", 1000, "wallet")
   print(add_result)
   ```

2. **Test Package Purchase**
   ```python
   # Test basic package purchase
   purchase = supabase.purchase_mode_credits("test@example.com", "basic", 100000)
   print(purchase)
   ```

## 🔧 CREDIT SYSTEM LOGIC

### Wallet System
- **Wallet Balance**: General credits for top-ups
- **Basic Credits**: Credits allocated for Basic mode features
- **Pro Credits**: Credits allocated for Pro mode features

### Credit Flow
1. **Top-up**: Add credits to wallet
2. **Purchase Mode**: Transfer credits from wallet to mode-specific credits
3. **Usage**: Deduct credits from mode-specific credits during feature usage

### Package Pricing
- **Basic Package**: 100,000 credits (Rp 100,000)
- **Pro Package**: 250,000 credits (Rp 250,000)

## 📊 DATABASE TABLES

### users
- `email`: User email (unique)
- `wallet_balance`: General credit balance
- `basic_credits`: Credits for Basic mode
- `pro_credits`: Credits for Pro mode
- `total_spent`: Total amount spent

### credit_transactions
- `email`: User email
- `transaction_type`: credit_add, credit_deduct, mode_purchase
- `credit_type`: wallet, basic_credits, pro_credits
- `amount`: Transaction amount
- `component`: Feature that used credits

### payment_transactions
- `email`: User email
- `package`: basic, pro, topup
- `amount`: Payment amount
- `credits`: Credits received (1 IDR = 1 Credit)
- `status`: pending, completed, failed

## 🔐 SECURITY FEATURES

### Row Level Security (RLS)
- All tables have RLS enabled
- Users can only access their own data
- Service role key for admin operations

### API Security
- JWT-based authentication
- Rate limiting via Supabase
- Secure API endpoints

## 🧪 TESTING CHECKLIST

### Basic Functionality
- [ ] User registration/login
- [ ] Credit balance display
- [ ] Top-up functionality
- [ ] Package purchase
- [ ] Mode activation (Basic/Pro)
- [ ] Credit usage tracking

### Advanced Features
- [ ] Demo mode tracking
- [ ] Session management
- [ ] Transaction history
- [ ] Payment processing
- [ ] Error handling

### Performance
- [ ] Database query performance
- [ ] API response times
- [ ] Concurrent user handling
- [ ] Data consistency

## 🚨 ROLLBACK PLAN

If migration fails:

1. **Immediate Rollback**
   ```bash
   # Restore VPS configuration
   git checkout HEAD~1 config/supabase_config.json
   git checkout HEAD~1 modules_client/supabase_client.py
   ```

2. **Database Rollback**
   - Restore VPS database from backup
   - Update application to use VPS endpoints

3. **Code Rollback**
   ```bash
   # Revert all Supabase changes
   git reset --hard HEAD~1
   ```

## 📈 MONITORING

### Supabase Dashboard
- Monitor database performance
- Check API usage
- Review error logs
- Track user activity

### Application Logs
- Check `logs/` directory
- Monitor credit transactions
- Track payment processing
- Review error messages

## 🔄 MIGRATION STATUS

### ✅ Completed
- [x] Supabase client implementation
- [x] Database schema design
- [x] Credit system logic
- [x] UI component updates
- [x] Configuration setup

### 🔄 In Progress
- [ ] Database migration execution
- [ ] Payment gateway integration
- [ ] Testing and validation
- [ ] Performance optimization

### ⏳ Pending
- [ ] Production deployment
- [ ] User data migration
- [ ] Monitoring setup
- [ ] Documentation updates

## 📞 SUPPORT

For migration issues:

1. **Check Logs**: Review application and Supabase logs
2. **Test Connectivity**: Verify Supabase connection
3. **Validate Schema**: Ensure all tables are created
4. **Review Permissions**: Check RLS policies

## 🎯 SUCCESS CRITERIA

Migration is successful when:

1. ✅ All credit operations work via Supabase
2. ✅ Payment processing functions correctly
3. ✅ User data is properly secured
4. ✅ Performance meets requirements
5. ✅ Error handling is robust
6. ✅ Monitoring is in place

---

**Note**: This migration completely replaces the VPS backend with Supabase. All data will be stored in Supabase PostgreSQL database with proper security and scalability. 