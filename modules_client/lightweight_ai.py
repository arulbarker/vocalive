# 🚀 LIGHTWEIGHT AI REPLY GENERATOR
# Optimized untuk mengatasi UI freeze dan "not responding"

import asyncio
import aiohttp
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import queue
import json
from typing import Optional

class LightweightAIReplyGenerator:
    """⚡ Lightweight AI reply generator yang tidak memblokir UI"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ai_reply")
        self.request_queue = queue.Queue(maxsize=50)
        self.is_running = True
        
        # ⚡ LIGHTWEIGHT: Simple response cache
        self.response_cache = {}
        self.cache_max_size = 100
        
        # ⚡ FAST: Pre-defined quick responses
        self.quick_responses = [
            "Terima kasih sudah berkomentar!",
            "Halo! Senang bisa berinteraksi dengan kamu",
            "Wah, komentar yang menarik!",
            "Terima kasih sudah menonton!",
            "Salam kenal! Semoga terhibur ya",
        ]
        
        print("[LIGHTWEIGHT_AI] AI Reply Generator initialized")

    def generate_reply_async(self, prompt: str, callback=None):
        """⚡ ASYNC: Generate reply without blocking UI"""
        try:
            # ⚡ FAST: Check cache first
            cache_key = prompt[:100]  # Use first 100 chars as key
            if cache_key in self.response_cache:
                reply = self.response_cache[cache_key]
                if callback:
                    callback(reply)
                return reply
            
            # ⚡ ASYNC: Submit to thread pool
            future = self.executor.submit(self._generate_reply_sync, prompt)
            
            if callback:
                # ⚡ ASYNC: Handle result in separate thread
                def handle_result():
                    try:
                        reply = future.result(timeout=10)  # 10 second timeout
                        if reply:
                            # ⚡ CACHE: Store in cache
                            self._add_to_cache(cache_key, reply)
                        callback(reply)
                    except Exception as e:
                        print(f"[LIGHTWEIGHT_AI] Error in async reply: {e}")
                        # ⚡ FALLBACK: Use quick response
                        callback(self._get_quick_response())
                
                threading.Thread(target=handle_result, daemon=True).start()
            
            return None  # Will be handled by callback
            
        except Exception as e:
            print(f"[LIGHTWEIGHT_AI] Error in generate_reply_async: {e}")
            if callback:
                callback(self._get_quick_response())
            return None

    def _generate_reply_sync(self, prompt: str) -> Optional[str]:
        """⚡ FAST: Synchronous reply generation with timeout"""
        if not self.api_key:
            return self._get_quick_response()
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # ⚡ LIGHTWEIGHT: Simplified payload
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,  # Reduced for faster response
                "temperature": 0.7,
            }
            
            # ⚡ FAST: Quick timeout
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=payload,
                timeout=8  # Reduced timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                if reply:
                    # ⚡ FAST: Simple text cleaning
                    reply = self._clean_reply(reply)
                    return reply
            
            print(f"[LIGHTWEIGHT_AI] API error: {response.status_code}")
            return self._get_quick_response()
            
        except Exception as e:
            print(f"[LIGHTWEIGHT_AI] Error generating reply: {e}")
            return self._get_quick_response()

    def _clean_reply(self, reply: str) -> str:
        """⚡ FAST: Simple reply cleaning"""
        try:
            # ⚡ FAST: Basic cleaning only
            reply = reply.strip()
            
            # ⚡ FAST: Remove common prefixes
            prefixes = ["AI:", "Bot:", "Assistant:", "Reply:"]
            for prefix in prefixes:
                if reply.startswith(prefix):
                    reply = reply[len(prefix):].strip()
            
            # ⚡ FAST: Limit length
            if len(reply) > 300:
                reply = reply[:297] + "..."
            
            return reply if reply else self._get_quick_response()
            
        except Exception:
            return self._get_quick_response()

    def _get_quick_response(self) -> str:
        """⚡ INSTANT: Get pre-defined quick response"""
        import random
        return random.choice(self.quick_responses)

    def _add_to_cache(self, key: str, value: str):
        """⚡ FAST: Add to cache with size limit"""
        try:
            if len(self.response_cache) >= self.cache_max_size:
                # ⚡ FAST: Remove oldest entries
                keys_to_remove = list(self.response_cache.keys())[:20]
                for k in keys_to_remove:
                    del self.response_cache[k]
            
            self.response_cache[key] = value
            
        except Exception as e:
            print(f"[LIGHTWEIGHT_AI] Cache error: {e}")

    def shutdown(self):
        """🛑 Shutdown gracefully"""
        print("[LIGHTWEIGHT_AI] Shutting down...")
        self.is_running = False
        try:
            self.executor.shutdown(wait=False)
        except Exception as e:
            print(f"[LIGHTWEIGHT_AI] Shutdown error: {e}")

# ⚡ GLOBAL INSTANCE
_ai_generator = None

def get_lightweight_ai_generator(api_key: str = None):
    """⚡ Get global lightweight AI generator instance"""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = LightweightAIReplyGenerator(api_key)
    return _ai_generator

def generate_reply_lightweight(prompt: str, callback=None) -> Optional[str]:
    """⚡ FAST: Generate reply using lightweight generator"""
    generator = get_lightweight_ai_generator()
    return generator.generate_reply_async(prompt, callback)