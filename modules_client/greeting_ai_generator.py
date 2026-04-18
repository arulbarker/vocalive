# modules_client/greeting_ai_generator.py
"""
Greeting AI Generator — generate 10 sapaan unik via Gemini
Teks plain (tanpa tanda baca/simbol) untuk TTS yang bersih
"""

import json
import logging
import re
import time
from typing import List

import requests

from modules_client.config_manager import config_manager

logger = logging.getLogger('VocaLive')

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL    = "gemini-3.1-flash-lite-preview"
GEMINI_FALLBACK = "gemini-flash-lite-latest"

FALLBACK_GREETINGS = [
    "Halo semuanya selamat datang di live kami",
    "Hai guys makasih udah mampir ke sini",
    "Selamat datang di live streaming kita hari ini",
    "Halo teman teman senang banget ada kalian di sini",
    "Hai hai welcome di live kita",
    "Semuanya udah hadir nih makasih ya udah join",
    "Halo guys ayo nonton bareng bareng di sini",
    "Hai semuanya yuk kita mulai live hari ini",
    "Selamat datang guys semoga betah di sini ya",
    "Halo teman teman baru dan yang sudah setia nonton",
]


def clean_greeting_text(text: str) -> str:
    """Strip semua simbol — hanya huruf, angka, dan spasi. Preserve Unicode letters."""
    cleaned = re.sub(r'[^\w\s]', '', text).replace('_', ' ')
    return ' '.join(cleaned.split())


def _parse_greeting_response(raw: str) -> List[str]:
    """
    Parse respons Gemini menjadi list 10 string.
    Coba JSON array dulu, fallback ke parse per-baris.
    """
    raw = raw.strip()

    # Coba JSON array
    try:
        # Hapus markdown code fence jika ada
        if raw.startswith('```'):
            lines = raw.split('\n')
            raw = '\n'.join(lines[1:-1])
        data = json.loads(raw)
        if isinstance(data, list):
            greetings = [clean_greeting_text(str(g)) for g in data if str(g).strip()]
            if len(greetings) >= 5:
                return greetings[:10]
    except Exception:
        pass

    # Fallback: parse per-baris, ambil baris yang tidak kosong
    lines = [line.strip() for line in raw.split('\n') if line.strip()]
    greetings = []
    for line in lines:
        # Hapus prefix nomor seperti "1." atau "1)"
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        # Hapus tanda kutip di awal/akhir
        line = line.strip('"\'')
        cleaned = clean_greeting_text(line)
        if cleaned and len(cleaned) > 5:
            greetings.append(cleaned)

    return greetings[:10] if len(greetings) >= 5 else []


