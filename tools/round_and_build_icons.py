#!/usr/bin/env python3
"""
Round all app icons from root logo.png and rebuild .icns.

Requirements:
  - Pillow (pip install pillow)
  - macOS iconutil in PATH

Outputs:
  - Rounded PNGs inside src/bubblebot/logo/icon.iconset/
  - Monochrome rounded status icons: src/bubblebot/logo/logo_white.png, logo_black.png
  - Rebuilt src/bubblebot/logo/icon.icns
"""
from __future__ import annotations

import os
import math
import subprocess
from pathlib import Path
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageOps, ImageChops, ImageFilter
except Exception as e:  # pragma: no cover - helpful error for local runs
    raise SystemExit("Pillow not installed. Run: pip install pillow")

ROOT = Path(__file__).resolve().parents[1]
SRC_LOGO = ROOT / "logo.png"
ASSET_DIR = ROOT / "src" / "bubblebot" / "logo"
ICONSET = ASSET_DIR / "icon.iconset"
ICNS = ASSET_DIR / "icon.icns"

# macOS iconset sizes
SIZES: Tuple[int, ...] = (16, 32, 128, 256, 512)

# Foreground content scale inside the outer shape (1.0 = fill the shape)
ICON_CONTENT_SCALE = 0.95
# Status bar icon should fill the canvas so outer silhouette is rounded
STATUS_CONTENT_SCALE = 1.0
# Outer shape (squircle) scale relative to canvas (e.g., 0.83 = 83% of canvas)
OUTER_SHAPE_SCALE = 0.83


def ensure_square_rgba(img: Image.Image, size: int, scale: float) -> Image.Image:
    """Return an RGBA square image with full-bleed background + centered content.
    - Background: image scaled to COVER the canvas (fills fully, cropped if needed)
    - Foreground: image scaled to CONTAIN within `scale*size` then centered
    This guarantees the outer silhouette can be a rounded squircle even when content < 100%.
    """
    img = img.convert("RGBA")
    # Full-bleed background (cover)
    cover = ImageOps.fit(img, (size, size), Image.LANCZOS, bleed=0.0, centering=(0.5, 0.5))
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(cover, (0, 0))
    # Foreground content (contain)
    content_px = max(1, int(size * float(scale)))
    contained = ImageOps.contain(img, (content_px, content_px), Image.LANCZOS)
    x = (size - contained.width) // 2
    y = (size - contained.height) // 2
    canvas.alpha_composite(contained, dest=(x, y))
    return canvas


def rounded_mask(size: int, radius_ratio: float = 0.18) -> Image.Image:
    """Simple rounded-rect mask (fallback)."""
    r = max(1, int(min(size, size) * radius_ratio))
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size, size)], radius=r, fill=255)
    return mask


def squircle_mask(size: int, exponent: float = 5.0, oversample: int = 4) -> Image.Image:
    """Generate an anti-aliased squircle (superellipse) mask approximating macOS Big Sur icon shape.
    Uses |x|^n + |y|^n <= 1 with n≈5.0 and oversampling for smooth edges.
    """
    W = size * oversample
    H = size * oversample
    hi = Image.new("L", (W, H), 0)
    px = hi.load()
    n = float(exponent)
    for j in range(H):
        # map j -> y in [-1, 1]
        y = (j + 0.5) / H * 2.0 - 1.0
        ay_n = abs(y) ** n
        for i in range(W):
            x = (i + 0.5) / W * 2.0 - 1.0
            inside = (abs(x) ** n + ay_n) <= 1.0
            if inside:
                px[i, j] = 255
    # downsample to target size for anti-aliased edge
    return hi.resize((size, size), Image.LANCZOS)


def make_rounded(img: Image.Image, size: int, radius_ratio: float = 0.18, scale: float = 1.0) -> Image.Image:
    base = ensure_square_rgba(img, size, scale)
    # Create scaled squircle mask centered on the canvas so the whole shape is OUTER_SHAPE_SCALE of canvas
    inner_size = max(1, int(size * OUTER_SHAPE_SCALE))
    try:
        inner = squircle_mask(inner_size)
    except Exception:
        inner = rounded_mask(inner_size, radius_ratio)
    mask = Image.new("L", (size, size), 0)
    ox = (size - inner.size[0]) // 2
    oy = (size - inner.size[1]) // 2
    mask.paste(inner, (ox, oy))
    base.putalpha(mask)
    return base


