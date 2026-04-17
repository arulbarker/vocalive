"""Tests untuk ui/theme.py — VocaLive Ocean Blue Design System."""

import re

import pytest

pytestmark = pytest.mark.unit

import ui.theme as theme

# ── Color constants ────────────────────────────────────────────

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

COLOR_CONSTANTS = [
    ("BG_BASE",      theme.BG_BASE),
    ("BG_SURFACE",   theme.BG_SURFACE),
    ("BG_ELEVATED",  theme.BG_ELEVATED),
    ("PRIMARY",      theme.PRIMARY),
    ("SECONDARY",    theme.SECONDARY),
    ("ACCENT",       theme.ACCENT),
    ("TEXT_PRIMARY", theme.TEXT_PRIMARY),
    ("TEXT_MUTED",   theme.TEXT_MUTED),
    ("SUCCESS",      theme.SUCCESS),
    ("ERROR",        theme.ERROR),
    ("WARNING",      theme.WARNING),
    ("INFO",         theme.INFO),
]


def test_color_constants_are_hex():
    """Semua 12 color constant harus format #RRGGBB."""
    for name, value in COLOR_CONSTANTS:
        assert HEX_RE.match(value), (
            f"{name}={value!r} bukan format hex #RRGGBB yang valid"
        )


def test_ocean_blue_branding():
    """Verifikasi nilai palet Ocean Blue utama sesuai CLAUDE.md."""
    assert theme.PRIMARY   == "#2563EB", f"PRIMARY salah: {theme.PRIMARY}"
    assert theme.SECONDARY == "#1E3A5F", f"SECONDARY salah: {theme.SECONDARY}"
    assert theme.ACCENT    == "#60A5FA", f"ACCENT salah: {theme.ACCENT}"
    assert theme.BG_BASE   == "#0F1623", f"BG_BASE salah: {theme.BG_BASE}"


# ── Radius values ──────────────────────────────────────────────

def test_radius_values():
    """RADIUS == '10px' dan semua konstanta radius mengandung 'px'."""
    assert theme.RADIUS == "10px", f"RADIUS salah: {theme.RADIUS}"
    assert "px" in theme.RADIUS,    "RADIUS tidak mengandung 'px'"
    assert "px" in theme.RADIUS_SM, "RADIUS_SM tidak mengandung 'px'"
    assert "px" in theme.RADIUS_LG, "RADIUS_LG tidak mengandung 'px'"


# ── Button helpers ─────────────────────────────────────────────

def test_btn_primary_returns_qss():
    """btn_primary() harus menghasilkan QSS dengan background-color dan border-radius."""
    qss = theme.btn_primary()
    assert isinstance(qss, str), "btn_primary() harus return str"
    assert "background-color" in qss, "btn_primary() tidak mengandung 'background-color'"
    assert "border-radius" in qss,    "btn_primary() tidak mengandung 'border-radius'"


def test_btn_helpers_accept_extra_css():
    """btn_success(extra) harus menyertakan CSS extra di dalam output."""
    extra = "font-size: 16px;"
    qss = theme.btn_success(extra)
    assert extra in qss, (
        f"btn_success() tidak menyertakan extra CSS '{extra}'"
    )


# ── Global QSS ─────────────────────────────────────────────────

def test_global_qss_not_empty():
    """GLOBAL_QSS harus string non-kosong panjang > 100 karakter dan memuat 'QMainWindow'."""
    assert isinstance(theme.GLOBAL_QSS, str), "GLOBAL_QSS harus bertipe str"
    assert len(theme.GLOBAL_QSS) > 100, (
        f"GLOBAL_QSS terlalu pendek: {len(theme.GLOBAL_QSS)} karakter"
    )
    assert "QMainWindow" in theme.GLOBAL_QSS, "GLOBAL_QSS tidak mengandung 'QMainWindow'"


# ── status_badge ───────────────────────────────────────────────

def test_status_badge_returns_qss():
    """status_badge() harus mengembalikan string non-kosong."""
    result = theme.status_badge()
    assert isinstance(result, str), "status_badge() harus return str"
    assert len(result) > 0, "status_badge() mengembalikan string kosong"
