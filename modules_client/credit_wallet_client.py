"""
Credit Wallet Client - UI Integration
Client-side manager untuk credit wallet system
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Import server wallet jika dalam development mode
try:
    from modules_server.credit_wallet import get_credit_wallet, get_user_balance, add_user_credits, spend_user_credits
    LOCAL_WALLET_AVAILABLE = True
except ImportError:
    LOCAL_WALLET_AVAILABLE = False

logger = logging.getLogger('StreamMate.CreditWalletClient')

class CreditWalletClient:
    """Client-side credit wallet manager"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id or self._get_current_user_id()
        self.local_mode = self._is_local_mode()
        
        logger.info(f"Credit Wallet Client initialized for {self.user_id} (local_mode: {self.local_mode})")
    
    def _get_current_user_id(self) -> str:
        """Get current user ID from config or generate one"""
        try:
            # Try to get from subscription status
            sub_file = Path("config/subscription_status.json")
            if sub_file.exists():
                with open(sub_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                    if 'user_email' in sub_data:
                        return sub_data['user_email']
            
            # Fallback to default test user
            return "test_user@streammate.dev"
        except Exception as e:
            logger.warning(f"Error getting user ID: {e}")
            return "test_user@streammate.dev"
    
    def _is_local_mode(self) -> bool:
        """Check if running in local development mode"""
        try:
            config_path = Path("config/development_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                return config.get('credit_wallet', {}).get('local_mode', False)
        except:
            pass
        return False
    
    def get_balance(self) -> int:
        """Get current user's credit balance"""
        if self.local_mode and LOCAL_WALLET_AVAILABLE:
            try:
                return get_user_balance(self.user_id)
            except Exception as e:
                logger.error(f"Error getting local balance: {e}")
                return 0
        else:
            # TODO: Implement remote API call
            logger.warning("Remote wallet API not implemented yet")
            return 0
    
    def get_wallet_info(self) -> Dict:
        """Get complete wallet information"""
        if self.local_mode and LOCAL_WALLET_AVAILABLE:
            try:
                wallet = get_credit_wallet()
                return wallet.get_wallet_info(self.user_id)
            except Exception as e:
                logger.error(f"Error getting wallet info: {e}")
                return None
        else:
            # TODO: Implement remote API call
            logger.warning("Remote wallet API not implemented yet")
            return None
    
    def add_credits(self, amount: int, description: str = "Top-up", reference_id: str = None) -> Tuple[bool, str]:
        """Add credits to user wallet"""
        if self.local_mode and LOCAL_WALLET_AVAILABLE:
            try:
                return add_user_credits(self.user_id, amount, description)
            except Exception as e:
                logger.error(f"Error adding credits: {e}")
                return False, f"Error: {str(e)}"
        else:
            # TODO: Implement remote API call
            logger.warning("Remote wallet API not implemented yet")
            return False, "Remote wallet not available"
    
    def spend_credits(self, amount: int, description: str = "Purchase", reference_id: str = None) -> Tuple[bool, str]:
        """Spend credits from user wallet"""
        if self.local_mode and LOCAL_WALLET_AVAILABLE:
            try:
                return spend_user_credits(self.user_id, amount, description)
            except Exception as e:
                logger.error(f"Error spending credits: {e}")
                return False, f"Error: {str(e)}"
        else:
            # TODO: Implement remote API call
            logger.warning("Remote wallet API not implemented yet")
            return False, "Remote wallet not available"
    
    def check_sufficient_balance(self, amount: int) -> Tuple[bool, int]:
        """Check if user has sufficient balance"""
        current_balance = self.get_balance()
        return current_balance >= amount, current_balance
    
    def get_transaction_history(self, limit: int = 50, transaction_type: str = None) -> List[Dict]:
        """Get transaction history"""
        if self.local_mode and LOCAL_WALLET_AVAILABLE:
            try:
                wallet = get_credit_wallet()
                return wallet.get_transaction_history(self.user_id, limit, transaction_type)
            except Exception as e:
                logger.error(f"Error getting transaction history: {e}")
                return []
        else:
            # TODO: Implement remote API call
            logger.warning("Remote wallet API not implemented yet")
            return []
    
    def format_balance(self, balance: int = None) -> str:
        """Format balance for display"""
        if balance is None:
            balance = self.get_balance()
        return f"{balance:,}"
    
    def can_afford(self, amount: int) -> bool:
        """Check if user can afford a purchase"""
        can_afford, _ = self.check_sufficient_balance(amount)
        return can_afford

# Global client instance
_client_instance = None

def get_credit_wallet_client(user_id: str = None) -> CreditWalletClient:
    """Get global credit wallet client instance"""
    global _client_instance
    if _client_instance is None or (user_id and _client_instance.user_id != user_id):
        _client_instance = CreditWalletClient(user_id)
    return _client_instance

# Convenience functions for UI
def get_current_balance() -> int:
    """Get current user's balance"""
    return get_credit_wallet_client().get_balance()

def format_current_balance() -> str:
    """Get formatted current balance"""
    return get_credit_wallet_client().format_balance()

def can_afford_purchase(amount: int) -> bool:
    """Check if current user can afford a purchase"""
    return get_credit_wallet_client().can_afford(amount)

def make_purchase(amount: int, description: str = "Purchase") -> Tuple[bool, str]:
    """Make a purchase using credits"""
    return get_credit_wallet_client().spend_credits(amount, description)

def add_credits_to_wallet(amount: int, description: str = "Top-up") -> Tuple[bool, str]:
    """Add credits to current user's wallet"""
    return get_credit_wallet_client().add_credits(amount, description)

# Credit packages for UI - RASIO 1:1 (1 Rupiah = 1 Credit)
CREDIT_PACKAGES = [
    {
        "id": "starter",
        "name": "🎯 Starter Pack",
        "price_idr": 50000,
        "credits": 50000,
        "bonus": 0,
        "total_credits": 50000,
        "description": "Good for: Basic mode testing",
        "popular": False
    },
    {
        "id": "regular", 
        "name": "🚀 Regular Pack",
        "price_idr": 100000,
        "credits": 100000,
        "bonus": 0,
        "total_credits": 100000,
        "description": "Good for: Basic mode + some upgrades",
        "popular": True
    }
]

def get_credit_packages() -> List[Dict]:
    """Get available credit packages"""
    return CREDIT_PACKAGES

def get_package_by_id(package_id: str) -> Optional[Dict]:
    """Get credit package by ID"""
    for package in CREDIT_PACKAGES:
        if package["id"] == package_id:
            return package
    return None 