#!/usr/bin/env python3
"""
Simple script untuk membuat environment loader
"""

import os

def create_env_loader():
    """Buat script untuk load environment variables"""
    print("🔧 Creating Environment Loader")
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
        print("Environment variables loaded from .env file")
    else:
        print(".env file not found. Using system environment variables.")
    
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
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("All required environment variables are set")
        return True

def get_env_var(var_name, default=None):
    """Get environment variable with default value"""
    return os.getenv(var_name, default)

if __name__ == "__main__":
    load_environment()
'''
    
    with open("env_loader.py", "w", encoding="utf-8") as f:
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
    print("🔧 CREATING ENVIRONMENT LOADER")
    print("=" * 60)
    
    # Create environment loader
    create_env_loader()
    
    # Update requirements
    update_requirements()
    
    print("\n" + "=" * 60)
    print("📊 SETUP COMPLETE")
    print("-" * 30)
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