# UI/UX Design Review — Hotel Price Checker v1.1.3

**Date:** 2026-02-04
**Tools Used:** Peekaboo (macOS UI capture), UI/UX Pro Max (design intelligence DB)
**Reviewed By:** Claude Code + Ricardo Rivera

---

## Current State

- **Framework:** CustomTkinter (Python desktop GUI)
- **Theme:** Dark mode default, light mode available via toggle
- **Brand:** Foundation for Puerto Rico colors (Blue `#3189A1`, Green `#B0CA5F`, Yellow `#FCAF17`, Red `#F04E37`, Grey `#3E4242`)
- **Layout:** Header bar + 4 tabs (API Keys, Hotels, Execute, Results)
- **Window:** 1100x700, min 1000x600

### UI/UX Pro Max Recommendations for This Product Type

| Domain | Recommendation |
|--------|---------------|
| Product | SaaS/Dashboard -> Glassmorphism + Flat Design, Executive Dashboard |
| Style | Dark Mode (OLED): Deep Black `#000000` or `#121212`, vibrant neon accents, 7:1+ contrast |
| Typography | **Poppins** (headings) + **Open Sans** (body) — Modern Professional pairing |
| Color | Trust blue `#2563EB` + orange CTA `#F97316` (SaaS general) or Financial Dashboard dark `#0F172A` + green `#22C55E` |
| UX | Skeleton loading states, 150-300ms animations, `prefers-reduced-motion` respect |

---

## Findings

### Critical (Priority High)

#### 1. Platform-Specific Fonts
- **File:** `ui/utils/theme.py:81-88`
- **Issue:** Uses "Segoe UI" (Windows) and "Consolas" (Windows) as font families. On macOS, these fall back to system defaults unpredictably.
- **Fix:** Detect OS and use platform-appropriate fonts:
  - macOS: "SF Pro Display" / "Helvetica Neue" + "SF Mono" / "Menlo"
  - Windows: "Segoe UI" + "Consolas"
  - Linux: "Ubuntu" / "Noto Sans" + "Ubuntu Mono"
- **Effort:** Low (modify `FUENTES` dict in `theme.py`)
- **Subagent:** Can be done independently

#### 2. Emoji Icons Throughout UI
- **Files:** `ui/app.py:58-63` (tab names), all tabs (buttons)
- **Issue:** Every tab and button uses emoji as icons. Emojis render differently per OS, don't scale well, and look unprofessional per UI/UX Pro Max guidelines.
- **Affected emojis:** `🔑 📋 ▶ 📊 💾 📂 🗑️ 🔍 ⬇️ 🔄 🌙 ☀️ 📋 📥 ⏹ 🗄️ ➕`
- **Fix:** Create `ui/utils/icons.py` module that loads PNG/SVG icons via `CTkImage`. Use Lucide or Heroicons icon set. Fall back to text-only if icon file missing.
- **Effort:** Medium (need to create icon set + loader module + replace all references)
- **Subagent:** Can be done independently. Needs to:
  1. Download icon PNGs (16x16, 32x32) from Lucide
  2. Create `ui/assets/icons/` directory
  3. Create `ui/utils/icons.py` loader
  4. Replace emoji strings in all tabs

#### 3. Hotels Tab Toolbar Overcrowded
- **File:** `ui/tabs/hotels_tab.py:283-376`
- **Issue:** 8 buttons in a single horizontal row: Download PR Hotels, Load Database, Load Excel, Save Excel, Delete, Clear All, Search All, Search Keys (Selection)
- **Fix:** Split into 2 rows or use grouped layout:
  - Row 1 (Data): Download PR Hotels | Load Database | Load Excel | Save Excel
  - Row 2 (Actions): Search All | Search Keys (Selection) | Delete | Clear All
  - Add visual separators between groups
- **Effort:** Medium (restructure `_crear_barra_herramientas`)
- **Subagent:** Can be done independently

---

### Medium (Priority Medium)

