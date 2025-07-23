#!/usr/bin/env python3
"""
StreamMate AI - Database Migration Script
Migrate from SQLite (VPS backup) to Supabase PostgreSQL
"""

import os
import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StreamMateSupabaseMigration:
    """Migration handler for StreamMate AI to Supabase"""
    
    def __init__(self):
        self.config = self.load_supabase_config()
        self.supabase: Client = create_client(
            self.config['url'],
            self.config['service_role_key']
        )
        self.sqlite_db_path = Path("../streammateai_server/data/license_data.db")
        self.billing_db_path = Path("../streammateai_server/billing_security.db")
        
        logger.info(f"🚀 StreamMate AI Migration initialized")
        logger.info(f"📊 Supabase URL: {self.config['url']}")
        logger.info(f"📁 SQLite DB: {self.sqlite_db_path}")
        
    def load_supabase_config(self) -> Dict[str, str]:
        """Load Supabase configuration"""
        config_path = Path("../config/supabase_config.json")
        if not config_path.exists():
            raise FileNotFoundError(f"Supabase config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def test_supabase_connection(self) -> bool:
        """Test connection to Supabase"""
        try:
            # Test with a simple query
            result = self.supabase.table('licenses').select('*').limit(1).execute()
            logger.info("✅ Supabase connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    def create_database_schema(self) -> bool:
        """Create database schema in Supabase"""
        try:
            schema_path = Path("supabase_schema.sql")
            if not schema_path.exists():
                logger.error(f"Schema file not found: {schema_path}")
                return False
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            # Note: Supabase client doesn't support raw SQL execution
            # This needs to be done via Supabase Dashboard SQL Editor
            logger.info("📋 Please execute the schema SQL in Supabase Dashboard:")
            logger.info("1. Go to Supabase Dashboard > SQL Editor")
            logger.info("2. Copy and paste the content from supabase_schema.sql")
            logger.info("3. Execute the SQL")
            logger.info("4. Return here and press Enter to continue...")
            
            input("Press Enter after executing schema in Supabase Dashboard...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return False
    
    def migrate_licenses_data(self) -> bool:
        """Migrate licenses data from SQLite to Supabase"""
        try:
            if not self.sqlite_db_path.exists():
                logger.warning(f"SQLite database not found: {self.sqlite_db_path}")
                return False
            
            # Connect to SQLite
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get licenses data
            cursor.execute("SELECT * FROM licenses")
            licenses_data = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(licenses)")
            columns = [col[1] for col in cursor.fetchall()]
            
            logger.info(f"📊 Found {len(licenses_data)} licenses to migrate")
            
            # Convert to list of dictionaries
            licenses_list = []
            for row in licenses_data:
                license_dict = dict(zip(columns, row))
                
                # Convert SQLite data types to PostgreSQL compatible
                if 'created_at' in license_dict and license_dict['created_at']:
                    try:
                        license_dict['created_at'] = datetime.fromisoformat(license_dict['created_at']).isoformat()
                    except:
                        license_dict['created_at'] = datetime.now().isoformat()
                else:
                    license_dict['created_at'] = datetime.now().isoformat()
                
                if 'updated_at' in license_dict and license_dict['updated_at']:
                    try:
                        license_dict['updated_at'] = datetime.fromisoformat(license_dict['updated_at']).isoformat()
                    except:
                        license_dict['updated_at'] = datetime.now().isoformat()
                else:
                    license_dict['updated_at'] = datetime.now().isoformat()
                
                # Remove SQLite auto-increment ID (PostgreSQL will use UUID)
                if 'id' in license_dict:
                    del license_dict['id']
                
                licenses_list.append(license_dict)
            
            # Insert into Supabase
            if licenses_list:
                result = self.supabase.table('licenses').insert(licenses_list).execute()
                logger.info(f"✅ Successfully migrated {len(licenses_list)} licenses")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Licenses migration failed: {e}")
            return False
    
    def migrate_transaction_history(self) -> bool:
        """Migrate transaction history from SQLite to Supabase"""
        try:
            if not self.sqlite_db_path.exists():
                logger.warning(f"SQLite database not found: {self.sqlite_db_path}")
                return False
            
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get transaction history data
            cursor.execute("SELECT * FROM transaction_history")
            transactions_data = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(transaction_history)")
            columns = [col[1] for col in cursor.fetchall()]
            
            logger.info(f"📊 Found {len(transactions_data)} transactions to migrate")
            
            # Convert to list of dictionaries
            transactions_list = []
            for row in transactions_data:
                transaction_dict = dict(zip(columns, row))
                
                # Convert timestamps
                if 'created_at' in transaction_dict and transaction_dict['created_at']:
                    try:
                        transaction_dict['created_at'] = datetime.fromisoformat(transaction_dict['created_at']).isoformat()
                    except:
                        transaction_dict['created_at'] = datetime.now().isoformat()
                else:
                    transaction_dict['created_at'] = datetime.now().isoformat()
                
                # Remove SQLite auto-increment ID
                if 'id' in transaction_dict:
                    del transaction_dict['id']
                
                transactions_list.append(transaction_dict)
            
            # Insert into Supabase
            if transactions_list:
                result = self.supabase.table('transaction_history').insert(transactions_list).execute()
                logger.info(f"✅ Successfully migrated {len(transactions_list)} transactions")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Transaction history migration failed: {e}")
            return False
    
    def migrate_credit_usage_history(self) -> bool:
        """Migrate credit usage history from SQLite to Supabase"""
        try:
            if not self.sqlite_db_path.exists():
                logger.warning(f"SQLite database not found: {self.sqlite_db_path}")
                return False
            
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get credit usage history data
            cursor.execute("SELECT * FROM credit_usage_history")
            usage_data = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(credit_usage_history)")
            columns = [col[1] for col in cursor.fetchall()]
            
            logger.info(f"📊 Found {len(usage_data)} usage records to migrate")
            
            # Convert to list of dictionaries
            usage_list = []
            for row in usage_data:
                usage_dict = dict(zip(columns, row))
                
                # Convert timestamps
                if 'created_at' in usage_dict and usage_dict['created_at']:
                    try:
                        usage_dict['created_at'] = datetime.fromisoformat(usage_dict['created_at']).isoformat()
                    except:
                        usage_dict['created_at'] = datetime.now().isoformat()
                else:
                    usage_dict['created_at'] = datetime.now().isoformat()
                
                # Remove SQLite auto-increment ID
                if 'id' in usage_dict:
                    del usage_dict['id']
                
                usage_list.append(usage_dict)
            
            # Insert into Supabase in batches (PostgreSQL has limits)
            batch_size = 100
            for i in range(0, len(usage_list), batch_size):
                batch = usage_list[i:i+batch_size]
                result = self.supabase.table('credit_usage_history').insert(batch).execute()
                logger.info(f"✅ Migrated batch {i//batch_size + 1}: {len(batch)} records")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Credit usage history migration failed: {e}")
            return False
    
    def migrate_billing_security_data(self) -> bool:
        """Migrate billing security data from SQLite to Supabase"""
        try:
            if not self.billing_db_path.exists():
                logger.warning(f"Billing database not found: {self.billing_db_path}")
                return True  # Not critical, continue
            
            conn = sqlite3.connect(self.billing_db_path)
            cursor = conn.cursor()
            
            # Migrate demo_usage table
            try:
                cursor.execute("SELECT * FROM demo_usage")
                demo_data = cursor.fetchall()
                
                cursor.execute("PRAGMA table_info(demo_usage)")
                columns = [col[1] for col in cursor.fetchall()]
                
                demo_list = []
                for row in demo_data:
                    demo_dict = dict(zip(columns, row))
                    
                    # Convert timestamps
                    for time_field in ['last_demo_time', 'created_at']:
                        if time_field in demo_dict and demo_dict[time_field]:
                            try:
                                demo_dict[time_field] = datetime.fromisoformat(demo_dict[time_field]).isoformat()
                            except:
                                demo_dict[time_field] = datetime.now().isoformat()
                    
                    # Remove SQLite auto-increment ID
                    if 'id' in demo_dict:
                        del demo_dict['id']
                    
                    demo_list.append(demo_dict)
                
                if demo_list:
                    result = self.supabase.table('demo_usage').insert(demo_list).execute()
                    logger.info(f"✅ Successfully migrated {len(demo_list)} demo usage records")
                
            except Exception as e:
                logger.warning(f"⚠️ Demo usage migration failed: {e}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Billing security migration failed: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify migration success"""
        try:
            # Check licenses count
            licenses_result = self.supabase.table('licenses').select('*').execute()
            licenses_count = len(licenses_result.data)
            
            # Check transactions count
            transactions_result = self.supabase.table('transaction_history').select('*').execute()
            transactions_count = len(transactions_result.data)
            
            # Check usage history count
            usage_result = self.supabase.table('credit_usage_history').select('*').execute()
            usage_count = len(usage_result.data)
            
            logger.info(f"📊 Migration Verification Results:")
            logger.info(f"   Licenses: {licenses_count} records")
            logger.info(f"   Transactions: {transactions_count} records")
            logger.info(f"   Usage History: {usage_count} records")
            
            # Check if we have data
            if licenses_count > 0:
                logger.info("✅ Migration verification successful")
                return True
            else:
                logger.warning("⚠️ No licenses found after migration")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    def run_full_migration(self) -> bool:
        """Run complete migration process"""
        logger.info("🚀 Starting StreamMate AI Migration to Supabase")
        
        # Step 1: Test connection
        if not self.test_supabase_connection():
            logger.error("❌ Cannot connect to Supabase. Please check configuration.")
            return False
        
        # Step 2: Create schema (manual step)
        if not self.create_database_schema():
            logger.error("❌ Schema creation failed")
            return False
        
        # Step 3: Migrate data
        steps = [
            ("Licenses", self.migrate_licenses_data),
            ("Transaction History", self.migrate_transaction_history),
            ("Credit Usage History", self.migrate_credit_usage_history),
            ("Billing Security", self.migrate_billing_security_data),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 Migrating {step_name}...")
            if not step_func():
                logger.error(f"❌ {step_name} migration failed")
                return False
        
        # Step 4: Verify migration
        if not self.verify_migration():
            logger.error("❌ Migration verification failed")
            return False
        
        logger.info("🎉 Migration completed successfully!")
        return True

def main():
    """Main migration function"""
    try:
        migration = StreamMateSupabaseMigration()
        success = migration.run_full_migration()
        
        if success:
            print("\n🎉 StreamMate AI successfully migrated to Supabase!")
            print("📋 Next steps:")
            print("1. Update client configuration to use Supabase")
            print("2. Create Supabase Edge Functions")
            print("3. Test all functionality")
        else:
            print("\n❌ Migration failed. Check migration.log for details.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 