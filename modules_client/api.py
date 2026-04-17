#!/usr/bin/env python3
"""
API Bridge untuk VocaLive Client
Menghubungkan aplikasi client dengan server VPS untuk AI processing
"""

import json
import json as _json
import logging
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from modules_client.config_manager import ConfigManager

logger = logging.getLogger('VocaLive.API')

# Load environment variables
load_dotenv()

class APIClient:
    """API Client - Local mode only"""
    def __init__(self):
        self.cfg = ConfigManager()
        self.base_url = "http://localhost:8888"
        print("[API] Local mode: Using local server")

        self.timeout = 30
        self.session = self._create_session()

    def cleanup(self):
        """Cleanup resources to prevent connection leaks"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
                logger.info("APIClient session closed successfully")
        except Exception as e:
            logger.warning(f"Error closing APIClient session: {e}")

    def _create_session(self):
        """Create a requests session with connection pooling and retry strategy"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_server_url(self):
        """Use local server"""
        return "http://localhost:8888"

    def _make_request(self, endpoint, data, timeout=None, max_retries=3):
        """Make request dengan error handling dan retry mechanism"""
        if timeout is None:
            timeout = self.timeout

        base_delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/{endpoint}"
                # Progressive timeout: shorter for first attempts
                current_timeout = timeout if attempt == 0 else min(timeout * 1.5, 15)

                response = self.session.post(url, json=data, timeout=current_timeout)
                response.raise_for_status()
                return response

            except requests.exceptions.ConnectionError as conn_err:
                logger.warning(f"Connection error to {self.base_url} (attempt {attempt + 1}): {conn_err}")
                last_exception = conn_err

                if self.base_url == "https://api.vocalive.com" and attempt == 0:
                    # Production server down, fallback ke localhost
                    logger.warning("Production server unavailable, trying localhost...")
                    self.base_url = "http://localhost:8888"
                    continue

                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue

            except requests.exceptions.Timeout as timeout_err:
                logger.warning(f"Request timeout to {self.base_url}/{endpoint} (attempt {attempt + 1}): {timeout_err}")
                last_exception = timeout_err

                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue

            except requests.exceptions.RequestException as req_err:
                logger.warning(f"Request error to {self.base_url}/{endpoint} (attempt {attempt + 1}): {req_err}")
                last_exception = req_err

                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue

        # All retries failed, raise the last exception
        logger.error(f"All {max_retries} attempts failed for {self.base_url}/{endpoint}")
        raise last_exception

    def generate_reply(self, prompt: str) -> str:
        """Generate AI reply melalui server"""
        try:
            response = self._make_request("ai_reply", {"text": prompt})
            return response.json().get("reply", "")
        except Exception as e:
            logger.error(f"AI API failed: {e}")
            # Fallback ke client-side DeepSeek
            try:
                from modules_client.deepseek_ai import generate_reply as local_gen
                logger.info("Using local DeepSeek fallback")
                return local_gen(prompt)
            except Exception as local_error:
                logger.error(f"Local fallback failed: {local_error}")

            return "Maaf, sistem AI sedang dalam maintenance"

# Global instance
_api_client = APIClient()

# Export functions
def generate_reply(prompt: str) -> str:
    return _api_client.generate_reply(prompt)

def cleanup_api_client():
    """Cleanup global API client resources"""
    global _api_client
    if _api_client:
        _api_client.cleanup()

def get_server_info():
    """Info server yang sedang digunakan (untuk debugging)"""
    return {
        "server_url": _api_client.base_url,
        "mode": "development" if "localhost" in _api_client.base_url else "production"
    }

