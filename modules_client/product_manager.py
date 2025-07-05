"""
Product Data Manager for CoHost Seller
Handles product slots, triggers, stock management, and database operations
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger('StreamMate.ProductManager')

class ProductManager:
    """Manages product data for CoHost Seller feature"""
    
    def __init__(self):
        self.config_file = Path("config/cohost_seller_products.json")
        self.products = {}
        self.max_slots = 10
        self.default_free_slots = 2
        self.slot_upgrade_cost = 100000  # 100,000 credits per slot
        self.load_products()
    
    def load_products(self):
        """Load product data from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.products = data.get("products", {})
                    logger.info(f"Loaded {len(self.products)} product slots")
            else:
                self.products = {}
                self.save_products()
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            self.products = {}
    
    def save_products(self):
        """Save product data to file"""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(exist_ok=True)
            
            data = {
                "products": self.products,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Product data saved")
        except Exception as e:
            logger.error(f"Error saving products: {e}")
    
    def get_available_slots(self) -> int:
        """Get number of available product slots for user"""
        # Check user's purchased slots from subscription data
        try:
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                    
                # Check if user has CoHost Seller subscription
                seller_data = sub_data.get("cohost_seller", {})
                purchased_slots = seller_data.get("purchased_slots", self.default_free_slots)
                return min(purchased_slots, self.max_slots)
        except Exception as e:
            logger.error(f"Error checking available slots: {e}")
        
        return self.default_free_slots
    
    def get_used_slots(self) -> int:
        """Get number of currently used product slots"""
        return len([p for p in self.products.values() if p.get("active", False)])
    
    def can_add_product(self) -> bool:
        """Check if user can add more products"""
        return self.get_used_slots() < self.get_available_slots()
    
    def add_product(self, slot_id: str, product_data: Dict[str, Any]) -> bool:
        """
        Add or update product in slot
        
        Args:
            slot_id: Unique slot identifier (1-10)
            product_data: Product information
                - judul_barang: Product title
                - scene_obs: OBS scene name
                - keterangan_produk: Product description
                - jumlah_stok: Stock quantity
                - trigger_keyword: Custom trigger word/phrase
        """
        try:
            if not self.can_add_product() and slot_id not in self.products:
                logger.error("Cannot add product: slot limit reached")
                return False
            
            # Validate required fields
            required_fields = ['judul_barang', 'scene_obs', 'keterangan_produk', 'jumlah_stok', 'trigger_keyword']
            for field in required_fields:
                if field not in product_data or not product_data[field]:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate trigger uniqueness
            trigger = product_data['trigger_keyword'].lower().strip()
            for existing_slot, existing_product in self.products.items():
                if (existing_slot != slot_id and 
                    existing_product.get('trigger_keyword', '').lower().strip() == trigger):
                    logger.error(f"Trigger '{trigger}' already used in slot {existing_slot}")
                    return False
            
            # Add product
            self.products[slot_id] = {
                **product_data,
                "active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "usage_count": product_data.get("usage_count", 0)
            }
            
            self.save_products()
            logger.info(f"Product added to slot {slot_id}: {product_data['judul_barang']}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return False
    
    def remove_product(self, slot_id: str) -> bool:
        """Remove product from slot"""
        try:
            if slot_id in self.products:
                product_name = self.products[slot_id].get('judul_barang', 'Unknown')
                del self.products[slot_id]
                self.save_products()
                logger.info(f"Product removed from slot {slot_id}: {product_name}")
                return True
            else:
                logger.warning(f"No product found in slot {slot_id}")
                return False
        except Exception as e:
            logger.error(f"Error removing product: {e}")
            return False
    
    def get_product(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """Get product data by slot ID"""
        return self.products.get(slot_id)
    
    def get_all_products(self) -> Dict[str, Dict[str, Any]]:
        """Get all active products"""
        return {k: v for k, v in self.products.items() if v.get("active", False)}
    
    def get_triggers_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Get mapping of triggers to product data for comment processing"""
        triggers = {}
        for slot_id, product in self.get_all_products().items():
            trigger = product.get('trigger_keyword', '').lower().strip()
            if trigger:
                triggers[trigger] = {
                    **product,
                    "slot_id": slot_id
                }
        return triggers
    
    def update_stock(self, slot_id: str, new_stock: int) -> bool:
        """Update product stock"""
        try:
            if slot_id in self.products:
                self.products[slot_id]['jumlah_stok'] = max(0, new_stock)
                self.products[slot_id]['updated_at'] = datetime.now().isoformat()
                self.save_products()
                logger.info(f"Stock updated for slot {slot_id}: {new_stock}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            return False
    
    def decrease_stock(self, slot_id: str, quantity: int = 1) -> bool:
        """Decrease product stock (for sales tracking)"""
        try:
            if slot_id in self.products:
                current_stock = self.products[slot_id].get('jumlah_stok', 0)
                new_stock = max(0, current_stock - quantity)
                return self.update_stock(slot_id, new_stock)
            return False
        except Exception as e:
            logger.error(f"Error decreasing stock: {e}")
            return False
    
    def increment_usage(self, slot_id: str):
        """Increment usage counter for product (when trigger is used)"""
        try:
            if slot_id in self.products:
                self.products[slot_id]['usage_count'] = self.products[slot_id].get('usage_count', 0) + 1
                self.products[slot_id]['last_used'] = datetime.now().isoformat()
                self.save_products()
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
    
    def get_product_by_trigger(self, trigger: str) -> Optional[Dict[str, Any]]:
        """Find product by trigger keyword"""
        trigger_lower = trigger.lower().strip()
        for slot_id, product in self.get_all_products().items():
            if product.get('trigger_keyword', '').lower().strip() == trigger_lower:
                return {**product, "slot_id": slot_id}
        return None
    
    def validate_obs_scenes(self, available_scenes: List[str]) -> Dict[str, List[str]]:
        """
        Validate that all product scenes exist in OBS
        
        Returns:
            Dict with 'valid' and 'invalid' scene lists
        """
        valid_scenes = []
        invalid_scenes = []
        
        for slot_id, product in self.get_all_products().items():
            scene_name = product.get('scene_obs', '')
            if scene_name:
                if scene_name in available_scenes:
                    valid_scenes.append(f"Slot {slot_id}: {scene_name}")
                else:
                    invalid_scenes.append(f"Slot {slot_id}: {scene_name} (NOT FOUND)")
        
        return {
            "valid": valid_scenes,
            "invalid": invalid_scenes
        }
    
    def get_slot_upgrade_info(self) -> Dict[str, Any]:
        """Get information about slot upgrades"""
        available_slots = self.get_available_slots()
        used_slots = self.get_used_slots()
        
        return {
            "available_slots": available_slots,
            "used_slots": used_slots,
            "free_slots_remaining": available_slots - used_slots,
            "max_slots": self.max_slots,
            "can_upgrade": available_slots < self.max_slots,
            "upgrade_cost_per_slot": self.slot_upgrade_cost,
            "slots_available_for_purchase": self.max_slots - available_slots
        }
    
    def purchase_slot_upgrade(self, slots_to_add: int) -> Dict[str, Any]:
        """
        Purchase additional product slots
        
        Returns:
            Dict with success status and details
        """
        try:
            current_slots = self.get_available_slots()
            total_cost = slots_to_add * self.slot_upgrade_cost
            
            if current_slots + slots_to_add > self.max_slots:
                return {
                    "success": False,
                    "error": f"Cannot exceed maximum {self.max_slots} slots"
                }
            
            # Check if user has enough credits
            from modules_server.real_credit_tracker import get_current_credit_balance
            current_balance = get_current_credit_balance()
            
            if current_balance < total_cost:
                return {
                    "success": False,
                    "error": f"Insufficient credits. Need {total_cost}, have {current_balance}"
                }
            
            # Deduct credits
            from modules_server.real_credit_tracker import force_credit_deduction
            deduction_success = force_credit_deduction(
                total_cost, 
                "slot_upgrade", 
                f"CoHost Seller slot upgrade (+{slots_to_add} slots)"
            )
            
            if not deduction_success:
                return {
                    "success": False,
                    "error": "Credit deduction failed"
                }
            
            # Update subscription data
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
            else:
                sub_data = {}
            
            if "cohost_seller" not in sub_data:
                sub_data["cohost_seller"] = {}
            
            sub_data["cohost_seller"]["purchased_slots"] = current_slots + slots_to_add
            sub_data["cohost_seller"]["last_upgrade"] = datetime.now().isoformat()
            
            with open(subscription_file, 'w', encoding='utf-8') as f:
                json.dump(sub_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "new_total_slots": current_slots + slots_to_add,
                "cost": total_cost,
                "remaining_balance": current_balance - total_cost
            }
            
        except Exception as e:
            logger.error(f"Error purchasing slot upgrade: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
product_manager = ProductManager()

def get_product_manager() -> ProductManager:
    """Get global product manager instance"""
    return product_manager
