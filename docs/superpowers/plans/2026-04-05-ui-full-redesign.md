# UI Full Redesign — Apply Gold Seller Design System

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform VocaLive UI from flat color-only theme to a fully designed modern app using existing `ui/theme.py` helpers.

**Architecture:** Apply `btn_primary/danger/success/ghost()`, `CARD_STYLE/CARD_ELEVATED_STYLE`, `label_title/subtitle/value()`, and `status_badge()` to all 5 tabs. No new code — just use the design system that already exists.

**Tech Stack:** PyQt6, QSS, `ui/theme.py` design system

---

### Task 1: CohostTabBasic — Buttons, Status Badge, and Card Layout

**Files:**
- Modify: `ui/cohost_tab_basic.py:681-799`

- [ ] Fix tutorial button style (green → btn_accent)
- [ ] Fix Start/Stop buttons (plain → btn_success / btn_danger)  
- [ ] Fix status_indicator (gray → status_badge)
- [ ] Wrap controls in styled QFrame card
- [ ] Add label_title to section headers

### Task 2: CohostTabBasic — Status Table and Log Area

**Files:**
- Modify: `ui/cohost_tab_basic.py` (status table, log QTextEdit)

- [ ] Apply LOG_TEXTEDIT_STYLE to log area
- [ ] Style status table headers

### Task 3: ConfigTab — Button Styles and Section Cards

**Files:**
- Modify: `ui/config_tab.py`

- [ ] Replace all inline button QPushButton styles with btn_primary/success/danger
- [ ] Wrap major sections in CARD_ELEVATED_STYLE frames
- [ ] Apply label_title to section headers

### Task 4: AnalyticsTab — Stat Cards and Value Labels

**Files:**
- Modify: `ui/analytics_tab.py`

- [ ] Apply label_value to stat numbers
- [ ] Apply CARD_STYLE to stat card frames
- [ ] Apply label_title to section headers

### Task 5: UserManagementTab — Cards and Headers

**Files:**
- Modify: `ui/user_management_tab.py`

- [ ] Apply btn_danger / btn_success to add/remove buttons
- [ ] Apply label_title to headers

### Task 6: DeveloperTab — Card Layout

**Files:**
- Modify: `ui/developer_tab.py`

- [ ] Apply CARD_ELEVATED_STYLE to social media frames
- [ ] Apply btn_primary to visit buttons
- [ ] Apply label_title to developer title

### Task 7: Commit

- [ ] git add + commit all changed files
