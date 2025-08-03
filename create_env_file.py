#!/usr/bin/env python3
"""
Script untuk membuat .env file dan mengamankan kredensial
"""

import os

def create_env_template():
    """Buat template .env file"""
    print("🔐 Creating .env Template")
    print("=" * 60)
    
    env_content = """# ============================================
# STREAMMATE AI ENVIRONMENT VARIABLES
# ============================================

# Supabase Configuration
SUPABASE_URL=https://nivwxqojwljihoybzgkc.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret_here

# Payment Gateway Configuration
STRIPE_SECRET_KEY=your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here
IPAYMU_API_KEY=your_ipaymu_api_key_here

# Application Configuration
APP_ENV=development
DEBUG_MODE=true
LOG_LEVEL=INFO

# Security Configuration
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# Database Configuration
DATABASE_URL=your_database_url_here

# External APIs
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CLOUD_API_KEY=your_google_cloud_api_key_here

# ============================================
# INSTRUCTIONS:
# 1. Copy this template to .env file
# 2. Replace 'your_*_here' with real values
# 3. Never commit .env file to git
# 4. Keep .env file secure
# ============================================
"""
    
    # Write to .env.template
    with open(".env.template", "w") as f:
        f.write(env_content)
    
    print("✅ .env.template created successfully!")
    print("📋 Next steps:")
    print("   1. Copy .env.template to .env")
    print("   2. Fill in real credentials")
    print("   3. Add .env to .gitignore")
    print("   4. Never commit .env file")

def create_gitignore_entry():
    """Tambah .env ke .gitignore"""
    print("\n📝 Adding .env to .gitignore")
    print("=" * 60)
    
    gitignore_content = """
# Environment Variables
.env
.env.local
.env.production
.env.staging

# Credentials
*.key
*.pem
*.p12
*.pfx

# Configuration files with secrets
config/*.json
config/*.key
config/*.pem

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.temp
temp/
tmp/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
"""
    
    # Check if .gitignore exists
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            existing_content = f.read()
        
        # Add new content if not already present
        if ".env" not in existing_content:
            with open(".gitignore", "a") as f:
                f.write(gitignore_content)
            print("✅ Added security entries to .gitignore")
        else:
            print("✅ .gitignore already contains security entries")
    else:
        # Create new .gitignore
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore with security entries")

def provide_security_instructions():
    """Beri instruksi keamanan"""
    print("\n🛡️ Security Instructions")
    print("=" * 60)
    
    print("📋 CRITICAL SECURITY STEPS:")
    print("-" * 40)
    
    print("1. 🔐 CREATE .env FILE:")
    print("   cp .env.template .env")
    print("   # Edit .env with real credentials")
    
    print("\n2. 🚫 PROTECT CREDENTIALS:")
    print("   - Never commit .env file")
    print("   - Use environment variables in code")
    print("   - Rotate keys regularly")
    
    print("\n3. 🔧 UPDATE CODE:")
    print("   - Replace hardcoded keys with os.getenv()")
    print("   - Use config files for non-sensitive data")
    print("   - Implement proper error handling")
    
    print("\n4. 📊 MONITORING:")
    print("   - Set up alerts for unauthorized access")
    print("   - Monitor API usage patterns")
    print("   - Regular security audits")

def main():
    """Main function"""
    print("🔐 CREDENTIALS SECURITY SETUP")
    print("=" * 60)
    
    # Create environment template
    create_env_template()
    
    # Update gitignore
    create_gitignore_entry()
    
    # Provide instructions
    provide_security_instructions()
    
    print("\n" + "=" * 60)
    print("🎯 SECURITY SETUP COMPLETE")
    print("-" * 30)
    
    print("✅ CREATED:")
    print("   • .env.template file")
    print("   • Updated .gitignore")
    print("   • Security instructions")
    
    print("\n📋 NEXT STEPS:")
    print("1. Copy .env.template to .env")
    print("2. Fill in real credentials")
    print("3. Update code to use environment variables")
    print("4. Test all functionality")
    print("5. Commit security improvements")

if __name__ == "__main__":
    main() 