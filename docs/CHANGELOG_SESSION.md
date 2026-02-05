# Session Changelog

## 2026-02-04 — Light Mode Contrast Fix

### Problem
Switching to Light Mode made most text invisible in the Execute and Results tabs. Labels like "Search Configuration", "Check-in date:", "Filter:", "Results Summary", radio buttons, and table headers all stayed white (`#f0f4f5`) against a light background.

### Root Cause
Labels were created with `text_color=self.tema["texto_principal"]` — a single hex color from the dark theme at init time. When `ctk.set_appearance_mode("light")` was called, CTk only auto-switches text colors for widgets **without** an explicit `text_color`. The explicit value locked them to the dark mode color permanently.

### Fix
Removed explicit `text_color` from all standard labels, checkboxes, and radio buttons. CTk now auto-adapts text color when the appearance mode switches. Kept explicit colors only for semantic values (success green, error red, etc.) and updated those in `cambiar_tema()`.

Also stored nested frames (`frame_log`, `frame_metricas`, `frame_header`) as instance variables so `cambiar_tema()` can update their `fg_color` when the theme changes.

### Files Modified
- **`ui/tabs/execute_tab.py`** — Removed `text_color` from 9 labels/checkbox ("Search Configuration", "Check-in date:", "Nights:", "Rooms:", "Adults:", "Children:", "Use cascade", "Progress", "Search Log"). Stored `frame_log` as `self.frame_log`. Updated `cambiar_tema` to include `frame_log`.
- **`ui/tabs/results_tab.py`** — Removed `text_color` from 7 labels/radio buttons ("Results Summary", "Distribution by Provider:", "Filter:", radio "All"/"With Price"/"No Price", table headers, "No results" placeholder). Stored `frame_metricas` and `frame_header` as instance variables. Expanded `cambiar_tema` to update nested frame backgrounds and metric value colors.
- **`ui/components/stats_panel.py`** — Removed `text_color` from 4 labels ("Search Statistics", counter sub-labels "Total"/"Success"/"Failures"/"Cache", "By Provider", provider names). Simplified `cambiar_tema`.
- **`ui/components/progress_bar.py`** — Removed `text_color` from percentage and ETA labels. Simplified `cambiar_tema`.
- **`ui/components/log_viewer.py`** — Removed `text_color` from textbox initialization.

### Design Decision
**Let CTk manage text colors automatically** rather than manually tracking and updating every label in `cambiar_tema()`. This is simpler, less error-prone, and follows CTk's intended usage pattern. Explicit colors are only used for semantic meaning (status colors, provider colors) where auto-switching would be incorrect.

### Verified
Captured screenshots of all 4 tabs in Light Mode after fix — all text now has proper dark-on-light contrast.

---

## 2026-02-04 — Remaining UI/UX Issues (#2, #11, #12) Completed

### Issue #2: Emoji Icons Replaced with CTkImage Icons
- **Created `ui/utils/icons.py`** — Pillow-based icon generator that draws 19 geometric icons (search, save, folder, trash, play, stop, etc.) at runtime. Returns `CTkImage` objects with automatic light/dark variants. Uses `@lru_cache` for performance.
- **Updated all button icons** across 6 files:
  - `ui/app.py` — Tab names cleaned (no emojis), refresh button uses icon, dark mode toggle cleaned
  - `ui/tabs/hotels_tab.py` — All 8 toolbar buttons + dialog buttons use CTkImage icons via `compound="left"`
  - `ui/tabs/execute_tab.py` — Start/Stop buttons use play/stop icons
  - `ui/tabs/results_tab.py` — Copy/Export buttons use copy/export icons
  - `ui/tabs/api_keys_tab.py` — Save Configuration button uses save icon
  - `ui/components/update_dialog.py` — Download button uses download icon, removed all emoji from dynamic text states