class APIBridge:
    """Bridge untuk komunikasi dengan API server"""

    def __init__(self):
        # Initialize server URLs first
        self.local_server = "http://localhost:8888"
        self.session = self._create_session()
        self.active_server = self._get_active_server()
        print("[API] Using local backend only")

    def cleanup(self):
        """Cleanup resources to prevent connection leaks"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
                logger.info("APIBridge session closed successfully")
        except Exception as e:
            logger.warning(f"Error closing APIBridge session: {e}")

    def _create_session(self):
        """Create requests session with connection pooling and retry strategy"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],
            backoff_factor=1
        )

        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_active_server(self):
        """Test koneksi server dan return yang aktif"""
        # Test local server
        try:
            response = self.session.get(f"{self.local_server}/api/health", timeout=10)
            if response.status_code == 200:
                print(f"[API] Local server active: {self.local_server}")
                return self.local_server
        except Exception:
            pass

        # Default ke local server
        print(f"[API] No server responded, defaulting to local: {self.local_server}")
        return self.local_server

# Global API bridge instance
api_bridge = APIBridge()

def cleanup_api_bridge():
    """Cleanup global API bridge resources"""
    global api_bridge
    if api_bridge:
        api_bridge.cleanup()

def generate_reply(prompt: str, timeout: int = 15, fast_mode: bool = False, max_tokens: int = None) -> str:
    """
    Generate AI reply using ONLY the configured AI provider - NO FALLBACK
    Clear error messages instead of confusing fallbacks

    Args:
        prompt: User prompt for AI
        timeout: Request timeout in seconds (not used with direct AI calls)
        fast_mode: If True, use aggressive timeout for faster response (OBS triggers)
        max_tokens: Max tokens in response (default based on mode: 80 fast, 150 normal)

    Returns:
        AI generated reply string, or clear error message if failed
    """
    start_time = time.time()
    print(f"[API] generate_reply called with prompt length: {len(prompt)}")
    if fast_mode:
        print("[API] ⚡ FAST MODE enabled - aggressive timeout for quick response")

    # Get AI provider from config
    from modules_client.config_manager import ConfigManager
    cfg = ConfigManager()
    ai_provider = cfg.get("ai_provider", "deepseek").lower()
    logger.info("[API] generate_reply: provider=%s, prompt_len=%d, fast_mode=%s", ai_provider, len(prompt), fast_mode)
    print(f"[API] Using ONLY configured provider: {ai_provider} (NO FALLBACK)")

    # Use ONLY the configured AI provider - NO FALLBACK
    # ChatGPT/OpenAI disabled — uncomment to re-enable
    # if ai_provider == "chatgpt" or ai_provider == "openai":
    #     ...

    if ai_provider == "gemini":
        try:
            print("[API] Using Gemini Flash Lite API (as configured)...")
            gemini_key = cfg.get("api_keys", {}).get("GEMINI_API_KEY")
            if not gemini_key:
                error_msg = "ERROR: Gemini dipilih sebagai AI provider, tetapi GEMINI_API_KEY tidak ditemukan. Silakan tambahkan API key di Settings."
                print(f"[API] {error_msg}")
                return error_msg

            from modules_client.gemini_ai import generate_reply as gemini_generate
            reply = gemini_generate(prompt, max_tokens=(max_tokens or 150), fast_mode=fast_mode)

            if reply and len(reply.strip()) > 0:
                logger.info("[API] generate_reply: reply_len=%d, elapsed=%.2fs", len(reply), time.time() - start_time)
                print(f"[API] Gemini success: {len(reply)} chars")
                try:
                    from modules_client.telemetry import capture as _tel_capture
                    _tel_capture("ai_reply_success", {"provider": "gemini", "reply_len": len(reply)})
                except Exception:
                    pass
                return reply
            else:
                error_msg = "ERROR: Gemini API tidak memberikan respons. Periksa API key atau coba lagi."
                print(f"[API] {error_msg}")
                try:
                    from modules_client.telemetry import capture as _tel_capture
                    _tel_capture("ai_reply_failed", {"provider": "gemini", "reason": "empty_response"})
                except Exception:
                    pass
                return error_msg

        except Exception as e:
            logger.error("[API] generate_reply error: %s", str(e))
            error_msg = f"ERROR Gemini: {str(e)}. Periksa API key Gemini Anda di Settings."
            print(f"[API] {error_msg}")
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("ai_reply_failed", {"provider": "gemini", "reason": str(e)[:100]})
            except Exception:
                pass
            return error_msg

    elif ai_provider == "deepseek":
        try:
            print("[API] Using DeepSeek API (as configured)...")

            # Check API key first
            deepseek_key = cfg.get("api_keys", {}).get("DEEPSEEK_API_KEY")
            if not deepseek_key:
                error_msg = "ERROR: DeepSeek dipilih sebagai AI provider, tetapi DEEPSEEK_API_KEY tidak ditemukan di konfigurasi. Silakan tambahkan API key di Settings."
                print(f"[API] {error_msg}")
                return error_msg

            # PERFORMANCE: Set tokens based on mode
            if max_tokens is None:
                max_tokens = 80 if fast_mode else 150  # Aggressive for OBS triggers

            print(f"[API] DeepSeek config: fast_mode={fast_mode}, max_tokens={max_tokens}")

            # Use global instance (already initialized with API key)
            from modules_client.deepseek_ai import generate_reply as deepseek_generate
            reply = deepseek_generate(prompt, max_tokens=max_tokens)

            if reply and len(reply.strip()) > 0:
                logger.info("[API] generate_reply: reply_len=%d, elapsed=%.2fs", len(reply), time.time() - start_time)
                print(f"[API] DeepSeek success: {len(reply)} chars")
                try:
                    from modules_client.telemetry import capture as _tel_capture
                    _tel_capture("ai_reply_success", {"provider": "deepseek", "reply_len": len(reply)})
                except Exception:
                    pass
                return reply
            else:
                error_msg = "ERROR: DeepSeek API tidak memberikan respons. Periksa API key dan koneksi internet, atau coba lagi nanti."
                print(f"[API] {error_msg}")
                try:
                    from modules_client.telemetry import capture as _tel_capture
                    _tel_capture("ai_reply_failed", {"provider": "deepseek", "reason": "empty_response"})
                except Exception:
                    pass
                return error_msg

        except Exception as e:
            logger.error("[API] generate_reply error: %s", str(e))
            error_msg = f"ERROR DeepSeek: {str(e)}. Periksa API key dan koneksi internet."
            print(f"[API] {error_msg}")
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("ai_reply_failed", {"provider": "deepseek", "reason": str(e)[:100]})
            except Exception:
                pass
            return error_msg

    else:
        error_msg = f"ERROR: AI provider '{ai_provider}' tidak dikenal. Pilih 'gemini' atau 'deepseek' di Settings."
        print(f"[API] {error_msg}")
        return error_msg

