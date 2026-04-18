# Bilingual i18n Support (Indonesia / English)

**Tanggal:** 2026-04-17
**Branch:** `feat/i18n-bilingual-support`
**Target versi:** v1.0.15
**Status:** Design — pending user final review

---

## 1. Goal & Non-Goals

### Goal

Menjadikan VocaLive bisa dipakai nyaman oleh **user global** (English) dan **user Indonesia**, dengan menambahkan lapisan bahasa (i18n) di atas app existing. **Tidak ada perubahan fitur, arsitektur, atau behavior** — hanya layer bahasa.

### Non-Goals (Out of Scope)

- Bahasa ke-3 (Melayu, Spanish, dll.) — struktur siap, implementasi ditunda
- Hot-reload UI tanpa restart aplikasi
- Translation management service (Crowdin, Lokalise, dll.)
- Right-to-left (RTL) language support
- Pluralization rules (0/1/few/many)
- Auto-translate via API — semua translation manual untuk kualitas
- Perubahan pada `output_language` AI (tetap Indonesia / Malaysia / English)
- Translate internal developer log (tetap seperti sekarang)
- Translate voice identifier (`Gemini-Puck`, `id-ID-Chirp3-*`)
- Fitur baru apapun — murni additive translation layer

---

## 2. Key Decisions (Confirmed With User)

| Keputusan | Pilihan |
|-----------|---------|
| **Scope translasi** | Full: UI chrome + system prompt AI + error messages + license/update dialog |
| **Hubungan UI language vs `output_language` AI** | **Independen total** — dua setting terpisah; `output_language` tidak diubah |
| **Default bahasa** | Detect dari OS Windows locale (id/ms → ID, selainnya → EN). User existing auto-migrate ke `"id"` untuk cegah kejutan. |
| **Lokasi language switcher** | Config Tab saja (tidak menambah toolbar/menu baru) |
| **Apply setelah ganti bahasa** | Restart-required (bukan hot-reload) — zero risk regresi |
| **Pendekatan teknis** | JSON dict-based translation manager (bukan Qt Linguist) |

---

## 3. Arsitektur

### 3.1 File Layout

```
vocalive/
├── modules_client/
│   └── i18n.py                     # NEW — translation manager
├── i18n/
│   ├── id.json                     # NEW — Indonesian (reference locale)
│   └── en.json                     # NEW — English
├── config/
│   ├── settings.json               # + field "ui_language": "id" | "en"
│   └── settings_default.json       # + field "ui_language": "id"
└── tests/
    └── test_i18n.py                # NEW — manager logic + key coverage tests
```

### 3.2 Public API — `modules_client/i18n.py`

```python
def init(fresh_install: bool = False) -> None:
    """Inisialisasi sekali di main.py setelah ConfigManager siap.

    fresh_install=True  → detect OS locale, save ke settings.json
    fresh_install=False → kalau field ui_language belum ada, force 'id' (migrasi)
    """

def t(key: str, **kwargs: Any) -> str:
    """Lookup terjemahan dengan fallback chain:
       current_lang dict → id.json (reference) → raw key string.
       kwargs untuk str.format substitusi."""

def current_language() -> str:
    """Return 'id' atau 'en'."""

def set_language(lang: str) -> None:
    """Simpan ke config. User harus restart app untuk apply."""
```

### 3.3 Key Naming Convention (Flat Dotted Keys)

```
<area>.<component>.<element>
```

Contoh:
- `cohost.btn.start`
- `config.label.ui_language`
- `license.dialog.title`
- `sales_template.general_seller.content`
- `err.api.gemini_key_missing`
- `common.yes`, `common.ok`, `common.cancel`

**Alasan flat vs nested:** greppable dengan `grep "cohost.btn.start" -r` → langsung dapat semua pemakaian. Nested butuh traverse manual.

### 3.4 Startup Sequence (`main.py`)