### Issue #11: Date Picker Added
- **Created `ui/utils/date_picker.py`** — Custom calendar popup widget built entirely with CTk (no external dependencies). Features:
  - `CalendarPopup`: Toplevel month grid with navigation (< prev / next >), day buttons, today highlight, selected date accent color
  - `DateEntry`: Compound widget with CTkEntry + calendar icon button
  - Theme-aware (dark/light), auto-closes on focus loss
- **Integrated in `execute_tab.py`** — Replaced plain CTkEntry with `DateEntry` widget for check-in date. Backwards-compatible via `self.entry_fecha` alias.

### Issue #12: Proportional Result Columns
- **Updated `results_tab.py`** — Replaced fixed-width `pack(side="left")` layout with `grid` layout using proportional weights:
  - `#`: 5%, `Hotel`: 35%, `Price`: 12%, `Currency`: 8%, `Provider`: 13%, `Check-in`: 13%, `Check-out`: 13%
  - Both header and data rows use identical grid weights for alignment
  - Hotel name truncation increased from 40 to 50 characters

### Design Decision: Pillow-Generated Icons (not external files)
- **Rationale:** Generates icons at runtime using Pillow's ImageDraw, avoiding external icon file dependencies (no downloads, no binary assets). Each icon is drawn at 2x resolution for Retina displays. CTkImage handles light/dark theme switching automatically.
- **Trade-off:** Icons are simpler geometric shapes vs. polished Lucide/Heroicons PNGs. Acceptable for a desktop tool.

### Files Created
- `ui/utils/icons.py` — 19-icon Pillow generator with CTkImage output
- `ui/utils/date_picker.py` — CalendarPopup + DateEntry widgets

### Files Modified
- `ui/app.py` — Clean tab names, icon imports, icon-based buttons
- `ui/tabs/hotels_tab.py` — All buttons with CTkImage icons, removed all emoji text
- `ui/tabs/execute_tab.py` — DateEntry integration, play/stop icons
- `ui/tabs/results_tab.py` — Proportional grid columns, copy/export icons
- `ui/tabs/api_keys_tab.py` — Save button icon
- `ui/components/update_dialog.py` — Download/retry button icons

---

## 2026-02-04 — UI/UX Improvements Implementation

### Group A: Theme System
- **Platform fonts** (`theme.py`): Detect OS via `platform.system()`. macOS: SF Pro Display + Menlo. Windows: Segoe UI + Consolas. Linux: Ubuntu + Ubuntu Mono.
- **Button role colors** (`theme.py`): New `BOTONES` dict with 5 roles (primario, peligro, secundario, exito, advertencia) using FPR brand colors. Updated `hotels_tab.py` (6 buttons) and `update_dialog.py` (2 buttons).
- **WCAG contrast** (`theme.py`): Dark theme `texto_secundario` improved from `#a8b5b8` to `#c4cfd2` (~5.5:1 ratio).
- **Theme propagation** (`app.py`): `_alternar_tema()` now calls `cambiar_tema()` on ExecuteTab and ResultsTab.

### Group C: Layout
- **Toolbar 2 rows** (`hotels_tab.py`): Split 8 buttons into `fila_data` (Download, Load DB, Load Excel, Save Excel) and `fila_acciones` (Search All, Search Selection, Delete, Clear All).
- **Header simplified** (`app.py`): Version integrated into title label. Removed separate version label. Header: Logo | Title+version | Updates btn | Theme Toggle.
- **Placeholders** (`hotels_tab.py`): Changed from generic ("Hotel name") to examples ("e.g., Hilton Ponce Golf & Casino").

### Group D: UX Polish
- **Loading indicators** (`hotels_tab.py`): Added indeterminate `CTkProgressBar` in status bar. Shown during: Excel load, DB load, key search, cache download.
- **Tooltips** (`tooltip.py`, `hotels_tab.py`, `app.py`): New lightweight `ToolTip` class. Added to all 8 toolbar buttons and update button.
- **Keyboard shortcuts** (`app.py`): Cmd/Ctrl+O (open Excel), Cmd/Ctrl+S (save Excel), Cmd/Ctrl+1-4 (switch tabs).

