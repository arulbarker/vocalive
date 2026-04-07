"""
Gemini AI Integration — Gemini 2.0 Flash Lite
"""

import requests
import json
import logging
import time
from typing import Optional
from modules_client.config_manager import config_manager

logger = logging.getLogger('VocaLive')

GEMINI_MODEL = "gemini-2.0-flash-lite"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiAI:
    """Gemini AI API client (REST, no SDK required)"""

    def __init__(self):
        self.api_key = config_manager.get("api_keys", {}).get("GEMINI_API_KEY", "")
        if not self.api_key:
            logger.warning("Gemini API key not found")

    def generate_reply(
        self,
        prompt: str,
        max_tokens: int = 150,
        fast_mode: bool = False,
        product_context: str = "",
    ) -> Optional[str]:
        if not self.api_key:
            logger.error("Gemini API key not available")
            return None

        max_retries = 1 if fast_mode else 3
        base_delay = 0.5 if fast_mode else 1.0

        user_context = config_manager.get("user_context", "")
        ai_language = config_manager.get("ai_language", "indonesian")

        language_prompts = {
            "indonesian": {
                "with_context": f"Context: {user_context.strip()}\n\nKamu adalah AI assistant yang membantu sesuai dengan context di atas. Balas dengan natural, friendly, dan sesuai karakter. Jangan sebutkan bahwa kamu adalah AI. Gunakan bahasa Indonesia yang natural.",
                "default": "Kamu adalah AI assistant yang membantu streamer berinteraksi dengan penonton. Balas dengan natural, friendly, dan relevan menggunakan bahasa Indonesia.",
            },
            "malaysian": {
                "with_context": f"Context: {user_context.strip()}\n\nKamu adalah AI assistant yang membantu sesuai context di atas. Balas dengan natural dan friendly menggunakan bahasa Malaysia casual.",
                "default": "Kamu adalah AI assistant untuk streamer. Balas dengan natural menggunakan bahasa Malaysia. Pakai gaya casual seperti 'lah', 'kan', 'aku', 'kau'.",
            },
            "english": {
                "with_context": f"Context: {user_context.strip()}\n\nYou are an AI assistant that helps according to the context above. Reply naturally and friendly in English. Don't mention you are an AI.",
                "default": "You are an AI assistant helping a streamer interact with viewers. Reply naturally and relevantly in English.",
            },
        }

        lang_prompts = language_prompts.get(ai_language.lower(), language_prompts["indonesian"])
        system_content = lang_prompts["with_context"] if (user_context and user_context.strip()) else lang_prompts["default"]
        if product_context:
            system_content += f"\n\n{product_context}"

        url = f"{GEMINI_API_BASE}/{GEMINI_MODEL}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_content}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7,
            },
        }

        for attempt in range(max_retries):
            try:
                timeout = 5 if fast_mode else (10 if attempt == 0 else 15)
                resp = requests.post(url, json=payload, timeout=timeout)

                if resp.status_code == 200:
                    data = resp.json()
                    reply = data["candidates"][0]["content"]["parts"][0]["text"]
                    logger.debug(f"Gemini reply: {len(reply)} chars (attempt {attempt + 1})")
                    return reply.strip()
                elif resp.status_code == 429:
                    logger.warning(f"Gemini rate limit, attempt {attempt + 1}")
                else:
                    logger.error(f"Gemini API error: {resp.status_code} — {resp.text[:200]}")

            except requests.exceptions.Timeout:
                logger.warning(f"Gemini timeout attempt {attempt + 1}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Gemini connection error attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Gemini error attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))

        return None

    def test_connection(self) -> bool:
        if not self.api_key:
            return False
        url = f"{GEMINI_API_BASE}/{GEMINI_MODEL}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Hello"}]}],
            "generationConfig": {"maxOutputTokens": 10},
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False


# Global instance
gemini_ai = GeminiAI()


def reinitialize_gemini():
    """Reinitialize Gemini AI (setelah ganti API key)"""
    global gemini_ai
    logger.info("[GEMINI_REINIT] Reinitializing Gemini AI...")
    gemini_ai = GeminiAI()
    logger.info("[GEMINI_REINIT] ✅ Gemini AI reinitialized successfully")


def generate_reply(
    prompt: str,
    max_tokens: int = 150,
    fast_mode: bool = False,
    product_context: str = "",
) -> Optional[str]:
    return gemini_ai.generate_reply(prompt, max_tokens, fast_mode, product_context)
