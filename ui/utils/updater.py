"""
Auto-update functionality for Hotel Price Checker.

Checks GitHub releases for new versions and handles download/installation.
"""

import logging
import os
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import requests
from packaging import version

logger = logging.getLogger(__name__)

# Application version - update this with each release
APP_VERSION = "1.2.2"

# GitHub repository info
GITHUB_OWNER = "FulanoXpr"
GITHUB_REPO = "Hotel-API"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Asset names for different platforms
WINDOWS_INSTALLER = "HotelPriceChecker-Setup.exe"
WINDOWS_ZIP = "HotelPriceChecker-Windows.zip"
MACOS_DMG = "HotelPriceChecker-macOS.dmg"


@dataclass
class UpdateInfo:
    """Information about an available update."""
    version: str
    download_url: str
    release_notes: str
    asset_name: str
    asset_size: int  # bytes


class Updater:
    """
    Handles checking for updates and downloading new versions.

    Usage:
        updater = Updater()

        # Check for updates (async)
        updater.check_for_update(
            on_update_available=lambda info: print(f"Update {info.version} available!"),
            on_no_update=lambda: print("No update available"),
            on_error=lambda e: print(f"Error: {e}")
        )

        # Download update (async)
        updater.download_update(
            update_info,
            on_progress=lambda current, total: print(f"{current}/{total}"),
            on_complete=lambda path: print(f"Downloaded to {path}"),
            on_error=lambda e: print(f"Error: {e}")
        )
    """

    def __init__(self):
        self.current_version = APP_VERSION
        self._download_cancelled = False

    def get_current_version(self) -> str:
        """Get the current application version."""
        return self.current_version

    def check_for_update(
        self,
        on_update_available: Optional[Callable[[UpdateInfo], None]] = None,
        on_no_update: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Check for updates asynchronously.

        Args:
            on_update_available: Callback when update is found, receives UpdateInfo
            on_no_update: Callback when no update is available
            on_error: Callback when error occurs, receives error message
        """
        def check():
            try:
                update_info = self._check_for_update_sync()
                if update_info:
                    if on_update_available:
                        on_update_available(update_info)
                else:
                    if on_no_update:
                        on_no_update()
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                if on_error:
                    on_error(str(e))

        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    def _check_for_update_sync(self) -> Optional[UpdateInfo]:
        """
        Check for updates synchronously.

        Returns:
            UpdateInfo if update available, None otherwise
        """
        try:
            response = requests.get(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Parse version from tag (remove 'v' prefix if present)
            tag = data.get("tag_name", "")
            remote_version = tag.lstrip("v")

            # Compare versions
            if not self._is_newer_version(remote_version):
                logger.info(f"No update available. Current: {self.current_version}, Latest: {remote_version}")
                return None

            # Find the appropriate asset for this platform
            asset = self._find_platform_asset(data.get("assets", []))
            if not asset:
                logger.warning("No compatible asset found for this platform")
                return None

            return UpdateInfo(
                version=remote_version,
                download_url=asset["browser_download_url"],
                release_notes=data.get("body", "No release notes available."),
                asset_name=asset["name"],
                asset_size=asset["size"],
            )

        except requests.RequestException as e:
            logger.error(f"Network error checking for updates: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing release data: {e}")
            raise

    def _is_newer_version(self, remote_version: str) -> bool:
        """Check if remote version is newer than current."""
        try:
            current = version.parse(self.current_version)
            remote = version.parse(remote_version)
            return remote > current
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return False

    def _find_platform_asset(self, assets: list) -> Optional[dict]:
        """Find the download asset for the current platform."""
        if sys.platform == "win32":
            # Prefer installer over ZIP
            preferred_names = [WINDOWS_INSTALLER, WINDOWS_ZIP]
        elif sys.platform == "darwin":
            preferred_names = [MACOS_DMG]
        else:
            # Linux - no pre-built binary yet
            return None

        for preferred in preferred_names:
            for asset in assets:
                if asset.get("name") == preferred:
                    return asset

        return None

    def download_update(
        self,
        update_info: UpdateInfo,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[Path], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Download update asynchronously.

        Args:
            update_info: Information about the update to download
            on_progress: Callback for progress updates (bytes_downloaded, total_bytes)
            on_complete: Callback when download completes, receives path to downloaded file
            on_error: Callback when error occurs
        """
        self._download_cancelled = False

        def download():
            try:
                path = self._download_update_sync(update_info, on_progress)
                if path and on_complete:
                    on_complete(path)
            except Exception as e:
                logger.error(f"Error downloading update: {e}")
                if on_error:
                    on_error(str(e))

        thread = threading.Thread(target=download, daemon=True)
        thread.start()

    def cancel_download(self) -> None:
        """Cancel an ongoing download."""
        self._download_cancelled = True

    def _download_update_sync(
        self,
        update_info: UpdateInfo,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[Path]:
        """
        Download update synchronously.

        Returns:
            Path to downloaded file, or None if cancelled
        """
        # Create temp directory for download
        temp_dir = Path(tempfile.gettempdir()) / "HotelPriceChecker_update"
        temp_dir.mkdir(exist_ok=True)

        download_path = temp_dir / update_info.asset_name

        try:
            response = requests.get(
                update_info.download_url,
                stream=True,
                timeout=30
            )
            response.raise_for_status()

            total_size = update_info.asset_size
            downloaded = 0
            chunk_size = 8192

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self._download_cancelled:
                        logger.info("Download cancelled by user")
                        return None

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if on_progress:
                            on_progress(downloaded, total_size)

            logger.info(f"Update downloaded to: {download_path}")
            return download_path

        except requests.RequestException as e:
            logger.error(f"Error downloading update: {e}")
            raise

    def install_update(self, installer_path: Path) -> bool:
        """
        Install the downloaded update.

        For Windows, this runs the installer and exits the current app.

        Args:
            installer_path: Path to the downloaded installer

        Returns:
            True if installation started successfully
        """
        if not installer_path.exists():
            logger.error(f"Installer not found: {installer_path}")
            return False

        try:
            if sys.platform == "win32":
                if installer_path.suffix.lower() == ".exe":
                    # Run installer and exit
                    logger.info(f"Starting installer: {installer_path}")
                    subprocess.Popen(
                        [str(installer_path)],
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                    return True
                elif installer_path.suffix.lower() == ".zip":
                    # For ZIP, just open the folder
                    os.startfile(installer_path.parent)
                    return True

            elif sys.platform == "darwin":
                if installer_path.suffix.lower() == ".dmg":
                    # Open DMG on macOS
                    subprocess.Popen(["open", str(installer_path)])
                    return True

            logger.warning(f"Don't know how to install: {installer_path}")
            return False

        except Exception as e:
            logger.error(f"Error starting installer: {e}")
            return False


def get_updater() -> Updater:
    """Get a singleton Updater instance."""
    if not hasattr(get_updater, "_instance"):
        get_updater._instance = Updater()
    return get_updater._instance