### Files Modified
- `ui/utils/theme.py` — platform fonts, BOTONES dict, contrast fix
- `ui/app.py` — header simplified, theme propagation, tooltips, keyboard shortcuts
- `ui/tabs/hotels_tab.py` — toolbar 2 rows, button colors, loading indicators, tooltips, placeholders
- `ui/components/update_dialog.py` — button colors

### Files Created
- `ui/utils/tooltip.py` — lightweight ToolTip widget for CustomTkinter

### Not Implemented (deferred)
- Issue #2 (Emoji icons → PNG icons): Requires downloading icon set + creating loader module. Medium effort.
- Issue #11 (Date picker): Requires tkcalendar dependency or custom widget.
- Issue #12 (Fixed-width columns): High effort, would need table widget rework.

---

## 2026-02-04 — UI/UX Design Review Setup

### Changes Made
- **Installed Peekaboo** (v3.0.0-beta3) via Homebrew — macOS UI capture CLI for screenshots and automation
- **Installed UI/UX Pro Max** CLI (`uipro-cli`) globally via npm, initialized in project with `uipro init --ai claude`
  - Added `.claude/skills/ui-ux-pro-max/scripts/` with design database and search tools
- **Updated CLAUDE.md** — Added mandatory change documentation rule

### Design Research Gathered
Searched UI/UX Pro Max database for recommendations matching our app profile (desktop SaaS dashboard tool for hotel price checking):

| Domain | Key Findings |
|--------|-------------|
| Product | Glassmorphism + Flat Design, Micro-interactions, Executive Dashboard style |
| Style | Dark Mode (OLED) or Swiss Modernism 2.0 for professional corporate feel |
| Color | Trust teal (`#0F766E`) + professional blue (`#0369A1`) — aligns with FPR brand blue (`#3189A1`) |

### Pending / Next Session
- [x] Capture app screenshot with Peekaboo
- [x] Analyze current UI design visually
- [x] Search typography and UX domains in UI/UX Pro Max
- [x] Compare current design against recommendations
- [x] Propose specific UI improvements
- [ ] Implement UI improvements (see `docs/UI_UX_REVIEW.md`)

### Files Modified
- `CLAUDE.md` — Added "Change Documentation" section
- `docs/CHANGELOG_SESSION.md` — Created (this file)

---

## 2026-02-04 — UI/UX Design Review Complete

### What Was Done
1. **Launched app** and captured API Keys tab screenshot with Peekaboo
2. **Read all UI source code**: `app.py`, all 4 tabs, `theme.py`, `progress_bar.py`, `stats_panel.py`
3. **Searched UI/UX Pro Max** across 5 domains: product, style, typography, color, UX
4. **Produced full analysis** with 13 findings across 3 priority levels
5. **Created implementation plan** at `docs/UI_UX_REVIEW.md`

### Key Findings Summary
- **3 Critical**: Platform fonts, emoji icons, toolbar overcrowded
- **5 Medium**: Inconsistent button colors, no loading states, contrast issues, header crowded, theme not propagating
- **5 Minor**: No tooltips, no keyboard shortcuts, no date picker, fixed columns, redundant placeholders

### Note on Peekaboo + Zed
Peekaboo click commands target screen-absolute coordinates, but when running Claude Code inside Zed's terminal, Zed intercepts focus. Solution: run Claude Code from Terminal.app for full Peekaboo interaction, or use `peekaboo window focus` + `peekaboo see` (capture works, clicks don't).

### Files Created
- `docs/UI_UX_REVIEW.md` — Full analysis and implementation plan
- `docs/CHANGELOG_SESSION.md` — Updated (this file)

### Pending / Next Session
- [ ] Implement fixes using tasks + parallel subagents (see `docs/UI_UX_REVIEW.md`)