```
1. UTF-8 encoding fix                               (harus pertama)
2. is_fresh_install = not settings_path.exists()    ← capture SEBELUM setup_validator
3. ConfigManager ready
4. setup_validator.ensure_settings_exists()         ← ini yang bikin settings.json kalau belum ada
5. i18n.init(fresh_install=is_fresh_install)        ← NEW, SEBELUM license
6. LicenseManager.is_license_valid()                ← dialog license sudah bilingual
7. telemetry.init(...)
8. QApplication + MainWindow
```

**Kritis:** Langkah 2 harus dijalankan **sebelum** langkah 4, karena `setup_validator` menciptakan `settings.json` kalau belum ada — jadi setelah langkah 4, `settings.json` pasti exists dan flag `is_fresh_install` jadi tidak akurat kalau kita cek belakangan.

---

## 4. Migration & OS Locale Detection

### 4.1 Matriks Skenario

| Skenario | Kondisi Awal | Behavior Startup |
|----------|--------------|-------------------|
| Fresh install Windows id-ID / ms-MY | `settings.json` belum ada | setup_validator copy default → `i18n.init(fresh_install=True)` → detect OS → save `"id"` |
| Fresh install Windows en-* | `settings.json` belum ada | Sama → detect OS → save `"en"` |
| User existing update (v1.0.14 → v1.0.15+) | `settings.json` ada, tidak punya field `ui_language` | `i18n.init(fresh_install=False)` → force save `"id"` (tanpa deteksi OS) |
| User existing yang kebetulan sudah punya field | `settings.json` ada, `ui_language` valid | Pakai nilai existing |
| Config corrupt / invalid value | `ui_language: "fr"` | Log warning → fallback `"id"` |

**Kritis:** Untuk user existing, **JANGAN deteksi OS locale** — mereka sudah terbiasa UI Indonesia, auto-switch ke English karena kebetulan Windows-nya EN akan dianggap bug.

### 4.2 Cara Deteksi Fresh Install

```python
# di main.py, SEBELUM setup_validator:
settings_path = app_root / "config" / "settings.json"
is_fresh_install = not settings_path.exists()

setup_validator.ensure_settings_exists()   # buat file kalau belum ada
i18n.init(fresh_install=is_fresh_install)
```

### 4.3 OS Locale Detection

```python
def _detect_os_locale() -> str:
    """Return 'id' atau 'en' berdasarkan Windows default locale.
    Fallback ke 'id' kalau deteksi gagal (safer default untuk user existing)."""
    try:
        import locale
        lang_tuple = locale.getdefaultlocale()
        if lang_tuple and lang_tuple[0]:
            lang = lang_tuple[0].lower()
            if lang.startswith(("id", "ms")):
                return "id"
            if lang.startswith("en"):
                return "en"
    except Exception as e:
        logger.warning(f"OS locale detection failed: {e}")
    return "id"
```

---

## 5. Integration Pattern — Mengganti String di UI

### 5.1 Pola Refactor Widget

```python
# SEBELUM
self.start_button = QPushButton("🚀 Mulai")
platform_label = QLabel("Platform:")
self.setWindowTitle("VocaLive CoHost")

# SESUDAH
from modules_client.i18n import t

self.start_button = QPushButton(t("cohost.btn.start"))
platform_label = QLabel(t("cohost.label.platform"))
self.setWindowTitle(t("cohost.window.title"))
```

### 5.2 Pola Refactor String dengan Placeholder

```python
# SEBELUM
QMessageBox.warning(self, "Error", f"TTS gagal: {reason}")

# SESUDAH
QMessageBox.warning(
    self,
    t("common.error"),
    t("cohost.err.tts_failed", reason=reason)
)
```

```json
"cohost.err.tts_failed": "TTS gagal: {reason}"     // id.json
"cohost.err.tts_failed": "TTS failed: {reason}"    // en.json
```

### 5.3 Yang TIDAK Di-translate

