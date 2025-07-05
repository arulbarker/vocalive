"""
Credit Wallet System - Local Development
Sistem dompet kredit internal untuk StreamMate AI
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import os

logger = logging.getLogger('StreamMate.CreditWallet')

class CreditWallet:
    """Credit Wallet Manager untuk local development"""
    
    def __init__(self, db_path: str = "data/wallet_dev.db", test_mode: bool = True):
        self.db_path = Path(db_path)
        self.test_mode = test_mode
        self.lock = threading.Lock()
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Credit Wallet initialized: {self.db_path} (test_mode: {test_mode})")
    
    def _init_database(self):
        """Initialize wallet database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    user_id TEXT PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    total_topup INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,  -- 'topup', 'spend', 'refund', 'bonus'
                    amount INTEGER NOT NULL,
                    balance_before INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    description TEXT,
                    reference_id TEXT,
                    metadata TEXT,  -- JSON for additional data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES wallets (user_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_user_id 
                ON transactions (user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_type 
                ON transactions (type)
            """)
            
            conn.commit()
    
    def get_balance(self, user_id: str) -> int:
        """Get user's current balance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT balance FROM wallets WHERE user_id = ?", 
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Create new wallet with default balance if in test mode
                if self.test_mode:
                    default_balance = 100000  # 100K credits for testing
                    self._create_wallet(user_id, default_balance)
                    return default_balance
                return 0
    
    def _create_wallet(self, user_id: str, initial_balance: int = 0) -> bool:
        """Create new wallet for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO wallets (user_id, balance, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, initial_balance))
                
                # Add initial transaction if balance > 0
                if initial_balance > 0:
                    conn.execute("""
                        INSERT INTO transactions 
                        (user_id, type, amount, balance_before, balance_after, description)
                        VALUES (?, 'topup', ?, 0, ?, ?)
                    """, (user_id, initial_balance, initial_balance, "Initial balance (test mode)"))
                
                conn.commit()
                logger.info(f"Created wallet for {user_id} with balance {initial_balance}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Wallet already exists for {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error creating wallet for {user_id}: {e}")
            return False
    
    def add_credits(self, user_id: str, amount: int, description: str = "Top-up", 
                   reference_id: str = None, metadata: Dict = None) -> Tuple[bool, str]:
        """Add credits to user wallet"""
        if amount <= 0:
            return False, "Amount must be positive"
        
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Get current balance
                    cursor = conn.execute(
                        "SELECT balance FROM wallets WHERE user_id = ?", 
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        balance_before = result[0]
                    else:
                        # Create wallet if doesn't exist
                        balance_before = 0
                        conn.execute("""
                            INSERT INTO wallets (user_id, balance, created_at, updated_at)
                            VALUES (?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (user_id,))
                    
                    balance_after = balance_before + amount
                    
                    # Update wallet balance
                    conn.execute("""
                        UPDATE wallets 
                        SET balance = ?, total_topup = total_topup + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (balance_after, amount, user_id))
                    
                    # Add transaction record
                    conn.execute("""
                        INSERT INTO transactions 
                        (user_id, type, amount, balance_before, balance_after, 
                         description, reference_id, metadata)
                        VALUES (?, 'topup', ?, ?, ?, ?, ?, ?)
                    """, (user_id, amount, balance_before, balance_after, 
                          description, reference_id, json.dumps(metadata) if metadata else None))
                    
                    conn.commit()
                    
                    logger.info(f"Added {amount} credits to {user_id}. Balance: {balance_before} → {balance_after}")
                    return True, f"Successfully added {amount:,} credits"
                    
            except Exception as e:
                logger.error(f"Error adding credits to {user_id}: {e}")
                return False, f"Error: {str(e)}"
    
    def spend_credits(self, user_id: str, amount: int, description: str = "Purchase", 
                     reference_id: str = None, metadata: Dict = None) -> Tuple[bool, str]:
        """Spend credits from user wallet"""
        if amount <= 0:
            return False, "Amount must be positive"
        
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Get current balance
                    cursor = conn.execute(
                        "SELECT balance FROM wallets WHERE user_id = ?", 
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    
                    if not result:
                        return False, "Wallet not found"
                    
                    balance_before = result[0]
                    
                    if balance_before < amount:
                        return False, f"Insufficient balance. Current: {balance_before:,}, Required: {amount:,}"
                    
                    balance_after = balance_before - amount
                    
                    # Update wallet balance
                    conn.execute("""
                        UPDATE wallets 
                        SET balance = ?, total_spent = total_spent + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (balance_after, amount, user_id))
                    
                    # Add transaction record
                    conn.execute("""
                        INSERT INTO transactions 
                        (user_id, type, amount, balance_before, balance_after, 
                         description, reference_id, metadata)
                        VALUES (?, 'spend', ?, ?, ?, ?, ?, ?)
                    """, (user_id, amount, balance_before, balance_after, 
                          description, reference_id, json.dumps(metadata) if metadata else None))
                    
                    conn.commit()
                    
                    logger.info(f"Spent {amount} credits from {user_id}. Balance: {balance_before} → {balance_after}")
                    return True, f"Successfully spent {amount:,} credits"
                    
            except Exception as e:
                logger.error(f"Error spending credits from {user_id}: {e}")
                return False, f"Error: {str(e)}"
    
    def get_wallet_info(self, user_id: str) -> Dict:
        """Get complete wallet information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT balance, total_topup, total_spent, created_at, updated_at
                FROM wallets WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "user_id": user_id,
                    "balance": result[0],
                    "total_topup": result[1],
                    "total_spent": result[2],
                    "created_at": result[3],
                    "updated_at": result[4]
                }
            else:
                # Create wallet if doesn't exist and in test mode
                if self.test_mode:
                    self._create_wallet(user_id, 100000)
                    return self.get_wallet_info(user_id)
                return None
    
    def get_transaction_history(self, user_id: str, limit: int = 50, 
                               transaction_type: str = None) -> List[Dict]:
        """Get user's transaction history"""
        with sqlite3.connect(self.db_path) as conn:
            if transaction_type:
                cursor = conn.execute("""
                    SELECT id, type, amount, balance_before, balance_after, 
                           description, reference_id, metadata, created_at
                    FROM transactions 
                    WHERE user_id = ? AND type = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, transaction_type, limit))
            else:
                cursor = conn.execute("""
                    SELECT id, type, amount, balance_before, balance_after, 
                           description, reference_id, metadata, created_at
                    FROM transactions 
                    WHERE user_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
            
            transactions = []
            for row in cursor.fetchall():
                metadata = None
                if row[7]:  # metadata field
                    try:
                        metadata = json.loads(row[7])
                    except:
                        pass
                
                transactions.append({
                    "id": row[0],
                    "type": row[1],
                    "amount": row[2],
                    "balance_before": row[3],
                    "balance_after": row[4],
                    "description": row[5],
                    "reference_id": row[6],
                    "metadata": metadata,
                    "created_at": row[8]
                })
            
            return transactions
    
    def check_sufficient_balance(self, user_id: str, amount: int) -> Tuple[bool, int]:
        """Check if user has sufficient balance"""
        current_balance = self.get_balance(user_id)
        return current_balance >= amount, current_balance
    
    def get_stats(self) -> Dict:
        """Get wallet system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_wallets,
                    SUM(balance) as total_balance,
                    SUM(total_topup) as total_topup,
                    SUM(total_spent) as total_spent
                FROM wallets
            """)
            result = cursor.fetchone()
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM transactions
            """)
            total_transactions = cursor.fetchone()[0]
            
            return {
                "total_wallets": result[0] or 0,
                "total_balance": result[1] or 0,
                "total_topup": result[2] or 0,
                "total_spent": result[3] or 0,
                "total_transactions": total_transactions
            }

# Global wallet instance
_wallet_instance = None

def get_credit_wallet(test_mode: bool = True) -> CreditWallet:
    """Get global credit wallet instance"""
    global _wallet_instance
    if _wallet_instance is None:
        # Check if development mode
        config_path = Path("config/development_config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            wallet_config = config.get('credit_wallet', {})
            db_path = wallet_config.get('database_path', 'data/wallet_dev.db')
            test_mode = wallet_config.get('test_mode', True)
        else:
            db_path = 'data/wallet_dev.db'
        
        _wallet_instance = CreditWallet(db_path, test_mode)
    
    return _wallet_instance

# Convenience functions
def get_user_balance(user_id: str) -> int:
    """Get user balance - convenience function"""
    return get_credit_wallet().get_balance(user_id)

def add_user_credits(user_id: str, amount: int, description: str = "Top-up") -> Tuple[bool, str]:
    """Add credits to user - convenience function"""
    return get_credit_wallet().add_credits(user_id, amount, description)

def spend_user_credits(user_id: str, amount: int, description: str = "Purchase") -> Tuple[bool, str]:
    """Spend user credits - convenience function"""
    return get_credit_wallet().spend_credits(user_id, amount, description)

def check_user_balance(user_id: str, required_amount: int) -> Tuple[bool, int]:
    """Check if user has sufficient balance - convenience function"""
    return get_credit_wallet().check_sufficient_balance(user_id, required_amount) 