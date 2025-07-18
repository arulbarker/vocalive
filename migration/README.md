# StreamMate AI - Supabase Migration Guide

Panduan lengkap untuk migrasi dari VPS server ke Supabase PostgreSQL.

## 🚀 Overview

Migrasi ini akan:
- ✅ Memindahkan database SQLite ke PostgreSQL (Supabase)
- ✅ Mengganti FastAPI endpoints dengan Supabase Edge Functions
- ✅ Update client-side code untuk menggunakan Supabase
- ✅ Mempertahankan semua functionality yang ada
- ✅ Menjaga sistem pembayaran iPaymu tetap berfungsi

## 📋 Prerequisites

1. **Supabase Project**: Sudah setup ✅
   - URL: `https://hpqhywhnddxqvxjzjjwe.supabase.co`
   - Keys: Anon & Service Role keys tersedia

2. **Python Dependencies**:
   ```bash
   pip install supabase python-dotenv
   ```

## 🔧 Migration Steps

### Step 1: Setup Database Schema

1. **Buka Supabase Dashboard**:
   - Go to: https://supabase.com/dashboard
   - Select project: `hpqhywhnddxqvxjzjjwe`
   - Go to SQL Editor

2. **Execute Schema**:
   - Copy content dari `migration/supabase_schema.sql`
   - Paste ke SQL Editor
   - Execute SQL

### Step 2: Migrate Data

1. **Install Dependencies**:
   ```bash
   cd migration
   pip install -r requirements.txt
   ```

2. **Run Migration Script**:
   ```bash
   python migrate_to_supabase.py
   ```

3. **Verify Migration**:
   - Check Supabase Dashboard > Table Editor
   - Verify data count matches SQLite backup

### Step 3: Deploy Edge Functions

1. **Install Supabase CLI**:
   ```bash
   npm install -g supabase
   ```

2. **Login & Link Project**:
   ```bash
   supabase login
   supabase link --project-ref hpqhywhnddxqvxjzjjwe
   ```

3. **Deploy Functions**:
   ```bash
   supabase functions deploy license-validate
   supabase functions deploy credit-update
   supabase functions deploy payment-callback
   ```

### Step 4: Update Client Configuration

1. **Update API Endpoints**:
   - Replace VPS URLs with Supabase URLs
   - Update authentication headers

2. **Test Functionality**:
   - License validation
   - Credit usage tracking
   - Payment processing

## 🗂️ Files Created

### Database & Migration
- `migration/supabase_schema.sql` - PostgreSQL schema
- `migration/migrate_to_supabase.py` - Data migration script
- `migration/requirements.txt` - Python dependencies

### Supabase Edge Functions
- `supabase/functions/license-validate/index.ts` - License validation
- `supabase/functions/credit-update/index.ts` - Credit usage updates
- `supabase/functions/payment-callback/index.ts` - Payment processing

### Client Integration
- `modules_client/supabase_client.py` - Supabase client wrapper
- `config/supabase_config.json` - Supabase configuration

## 🔄 API Endpoint Mapping

| Old VPS Endpoint | New Supabase Endpoint |
|------------------|----------------------|
| `/api/license/validate` | `/functions/v1/license-validate` |
| `/api/license/update_usage` | `/functions/v1/credit-update` |
| `/api/payment/callback` | `/functions/v1/payment-callback` |
| `/api/health` | Direct table query |

## 📊 Database Schema Comparison

| SQLite Table | PostgreSQL Table | Changes |
|--------------|------------------|---------|
| `licenses` | `licenses` | Added UUID primary key, better data types |
| `transaction_history` | `transaction_history` | Added foreign key constraints |
| `credit_usage_history` | `credit_usage_history` | Added indexes for performance |
| `demo_usage` | `demo_usage` | Added proper date handling |

## 🔒 Security Features

- **Row Level Security (RLS)**: Users can only access their own data
- **Service Role**: Admin operations use service role key
- **API Keys**: Separate anon and service role keys
- **CORS**: Properly configured for client access

## 🧪 Testing Checklist

After migration, test these features:

- [ ] User login and authentication
- [ ] License validation
- [ ] Credit balance display
- [ ] Credit usage tracking
- [ ] Payment processing (iPaymu)
- [ ] Transaction history
- [ ] Usage history
- [ ] Demo mode functionality

## 🚨 Rollback Plan

If migration fails:

1. **Revert Client Code**:
   ```bash
   git checkout HEAD~1 modules_client/api.py
   ```

2. **Restore VPS Connection**:
   - Update server URLs back to VPS
   - Restore original API endpoints

3. **Database Backup**:
   - Original SQLite backup available in `streammateai_server/`

## 📞 Support

Jika ada masalah selama migrasi:
1. Check `migration.log` untuk error details
2. Verify Supabase project settings
3. Confirm all Edge Functions deployed correctly
4. Test database connectivity

## 🎉 Post-Migration

Setelah migrasi berhasil:
1. Monitor system performance
2. Verify all payments processed correctly
3. Update documentation
4. Inform users of any changes (if any)

---

**Status**: ✅ Ready for execution
**Estimated Time**: 30-60 minutes
**Risk Level**: Low (with rollback plan) 