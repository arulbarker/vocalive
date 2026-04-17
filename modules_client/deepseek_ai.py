"""
DeepSeek AI Integration - Updated to use Supabase config
"""

import json
import logging
import time
from typing import Any, Dict, Optional

import requests

from modules_client.config_manager import config_manager

logger = logging.getLogger('VocaLive.DeepSeek')

class DeepSeekAI:
    """DeepSeek AI API client"""

    def __init__(self):
        self.base_url = "https://api.deepseek.com/v1"

    @property
    def api_key(self) -> Optional[str]:
        """Read API key fresh setiap kali — tidak cache, agar selalu up-to-date."""
        return config_manager.get_api_key("DEEPSEEK_API_KEY")

    def generate_reply(self, prompt: str, max_tokens: int = 150, fast_mode: bool = False, product_context: str = "") -> Optional[str]:
        """
        Generate AI reply using DeepSeek with retry mechanism

        Args:
            prompt: The prompt to send to DeepSeek
            max_tokens: Maximum tokens in response (default 150 for speed)
            fast_mode: If True, use aggressive timeout (5s) for speed
            product_context: Optional product/scene context to inject into system prompt
        """
        if not self.api_key:
            logger.error("DeepSeek API key not available")
            return None

        logger.info("[DEEPSEEK] Request: model=%s, prompt_len=%d, max_tokens=%d, fast_mode=%s", "deepseek-chat", len(prompt), max_tokens, fast_mode)
        # PERFORMANCE: Reduce retries in fast mode
        max_retries = 1 if fast_mode else 3
        base_delay = 0.5 if fast_mode else 1.0

        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                # Get custom context and language from settings
                user_context = config_manager.get("user_context", "")
                ai_language = config_manager.get("ai_language", "indonesian")  # Default to Indonesian

                # Build system message with language and context
                language_prompts = {
                    "indonesian": {
                        "with_context": f"Context: {user_context.strip()}\n\nKamu adalah AI assistant yang membantu sesuai dengan context di atas. Balas dengan natural, friendly, dan sesuai dengan karakter/peran yang diberikan dalam context. Jangan sebutkan bahwa kamu adalah AI. Gunakan bahasa Indonesia yang natural.",
                        "default": "Kamu adalah AI assistant yang membantu streamer untuk berinteraksi dengan penonton. Balas dengan natural, friendly, dan relevan menggunakan bahasa Indonesia."
                    },
                    "malaysian": {
                        "with_context": f"Context: {user_context.strip()}\n\nKamu adalah AI assistant yang membantu sesuai dengan context di atas. Balas dengan natural, friendly, dan sesuai dengan karakter/peran yang diberikan dalam context. Jangan sebutkan bahwa kamu adalah AI. Gunakan bahasa Malaysia yang natural dan casual.",
                        "default": "Kamu adalah AI assistant yang membantu streamer untuk berinteraksi dengan penonton. Balas dengan natural, friendly, dan relevan menggunakan bahasa Malaysia. Gunakan perkataan seperti 'kau', 'aku', 'lah', 'kan', dan gaya bahasa Malaysia yang casual."
                    },
                    "english": {
                        "with_context": f"Context: {user_context.strip()}\n\nYou are an AI assistant that helps according to the context above. Reply naturally, friendly, and according to the character/role given in the context. Don't mention that you are AI. Use natural English.",
                        "default": "You are an AI assistant that helps streamers interact with viewers. Reply naturally, friendly, and relevantly using English."
                    }
                }

                # Get appropriate prompt based on language
                lang_prompts = language_prompts.get(ai_language.lower(), language_prompts["indonesian"])

                if user_context and user_context.strip():
                    system_content = lang_prompts["with_context"]
                else:
                    system_content = lang_prompts["default"]

                # Inject product context jika ada
                if product_context:
                    system_content += f"\n\n{product_context}"

                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }

                # PERFORMANCE: Dynamic timeout based on mode
                if fast_mode:
                    # Fast mode: aggressive timeout for OBS triggers
                    timeout = 5  # 5s max for fast response
                else:
                    # Normal mode: progressive timeout
                    # First attempt: 10s, retry: 15s (reduced from 15s/20s)
                    timeout = 10 if attempt == 0 else 15

                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    reply = result["choices"][0]["message"]["content"]
                    logger.info("[DEEPSEEK] Response: status=%d, reply_len=%d", response.status_code, len(reply))
                    logger.debug(f"DeepSeek reply generated: {len(reply)} chars (attempt {attempt + 1})")
                    return reply
                elif response.status_code == 429:  # Rate limit
                    logger.warning("[DEEPSEEK] Error: model=%s, status=%d", "deepseek-chat", response.status_code)
                    logger.warning(f"DeepSeek rate limit hit, attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        time.sleep(delay)
                        continue
                else:
                    logger.warning("[DEEPSEEK] Error: model=%s, status=%d", "deepseek-chat", response.status_code)
                    logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    return None

            except requests.exceptions.Timeout as e:
                logger.warning(f"DeepSeek timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                logger.error(f"DeepSeek timeout after {max_retries} attempts")
                return None
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"DeepSeek connection error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                logger.error(f"DeepSeek connection failed after {max_retries} attempts")
                return None
            except Exception as e:
                logger.error(f"Error generating DeepSeek reply on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                return None

        return None

    def test_connection(self) -> bool:
        """Test DeepSeek API connection"""
        try:
            if not self.api_key:
                return False

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ],
                "max_tokens": 10
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"DeepSeek connection test failed: {e}")
            return False

# Global instance
deepseek_ai = DeepSeekAI()

def reinitialize_deepseek():
    """Reinitialize DeepSeek AI (useful after changing API keys)"""
    global deepseek_ai
    logger.info("[DEEPSEEK_REINIT] Reinitializing DeepSeek AI...")
    deepseek_ai = DeepSeekAI()
    logger.info("[DEEPSEEK_REINIT] ✅ DeepSeek AI reinitialized successfully")

def generate_reply(prompt: str, max_tokens: int = 500, fast_mode: bool = False, product_context: str = "") -> Optional[str]:
    """Generate AI reply using DeepSeek"""
    return deepseek_ai.generate_reply(prompt, max_tokens, fast_mode, product_context)
