"""
Tooltip ligero para CustomTkinter.

Muestra un tooltip al pasar el cursor sobre un widget.
"""

import customtkinter as ctk


class ToolTip:
    """
    Tooltip que aparece al hacer hover sobre un widget CTk.

    Attributes:
        widget: Widget al que se asocia el tooltip.
        text: Texto a mostrar.
    """

    def __init__(self, widget: ctk.CTkBaseClass, text: str, delay: int = 500) -> None:
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tip_window = None
        self._after_id = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self._tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self._tip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        # Quitar de la barra de tareas
        tw.attributes("-topmost", True)

        label = ctk.CTkLabel(
            tw,
            text=self.text,
            corner_radius=4,
            fg_color=("gray85", "gray20"),
            text_color=("gray10", "gray90"),
            padx=8,
            pady=4,
        )
        label.pack()

    def _hide(self, event=None) -> None:
        self._cancel()
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

    def update_text(self, text: str) -> None:
        """Actualiza el texto del tooltip."""
        self.text = text
