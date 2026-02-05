"""
Lightweight calendar date picker widget for CustomTkinter.

Provides a dropdown calendar popup that replaces the need for
tkcalendar dependency. Opens as a Toplevel window anchored
below the triggering widget.
"""

import calendar
from datetime import date, datetime
from typing import Callable, Optional

import customtkinter as ctk

from ui.utils.theme import FUENTES, obtener_tema, TemaMode


class CalendarPopup(ctk.CTkToplevel):
    """
    Calendar popup window showing a month grid.

    Attributes:
        selected_date: The currently selected date.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        initial_date: Optional[date] = None,
        on_select: Optional[Callable[[date], None]] = None,
        modo_tema: TemaMode = "dark",
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)

        self._on_select = on_select
        self._modo_tema = modo_tema
        self._tema = obtener_tema(modo_tema)

        # Current view month/year
        now = initial_date or date.today()
        self._year = now.year
        self._month = now.month
        self._selected = now

        # Window config
        self.title("")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.overrideredirect(True)  # No title bar

        # Position below the master widget
        self._position_below(master)

        # Build UI
        self._build()

        # Close on click outside
        self.bind("<FocusOut>", lambda e: self._check_focus_out(e))
        self.focus_set()

    def _position_below(self, widget: ctk.CTkBaseClass) -> None:
        """Position popup directly below the given widget."""
        widget.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 2
        self.geometry(f"+{x}+{y}")

    def _build(self) -> None:
        """Build the calendar UI."""
        bg = self._tema["fondo_secundario"]
        fg = self._tema["texto_principal"]
        fg2 = self._tema["texto_secundario"]
        accent = self._tema["acento"]

        self.configure(fg_color=bg)

        # Main frame with border effect
        self.main = ctk.CTkFrame(self, fg_color=bg, corner_radius=8, border_width=1,
                                  border_color=self._tema["borde"])
        self.main.pack(padx=2, pady=2)

        # Navigation bar: < Month Year >
        nav = ctk.CTkFrame(self.main, fg_color="transparent")
        nav.pack(fill="x", padx=8, pady=(8, 4))

        self._btn_prev = ctk.CTkButton(
            nav, text="<", width=28, height=28,
            fg_color="transparent", hover_color=self._tema["borde"],
            text_color=fg, command=self._prev_month,
        )
        self._btn_prev.pack(side="left")

        self._label_month = ctk.CTkLabel(
            nav, text="", font=FUENTES.get("encabezado", ("Segoe UI", 14, "bold")),
            text_color=fg,
        )
        self._label_month.pack(side="left", expand=True)

        self._btn_next = ctk.CTkButton(
            nav, text=">", width=28, height=28,
            fg_color="transparent", hover_color=self._tema["borde"],
            text_color=fg, command=self._next_month,
        )
        self._btn_next.pack(side="right")

        # Day-of-week headers
        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.pack(fill="x", padx=8)

        for day_name in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            ctk.CTkLabel(
                header, text=day_name, width=32, height=20,
                font=FUENTES.get("pequena", ("Segoe UI", 10)),
                text_color=fg2,
            ).pack(side="left", padx=1)

        # Day grid
        self._grid_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self._grid_frame.pack(fill="x", padx=8, pady=(2, 8))

        self._render_month()

    def _render_month(self) -> None:
        """Render the day buttons for the current month."""
        # Update header
        month_name = calendar.month_name[self._month]
        self._label_month.configure(text=f"{month_name} {self._year}")

        # Clear existing buttons
        for widget in self._grid_frame.winfo_children():
            widget.destroy()

        cal = calendar.Calendar(firstweekday=0)  # Monday first
        weeks = cal.monthdayscalendar(self._year, self._month)

        fg = self._tema["texto_principal"]
        fg2 = self._tema["texto_secundario"]
        accent = self._tema["acento"]
        today = date.today()

        for week in weeks:
            row = ctk.CTkFrame(self._grid_frame, fg_color="transparent")
            row.pack(fill="x")

            for day_num in week:
                if day_num == 0:
                    # Empty cell
                    ctk.CTkLabel(row, text="", width=32, height=28).pack(side="left", padx=1)
                else:
                    d = date(self._year, self._month, day_num)
                    is_today = d == today
                    is_selected = d == self._selected

                    if is_selected:
                        btn_fg = accent
                        text_color = "#ffffff"
                    elif is_today:
                        btn_fg = self._tema["borde"]
                        text_color = fg
                    else:
                        btn_fg = "transparent"
                        text_color = fg

                    btn = ctk.CTkButton(
                        row, text=str(day_num), width=32, height=28,
                        fg_color=btn_fg,
                        hover_color=self._tema["acento_hover"] if not is_selected else accent,
                        text_color=text_color,
                        font=FUENTES.get("pequena", ("Segoe UI", 10)),
                        corner_radius=4,
                        command=lambda d=d: self._select_date(d),
                    )
                    btn.pack(side="left", padx=1)

    def _prev_month(self) -> None:
        """Navigate to previous month."""
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._render_month()

    def _next_month(self) -> None:
        """Navigate to next month."""
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._render_month()

    def _select_date(self, d: date) -> None:
        """Handle date selection."""
        self._selected = d
        if self._on_select:
            self._on_select(d)
        self.destroy()

    def _check_focus_out(self, event) -> None:
        """Close popup when focus leaves (click outside)."""
        # Small delay to allow button clicks within the popup to register
        self.after(150, self._maybe_close)

    def _maybe_close(self) -> None:
        """Close if focus is no longer on this window."""
        try:
            focused = self.focus_get()
            if focused is None or not str(focused).startswith(str(self)):
                self.destroy()
        except Exception:
            pass


class DateEntry(ctk.CTkFrame):
    """
    Date entry widget with a text field and calendar button.

    Combines a CTkEntry (YYYY-MM-DD) with a calendar popup trigger.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        initial_date: Optional[str] = None,
        modo_tema: TemaMode = "dark",
        width: int = 150,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._modo_tema = modo_tema
        self._popup: Optional[CalendarPopup] = None

        # Entry field
        self.entry = ctk.CTkEntry(
            self, width=width - 32,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            placeholder_text="YYYY-MM-DD",
        )
        self.entry.pack(side="left")

        if initial_date:
            self.entry.insert(0, initial_date)

        # Calendar button
        from ui.utils.icons import get_icon
        self.btn_cal = ctk.CTkButton(
            self, text="", image=get_icon("calendar"),
            width=28, height=28,
            fg_color="transparent",
            hover_color=obtener_tema(modo_tema)["borde"],
            command=self._toggle_popup,
        )
        self.btn_cal.pack(side="left", padx=(4, 0))

    def _toggle_popup(self) -> None:
        """Open or close the calendar popup."""
        if self._popup is not None:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None
            return

        # Parse current date from entry
        try:
            d = datetime.strptime(self.entry.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            d = date.today()

        self._popup = CalendarPopup(
            self.entry,
            initial_date=d,
            on_select=self._on_date_selected,
            modo_tema=self._modo_tema,
        )

    def _on_date_selected(self, d: date) -> None:
        """Handle date selection from popup."""
        self.entry.delete(0, "end")
        self.entry.insert(0, d.strftime("%Y-%m-%d"))
        self._popup = None

    def get(self) -> str:
        """Get the current date string."""
        return self.entry.get().strip()

    def set(self, value: str) -> None:
        """Set the date string."""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def cambiar_tema(self, modo_tema: TemaMode) -> None:
        """Update theme."""
        self._modo_tema = modo_tema
        tema = obtener_tema(modo_tema)
        self.btn_cal.configure(hover_color=tema["borde"])
