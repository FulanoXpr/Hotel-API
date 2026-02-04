#!/usr/bin/env python3
"""
Create Windows .ico file from the FPR logo PNG.

Usage:
    python create_icon.py

Output: ui/assets/icon.ico
"""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow not installed. Run: pip install Pillow")
    exit(1)


def create_ico():
    """Convert PNG logo to ICO with multiple sizes."""
    base_path = Path(__file__).parent
    png_path = base_path / "ui" / "assets" / "fpr_logo.png"
    ico_path = base_path / "ui" / "assets" / "icon.ico"

    if not png_path.exists():
        print(f"[ERROR] Logo not found: {png_path}")
        return False

    print(f"[INFO] Loading: {png_path}")

    # Open the PNG
    img = Image.open(png_path)

    # Convert to RGBA if needed
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # ICO sizes (Windows standard)
    sizes = [16, 24, 32, 48, 64, 128, 256]

    # Create resized versions
    icons = []
    for size in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        icons.append(resized)
        print(f"  Created {size}x{size}")

    # Save as ICO
    icons[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=icons[1:],
    )

    print(f"[OK] Created: {ico_path}")
    return True


if __name__ == "__main__":
    create_ico()
