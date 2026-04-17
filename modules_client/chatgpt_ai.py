#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT AI Integration - OpenAI API
"""

import logging
from typing import Optional

import requests

from modules_client.config_manager import config_manager

logger = logging.getLogger('VocaLive')

class ChatGPTAI:
    """ChatGPT AI API client"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config_manager.get_api_key("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"

        if not self.api_key:
            logger.warning("OpenAI API key not found")

    def generate_reply(self, prompt: str, max_tokens: int = 500, product_context: str = "") -> Optional[str]:
        """Generate AI reply using ChatGPT with custom context support"""
        if not self.api_key:
            logger.error("OpenAI API key not available")
            return None

        try:
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

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "gpt-3.5-turbo",
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

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                logger.debug(f"ChatGPT reply generated: {len(reply)} chars")
                return reply
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error generating ChatGPT reply: {e}")
            return None

    def test_connection(self) -> bool:
        """Test OpenAI API connection (synchronous version for PyQt compatibility)"""
        try:
            if not self.api_key:
                return False

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "gpt-3.5-turbo",
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
            logger.error(f"ChatGPT connection test failed: {e}")
            return False

# Global instance
chatgpt_ai = ChatGPTAI()

def reinitialize_chatgpt():
    """Reinitialize ChatGPT AI (useful after changing API keys)"""
    global chatgpt_ai
    logger.info("[CHATGPT_REINIT] Reinitializing ChatGPT AI...")
    chatgpt_ai = ChatGPTAI()
    logger.info("[CHATGPT_REINIT] ✅ ChatGPT AI reinitialized successfully")

def generate_reply(prompt: str, max_tokens: int = 500, product_context: str = "") -> Optional[str]:
    """Generate AI reply using ChatGPT"""
    return chatgpt_ai.generate_reply(prompt, max_tokens, product_context)