#### 4. Inconsistent Button Colors
- **Files:** Multiple tabs
- **Issue:** Mix of 3 color systems — CSS names (`"darkorange"`, `"firebrick"`, `"gray50"`), theme colors (`tema["estados"]["exito"]`), and CTk defaults.
- **Fix:** Define button role colors in `theme.py`:
  ```python
  BOTONES = {
      "primario": {"fg": FPR_BLUE, "hover": FPR_BLUE_LIGHT},
      "peligro": {"fg": FPR_RED, "hover": "#c0392b"},
      "secundario": {"fg": FPR_GREY, "hover": "#555"},
      "exito": {"fg": FPR_GREEN, "hover": "#8fb34a"},
      "advertencia": {"fg": FPR_YELLOW, "hover": "#e09a10"},
  }
  ```
  Then use `BOTONES["peligro"]["fg"]` instead of `"firebrick"`.
- **Effort:** Low
- **Subagent:** Can be done independently

#### 5. No Loading State Feedback
- **Files:** `hotels_tab.py` (Excel load, key search), `api_keys_tab.py` (test connection)
- **Issue:** Buttons change text to "Loading..." but no visual indicator (spinner, skeleton). UI feels frozen during long operations.
- **Fix:** Use `CTkProgressBar(mode="indeterminate")` during async operations. Show it below the toolbar or in the status bar.
- **Effort:** Medium
- **Subagent:** Can be done independently

#### 6. Insufficient Text Contrast (WCAG)
- **File:** `ui/utils/theme.py:51`
- **Issue:** `texto_secundario: "#a8b5b8"` on `fondo_principal: "#1a2528"` = ~4.2:1 contrast ratio. WCAG AA requires 4.5:1 for normal text.
- **Fix:** Change to `"#c4cfd2"` or lighter for WCAG AA compliance.
- **Effort:** Low (single line change)
- **Subagent:** Should be bundled with #4 (theme changes)

#### 7. Header Bar Crowded
- **File:** `ui/app.py:125-191`
- **Issue:** 5 elements crammed into header: Logo, Title, Version, Update button, Dark Mode toggle. Version label overlaps with refresh button.
- **Fix:** Move version to tooltip on the refresh button or to an "About" dialog. Simplify header to: Logo + Title | (spacer) | Theme Toggle.
- **Effort:** Low
- **Subagent:** Can be done independently

#### 8. Theme Toggle Doesn't Propagate to ExecuteTab/ResultsTab
- **File:** `ui/app.py:383-392`
- **Issue:** `_alternar_tema()` calls `aplicar_tema()` globally but never calls `cambiar_tema()` on `ExecuteTab` or `ResultsTab`, which have hardcoded colors from initialization.
- **Fix:** Add to `_alternar_tema()`:
  ```python
  if self.tab_ejecutar and hasattr(self.tab_ejecutar, 'cambiar_tema'):
      self.tab_ejecutar.cambiar_tema(self.modo_tema)
  if self.tab_resultados and hasattr(self.tab_resultados, 'cambiar_tema'):
      self.tab_resultados.cambiar_tema(self.modo_tema)
  ```
- **Effort:** Low (3-4 lines)
- **Subagent:** Should be bundled with #4/#6 (theme changes)

---

### Minor (Priority Low)

#### 9. No Tooltips on Buttons
- **Files:** All tabs
- **Issue:** No tooltips anywhere. With 8+ buttons in Hotels tab, user must read every label.
- **Fix:** Create `CTkToolTip` wrapper or use `tktooltip` package. Add to all buttons.
- **Effort:** Medium

#### 10. No Keyboard Shortcuts
- **Files:** `ui/app.py`
- **Issue:** No keyboard bindings for common operations (Ctrl+S save, Ctrl+O open, etc.)
- **Fix:** Add `self.bind_all("<Control-s>", ...)` etc. in `HotelPriceApp.__init__`.
- **Effort:** Medium