# REMOVED: _get_fallback_response - No more fallback responses
# Users will get clear error messages instead of confusing fallbacks

def generate_reply_with_scene(prompt: str, fast_mode: bool = False) -> tuple[str, int]:
    """
    Generate AI reply dan deteksi scene_id produk dalam satu API call.

    Returns:
        (reply_text, scene_id) — scene_id=0 berarti tidak ada produk yang relevan.
    """
    from modules_client.config_manager import ConfigManager
    from modules_client.product_scene_manager import ProductSceneManager

    psm = ProductSceneManager()
    product_context = psm.build_product_context()
    logger.info("[API] generate_reply_with_scene: prompt_len=%d, scene_id=%d", len(prompt), 0)

    if not product_context:
        # Tidak ada produk terdaftar — gunakan reply biasa
        reply = generate_reply(prompt, fast_mode=fast_mode)
        return (reply or ""), 0

    cfg = ConfigManager()
    ai_provider = cfg.get("ai_provider", "deepseek").lower()
    max_tokens = 120 if fast_mode else 180  # lebih besar karena AI harus wrap dalam JSON

    raw = None
    if ai_provider == "gemini":
        gemini_key = cfg.get("api_keys", {}).get("GEMINI_API_KEY")
        if not gemini_key:
            return "ERROR: GEMINI_API_KEY tidak ditemukan di konfigurasi.", 0
        try:
            from modules_client.gemini_ai import generate_reply as gemini_gen
            raw = gemini_gen(prompt, max_tokens=max_tokens, fast_mode=fast_mode, product_context=product_context)
        except Exception as e:
            logger.error(f"generate_reply_with_scene Gemini error: {e}")
            return f"ERROR Gemini: {e}", 0
    elif ai_provider == "deepseek":
        deepseek_key = cfg.get("api_keys", {}).get("DEEPSEEK_API_KEY")
        if not deepseek_key:
            return "ERROR: DEEPSEEK_API_KEY tidak ditemukan di konfigurasi.", 0
        try:
            from modules_client.deepseek_ai import generate_reply as deepseek_gen
            raw = deepseek_gen(prompt, max_tokens=max_tokens, fast_mode=fast_mode, product_context=product_context)
        except Exception as e:
            logger.error(f"generate_reply_with_scene DeepSeek error: {e}")
            return f"ERROR DeepSeek: {e}", 0
    else:
        return f"ERROR: AI provider '{ai_provider}' tidak dikenal.", 0

    if not raw:
        return "", 0

    # Parse JSON response dari AI
    # Coba direct parse dulu, baru regex sebagai fallback
    def _parse_scene_json(text: str):
        try:
            data = _json.loads(text.strip())
            return str(data.get("reply", "")).strip(), int(data.get("scene_id", 0))
        except Exception:
            pass
        try:
            match = re.search(r'\{[^{}]*"reply"[^{}]*\}', text, re.DOTALL)
            if match:
                data = _json.loads(match.group())
                return str(data.get("reply", "")).strip(), int(data.get("scene_id", 0))
        except Exception:
            pass
        return None, None

    reply_text, scene_id = _parse_scene_json(raw)
    if reply_text is not None:
        logger.debug(f"generate_reply_with_scene: reply={len(reply_text)}chars, scene_id={scene_id}")
        return reply_text, scene_id

    logger.warning(f"generate_reply_with_scene: gagal parse JSON. Raw: {raw[:100]}")
    # Fallback: gunakan raw sebagai reply, scene_id=0
    return raw.strip(), 0


