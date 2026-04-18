"""Sales Templates for VocaLive CoHost AI — i18n aware with audience split.

Audience-aware field resolution:
    name        → UI language (user browses dropdown dalam bahasa UI)
    description → UI language (user reads description dalam bahasa UI)
    content     → output_language (AI system prompt — HARUS match target reply
                  language supaya AI tidak mix bahasa saat UI=en + output=ID)

IMPORTANT: jangan pernah `TEMPLATES = get_templates()` di module level.
Evaluasi top-level mengambil nilai SEBELUM i18n.init() dipanggil, menghasilkan
raw key strings. Semua caller WAJIB panggil get_templates() lazily setiap kali
butuh data template.
"""
from modules_client.i18n import t

TEMPLATE_KEYS = [
    "general_seller",
    "fashion_seller",
    "food_seller",
    "beauty_seller",
    "electronics_seller",
    "household_seller",
    "baby_seller",
    "health_seller",
    "digital_seller",
    "automotive_seller",
]


def _content_for(template_key: str, output_lang: str) -> str:
    """Resolve template content mengikuti output_language (bukan ui_language).

    Indonesia/Malaysia → id.json content (linguistically close enough)
    English            → en.json content

    Fallback chain: target locale → t() via ui_language → raw key string.
    """
    from modules_client import i18n

    locale = "en" if output_lang == "English" else "id"
    key = f"sales_template.{template_key}.content"
    data = i18n._load_json_file(locale)
    value = data.get(key)
    if value:
        return value
    # Fallback: pakai t() (ui_language) kalau JSON lookup gagal
    return t(key)


def _get_output_language() -> str:
    """Ambil output_language dari config. Default 'Indonesia'."""
    try:
        from modules_client.config_manager import ConfigManager
        cfg = ConfigManager()
        return cfg.get("output_language", "Indonesia") or "Indonesia"
    except Exception:
        return "Indonesia"


def get_templates() -> dict:
    """Return dict template — name/description per UI lang, content per output_language.

    Panggil setiap kali butuh data fresh (jangan cache module-level).
    """
    output_lang = _get_output_language()
    return {
        key: {
            "name": t(f"sales_template.{key}.name"),
            "description": t(f"sales_template.{key}.description"),
            "content": _content_for(key, output_lang),
        }
        for key in TEMPLATE_KEYS
    }


def get_template_list():
    """Return list of (key, name, description) tuples for all templates.

    Backward-compat wrapper untuk caller lama. Evaluasi lazy via get_templates().
    """
    templates = get_templates()
    return [
        (key, data["name"], data["description"])
        for key, data in templates.items()
    ]


def get_template(template_key: str) -> str:
    """Return template content string for the given key. Returns empty string if not found.

    Content mengikuti `output_language` (bukan ui_language) karena dipakai sebagai
    AI system prompt — harus match bahasa balasan AI ke viewer.
    """
    if not template_key or template_key not in TEMPLATE_KEYS:
        return ""
    output_lang = _get_output_language()
    return _content_for(template_key, output_lang)