def save_iconset(img: Image.Image, radius_ratio: float = 0.18) -> None:
    ICONSET.mkdir(parents=True, exist_ok=True)
    # Clear iconset folder first
    for p in ICONSET.glob("*.png"):
        p.unlink()
    for size in SIZES:
        base = make_rounded(img, size, radius_ratio, ICON_CONTENT_SCALE)
        base.save(ICONSET / f"icon_{size}x{size}.png")
        retina = make_rounded(img, size * 2, radius_ratio, ICON_CONTENT_SCALE)
        retina.save(ICONSET / f"icon_{size}x{size}@2x.png")


def _extract_bubble_mask(img: Image.Image, work_size: int = 256) -> Image.Image:
    """Extract central 'bubble' as a binary mask (L-mode) from logo.png.
    Heuristic: detect near-white, low-saturation regions, then keep the largest
    connected component (the central bubble), discarding sparkles.
    Returns an L image at work_size with 0..255 values.
    """
    src = ImageOps.contain(img.convert("RGB"), (work_size, work_size), Image.LANCZOS)
    hsv = src.convert("HSV")
    H, S, V = hsv.split()
    # Threshold: low saturation and high value
    s_th = 40   # 0..255, lower = more selective (near white)
    v_th = 210  # 0..255, higher = brighter
    s_px = S.load(); v_px = V.load()
    bw = Image.new("L", (src.width, src.height), 0)
    m = bw.load()
    for y in range(src.height):
        for x in range(src.width):
            if s_px[x, y] <= s_th and v_px[x, y] >= v_th:
                m[x, y] = 255
    # Morphological cleanup: close small holes and remove speckles
    bw = bw.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    # Connected-component: keep largest
    data = bw.load()
    W, Ht = bw.size
    visited = [[False]*W for _ in range(Ht)]
    best = []
    best_area = 0
    from collections import deque
    for y in range(Ht):
        for x in range(W):
            if data[x, y] < 128 or visited[y][x]:
                continue
            q = deque([(x, y)])
            visited[y][x] = True
            comp = []
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < W and 0 <= ny < Ht and not visited[ny][nx] and data[nx, ny] >= 128:
                        visited[ny][nx] = True
                        q.append((nx, ny))
            if len(comp) > best_area:
                best_area = len(comp)
                best = comp
    mask = Image.new("L", (W, Ht), 0)
    if best:
        mp = mask.load()
        for x, y in best:
            mp[x, y] = 255
        # Smooth edges a touch
        mask = mask.filter(ImageFilter.GaussianBlur(0.6))
    return mask


def save_status_icons(img: Image.Image, radius_ratio: float = 0.25) -> None:
    # Build transparent background status icons with only the central bubble filled
    size = 18
    mask = _extract_bubble_mask(img, work_size=256)
    # Fit mask into 18x18 with small padding
    bbox = mask.getbbox() or (0,0,mask.width, mask.height)
    crop = mask.crop(bbox)
    # Scale to 18 with slight margin
    pad_scale = 0.92
    target = int(size * pad_scale)
    scaled = crop.resize((target, target), Image.LANCZOS)
    # Center onto transparent canvas
    alpha = Image.new("L", (size, size), 0)
    ox = (size - target)//2
    oy = (size - target)//2
    alpha.paste(scaled, (ox, oy))
    # Compose white and black variants
    for name, color in (("logo_white.png", (255,255,255,255)), ("logo_black.png", (0,0,0,255))):
        out = Image.new("RGBA", (size, size), (0,0,0,0))
        fg = Image.new("RGBA", (size, size), color)
        out = Image.composite(fg, out, alpha)
        out.save(ASSET_DIR / name)


def build_icns() -> None:
    if not ICONSET.exists():
        raise SystemExit(f"Iconset not found: {ICONSET}")
    cmd = [
        "/usr/bin/iconutil",
        "--convert",
        "icns",
        "--output",
        str(ICNS),
        str(ICONSET),
    ]
    subprocess.run(cmd, check=True)


def main():
    if not SRC_LOGO.exists():
        raise SystemExit(f"Source logo not found: {SRC_LOGO}")
    img = Image.open(SRC_LOGO)
    # Slight rounding suitable for macOS style
    radius_ratio = 0.18
    save_iconset(img, radius_ratio)
    save_status_icons(img, radius_ratio=0.25)
    build_icns()
    print("Rounded icons generated and .icns rebuilt.")


if __name__ == "__main__":
    main()