- **User data** — greeting slots, product names, trigger_words, user_context, tiktok_nickname
- **Voice identifier** — `Gemini-Puck`, `id-ID-Chirp3-HD-Aoede` (technical IDs)
- **`output_language` combo values** — tetap literal `"Indonesia"`, `"Malaysia"`, `"English"` (value disimpan ke settings.json)
- **Developer log** — `logger.info/debug/error` tetap bahasa original (konsisten untuk Sentry/MCP debugging)
- **API raw error from server** — kita translate wrapper kita, bukan payload server

### 5.4 Namespace Allocation

| File UI | Namespace prefix | Est. strings |
|---------|------------------|--------------|
| `main_window.py` | `main.*` | ~30 |
| `cohost_tab_basic.py` | `cohost.*` | ~50 |
| `config_tab.py` | `config.*` | ~45 |
| `product_scene_tab.py` | `product.*` | ~20 |
| `analytics_tab.py` | `analytics.*` | ~25 |
| `user_management_tab.py` | `users.*` | ~15 |
| `virtual_camera_tab.py` | `camera.*` | ~15 |
| `license_dialog.py` | `license.*` | ~15 |
| `update_dialog.py` | `update.*` | ~10 |
| `product_popup_window.py` | `popup.*` | ~5 |
| Common shared | `common.*` | ~20 |
| Sales templates | `sales_template.*` | ~50 |
| AI / TTS errors | `err.*` | ~15 |
| **Total** | | **~315 keys** |

### 5.5 Language Switcher di Config Tab

```python
# Di section "Umum" Config Tab, SETELAH output_language combo existing:
ui_lang_label = QLabel(t("config.label.ui_language"))
self.ui_lang_combo = QComboBox()
self.ui_lang_combo.addItem("Bahasa Indonesia", "id")
self.ui_lang_combo.addItem("English", "en")
self.ui_lang_combo.setCurrentIndex(0 if i18n.current_language() == "id" else 1)
self.ui_lang_combo.currentIndexChanged.connect(self.on_ui_language_changed)

def on_ui_language_changed(self, idx):
    new_lang = self.ui_lang_combo.itemData(idx)
    if new_lang == i18n.current_language():
        return
    i18n.set_language(new_lang)
    QMessageBox.information(
        self, t("common.info"), t("config.info.restart_required")
    )
```

**Label sengaja bilingual** (`"UI Language / Bahasa Antarmuka:"`) supaya user yang salah pilih bahasa pun masih paham setting ini apa.

---

## 6. Non-UI String Translation

### 6.1 Sales Templates (`sales_templates.py`)

```python
from modules_client.i18n import t

TEMPLATE_KEYS = [
    "general_seller", "fashion_seller", "food_seller",
    "beauty_seller", "electronics_seller", ...
]

def get_templates() -> dict:
    """Dipanggil LAZILY setiap butuh — TIDAK di-cache di module level.
    Alasan: kalau kita cache di top level (`TEMPLATES = get_templates()`),
    evaluasi terjadi saat import — yang kemungkinan SEBELUM `i18n.init()`
    dipanggil di main.py. Hasilnya: TEMPLATES berisi raw key string, bukan translasi.
    """
    return {
        key: {
            "name": t(f"sales_template.{key}.name"),
            "description": t(f"sales_template.{key}.description"),
            "content": t(f"sales_template.{key}.content"),
        }
        for key in TEMPLATE_KEYS
    }
```

**Migration untuk caller existing:** semua pemakaian `from sales_templates import TEMPLATES` harus di-refactor ke `from sales_templates import get_templates; templates = get_templates()`. Ini **breaking change** di module sales_templates tapi terisolasi (scan terlebih dahulu untuk list caller).

**Template content mengikuti UI language**, bukan `output_language`. Alasan: user baca/pilih template di UI — yang dia baca harus sesuai bahasa UI-nya. `output_language` tetap di-append sebagai instruksi terpisah di system prompt akhir:

```
[template content dalam UI language]
Respond in: {output_language}
```

### 6.2 AI Error Messages (`gemini_ai.py`, `deepseek_ai.py`, `api.py`)

String error yang bocor ke UI di-bungkus `t()`. Internal log (`logger.error`) tetap bahasa original.

```python
# SEBELUM
raise Exception("API key Gemini tidak ditemukan di config/settings.json")

# SESUDAH
raise Exception(t("err.api.gemini_key_missing"))
```

### 6.3 TTS Engine Errors (`modules_server/tts_engine.py`)

```python
# Log internal TETAP original — developer/Sentry facing
logger.error(f"TTS Gemini gagal: {e}")

# Signal ke UI di-translate — user facing
self.error_signal.emit(t("err.tts.gemini_failed", reason=str(e)))
```

### 6.4 Greeting AI Generator (`greeting_ai_generator.py`) — SPECIAL CASE

Prompt ke Gemini untuk generate 10 greeting **mengikuti `output_language`, BUKAN `ui_language`**. Alasan: greeting yang dihasilkan adalah kalimat yang akan didengar viewer — harus sesuai bahasa viewer (yang dikontrol `output_language`), bukan bahasa UI user.

```python
output_lang = cfg.get("output_language", "Indonesia")
prompt_templates = {
    "Indonesia": "Buat 10 sapaan unik untuk {n}...",
    "English": "Generate 10 unique greetings for {n}...",
    "Malaysia": "Buatkan 10 sapaan unik untuk {n} dalam bahasa Melayu..."
}
prompt = prompt_templates.get(output_lang, prompt_templates["Indonesia"]).format(n=nickname)
```

Ini **tidak** pakai JSON i18n manager — ini variasi prompt terikat ke `output_language`, bukan UI language.

---

## 7. Testing Strategy

### 7.1 Test File Baru: `tests/test_i18n.py`

**Tier 1 — Pure logic (no I/O):**
- `test_detect_os_locale_indonesian` — Windows id-ID → `"id"`
- `test_detect_os_locale_malaysian` — Windows ms-MY → `"id"` (mapped)
- `test_detect_os_locale_english` — Windows en-US → `"en"`
- `test_detect_os_locale_fallback_on_exception` — OSError → `"id"`
- `test_t_returns_translation` — lookup sukses
- `test_t_fallback_to_id_when_key_missing_in_en`
- `test_t_fallback_to_key_when_missing_both`
- `test_t_format_placeholder` — `t('err.api.timeout', seconds=30)` → "...30 detik"
- `test_init_fresh_install_detects_os`
- `test_init_existing_user_forces_id` — migration path
- `test_invalid_ui_language_falls_back_to_id` — corrupt config

**Tier 2 — I/O (real JSON files):**
- `test_all_ui_keys_exist_in_both_locales` ⭐ **KEY TEST** — regex scan semua `t("...")` di `ui/*.py` + `modules_client/*.py`, assert setiap key ada di `id.json` DAN `en.json`
- `test_no_orphan_keys_in_json` — warn (tidak fail) kalau JSON punya key yang tidak pernah dipakai
- `test_all_locales_have_same_keys` — `set(id_keys) == set(en_keys)`
- `test_format_placeholders_consistent_across_locales` — `{reason}` di id juga ada di en

### 7.2 Modifikasi Test Existing

| File | Perubahan |
|------|-----------|
| `tests/test_config_tab.py` | Tambah test `ui_lang_combo` visibility + persistence |
| `tests/test_license_dialog.py` | Label/title dari `t()` — pakai `i18n_id`/`i18n_en` fixture |
| `tests/test_setup_validator.py` | Settings.json hasil migrasi punya field `ui_language` |
| `tests/conftest.py` | Tambah fixture `i18n_id` dan `i18n_en` untuk switch bahasa per-test |