def generate_greetings_with_ai(retry_on_fail: bool = True) -> List[str]:
    """
    Generate 10 teks sapaan unik via Gemini.
    Gunakan user_context dari settings sebagai konteks.
    Return list 10 string plain text (tanpa tanda baca).
    Jika gagal, return FALLBACK_GREETINGS.

    PENTING: Harus dipanggil dari background thread — retry path blocks selama 30 detik.
    """
    api_key = config_manager.get("api_keys", {}).get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("[GREETING_AI] Tidak ada API key Gemini, pakai fallback greetings")
        return FALLBACK_GREETINGS.copy()

    user_context = config_manager.get("user_context", "").strip()

    # Greeting AI mengikuti ui_language (bahasa sistem/utama) — user expectation:
    # "install English → semuanya English". Malaysia specific user bisa override via
    # output_language (viewer-facing AI reply) yang dicheck sebagai secondary.
    from modules_client import i18n
    ui_lang = i18n.current_language()  # "id" | "en"
    # Map ui_language → template key. Check output_language sebagai override untuk
    # case user sengaja pilih Malaysia di output (ui tidak punya opsi Malaysia).
    output_lang_raw = config_manager.get("output_language", "Indonesia")
    if output_lang_raw == "Malaysia":
        output_lang = "Malaysia"
    elif ui_lang == "en":
        output_lang = "English"
    else:
        output_lang = "Indonesia"

    prompt_templates = {
        "Indonesia": {
            "context_with": "Sesuai konteks berikut: {context}",
            "context_default": "untuk live streaming jualan online Indonesia",
            "body": (
                "Buatkan 10 variasi sapaan DALAM BAHASA INDONESIA untuk live streaming TikTok {context_line}\n"
                "Syarat ketat:\n"
                "- BAHASA WAJIB: Indonesia 100 persen abaikan bahasa konteks kalau berbeda\n"
                "- Setiap sapaan 1 sampai 2 kalimat natural dan percakapan\n"
                "- Semua 10 sapaan berbeda satu sama lain dalam variasi kata gaya dan panjang\n"
                "- JANGAN gunakan tanda baca apapun termasuk titik koma tanda seru tanda tanya tanda kutip\n"
                "- JANGAN gunakan simbol markdown seperti bintang garis bawah pagar atau tanda kurung\n"
                "- Hanya huruf biasa dan spasi\n"
                'Format respons: JSON array dengan tepat 10 string\n'
                '["sapaan1", "sapaan2", "sapaan3", ...]'
            ),
        },
        "English": {
            "context_with": "Based on the following context: {context}",
            "context_default": "for an online shopping live stream",
            "body": (
                "Generate 10 varied greetings IN ENGLISH for a TikTok live stream {context_line}\n"
                "Strict requirements:\n"
                "- LANGUAGE MUST be English 100 percent. Even if the context above is in another language ignore its language and respond only in English\n"
                "- Each greeting is 1 to 2 natural, conversational sentences\n"
                "- All 10 greetings differ from one another in word choice, style, and length\n"
                "- DO NOT use any punctuation including periods commas exclamation marks question marks or quotes\n"
                "- DO NOT use markdown symbols like asterisks underscores hashes or parentheses\n"
                "- Only plain letters and spaces\n"
                "Response format: JSON array with exactly 10 strings\n"
                '["greeting1", "greeting2", "greeting3", ...]'
            ),
        },
        "Malaysia": {
            "context_with": "Berdasarkan konteks berikut: {context}",
            "context_default": "untuk siaran langsung jualan online",
            "body": (
                "Buatkan 10 variasi sapaan DALAM BAHASA MELAYU untuk siaran langsung TikTok {context_line}\n"
                "Syarat ketat:\n"
                "- BAHASA WAJIB: Melayu 100 peratus abaikan bahasa konteks kalau berbeza\n"
                "- Setiap sapaan 1 hingga 2 ayat natural dan perbualan\n"
                "- Semua 10 sapaan berbeza antara satu sama lain dalam pilihan kata gaya dan panjang\n"
                "- JANGAN gunakan sebarang tanda baca termasuk titik koma tanda seru tanda tanya tanda petik\n"
                "- JANGAN gunakan simbol markdown seperti bintang garis bawah pagar atau kurungan\n"
                "- Hanya huruf biasa dan ruang\n"
                "Format respons: JSON array dengan tepat 10 string\n"
                '["sapaan1", "sapaan2", "sapaan3", ...]'
            ),
        },
    }

    template = prompt_templates.get(output_lang, prompt_templates["Indonesia"])
    context_line = (
        template["context_with"].format(context=user_context)
        if user_context
        else template["context_default"]
    )
    prompt = template["body"].format(context_line=context_line)

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 600, "temperature": 0.9},
    }

    models = [GEMINI_MODEL, GEMINI_FALLBACK]
    for model in models:
        try:
            url = f"{GEMINI_API_BASE}/{model}:generateContent"
            resp = requests.post(url, headers=headers, json=payload, timeout=20)

            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                greetings = _parse_greeting_response(raw_text)

                if len(greetings) >= 5:
                    # Pad ke 10 jika kurang
                    original_len = len(greetings)
                    while len(greetings) < 10:
                        greetings.append(greetings[len(greetings) % original_len])
                    logger.info(f"[GREETING_AI] Generated {len(greetings)} greetings via {model}")
                    return greetings[:10]
                else:
                    logger.warning(f"[GREETING_AI] Response terlalu sedikit ({len(greetings)} item), coba model berikutnya")
                    continue

            elif resp.status_code == 403:
                logger.warning(f"[GREETING_AI] 403 pada {model}, coba fallback model")
                continue
            elif resp.status_code == 429:
                logger.warning(f"[GREETING_AI] Rate limit pada {model}, coba model berikutnya")
                continue
            else:
                logger.error(f"[GREETING_AI] API error {resp.status_code}: {resp.text[:200]}")

        except requests.exceptions.Timeout:
            logger.warning(f"[GREETING_AI] Timeout pada {model}")
        except Exception as e:
            logger.error(f"[GREETING_AI] Error pada {model}: {e}")

    # Retry sekali setelah 30 detik jika diminta
    if retry_on_fail:
        logger.warning("[GREETING_AI] Semua model gagal, retry dalam 30 detik...")
        time.sleep(30)
        return generate_greetings_with_ai(retry_on_fail=False)

    logger.warning("[GREETING_AI] Gagal generate, pakai fallback greetings")
    return FALLBACK_GREETINGS.copy()
