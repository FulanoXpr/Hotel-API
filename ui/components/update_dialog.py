"""
Update dialog component for Hotel Price Checker.

Shows update availability and handles download/installation.
"""

import sys
import threading
from typing import Any, Optional

import customtkinter as ctk

from ui.utils.theme import TAMANOS, obtener_fuente
from ui.utils.updater import UpdateInfo, Updater, get_updater


class UpdateDialog(ctk.CTkToplevel):
    """
    Dialog for showing update information and handling installation.

    Usage:
        dialog = UpdateDialog(parent, update_info)
        # Dialog handles download and installation
    """

    def __init__(
        self,
        master: Any,
        update_info: UpdateInfo,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the update dialog.

        Args:
            master: Parent widget
            update_info: Information about the available update
        """
        super().__init__(master, **kwargs)

        self.update_info = update_info
        self.updater = get_updater()
        self._download_path: Optional[str] = None

        # Configure window
        self.title("Update Available")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 400) // 2
        self.geometry(f"+{x}+{y}")

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        padding = TAMANOS["padding_medio"]

        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=padding, pady=padding)

        # Title
        title_text = f"🎉 Version {self.update_info.version} Available!"
        self.label_title = ctk.CTkLabel(
            self.main_frame,
            text=title_text,
            font=obtener_fuente("subtitulo"),
        )
        self.label_title.pack(pady=(padding, 5))

        # Current version info
        current_version = self.updater.get_current_version()
        version_text = f"Current version: {current_version} → New version: {self.update_info.version}"
        self.label_version = ctk.CTkLabel(
            self.main_frame,
            text=version_text,
            font=obtener_fuente("normal"),
            text_color="gray",
        )
        self.label_version.pack(pady=5)

        # Release notes
        ctk.CTkLabel(
            self.main_frame,
            text="Release Notes:",
            font=obtener_fuente("encabezado"),
            anchor="w",
        ).pack(fill="x", padx=padding, pady=(padding, 5))

        self.textbox_notes = ctk.CTkTextbox(
            self.main_frame,
            font=obtener_fuente("pequena"),
            height=150,
            wrap="word",
        )
        self.textbox_notes.pack(fill="both", expand=True, padx=padding, pady=5)
        self.textbox_notes.insert("1.0", self.update_info.release_notes or "No release notes.")
        self.textbox_notes.configure(state="disabled")

        # Download size
        size_mb = self.update_info.asset_size / (1024 * 1024)
        size_text = f"Download size: {size_mb:.1f} MB"
        self.label_size = ctk.CTkLabel(
            self.main_frame,
            text=size_text,
            font=obtener_fuente("pequena"),
            text_color="gray",
        )
        self.label_size.pack(pady=5)

        # Progress bar (hidden initially)
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=padding, pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.set(0)

        self.label_progress = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=obtener_fuente("pequena"),
        )

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=padding, pady=padding)

        self.btn_later = ctk.CTkButton(
            self.button_frame,
            text="Later",
            width=100,
            fg_color="gray50",
            command=self.destroy,
        )
        self.btn_later.pack(side="left", padx=5)

        self.btn_download = ctk.CTkButton(
            self.button_frame,
            text="⬇️ Download & Install",
            width=180,
            fg_color="green",
            hover_color="darkgreen",
            command=self._start_download,
        )
        self.btn_download.pack(side="right", padx=5)

    def _start_download(self) -> None:
        """Start downloading the update."""
        # Show progress bar
        self.progress_bar.pack(fill="x", pady=5)
        self.label_progress.pack(pady=2)

        # Update buttons
        self.btn_download.configure(state="disabled", text="⬇️ Downloading...")
        self.btn_later.configure(text="Cancel", command=self._cancel_download)

        # Start download
        self.updater.download_update(
            self.update_info,
            on_progress=self._on_progress,
            on_complete=self._on_download_complete,
            on_error=self._on_download_error,
        )

    def _cancel_download(self) -> None:
        """Cancel the download."""
        self.updater.cancel_download()
        self.destroy()

    def _on_progress(self, downloaded: int, total: int) -> None:
        """Handle download progress update."""
        def update():
            progress = downloaded / total if total > 0 else 0
            self.progress_bar.set(progress)

            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.label_progress.configure(
                text=f"{downloaded_mb:.1f} / {total_mb:.1f} MB ({progress*100:.0f}%)"
            )

        self.after(0, update)

    def _on_download_complete(self, path) -> None:
        """Handle download completion."""
        def update():
            self._download_path = path
            self.progress_bar.set(1)
            self.label_progress.configure(text="Download complete!", text_color="green")

            # Update buttons
            self.btn_later.configure(text="Close", command=self.destroy)
            self.btn_download.configure(
                state="normal",
                text="🚀 Install Now",
                command=self._install_update,
            )

        self.after(0, update)

    def _on_download_error(self, error: str) -> None:
        """Handle download error."""
        def update():
            self.label_progress.configure(
                text=f"Download failed: {error}",
                text_color="red"
            )
            self.btn_later.configure(text="Close", command=self.destroy)
            self.btn_download.configure(
                state="normal",
                text="🔄 Retry",
                command=self._start_download,
            )

        self.after(0, update)

    def _install_update(self) -> None:
        """Install the downloaded update."""
        if not self._download_path:
            return

        from pathlib import Path
        from tkinter import messagebox

        path = Path(self._download_path)

        # Confirm installation
        confirm = messagebox.askyesno(
            "Install Update",
            f"Ready to install version {self.update_info.version}.\n\n"
            "The application will close and the installer will start.\n\n"
            "Continue?",
            parent=self
        )

        if not confirm:
            return

        # Start installer
        success = self.updater.install_update(path)

        if success:
            # Close the entire application
            self.destroy()
            # Get the root window and destroy it
            root = self.master.winfo_toplevel()
            root.quit()
            root.destroy()
            sys.exit(0)
        else:
            messagebox.showerror(
                "Installation Error",
                "Failed to start the installer.\n\n"
                f"You can manually run:\n{path}",
                parent=self
            )


def show_update_dialog(parent: Any, update_info: UpdateInfo) -> None:
    """
    Show the update dialog.

    Args:
        parent: Parent widget
        update_info: Information about the available update
    """
    dialog = UpdateDialog(parent, update_info)
    dialog.focus()