### 7.3 Manual QA Additions (ditambah ke CLAUDE.md)

```markdown
#### 🌐 Bilingual / i18n
- [ ] Fresh install Windows id-ID → UI Indonesia
- [ ] Fresh install Windows en-US → UI English
- [ ] Update dari v1.0.14 → UI tetap Indonesia (migration)
- [ ] Ganti UI lang di Config Tab → restart → semua tab pakai bahasa baru
- [ ] License dialog bilingual (saat first install sebelum login)
- [ ] Update dialog bilingual
- [ ] Sales template dropdown: nama & content sesuai UI lang
- [ ] Template dikirim ke AI sesuai UI lang, tapi AI output tetap ikuti output_language
- [ ] Error TTS ditampilkan dalam UI lang
- [ ] Greeting AI tetap pakai output_language (UI=EN + output=ID → greeting ID)
```

### 7.4 CI Pipeline

Tidak perlu workflow baru. Existing `test.yml` (pytest Windows) + `lint.yml` (ruff Ubuntu) otomatis cover. Branch `feat/i18n-bilingual-support` auto-trigger karena matches `feat/**`.

---

## 8. Implementation Phases

Prinsip: **tiap phase tetap kirim app yang fully-functional**, bisa commit + pytest hijau. Tidak ada phase yang meninggalkan app setengah jalan.

### Phase 0 — Prep (scaffolding)
Create branch, `modules_client/i18n.py`, empty `i18n/{id,en}.json`, update `settings_default.json`, hook ke `main.py`, Tier 1 tests. **Exit criteria:** pytest hijau, behavior 100% identik.

### Phase 1 — Common keys + Language switcher di Config Tab
Tambah `common.*`, `config.label.ui_language`, combo switcher. **Exit criteria:** user bisa lihat & ganti, tab lain masih ID.

### Phase 2 — License Dialog + Update Dialog + Main Window chrome
First-impression surface. **Exit criteria:** fresh install EN → login dialog + toolbar English.

### Phase 3 — Config Tab full translate
~45 string → `config.*`.

### Phase 4 — Cohost Tab full translate
~50 string → `cohost.*`. Log viewer pisah user-facing vs developer-log.

### Phase 5 — Sisa 5 tab (paralel via sub-agents)
`product_scene`, `analytics`, `user_management`, `virtual_camera`, `product_popup` — dispatch 5 agents paralel, satu per tab.

### Phase 6 — Sales templates + AI/TTS error messages
Refactor `sales_templates.py` → `get_templates()`, error messages → `err.*` namespace, greeting AI generator prompt variation.

### Phase 7 — Full coverage test + QA
Run `test_all_ui_keys_exist_in_both_locales`, manual QA di Windows id-ID + en-US VM.

### Phase 8 — Docs + Release
Update CLAUDE.md (i18n section + bilingual QA checklist), bump ke v1.0.15, build EXE, PR ke main, tag release.

### Estimasi Per Phase

| Phase | Commits | LOC | Risk | Parallel? |
|-------|---------|-----|------|-----------|
| 0 | 1 | ~300 | Low | No |
| 1 | 1 | ~100 | Low | No |
| 2 | 1 | ~200 | Med | No |
| 3 | 1 | ~400 | Med | No |
| 4 | 1 | ~450 | Med | No |
| 5 | 5 | ~500 | Low | **Yes (5 agents)** |
| 6 | 1 | ~300 | Med | No |
| 7 | 1 | ~50 | Low | No |
| 8 | 1 | ~100 | Low | No |

**Total: ~12 commits, ~2400 LOC, 3-5 sesi kerja.**

---

## 9. Build System Impact

### 9.1 `build_production_exe_fixed.py`

Tambah `i18n/*.json` ke `datas` list:

```python
datas = [
    # ... existing
    ('i18n/id.json', 'i18n'),
    ('i18n/en.json', 'i18n'),
]
```

