#!/usr/bin/env python3
"""
Script untuk update kode agar menggunakan environment variables
"""

import os
import re

def update_supabase_client():
    """Update supabase_client.py untuk menggunakan environment variables"""
    print("🔧 Updating supabase_client.py")
    print("=" * 60)
    
    if not os.path.exists("modules_client/supabase_client.py"):
        print("❌ supabase_client.py not found")
        return False
    
    try:
        with open("modules_client/supabase_client.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace hardcoded Supabase URL and key
        old_content = content
        
        # Replace hardcoded URL
        content = re.sub(
            r'SUPABASE_URL\s*=\s*["\'][^"\']+["\']',
            'SUPABASE_URL = os.getenv("SUPABASE_URL", "https://nivwxqojwljihoybzgkc.supabase.co")',
            content
        )
        
        # Replace hardcoded service role key
        content = re.sub(
            r'SERVICE_ROLE_KEY\s*=\s*["\'][^"\']+["\']',
            'SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")',
            content
        )
        
        # Add os import if not present
        if "import os" not in content:
            content = "import os\n" + content
        
        # Write updated content
        with open("modules_client/supabase_client.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        if content != old_content:
            print("✅ supabase_client.py updated successfully!")
            return True
        else:
            print("ℹ️  No changes needed in supabase_client.py")
            return True
            
    except Exception as e:
        print(f"❌ Error updating supabase_client.py: {e}")
        return False

def update_main_py():
    """Update main.py untuk menggunakan environment variables"""
    print("\n🔧 Updating main.py")
    print("=" * 60)
    
    if not os.path.exists("main.py"):
        print("❌ main.py not found")
        return False
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        old_content = content
        
        # Replace hardcoded Stripe keys
        content = re.sub(
            r'stripe\.SecretKey\s*=\s*["\'][^"\']+["\']',
            'stripe.SecretKey = os.getenv("STRIPE_SECRET_KEY")',
            content
        )
        
        content = re.sub(
            r'stripe\.PublishableKey\s*=\s*["\'][^"\']+["\']',
            'stripe.PublishableKey = os.getenv("STRIPE_PUBLISHABLE_KEY")',
            content
        )
        
        # Add os import if not present
        if "import os" not in content:
            # Find the first import line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i, "import os")
                    break
            content = '\n'.join(lines)
        
        # Write updated content
        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        if content != old_content:
            print("✅ main.py updated successfully!")
            return True
        else:
            print("ℹ️  No changes needed in main.py")
            return True
            
    except Exception as e:
        print(f"❌ Error updating main.py: {e}")
        return False

def update_google_oauth():
    """Update google_oauth.py untuk menggunakan environment variables"""
    print("\n🔧 Updating google_oauth.py")
    print("=" * 60)
    
    if not os.path.exists("modules_client/google_oauth.py"):
        print("❌ google_oauth.py not found")
        return False
    
    try:
        with open("modules_client/google_oauth.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        old_content = content
        
        # Replace hardcoded client ID and secret
        content = re.sub(
            r'client_id\s*=\s*["\'][^"\']+["\']',
            'client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")',
            content
        )
        
        content = re.sub(
            r'client_secret\s*=\s*["\'][^"\']+["\']',
            'client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")',
            content
        )
        
        # Add os import if not present
        if "import os" not in content:
            content = "import os\n" + content
        
        # Write updated content
        with open("modules_client/google_oauth.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        if content != old_content:
            print("✅ google_oauth.py updated successfully!")
            return True
        else:
            print("ℹ️  No changes needed in google_oauth.py")
            return True
            
    except Exception as e:
        print(f"❌ Error updating google_oauth.py: {e}")
        return False

def update_ipaymu_handler():
    """Update ipaymu_handler.py untuk menggunakan environment variables"""
    print("\n🔧 Updating ipaymu_handler.py")
    print("=" * 60)
    
    if not os.path.exists("modules_server/ipaymu_handler.py"):
        print("❌ ipaymu_handler.py not found")
        return False
    
    try:
        with open("modules_server/ipaymu_handler.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        old_content = content
        
        # Replace hardcoded API key
        content = re.sub(
            r'api_key\s*=\s*["\'][^"\']+["\']',
            'api_key = os.getenv("IPAYMU_API_KEY")',
            content
        )
        
        # Add os import if not present
        if "import os" not in content:
            content = "import os\n" + content
        
        # Write updated content
        with open("modules_server/ipaymu_handler.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        if content != old_content:
            print("✅ ipaymu_handler.py updated successfully!")
            return True
        else:
            print("ℹ️  No changes needed in ipaymu_handler.py")
            return True
            
    except Exception as e:
        print(f"❌ Error updating ipaymu_handler.py: {e}")
        return False

def create_env_loader():
    """Buat script untuk load environment variables"""
    print("\n🔧 Creating Environment Loader")
    print("=" * 60)
    
    env_loader_content = '''#!/usr/bin/env python3
"""
Environment variables loader for StreamMate AI
"""

import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    # Load .env file if it exists
    if os.path.exists('.env'):
        load_dotenv()
        print("✅ Environment variables loaded from .env file")
    else:
        print("⚠️  .env file not found. Using system environment variables.")
    
    # Required environment variables
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    # Check if required variables are set
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def get_env_var(var_name, default=None):
    """Get environment variable with default value"""
    return os.getenv(var_name, default)

if __name__ == "__main__":
    load_environment()
'''
    
    with open("env_loader.py", "w") as f:
        f.write(env_loader_content)
    
    print("✅ env_loader.py created successfully!")

def update_requirements():
    """Update requirements.txt untuk include python-dotenv"""
    print("\n🔧 Updating requirements.txt")
    print("=" * 60)
    
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        # Check if python-dotenv is already included
        if "python-dotenv" not in content:
            with open("requirements.txt", "a") as f:
                f.write("\npython-dotenv==1.0.0\n")
            print("✅ Added python-dotenv to requirements.txt")
        else:
            print("ℹ️  python-dotenv already in requirements.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating requirements.txt: {e}")
        return False

def main():
    """Main function"""
    print("🔧 UPDATING CODE FOR ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    # Update all files
    files_updated = 0
    
    if update_supabase_client():
        files_updated += 1
    
    if update_main_py():
        files_updated += 1
    
    if update_google_oauth():
        files_updated += 1
    
    if update_ipaymu_handler():
        files_updated += 1
    
    # Create environment loader
    create_env_loader()
    files_updated += 1
    
    # Update requirements
    if update_requirements():
        files_updated += 1
    
    print("\n" + "=" * 60)
    print("📊 UPDATE SUMMARY")
    print("-" * 30)
    print(f"✅ Files updated: {files_updated}")
    print("✅ Environment loader created")
    print("✅ Requirements updated")
    
    print("\n📋 NEXT STEPS:")
    print("-" * 30)
    print("1. Install python-dotenv: pip install python-dotenv")
    print("2. Test application functionality")
    print("3. Verify all credentials work")
    print("4. Commit security improvements")

if __name__ == "__main__":
    main() 