#### 11. Date Input Without Date Picker
- **File:** `ui/tabs/execute_tab.py:123-130`
- **Issue:** Check-in date is a plain text entry. User must type "YYYY-MM-DD" manually.
- **Fix:** Use `tkcalendar.DateEntry` or add date validation with visual feedback.
- **Effort:** Medium

#### 12. Fixed-Width Result Columns
- **File:** `ui/tabs/results_tab.py:239-261`
- **Issue:** Columns have fixed widths (Hotel=300, Price=100). Don't adapt to content or window size.
- **Fix:** Use weight-based column sizing or a proper table widget like `CTkTable`.
- **Effort:** High

#### 13. Redundant Placeholders
- **File:** `ui/tabs/hotels_tab.py:411-416`
- **Issue:** "Name:" label + "Hotel name" placeholder is redundant.
- **Fix:** Keep labels, remove or simplify placeholders to example values ("e.g., Hilton Ponce").
- **Effort:** Low

---

## Implementation Plan (For Next Session)

### Suggested Subagent Strategy

The fixes can be parallelized into **4 independent groups**:

#### Group A: Theme System (Issues #1, #4, #6, #8)
- Modify `ui/utils/theme.py` — platform fonts, button roles, contrast fix
- Modify `ui/app.py` — theme propagation
- **Files:** `ui/utils/theme.py`, `ui/app.py`
- **Dependencies:** None

#### Group B: Icon System (Issue #2)
- Create `ui/assets/icons/` directory with PNG icons
- Create `ui/utils/icons.py` loader module
- Update `ui/app.py` tab names
- Update all tabs to use icon module
- **Files:** New `ui/utils/icons.py`, new `ui/assets/icons/*.png`, all tabs
- **Dependencies:** None (but touches same files as Group C)

#### Group C: Layout Improvements (Issues #3, #7, #13)
- Restructure Hotels tab toolbar into 2 rows
- Simplify header bar
- Fix redundant placeholders
- **Files:** `ui/tabs/hotels_tab.py`, `ui/app.py`
- **Dependencies:** None (but touches same files as Group B)

#### Group D: UX Polish (Issues #5, #9, #10, #11)
- Add loading indicators
- Add tooltips
- Add keyboard shortcuts
- Improve date input
- **Files:** Multiple tabs, `ui/app.py`
- **Dependencies:** None

### Recommended Execution Order

1. **Group A first** (theme) — smallest scope, biggest visual impact
2. **Group C second** (layout) — improves usability
3. **Group B third** (icons) — biggest effort, most visual change
4. **Group D last** (UX polish) — nice-to-have improvements

Groups A and C can run as parallel subagents. Group B should run after A+C merge to avoid conflicts. Group D can run independently at any time.

---

## Reference: Brand Colors (FPR)

| Color  | Hex       | Role                     |
|--------|-----------|--------------------------|
| Blue   | `#3189A1` | Primary accent, buttons  |
| Green  | `#B0CA5F` | Success states           |
| Yellow | `#FCAF17` | Warning states           |
| Red    | `#F04E37` | Error states             |
| Grey   | `#3E4242` | Secondary backgrounds    |

## Reference: Current UI Files

| File | Purpose |
|------|---------|
| `ui/app.py` | Main window, header, tabview, theme toggle |
| `ui/utils/theme.py` | Colors, fonts, sizes, theme config |
| `ui/tabs/api_keys_tab.py` | API credential management |
| `ui/tabs/hotels_tab.py` | Hotel list management, toolbar |
| `ui/tabs/execute_tab.py` | Search config, progress, log, stats |
| `ui/tabs/results_tab.py` | Results table, metrics, export |
| `ui/components/progress_bar.py` | Progress bar with ETA |
| `ui/components/stats_panel.py` | Live search statistics |
| `ui/components/hotel_table.py` | Hotel data table |
| `ui/components/log_viewer.py` | Search log display |
| `ui/components/api_key_frame.py` | Reusable API key input frame |
| `ui/components/update_dialog.py` | Auto-update notification |
