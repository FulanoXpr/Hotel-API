"""
Icon generation module for Hotel Price Checker.

Generates simple geometric icons using Pillow's ImageDraw,
avoiding external icon file dependencies. Each icon is drawn
on a transparent background with anti-aliased lines.

Icons are returned as CTkImage objects with separate light/dark
variants (white icons for dark backgrounds, dark icons for light).
"""

from functools import lru_cache
from typing import Callable, Dict, Tuple

from PIL import Image, ImageDraw

import customtkinter as ctk


# Default icon sizes
ICON_SIZE_SM = (16, 16)
ICON_SIZE_MD = (20, 20)

# Colors for icon variants
_DARK_COLOR = "#2b2b2b"   # For light theme backgrounds
_LIGHT_COLOR = "#e8e8e8"  # For dark theme backgrounds


def _new_canvas(size: int = 16) -> Tuple[Image.Image, ImageDraw.Draw]:
    """Create a transparent RGBA canvas and its draw context."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    return img, draw


def _draw_key(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Key icon — circle head + shaft + teeth."""
    # Circle head (top-left)
    r = s * 0.22
    cx, cy = s * 0.35, s * 0.3
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(1, s // 12))
    # Shaft
    draw.line([(cx, cy + r), (cx, s * 0.85)], fill=color, width=max(1, s // 12))
    # Teeth
    draw.line([(cx, s * 0.65), (cx + s * 0.2, s * 0.65)], fill=color, width=max(1, s // 12))
    draw.line([(cx, s * 0.78), (cx + s * 0.15, s * 0.78)], fill=color, width=max(1, s // 12))


def _draw_list(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """List / clipboard icon — three horizontal lines."""
    w = max(1, s // 12)
    x1, x2 = s * 0.25, s * 0.75
    for y_frac in (0.3, 0.5, 0.7):
        y = s * y_frac
        draw.line([(x1, y), (x2, y)], fill=color, width=w)


def _draw_play(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Play icon — right-pointing triangle."""
    m = s * 0.2  # margin
    draw.polygon(
        [(m, m), (s - m, s * 0.5), (m, s - m)],
        fill=color,
    )


def _draw_chart(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Chart icon — three vertical bars."""
    w = max(2, int(s * 0.15))
    gap = s * 0.05
    bars = [
        (s * 0.15, s * 0.55, s * 0.85),   # short
        (s * 0.42, s * 0.25, s * 0.85),   # tall
        (s * 0.69, s * 0.4, s * 0.85),    # medium
    ]
    for x, y_top, y_bot in bars:
        draw.rectangle([x, y_top, x + w, y_bot], fill=color)


def _draw_download(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Download icon — down arrow + base line."""
    w = max(1, s // 12)
    cx = s * 0.5
    # Vertical shaft
    draw.line([(cx, s * 0.15), (cx, s * 0.6)], fill=color, width=w)
    # Arrowhead
    draw.line([(s * 0.3, s * 0.45), (cx, s * 0.65)], fill=color, width=w)
    draw.line([(s * 0.7, s * 0.45), (cx, s * 0.65)], fill=color, width=w)
    # Base line
    draw.line([(s * 0.2, s * 0.82), (s * 0.8, s * 0.82)], fill=color, width=w)


def _draw_database(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Database icon — stacked rounded rectangles."""
    w = max(1, s // 12)
    x1, x2 = s * 0.2, s * 0.8
    h = s * 0.18
    for y_top in (s * 0.15, s * 0.4, s * 0.65):
        draw.rounded_rectangle(
            [x1, y_top, x2, y_top + h],
            radius=max(1, s // 10),
            outline=color,
            width=w,
        )


def _draw_folder(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Folder icon — rectangle with tab."""
    w = max(1, s // 12)
    # Tab
    draw.polygon(
        [(s * 0.15, s * 0.3), (s * 0.15, s * 0.2), (s * 0.4, s * 0.2), (s * 0.45, s * 0.3)],
        outline=color,
        width=w,
    )
    # Body
    draw.rounded_rectangle(
        [s * 0.15, s * 0.3, s * 0.85, s * 0.8],
        radius=max(1, s // 12),
        outline=color,
        width=w,
    )


def _draw_save(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Save / floppy disk icon."""
    w = max(1, s // 12)
    m = s * 0.15
    # Outer rectangle
    draw.rounded_rectangle(
        [m, m, s - m, s - m],
        radius=max(1, s // 10),
        outline=color,
        width=w,
    )
    # Top slot (disk opening)
    draw.rectangle([s * 0.35, m, s * 0.65, s * 0.4], fill=color)
    # Bottom label area
    draw.rectangle([s * 0.25, s * 0.55, s * 0.75, s * 0.78], outline=color, width=w)


def _draw_search(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Search / magnifying glass icon."""
    w = max(1, s // 10)
    r = s * 0.25
    cx, cy = s * 0.4, s * 0.4
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)
    # Handle
    draw.line(
        [(cx + r * 0.7, cy + r * 0.7), (s * 0.82, s * 0.82)],
        fill=color,
        width=max(2, s // 8),
    )


def _draw_trash(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Trash icon — can with lid."""
    w = max(1, s // 12)
    # Lid
    draw.line([(s * 0.2, s * 0.28), (s * 0.8, s * 0.28)], fill=color, width=w)
    # Handle on lid
    draw.line([(s * 0.4, s * 0.28), (s * 0.4, s * 0.18)], fill=color, width=w)
    draw.line([(s * 0.4, s * 0.18), (s * 0.6, s * 0.18)], fill=color, width=w)
    draw.line([(s * 0.6, s * 0.18), (s * 0.6, s * 0.28)], fill=color, width=w)
    # Can body (trapezoid)
    draw.polygon(
        [(s * 0.25, s * 0.32), (s * 0.75, s * 0.32), (s * 0.7, s * 0.85), (s * 0.3, s * 0.85)],
        outline=color,
        width=w,
    )


def _draw_clear(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Clear / X icon."""
    w = max(2, s // 8)
    m = s * 0.25
    draw.line([(m, m), (s - m, s - m)], fill=color, width=w)
    draw.line([(s - m, m), (m, s - m)], fill=color, width=w)


def _draw_plus(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Plus icon."""
    w = max(2, s // 8)
    m = s * 0.25
    cx, cy = s * 0.5, s * 0.5
    draw.line([(cx, m), (cx, s - m)], fill=color, width=w)
    draw.line([(m, cy), (s - m, cy)], fill=color, width=w)


def _draw_refresh(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Refresh / circular arrow icon."""
    w = max(1, s // 10)
    m = s * 0.18
    # Draw arc (3/4 circle)
    draw.arc([m, m, s - m, s - m], start=30, end=330, fill=color, width=w)
    # Arrowhead at the end of the arc
    ax, ay = s * 0.72, s * 0.22
    draw.polygon(
        [(ax, ay - s * 0.1), (ax + s * 0.12, ay + s * 0.02), (ax - s * 0.02, ay + s * 0.08)],
        fill=color,
    )


def _draw_moon(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Moon / crescent icon for dark mode."""
    # Draw full circle
    m = s * 0.18
    draw.ellipse([m, m, s - m, s - m], fill=color)
    # Cut out with offset circle (transparent)
    offset = s * 0.22
    draw.ellipse(
        [m + offset, m - s * 0.05, s - m + offset, s - m - s * 0.05],
        fill=(0, 0, 0, 0),
    )


def _draw_sun(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Sun icon for light mode."""
    import math

    cx, cy = s * 0.5, s * 0.5
    r = s * 0.18
    w = max(1, s // 12)
    # Center circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    # Rays
    ray_inner = s * 0.28
    ray_outer = s * 0.42
    for i in range(8):
        angle = math.radians(i * 45)
        x1 = cx + ray_inner * math.cos(angle)
        y1 = cy + ray_inner * math.sin(angle)
        x2 = cx + ray_outer * math.cos(angle)
        y2 = cy + ray_outer * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=w)


def _draw_stop(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Stop icon — filled square."""
    m = s * 0.25
    draw.rectangle([m, m, s - m, s - m], fill=color)


def _draw_export(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Export icon — arrow out of box."""
    w = max(1, s // 12)
    # Box (open top)
    draw.line([(s * 0.2, s * 0.4), (s * 0.2, s * 0.85)], fill=color, width=w)
    draw.line([(s * 0.2, s * 0.85), (s * 0.8, s * 0.85)], fill=color, width=w)
    draw.line([(s * 0.8, s * 0.85), (s * 0.8, s * 0.4)], fill=color, width=w)
    # Up arrow
    cx = s * 0.5
    draw.line([(cx, s * 0.6), (cx, s * 0.12)], fill=color, width=w)
    draw.line([(s * 0.32, s * 0.28), (cx, s * 0.12)], fill=color, width=w)
    draw.line([(s * 0.68, s * 0.28), (cx, s * 0.12)], fill=color, width=w)


def _draw_copy(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Copy / clipboard icon — two overlapping rectangles."""
    w = max(1, s // 12)
    # Back rectangle
    draw.rounded_rectangle(
        [s * 0.3, s * 0.15, s * 0.85, s * 0.7],
        radius=max(1, s // 14),
        outline=color,
        width=w,
    )
    # Front rectangle (filled background to create overlap effect)
    draw.rounded_rectangle(
        [s * 0.15, s * 0.3, s * 0.7, s * 0.85],
        radius=max(1, s // 14),
        outline=color,
        fill=(0, 0, 0, 0),
        width=w,
    )


def _draw_calendar(draw: ImageDraw.Draw, color: str, s: int) -> None:
    """Calendar icon — rectangle with grid."""
    w = max(1, s // 12)
    m = s * 0.15
    # Outer box
    draw.rounded_rectangle(
        [m, s * 0.22, s - m, s - m],
        radius=max(1, s // 12),
        outline=color,
        width=w,
    )
    # Top hooks
    draw.line([(s * 0.35, s * 0.12), (s * 0.35, s * 0.32)], fill=color, width=w)
    draw.line([(s * 0.65, s * 0.12), (s * 0.65, s * 0.32)], fill=color, width=w)
    # Header line
    draw.line([(m, s * 0.4), (s - m, s * 0.4)], fill=color, width=w)
    # Grid dots (days)
    dot_r = max(1, s // 16)
    for row in range(2):
        for col in range(3):
            dx = s * 0.3 + col * s * 0.2
            dy = s * 0.52 + row * s * 0.17
            draw.ellipse([dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r], fill=color)


# Registry of all icon draw functions
_ICON_REGISTRY: Dict[str, Callable] = {
    "key": _draw_key,
    "list": _draw_list,
    "play": _draw_play,
    "chart": _draw_chart,
    "download": _draw_download,
    "database": _draw_database,
    "folder": _draw_folder,
    "save": _draw_save,
    "search": _draw_search,
    "trash": _draw_trash,
    "clear": _draw_clear,
    "plus": _draw_plus,
    "refresh": _draw_refresh,
    "moon": _draw_moon,
    "sun": _draw_sun,
    "stop": _draw_stop,
    "export": _draw_export,
    "copy": _draw_copy,
    "calendar": _draw_calendar,
}


def _generate_icon(name: str, size: int, color: str) -> Image.Image:
    """Generate a single icon image."""
    draw_fn = _ICON_REGISTRY.get(name)
    if draw_fn is None:
        raise ValueError(f"Unknown icon: {name}. Available: {list(_ICON_REGISTRY.keys())}")
    img, draw = _new_canvas(size)
    draw_fn(draw, color, size)
    return img


@lru_cache(maxsize=128)
def get_icon(name: str, size: Tuple[int, int] = ICON_SIZE_SM) -> ctk.CTkImage:
    """
    Get a CTkImage icon with automatic light/dark variants.

    Args:
        name: Icon name (e.g., "search", "save", "folder").
        size: Tuple (width, height) for display size.

    Returns:
        CTkImage with light and dark variants.
    """
    # Generate at 2x for retina, CTkImage handles scaling
    render_size = max(size[0], size[1]) * 2

    light_img = _generate_icon(name, render_size, _DARK_COLOR)
    dark_img = _generate_icon(name, render_size, _LIGHT_COLOR)

    return ctk.CTkImage(
        light_image=light_img,
        dark_image=dark_img,
        size=size,
    )


def available_icons() -> list:
    """Return list of available icon names."""
    return sorted(_ICON_REGISTRY.keys())
