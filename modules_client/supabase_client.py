#!/usr/bin/env python3
"""
StreamMate AI - Supabase Client Wrapper
Complete replacement for VPS server communication using Supabase
"""

import json
import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import hashlib
import hmac

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Complete Supabase client for StreamMate AI"""
    
    def __init__(self):
        self.config = self._load_config()
        self.base_url = self.config['url']
        self.anon_key = self.config['anon_key']
        self.service_role_key = self.config['service_role_key']
        
        # Headers for API requests
        self.headers = {
            'apikey': self.anon_key,
            'Authorization': f'Bearer {self.anon_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Service role headers (for admin operations)
        self.service_headers = {
            'apikey': self.service_role_key,
            'Authorization': f'Bearer {self.service_role_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        logger.info(f"🚀 Supabase client initialized: {self.base_url}")
    
    def _load_config(self) -> Dict[str, str]:
        """Load Supabase configuration"""
        config_path = Path("config/supabase_config.json")
        if not config_path.exists():
            raise FileNotFoundError(f"Supabase config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, use_service_role: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Supabase"""
        headers = self.service_headers if use_service_role else self.headers
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Supabase request failed: {e}")
            raise
    
    def validate_license(self, email: str, hardware_id: str = None) -> Dict[str, Any]:
        """Validate user license and get credit balance"""
        try:
            # Get user data from Supabase
            user_data = self.get_user_data(email)
            
            if not user_data:
                return {
                    "is_valid": False,
                    "tier": "none",
                    "message": "User not found",
                    "source": "supabase",
                    "hours_credit": 0.0
                }
            
            # Check wallet balance
            wallet_balance = float(user_data.get("wallet_balance", 0))
            basic_credits = float(user_data.get("basic_credits", 0))
            pro_credits = float(user_data.get("pro_credits", 0))
            
            # Determine tier based on credits
            if pro_credits > 0:
                tier = "pro"
                available_credits = pro_credits
            elif basic_credits > 0:
                tier = "basic"
                available_credits = basic_credits
            else:
                tier = "none"
                available_credits = 0
            
            return {
                "is_valid": available_credits > 0,
                "tier": tier,
                "message": "License validated via Supabase",
                "source": "supabase",
                "hours_credit": available_credits,
                "wallet_balance": wallet_balance,
                "basic_credits": basic_credits,
                "pro_credits": pro_credits
            }
            
        except Exception as e:
            logger.error(f"License validation failed: {e}")
            return {
                "is_valid": False,
                "tier": "none",
                "message": f"License validation failed: {str(e)}",
                "source": "supabase_error",
                "hours_credit": 0.0
            }
    
    def get_credit_balance(self, email: str) -> Dict[str, Any]:
        """Get complete credit balance for user"""
        try:
            user_data = self.get_user_data(email)
            
            if not user_data:
                return {
                    "status": "error",
                    "message": "User not found",
                    "data": {
                        "email": email,
                        "wallet_balance": 0,
                        "basic_credits": 0,
                        "pro_credits": 0,
                        "total_credits": 0
                    }
                }
            
            wallet_balance = float(user_data.get("wallet_balance", 0))
            basic_credits = float(user_data.get("basic_credits", 0))
            pro_credits = float(user_data.get("pro_credits", 0))
            total_credits = wallet_balance + basic_credits + pro_credits
            
            return {
                "status": "success",
                "message": "Credit balance retrieved",
                "data": {
                    "email": email,
                    "wallet_balance": wallet_balance,
                    "basic_credits": basic_credits,
                    "pro_credits": pro_credits,
                    "total_credits": total_credits,
                    "last_updated": user_data.get("updated_at", datetime.now().isoformat())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get credit balance: {e}")
            return {
                "status": "error",
                "message": f"Failed to get credit balance: {str(e)}",
                "data": {
                    "email": email,
                    "wallet_balance": 0,
                    "basic_credits": 0,
                    "pro_credits": 0,
                    "total_credits": 0
                }
            }
    
    def get_user_data(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user data from Supabase"""
        try:
            response = self._make_request(
                'GET',
                f"/rest/v1/users?email=eq.{email}",
                use_service_role=True
            )
            
            if response and len(response) > 0:
                return response[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user data: {e}")
            return None
    
    def create_user(self, email: str, name: str = None) -> Dict[str, Any]:
        """Create new user in Supabase"""
        try:
            user_data = {
                "email": email,
                "name": name or email.split('@')[0],
                "wallet_balance": 0,
                "basic_credits": 0,
                "pro_credits": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self._make_request(
                'POST',
                '/rest/v1/users',
                user_data,
                use_service_role=True
            )
            
            return {
                "status": "success",
                "message": "User created successfully",
                "data": response[0] if response else user_data
            }
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return {
                "status": "error",
                "message": f"Failed to create user: {str(e)}"
            }
    
    def add_credits(self, email: str, amount: float, credit_type: str = "wallet", 
                   order_id: str = None, description: str = None) -> Dict[str, Any]:
        """Add credits to user account"""
        try:
            # Get current user data
            user_data = self.get_user_data(email)
            
            if not user_data:
                # Create user if doesn't exist
                create_result = self.create_user(email)
                if create_result["status"] != "success":
                    return create_result
                user_data = self.get_user_data(email)
            
            # Calculate new balance
            current_balance = float(user_data.get(f"{credit_type}_credits", 0))
            new_balance = current_balance + amount
            
            # Update user credits
            update_data = {
                f"{credit_type}_credits": new_balance,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self._make_request(
                'PATCH',
                f"/rest/v1/users?email=eq.{email}",
                update_data,
                use_service_role=True
            )
            
            # Log transaction
            self._log_transaction(email, amount, "credit_add", credit_type, order_id, description)
            
            return {
                "status": "success",
                "message": f"Added {amount} credits to {credit_type}",
                "data": {
                    "email": email,
                    "credit_type": credit_type,
                    "amount_added": amount,
                    "previous_balance": current_balance,
                    "new_balance": new_balance,
                    "order_id": order_id
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to add credits: {e}")
            return {
                "status": "error",
                "message": f"Failed to add credits: {str(e)}"
            }
    
    def deduct_credits(self, email: str, amount: float, credit_type: str = "wallet",
                      component: str = None, description: str = None) -> Dict[str, Any]:
        """Deduct credits from user account"""
        try:
            # Get current user data
            user_data = self.get_user_data(email)
            
            if not user_data:
                return {
                    "status": "error",
                    "message": "User not found"
                }
            
            # Check current balance
            current_balance = float(user_data.get(f"{credit_type}_credits", 0))
            
            if current_balance < amount:
                return {
                    "status": "error",
                    "message": "Insufficient credits",
                    "data": {
                        "email": email,
                        "credit_type": credit_type,
                        "current_balance": current_balance,
                        "requested_amount": amount
                    }
                }
            
            # Calculate new balance
            new_balance = current_balance - amount
            
            # Update user credits
            update_data = {
                f"{credit_type}_credits": new_balance,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self._make_request(
                'PATCH',
                f"/rest/v1/users?email=eq.{email}",
                update_data,
                use_service_role=True
            )
            
            # Log transaction
            self._log_transaction(email, amount, "credit_deduct", credit_type, 
                                component, description, is_deduction=True)
            
            return {
                "status": "success",
                "message": f"Deducted {amount} credits from {credit_type}",
                "data": {
                    "email": email,
                    "credit_type": credit_type,
                    "amount_deducted": amount,
                    "previous_balance": current_balance,
                    "new_balance": new_balance,
                    "component": component
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to deduct credits: {e}")
            return {
                "status": "error",
                "message": f"Failed to deduct credits: {str(e)}"
            }
    
    def purchase_mode_credits(self, email: str, mode: str, credits_needed: float) -> Dict[str, Any]:
        """Purchase credits for specific mode (basic/pro) from wallet"""
        try:
            # Get current user data
            user_data = self.get_user_data(email)
            
            if not user_data:
                return {
                    "status": "error",
                    "message": "User not found"
                }
            
            wallet_balance = float(user_data.get("wallet_balance", 0))
            
            if wallet_balance < credits_needed:
                return {
                    "status": "error",
                    "message": "Insufficient wallet balance",
                    "data": {
                        "email": email,
                        "wallet_balance": wallet_balance,
                        "credits_needed": credits_needed
                    }
                }
            
            # Deduct from wallet
            wallet_result = self.deduct_credits(email, credits_needed, "wallet", 
                                              "mode_purchase", f"Purchase {mode} mode credits")
            
            if wallet_result["status"] != "success":
                return wallet_result
            
            # Add to mode credits
            mode_result = self.add_credits(email, credits_needed, f"{mode}_credits",
                                         None, f"Purchased {mode} mode credits")
            
            if mode_result["status"] != "success":
                # Rollback wallet deduction if mode addition fails
                self.add_credits(email, credits_needed, "wallet", None, "Rollback failed mode purchase")
                return mode_result
            
            return {
                "status": "success",
                "message": f"Successfully purchased {credits_needed} credits for {mode} mode",
                "data": {
                    "email": email,
                    "mode": mode,
                    "credits_purchased": credits_needed,
                    "wallet_deduction": wallet_result["data"],
                    "mode_addition": mode_result["data"]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to purchase mode credits: {e}")
            return {
                "status": "error",
                "message": f"Failed to purchase mode credits: {str(e)}"
            }
    
    def create_payment_transaction(self, email: str, package: str, amount: float) -> Dict[str, Any]:
        """Create payment transaction record"""
        try:
            transaction_data = {
                'email': email,
                'transaction_type': 'pending_payment',
                'package': package,
                'amount': amount,
                'credits': amount,  # 1 IDR = 1 Credit
                'order_id': f"{email}_{int(datetime.now().timestamp())}",
                'description': f"Payment for {package} package",
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self._make_request(
                'POST',
                '/rest/v1/payment_transactions',
                transaction_data,
                use_service_role=True
            )
            
            return {
                'status': 'success',
                'message': 'Payment transaction created',
                'data': response[0] if response else transaction_data
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment transaction: {e}")
            return {
                'status': 'error',
                'message': f'Failed to create payment transaction: {str(e)}'
            }
    
    def _log_transaction(self, email: str, amount: float, transaction_type: str, 
                        credit_type: str, order_id: str = None, description: str = None,
                        is_deduction: bool = False) -> None:
        """Log credit transaction"""
        try:
            transaction_log = {
                'email': email,
                'transaction_type': transaction_type,
                'credit_type': credit_type,
                'amount': amount,
                'is_deduction': is_deduction,
                'order_id': order_id,
                'description': description,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            self._make_request(
                'POST',
                '/rest/v1/credit_transactions',
                transaction_log,
                use_service_role=True
            )
            
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}")
    
    def get_transaction_history(self, email: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user transaction history"""
        try:
            response = self._make_request(
                'GET',
                f"/rest/v1/credit_transactions?email=eq.{email}&order=created_at.desc&limit={limit}",
                use_service_role=True
            )
            
            return response or []
            
        except Exception as e:
            logger.error(f"Failed to get transaction history: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health"""
        try:
            # Simple query to test connection
            response = self._make_request(
                'GET',
                '/rest/v1/users?limit=1',
                use_service_role=True
            )
            
            return {
                'status': 'success',
                'message': 'Supabase connection healthy',
                'data': {
                    'connected': True,
                    'response_time': 'OK',
                    'database': 'PostgreSQL'
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'message': f'Health check failed: {str(e)}',
                'data': {
                    'connected': False,
                    'error': str(e)
                }
            }

# Global instance
supabase_client = SupabaseClient()

def get_supabase_client() -> SupabaseClient:
    """Get global Supabase client instance"""
    return supabase_client 