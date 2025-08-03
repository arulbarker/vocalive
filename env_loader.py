#!/usr/bin/env python3
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
