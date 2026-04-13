"""
telemetry.py — Wrapper PostHog + Sentry untuk VocaLive.
Semua calls dibungkus try/except — telemetry failure tidak boleh crash app.
Device ID dibaca dari config/device_id.dat (sama dengan license system).
"""
import os
import sys
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Internal state ---
_initialized = False
_device_id = "anonymous"
_app_version = "unknown"

def _get_app_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent

def _read_device_id() -> str:
    """Baca device_id dari config/device_id.dat (dibuat oleh license_manager)."""
    try:
        device_id_path = _get_app_root() / "config" / "device_id.dat"
        if device_id_path.exists():
            data = json.loads(device_id_path.read_text(encoding="utf-8"))
            return data.get("id", "anonymous")[:32]
    except Exception:
        pass
    return "anonymous"

def init(posthog_api_key: str, sentry_dsn: str, version: str):
    """
    Init PostHog dan Sentry. Panggil sekali di main.py setelah UTF-8 fix.
    posthog_api_key: Project API Key (phc_xxx) dari PostHog
    sentry_dsn: DSN dari Sentry project
    version: VERSION string dari version.py
    """
    global _initialized, _device_id, _app_version

    if _initialized:
        return

    _app_version = version
    _device_id = _read_device_id()

    # Init Sentry
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=sentry_dsn,
            release=f"vocalive@{version}",
            traces_sample_rate=0.1,
            attach_stacktrace=True,
            auto_session_tracking=True,  # Release Health: track crash-free sessions
        )
        logger.info("[telemetry] Sentry initialized")
    except Exception as e:
        logger.warning(f"[telemetry] Sentry init failed (non-fatal): {e}")

    # Init PostHog
    try:
        import posthog
        posthog.api_key = posthog_api_key
        posthog.host = "https://app.posthog.com"
        posthog.disabled = not posthog_api_key  # disable jika key kosong
        logger.info("[telemetry] PostHog initialized")
    except Exception as e:
        logger.warning(f"[telemetry] PostHog init failed (non-fatal): {e}")

    _initialized = True

def capture(event: str, properties: dict = None):
    """
    Kirim custom event ke PostHog.
    Selalu sertakan app=vocalive dan version otomatis.
    """
    if not _initialized:
        return
    try:
        import posthog
        props = {"app": "vocalive", "version": _app_version}
        if properties:
            props.update(properties)
        posthog.capture(_device_id, event, props)
    except Exception as e:
        logger.debug(f"[telemetry] capture failed (non-fatal): {e}")

def close():
    """
    Flush semua pending events dan tutup sesi Sentry dengan bersih.
    Panggil sebelum app.quit() agar Release Health mencatat sesi sebagai 'healthy'.
    """
    if not _initialized:
        return
    try:
        import sentry_sdk
        sentry_sdk.flush(timeout=2)
    except Exception as e:
        logger.debug(f"[telemetry] flush failed (non-fatal): {e}")

def set_user_context(extra: dict):
    """Tambah context ke Sentry untuk error report berikutnya."""
    if not _initialized:
        return
    try:
        import sentry_sdk
        with sentry_sdk.configure_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
    except Exception as e:
        logger.debug(f"[telemetry] set_user_context failed (non-fatal): {e}")