def test_api_connection():
    """Test API connection and return status"""
    from modules_client.config_manager import ConfigManager
    cfg = ConfigManager()
    ai_provider = cfg.get("ai_provider", "deepseek").lower()

    results = {
        "local_server": False,
        "deepseek_direct": False,
        "chatgpt_direct": False,
        "active_server": None,
        "ai_provider": ai_provider
    }

    # Test local server
    try:
        response = api_bridge.session.get(f"{api_bridge.local_server}/api/health", timeout=10)
        results["local_server"] = response.status_code == 200
    except (requests.exceptions.RequestException, ConnectionError) as e:
        pass

    # Test direct DeepSeek
    deepseek_key = cfg.get("api_keys", {}).get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key and len(deepseek_key) > 10:
        try:
            headers = {"Authorization": f"Bearer {deepseek_key}"}
            response = api_bridge.session.get("https://api.deepseek.com/v1/models", headers=headers, timeout=5)
            results["deepseek_direct"] = response.status_code == 200
        except (requests.exceptions.RequestException, ConnectionError) as e:
            pass

    # Test direct ChatGPT/OpenAI
    openai_key = cfg.get("api_keys", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if openai_key and len(openai_key) > 10:
        try:
            headers = {"Authorization": f"Bearer {openai_key}"}
            response = api_bridge.session.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
            results["chatgpt_direct"] = response.status_code == 200
        except (requests.exceptions.RequestException, ConnectionError) as e:
            pass

    results["active_server"] = api_bridge.active_server
    return results

if __name__ == "__main__":
    # Test script
    print("Testing API connections...")
    status = test_api_connection()

    print("\n=== API Connection Status ===")
    print(f"AI Provider: {status['ai_provider'].upper()}")
    print(f"Local Server (localhost:8888): {'✅' if status['local_server'] else '❌'}")
    print(f"Direct DeepSeek API: {'✅' if status['deepseek_direct'] else '❌'}")
    print(f"Direct ChatGPT API: {'✅' if status['chatgpt_direct'] else '❌'}")
    print(f"Active Server: {status['active_server']}")

    # Test generate_reply
    print("\n=== Testing AI Generation ===")
    test_prompt = "Penonton TestUser bertanya: halo bang apa kabar?"
    result = generate_reply(test_prompt)
    print(f"Test Result: {result}")
