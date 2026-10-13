"""
PWA Icon Generator for Istanbul Transit Core.
Creates high-resolution SVG and PNG icons (192, 512, maskable, apple-touch-icon).
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ICONS_DIR = Path(__file__).parent.parent / "static" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Generate SVG Icon
svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16" />
      <stop offset="50%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#1e293b" />
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="50%" stop-color="#0284c7" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
    <linearGradient id="m2Grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#06b6d4" />
    </linearGradient>
    <linearGradient id="metrobusGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ef4444" />
      <stop offset="100%" stop-color="#f59e0b" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="12" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Base with Rounded Corners -->
  <rect width="512" height="512" rx="112" fill="url(#bgGrad)" />

  <!-- Outer Glowing Accent Ring -->
  <circle cx="256" cy="256" r="190" fill="none" stroke="url(#accentGrad)" stroke-width="8" opacity="0.4" />
  <circle cx="256" cy="256" r="176" fill="none" stroke="#334155" stroke-width="2" stroke-dasharray="8 8" opacity="0.6" />

  <!-- Metro Lines Geometry (Symbolizing Istanbul transit crossroads) -->
  <!-- Metrobüs Arc -->
  <path d="M 110 370 Q 256 120 402 370" fill="none" stroke="url(#metrobusGrad)" stroke-width="14" stroke-linecap="round" />
  
  <!-- M2 / Marmaray Intersecting Line -->
  <path d="M 120 200 C 200 340 312 340 392 200" fill="none" stroke="url(#m2Grad)" stroke-width="14" stroke-linecap="round" />

  <!-- Central Navigation Compass / Pin Symbol -->
  <g transform="translate(256, 256)" filter="url(#glow)">
    <!-- Central Outer Pulse Circle -->
    <circle cx="0" cy="0" r="74" fill="#0f172a" stroke="url(#accentGrad)" stroke-width="6" />
    
    <!-- Dynamic Transit Arrow / Compass Needle -->
    <path d="M 0 -52 L 36 34 L 0 18 L -36 34 Z" fill="url(#accentGrad)" />
    
    <!-- Central Transit Hub Station Dot -->
    <circle cx="0" cy="0" r="10" fill="#ffffff" />
  </g>

  <!-- Transfer Hub Station Nodes -->
  <circle cx="160" cy="285" r="10" fill="#ffffff" stroke="#10b981" stroke-width="4" />
  <circle cx="352" cy="285" r="10" fill="#ffffff" stroke="#ef4444" stroke-width="4" />
  <circle cx="256" cy="180" r="12" fill="#ffffff" stroke="#06b6d4" stroke-width="4" />

  <!-- Modern Monogram Text Badge 'İT' at Bottom -->
  <rect x="206" y="405" width="100" height="34" rx="17" fill="#1e293b" stroke="#38bdf8" stroke-width="2" opacity="0.9" />
  <text x="256" y="428" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="900" fill="#38bdf8" text-anchor="middle" letter-spacing="3">İSTANBUL</text>
</svg>
"""

(ICONS_DIR / "icon.svg").write_text(svg_content.strip(), encoding="utf-8")
print("Saved icon.svg")


def create_png_icon(size: int, is_maskable: bool = False, is_apple: bool = False) -> Image.Image:
    """Renders a clean high-dpi PNG icon matching the design with PIL."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    scale = size / 512.0
    
    # Background
    if is_maskable:
        # Full bleed background for adaptive icons
        draw.rectangle([0, 0, size, size], fill=(15, 23, 42, 255))
    elif is_apple:
        # Apple touch icons prefer solid rounded or square (iOS masks it itself)
        draw.rectangle([0, 0, size, size], fill=(15, 23, 42, 255))
    else:
        # Standalone icon with rounded rect
        corner = int(112 * scale)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=corner, fill=(15, 23, 42, 255))

    center = size / 2.0
    r_outer = 180 * scale
    draw.ellipse(
        [center - r_outer, center - r_outer, center + r_outer, center + r_outer],
        outline=(2, 132, 199, 180),
        width=max(2, int(6 * scale))
    )

    # Metro Curves
    pts_red = []
    pts_cyan = []
    steps = 40
    for i in range(steps + 1):
        t = i / steps
        # Parabola arc 1
        x1 = (110 + (402 - 110) * t) * scale
        y1 = (370 - 4 * 160 * t * (1 - t)) * scale
        pts_red.append((x1, y1))
        
        # Parabola arc 2
        x2 = (120 + (392 - 120) * t) * scale
        y2 = (210 + 4 * 140 * t * (1 - t)) * scale
        pts_cyan.append((x2, y2))

    draw.line(pts_red, fill=(239, 68, 68, 240), width=max(3, int(12 * scale)), joint="curve")
    draw.line(pts_cyan, fill=(16, 185, 129, 240), width=max(3, int(12 * scale)), joint="curve")

    # Central Hub
    r_hub = int(68 * scale)
    draw.ellipse(
        [center - r_hub, center - r_hub, center + r_hub, center + r_hub],
        fill=(15, 23, 42, 255),
        outline=(6, 182, 212, 255),
        width=max(2, int(5 * scale))
    )

    # Navigation Arrow
    arrow_tip = (center, center - int(48 * scale))
    arrow_right = (center + int(32 * scale), center + int(32 * scale))
    arrow_mid = (center, center + int(16 * scale))
    arrow_left = (center - int(32 * scale), center + int(32 * scale))

    draw.polygon([arrow_tip, arrow_right, arrow_mid], fill=(2, 132, 199, 255))
    draw.polygon([arrow_tip, arrow_mid, arrow_left], fill=(6, 182, 212, 255))

    # Center dot
    r_dot = max(2, int(8 * scale))
    draw.ellipse(
        [center - r_dot, center - r_dot, center + r_dot, center + r_dot],
        fill=(255, 255, 255, 255)
    )

    # Node stations
    n1 = ((160 * scale), (285 * scale))
    n2 = ((352 * scale), (285 * scale))
    r_node = max(3, int(8 * scale))
    draw.ellipse([n1[0] - r_node, n1[1] - r_node, n1[0] + r_node, n1[1] + r_node], fill=(255, 255, 255), outline=(16, 185, 129), width=max(1, int(3 * scale)))
    draw.ellipse([n2[0] - r_node, n2[1] - r_node, n2[0] + r_node, n2[1] + r_node], fill=(255, 255, 255), outline=(239, 68, 68), width=max(1, int(3 * scale)))

    return img


# Generate all required PNG targets
sizes = {
    "icon-192.png": (192, False, False),
    "icon-512.png": (512, False, False),
    "icon-maskable-192.png": (192, True, False),
    "icon-maskable-512.png": (512, True, False),
    "apple-touch-icon.png": (180, False, True),
    "favicon.png": (64, False, False),
}

for filename, (s, maskable, apple) in sizes.items():
    icon_img = create_png_icon(s, is_maskable=maskable, is_apple=apple)
    out_path = ICONS_DIR / filename
    icon_img.save(out_path, format="PNG", optimize=True)
    print(f"Generated {filename} ({s}x{s})")

print("All icons successfully created!")
