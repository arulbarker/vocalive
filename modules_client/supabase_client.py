#!/usr/bin/env python3
"""
StreamMate AI - Supabase Client Wrapper
Replacement for VPS server communication using Supabase
"""

import json
import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class StreamMateSupabaseClient:
    """Supabase client wrapper for StreamMate AI"""
    
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
        """Validate user license via Supabase Edge Function"""
        try:
            # Call Edge Function for license validation
            response = requests.post(
                f"{self.base_url}/functions/v1/license-validate",
                headers={
                    'Authorization': f'Bearer {self.anon_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'email': email,
                    'hardware_id': hardware_id
                },
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"License validation failed: {e}")
            return {
                'status': 'error',
                'message': f'License validation failed: {str(e)}'
            }
    
    def update_credit_usage(self, email: str, credits_used: float, sync_type: str = 'manual', 
                          component: str = 'client', description: str = None) -> Dict[str, Any]:
        """Update credit usage via Supabase Edge Function"""
        try:
            response = requests.post(
                f"{self.base_url}/functions/v1/credit-update",
                headers={
                    'Authorization': f'Bearer {self.anon_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'email': email,
                    'credits_used': credits_used,
                    'sync_type': sync_type,
                    'component': component,
                    'description': description
                },
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Credit update failed: {e}")
            return {
                'status': 'error',
                'message': f'Credit update failed: {str(e)}'
            }
    
    def get_user_licenses(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user license data directly from Supabase table"""
        try:
            response = self._make_request(
                'GET',
                f"/rest/v1/licenses?email=eq.{email}",
                use_service_role=True
            )
            
            if response and len(response) > 0:
                return response[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user license: {e}")
            return None
    
    def get_transaction_history(self, email: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user transaction history"""
        try:
            response = self._make_request(
                'GET',
                f"/rest/v1/transaction_history?email=eq.{email}&order=created_at.desc&limit={limit}",
                use_service_role=True
            )
            
            return response or []
            
        except Exception as e:
            logger.error(f"Failed to get transaction history: {e}")
            return []
    
    def get_usage_history(self, email: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user credit usage history"""
        try:
            response = self._make_request(
                'GET',
                f"/rest/v1/credit_usage_history?email=eq.{email}&order=created_at.desc&limit={limit}",
                use_service_role=True
            )
            
            return response or []
            
        except Exception as e:
            logger.error(f"Failed to get usage history: {e}")
            return []
    
    def create_payment_transaction(self, email: str, package: str, amount: float) -> Dict[str, Any]:
        """Create payment transaction record"""
        try:
            # This would integrate with iPaymu
            # For now, we'll create a placeholder transaction
            transaction_data = {
                'email': email,
                'transaction_type': 'pending_payment',
                'credit_amount': amount,  # 1 IDR = 1 Credit
                'price': amount,
                'order_id': f"{email}_{int(datetime.now().timestamp())}",
                'description': f"Payment for {package} package",
                'created_at': datetime.now().isoformat()
            }
            
            response = self._make_request(
                'POST',
                '/rest/v1/transaction_history',
                transaction_data,
                use_service_role=True
            )
            
            return {
                'status': 'success',
                'data': response[0] if response else transaction_data
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment transaction: {e}")
            return {
                'status': 'error',
                'message': f'Failed to create payment transaction: {str(e)}'
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health"""
        try:
            # Simple query to test connection
            response = self._make_request(
                'GET',
                '/rest/v1/licenses?limit=1',
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
    
    def generate_ai_reply(self, prompt: str, timeout: int = 30) -> str:
        """Generate AI reply - placeholder for future Edge Function"""
        # This would be implemented as a Supabase Edge Function
        # For now, return a placeholder
        logger.warning("AI generation not yet implemented in Supabase")
        return "AI generation via Supabase Edge Function coming soon..."

# Global instance
supabase_client = StreamMateSupabaseClient()

def get_supabase_client() -> StreamMateSupabaseClient:
    """Get global Supabase client instance"""
    return supabase_client 