### 9.2 Path Resolution di Frozen EXE

`i18n.py` harus pakai pola `_get_app_root()` yang sama seperti `config_manager.py`:

```python
def _i18n_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "i18n"
    return Path(__file__).parent.parent / "i18n"
```

### 9.3 Telemetry

Tambah property `ui_language` ke `telemetry.set_user_context()` call di `main.py`:

```python
telemetry.set_user_context({
    "platform": "windows",
    "app_mode": APP_MODE,
    "ui_language": i18n.current_language(),   # NEW
})
```

Sehingga PostHog/Sentry bisa filter user per bahasa UI → insight seberapa banyak user EN vs ID.

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Key missing di salah satu JSON saat refactor | Medium | High (UI nampak raw key) | Test `test_all_ui_keys_exist_in_both_locales` mandatory hijau sebelum commit |
| Developer lupa `from i18n import t` saat tambah string baru | Medium | Medium | Ruff custom rule? (opsional) + CI test catch |
| Translation tidak natural / awkward | High | Low | Phase 7 manual QA review, bisa polish nanti tanpa code change |
| `locale.getdefaultlocale()` deprecated di Python 3.12+ | Low | Low | Masih work di Python 3.11 yang dipakai. Kalau upgrade Python, refactor ke `locale.getlocale()` |
| PyInstaller miss `i18n/*.json` | Low | High (app crash di EXE) | Eksplisit tambah ke `datas`, smoke test EXE tiap phase |
| Test `test_all_ui_keys_exist_in_both_locales` too slow (regex scan banyak file) | Low | Low | Cache scan result; <2 detik acceptable |
| User existing pindah Windows lang ke EN lalu update | Low | Medium | Migration force `"id"` ignorekan OS lang — dijamin tidak berubah |

---

## 11. Future Extensions (Post-v1.0.15)

Hanya dicatat, **tidak dikerjakan sekarang**:

- Bahasa ke-3 (Melayu dedicated, Spanish, dll.) — tinggal tambah `ms.json` / `es.json` + combo option
- Hot-reload UI via `retranslateUi()` pattern — kalau user complain restart annoying
- Export translation coverage report (% diterjemahkan per file) untuk dashboard
- Integration ke Crowdin/Lokalise untuk crowd-sourced translation
- Deteksi bahasa viewer TikTok → auto-switch `output_language` (terpisah dari UI)

---

## 12. Acceptance Criteria

Design ini dianggap **selesai diimplementasikan** bila semua di bawah ini true:

- [ ] Pytest 213+ tests hijau (existing) + 15-20 test baru hijau
- [ ] Fresh install di Windows id-ID → UI auto-Indonesia
- [ ] Fresh install di Windows en-US → UI auto-English
- [ ] User existing v1.0.14 update ke v1.0.15 → UI tetap Indonesia (zero perception change)
- [ ] Ganti bahasa di Config Tab → restart → semua tab, dialog, error konsisten dalam bahasa baru
- [ ] `output_language` combo masih berfungsi sama persis seperti sebelumnya (3 opsi, AI balas sesuai pilihan)
- [ ] Semua QA checklist bilingual manual lulus di Windows 10 + 11
- [ ] Build EXE `dist/VocaLive-v1.0.15.zip` size tetap ~236MB (tidak bloat)
- [ ] PostHog event `app_launched` menyertakan `ui_language` property
- [ ] Tidak ada feature existing yang berubah behavior-nya

---

## 13. Referensi

- CLAUDE.md — arsitektur, build pitfalls, version management, manual QA checklist
- `modules_client/config_manager.py` — pattern path resolution (frozen vs dev)
- `modules_client/telemetry.py` — pattern never-crash wrapper (diadopsi untuk `i18n.py`)
- PyQt6 docs — widget text API (`setText`, `setWindowTitle`, dll.)
- Python `locale` module — OS locale detection
