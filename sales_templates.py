"""Sales Templates for VocaLive CoHost AI — i18n aware.

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


def get_templates() -> dict:
    """Return dict template dalam UI language aktif. Panggil setiap butuh data fresh."""
    return {
        key: {
            "name": t(f"sales_template.{key}.name"),
            "description": t(f"sales_template.{key}.description"),
            "content": t(f"sales_template.{key}.content"),
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

    Backward-compat wrapper — memanggil get_templates() setiap kali supaya
    terjemahan aktif sesuai UI language.
    """
    if not template_key or template_key not in TEMPLATE_KEYS:
        return ""
    return t(f"sales_template.{template_key}.content")
