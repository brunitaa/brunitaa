#!/usr/bin/env python3
"""Generate the animated GitHub profile banners.

Run from the repository root:
    python scripts/banner/generate.py
"""

from __future__ import annotations

import html
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets/source/portrait.png"
SOURCE_SVG = ROOT / "assets/source/portrait.svg"
ASSETS = ROOT / "assets"
LOGOS = Path(__file__).resolve().parent / "logos"
DATA = Path(__file__).resolve().parent / "data"

W, H = 1180, 610
LOOP_SECONDS = 14.2
INTRO_SECONDS = 3.2
TRAVELLER_COUNT = 900
SEED = 314159

ROWS = [
    ("Engineer", "Bruna Antelo Prado"),
    ("Role", "Systems Engineer · Product-minded builder"),
    ("Base", "Bolivia · LATAM"),
    ("Education", "Systems Engineering"),
    ("Focus", "Backend + APIs + thoughtful UX"),
    ("Mission", "Solve real problems with code"),
    ("Toolchain", "VS Code · Git · Docker"),
    ("Core.Lang", "Python · JavaScript · TypeScript"),
    ("Frontend", "React · Tailwind · Web products"),
    ("Backend", "FastAPI · Express · Node"),
    ("Data", "Postgres · MongoDB · SQL"),
    ("Infra", "AWS · Azure · Vercel"),
    ("Grid.Mail", "bruna.antelo.dev@gmail.com"),
    ("Grid.LinkedIn", "/in/bruna-antelo"),
    ("Grid.GitHub", "brunitaa"),
    ("Grid.X", "@brunitaa"),
]

THEMES = {
    "dark": {
        "bg": "#0A101F",
        "panel": "#0D1628",
        "panel2": "#101B30",
        "line": "#25344C",
        "muted": "#8291A8",
        "text": "#DDE7F5",
        "portrait": "#AA9BEF",
        "chrome": "#22D3EE",
        "accent": "#10B981",
        "shadow": "#02050B",
    },
    "light": {
        "bg": "#F6F8FA",
        "panel": "#FFFFFF",
        "panel2": "#EDF3F7",
        "line": "#CBD7E1",
        "muted": "#64748B",
        "text": "#172033",
        "portrait": "#4A3D7A",
        "chrome": "#0891B2",
        "accent": "#10B981",
        "shadow": "#AAB7C4",
    },
}


def ensure_source_portrait() -> Path:
    """Ensure a portrait source exists without overwriting a real user image."""
    SOURCE.parent.mkdir(parents=True, exist_ok=True)

    portrait_svg = '''
    <svg xmlns="http://www.w3.org/2000/svg" width="420" height="500" viewBox="0 0 420 500">
      <defs>
        <linearGradient id="skin" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#f7d7bb"/>
          <stop offset="100%" stop-color="#e7b993"/>
        </linearGradient>
      </defs>
      <g>
        <path d="M70 415C110 350 150 318 175 294H245C270 318 310 350 350 415V500H70V415Z" fill="#4B3A70"/>
        <ellipse cx="210" cy="205" rx="94" ry="110" fill="url(#skin)"/>
        <path d="M118 182C118 108 164 58 210 58C255 58 302 108 302 182C292 146 276 118 250 96C235 85 224 80 210 80C176 80 142 117 129 154C124 168 120 175 118 182Z" fill="#1c1b2b"/>
        <path d="M132 166C146 121 170 100 210 100C250 100 274 121 288 166C280 141 261 120 210 120C160 120 142 139 132 166Z" fill="#201d31" opacity="0.85"/>
        <circle cx="175" cy="211" r="6" fill="#1c1b2b"/>
        <circle cx="245" cy="211" r="6" fill="#1c1b2b"/>
        <path d="M176 246C188 258 203 264 210 264C217 264 232 258 244 246" fill="none" stroke="#8f5a47" stroke-width="6" stroke-linecap="round"/>
        <path d="M170 286C189 298 201 302 210 302C219 302 231 298 250 286" fill="none" stroke="#a06d5d" stroke-width="7" stroke-linecap="round"/>
        <path d="M138 328C170 355 188 362 210 362C232 362 250 355 282 328L294 500H126L138 328Z" fill="#2c2443" opacity="0.92"/>
        <circle cx="210" cy="155" r="12" fill="#f2d9c4" opacity="0.28"/>
      </g>
    </svg>
    '''
    if not SOURCE_SVG.exists():
        SOURCE_SVG.write_text(portrait_svg.strip(), encoding="utf-8")

    # Keep an existing, real portrait image intact. Only generate the fallback
    # placeholder if there is no source PNG at all.
    if SOURCE.exists():
        return SOURCE

    image = Image.new("RGBA", (420, 500), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 415, 350, 500), radius=18, fill=(75, 58, 112, 255))
    draw.ellipse((116, 95, 304, 305), fill=(247, 215, 187, 255))
    draw.polygon([(118, 182), (145, 108), (175, 82), (210, 62), (246, 82), (275, 108), (302, 182), (292, 146), (273, 120), (236, 98), (210, 86), (185, 98), (147, 120), (128, 146)], fill=(28, 27, 43, 255))
    draw.ellipse((146, 180, 170, 236), fill=(28, 27, 43, 255))
    draw.ellipse((250, 180, 274, 236), fill=(28, 27, 43, 255))
    draw.arc((176, 240, 244, 268), start=180, end=0, fill=(143, 90, 71, 255), width=6)
    draw.arc((170, 283, 250, 307), start=180, end=0, fill=(160, 109, 93, 255), width=7)
    draw.polygon([(138, 328), (152, 370), (210, 360), (268, 370), (282, 328), (294, 500), (126, 500)], fill=(44, 36, 67, 255))
    image.save(SOURCE, optimize=True)

    return SOURCE


def make_logos() -> dict[str, Image.Image]:
    """Create software-oriented symbols for the banner: code, data, and platform stack."""
    LOGOS.mkdir(parents=True, exist_ok=True)
    size = 400
    logos: dict[str, Image.Image] = {}

    # Code / API icon: paired brackets and a slash.
    code = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(code)
    stroke = 42
    d.line([(154, 95), (66, 200), (154, 305)], fill="black", width=stroke, joint="curve")
    d.line([(246, 95), (334, 200), (246, 305)], fill="black", width=stroke, joint="curve")
    d.line([(225, 72), (174, 328)], fill="black", width=stroke)
    logos["code"] = code

    # Data / backend icon: layered database cylinders.
    data = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(data)
    body = [(95, 145), (305, 145), (305, 280), (95, 280)]
    d.rounded_rectangle((95, 120, 305, 295), radius=20, fill="black")
    d.ellipse((95, 120, 305, 155), fill="black")
    d.ellipse((95, 260, 305, 295), fill="black")
    d.line((145, 178, 145, 245), fill="white", width=8)
    d.line((200, 178, 200, 245), fill="white", width=8)
    d.line((255, 178, 255, 245), fill="white", width=8)
    d.line((105, 175, 295, 175), fill="white", width=7)
    d.line((105, 210, 295, 210), fill="white", width=7)
    d.line((105, 245, 295, 245), fill="white", width=7)
    logos["data"] = data

    # Stack / product icon: layered blocks and a node.
    stack = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(stack)
    layers = [(90, 150), (310, 150), (310, 250), (90, 250), (90, 150)]
    d.rectangle((100, 120, 300, 170), fill="black")
    d.rectangle((70, 180, 330, 230), fill="black")
    d.rectangle((120, 240, 280, 290), fill="black")
    d.ellipse((182, 143, 218, 179), fill="white")
    d.ellipse((278, 203, 314, 239), fill="white")
    d.ellipse((86, 203, 122, 239), fill="white")
    d.line((200, 175, 200, 205), fill="white", width=8)
    d.line((200, 205, 296, 219), fill="white", width=8)
    d.line((200, 205, 104, 219), fill="white", width=8)
    logos["stack"] = stack

    for name, image in logos.items():
        image.save(LOGOS / f"{name}.png", optimize=True)
    return logos


def floyd_steinberg(gray: np.ndarray) -> np.ndarray:
    """Serpentine 1-bit Floyd-Steinberg diffusion; True means a lit pixel."""
    work = gray.astype(np.float32) / 255.0
    out = np.zeros_like(work, dtype=bool)
    height, width = work.shape
    for y in range(height):
        left_to_right = y % 2 == 0
        xs = range(width) if left_to_right else range(width - 1, -1, -1)
        direction = 1 if left_to_right else -1
        for x in xs:
            old = work[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = bool(new)
            err = old - new
            nx = x + direction
            if 0 <= nx < width:
                work[y, nx] += err * 7 / 16
            if y + 1 < height:
                if 0 <= x - direction < width:
                    work[y + 1, x - direction] += err * 3 / 16
                work[y + 1, x] += err * 5 / 16
                if 0 <= nx < width:
                    work[y + 1, nx] += err * 1 / 16
    return out


def portrait_points(theme: str, rng: np.random.Generator) -> np.ndarray:
    """Return sampled x/y banner coordinates from a stable portrait grid."""
    source = Image.open(SOURCE).convert("RGBA")

    # Use the earlier stable crop that keeps the face complete without the overly
    # flattened, wall-like look caused by the more aggressive tuning.
    crop = ImageOps.fit(source, (420, 500), centering=(0.5, 0.55))
    crop = crop.resize((300, 340), Image.Resampling.LANCZOS)

    rgb = crop.convert("RGB")
    alpha = np.asarray(crop.getchannel("A"), dtype=np.float32) / 255.0

    if theme == "dark":
        lum = np.asarray(ImageOps.grayscale(rgb), dtype=np.float32)
        prepared = Image.fromarray(np.uint8(np.clip(lum * alpha, 0, 255)), "L")
        select_lit = True
    else:
        white = Image.new("RGBA", crop.size, "white")
        white.alpha_composite(crop)
        prepared = ImageOps.grayscale(white.convert("RGB"))
        select_lit = False

    if theme == "dark":
        mask = Image.fromarray(np.uint8((alpha > 0.08) * 255), "L")
        prepared = ImageOps.equalize(prepared, mask=mask)
    else:
        prepared = ImageOps.autocontrast(prepared, cutoff=0)

    prepared = ImageEnhance.Contrast(prepared).enhance(1.8)
    prepared = prepared.filter(ImageFilter.GaussianBlur(radius=0.6))
    bits = floyd_steinberg(np.asarray(prepared))
    active = bits if select_lit else ~bits
    if theme == "dark":
        active &= alpha > 0.08
    else:
        active &= np.asarray(prepared) < 240

    ys, xs = np.where(active)
    if len(xs) == 0:
        return np.zeros((0, 2), dtype=np.float32)
    points = np.column_stack((74 + xs, 154 + ys)).astype(np.float32)
    if len(points) > 18000:
        points = points[rng.choice(len(points), 18000, replace=False)]
    return points


def sample_logo_points(
    image: Image.Image, rng: np.random.Generator, count: int
) -> np.ndarray:
    """Sample a silhouette into the portrait frame's visual coordinate space."""
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.where(alpha > 127)
    chosen = rng.choice(len(xs), count, replace=len(xs) < count)
    # Logo occupies a centered 270x270 square inside VISUAL.MAP.
    return np.column_stack((89 + xs[chosen] * 0.675, 188 + ys[chosen] * 0.675)).astype(
        np.float32
    )


def transport(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Order target points by minimum-cost assignment from source points."""
    rows, cols = linear_sum_assignment(cdist(source, target, metric="sqeuclidean"))
    ordered = np.empty_like(target)
    ordered[rows] = target[cols]
    return ordered


def num(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def point_path(points: np.ndarray) -> str:
    """Aggregate adjacent horizontal one-pixel dots into compact SVG path runs."""
    if not len(points):
        return ""
    integer = np.rint(points).astype(int)
    unique = sorted({(int(x), int(y)) for x, y in integer}, key=lambda p: (p[1], p[0]))
    chunks: list[str] = []
    i = 0
    while i < len(unique):
        x0, y = unique[i]
        x1 = x0
        i += 1
        while i < len(unique) and unique[i][1] == y and unique[i][0] <= x1 + 1:
            x1 = unique[i][0]
            i += 1
        chunks.append(f"M{x0} {y}h{x1 - x0 + 1}")
    return "".join(chunks)


def dotted_leader(x1: float, x2: float, y: float) -> str:
    if x2 <= x1:
        return ""
    return "".join(f"M{x} {num(y)}h1" for x in np.arange(x1, x2, 5.0))


def text_width(text: str, font_size: float) -> float:
    """Stable monospace width used both for textLength and leader placement."""
    return len(text) * font_size * 0.605


def animate_values(points: list[np.ndarray], index: int) -> str:
    return ";".join(f"{num(p[index, 0])} {num(p[index, 1])}" for p in points)


def render_svg(
    theme_name: str,
    portrait: np.ndarray,
    logo_points: dict[str, np.ndarray],
    rng: np.random.Generator,
) -> str:
    t = THEMES[theme_name]
    n = min(TRAVELLER_COUNT, len(portrait))
    source = portrait[rng.choice(len(portrait), n, replace=False)]
    code = transport(source, logo_points["code"][:n])
    data = transport(code, logo_points["data"][:n])
    stack = transport(data, logo_points["stack"][:n])

    # Explicit uneven phase boundaries: 3.0 portrait, 2.0 per logo,
    # and four 1.3 transitions = 14.2 seconds.
    times = [0, 3.0, 4.3, 6.3, 7.6, 9.6, 10.9, 12.9, 14.2]
    key_times = ";".join(num(v / LOOP_SECONDS) for v in times)
    # Returning each traveller to its exact starting portrait coordinate keeps
    # the repeat boundary seamless. All logo-to-logo morphs use optimal transport.
    frames = [source, source, code, code, data, data, stack, stack, source]
    opacity_values = "0;0;1;1;1;1;1;1;0"

    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
        'aria-labelledby="title desc">',
        "<title id=\"title\">Bruna's live system profile</title>",
        '<desc id="desc">Animated terminal profile for Bruna, a software developer from Bolivia, '
        "highlighting learning, building, and community impact.</desc>",
        "<defs>",
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">'
        f'<feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="{t["shadow"]}" '
        'flood-opacity=".28"/></filter>',
        '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%">'
        f'<feGaussianBlur stdDeviation="3" result="b"/><feFlood flood-color="{t["chrome"]}" '
        'flood-opacity=".35"/><feComposite in2="b" operator="in"/>'
        '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<clipPath id="visualClip"><rect x="49" y="124" width="390" height="414" rx="3"/></clipPath>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
        f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" '
        f'stroke="{t["line"]}" filter="url(#shadow)"/>',
        f'<path d="M13 62H1167" stroke="{t["line"]}"/>',
        '<circle cx="38" cy="38" r="6" fill="#FF5F57"/>'
        '<circle cx="59" cy="38" r="6" fill="#FEBC2E"/>'
        '<circle cx="80" cy="38" r="6" fill="#28C840"/>',
        f'<text x="590" y="43" text-anchor="middle" fill="{t["muted"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
        'letter-spacing=".4">brunitaa // systems • software • people</text>',
        # Left visual frame.
        f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["panel2"]}" '
        f'stroke="{t["line"]}"/>',
        f'<path d="M35 124H453" stroke="{t["line"]}"/>',
        f'<text x="49" y="111" fill="{t["chrome"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
        'font-weight="700" letter-spacing="1.2">PORTRAIT / SIGNAL</text>',
        f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">300×340 / 1-BIT</text>',
        f'<path d="M49 141h12M49 141v12M439 141h-12M439 141v12M49 539h12M49 539v-12'
        f'M439 539h-12M439 539v-12" fill="none" stroke="{t["chrome"]}" opacity=".55"/>',
        '<g clip-path="url(#visualClip)" shape-rendering="crispEdges">',
        # Loop layer stays visible at t=0 so camo/static first frames still show the face.
        # Intro duplicate below shimmers on top, then hands off at 3.2s.
        '<g opacity="1">',
    ]

    # Dense portrait drift: 94 independently noisy bands moving toward the code icon centroid.
    code_centroid = code.mean(axis=0)
    band_ids = rng.integers(0, 94, size=len(portrait))
    noise = rng.normal(0, 4, size=(94, 2))
    for band in range(94):
        pts = portrait[band_ids == band]
        if not len(pts):
            continue
        centroid = pts.mean(axis=0)
        delta = (code_centroid - centroid) * 0.18 + noise[band]
        d = point_path(pts)
        parts.append(
            f'<path d="{d}" fill="none" stroke="{t["portrait"]}" stroke-width="1" '
            'opacity=".94"/>'
        )

    # Optimal-transport travellers, represented as tiny path squares (never glyphs).
    for i in range(n):
        positions = animate_values(frames, i)
        parts.append(
            f'<path d="M-.65-.65h1.3v1.3h-1.3z" fill="{t["portrait"]}" opacity=".94"/>'
        )
    parts.append("</g>")

    # One-shot scattered intro: sixty random, interleaved point groups.
    intro_ids = rng.integers(0, 60, size=len(portrait))
    order = rng.permutation(60)
    starts = np.empty(60)
    starts[order] = np.linspace(0.05, 1.2, 60)
    for group in range(60):
        pts = portrait[intro_ids == group]
        if not len(pts):
            continue
        parts.append(
            f'<path d="{point_path(pts)}" fill="none" stroke="{t["portrait"]}" '
            'stroke-width="1" opacity=".8"/>'
        )
    parts.extend(
        [
            "</g>",
            # Small frame telemetry.
            f'<text x="58" y="551" fill="{t["muted"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="10">'
            f'PTS {len(portrait):05d} · FS/SERPENTINE</text>',
            # Right information panel.
            f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" '
            f'stroke="{t["line"]}"/>',
            f'<path d="M474 124H1146" stroke="{t["line"]}"/>',
            f'<text x="490" y="111" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
            'font-weight="700" letter-spacing="1.2">BRUNA / ID</text>',
            # LIVE badge and handle pill.
            '<g filter="url(#glow)"><circle cx="915" cy="106" r="4" fill="#FF4D5A"/></g>',
            '<text x="927" y="111" fill="#FF4D5A" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" '
            'font-weight="700">LIVE</text>',
            f'<rect x="982" y="94" width="146" height="24" rx="12" fill="{t["chrome"]}" opacity=".16" '
            f'stroke="{t["chrome"]}"/>',
            f'<text x="1055" y="111" text-anchor="middle" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14" '
            'font-weight="700">@brunitaa</text>',
            f'<text x="490" y="170" fill="{t["text"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="52" '
            'font-weight="800" letter-spacing="1.4">BRUNA</text>',
            f'<text x="490" y="220" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="48" '
            'font-weight="800" letter-spacing="1.4">ANTELO</text>',
            f'<text x="490" y="258" fill="{t["text"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="22" '
            'font-weight="700" letter-spacing="1.6">SYSTEMS ENGINEER // FULL STACK</text>',
            f'<text x="490" y="292" fill="{t["muted"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
            'font-weight="600" letter-spacing="1.6">LATAM • BOLIVIA / SOFTWARE • PRODUCT • PEOPLE</text>',
            f'<rect x="490" y="310" width="85" height="24" rx="12" fill="{t["chrome"]}" opacity=".12" stroke="{t["chrome"]}"/>'
            f'<text x="532" y="327" text-anchor="middle" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" '
            'font-weight="700">BUILD</text>',
            f'<rect x="585" y="310" width="100" height="24" rx="12" fill="{t["chrome"]}" opacity=".12" stroke="{t["chrome"]}"/>'
            f'<text x="635" y="327" text-anchor="middle" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" '
            'font-weight="700">LEARN</text>',
            f'<rect x="695" y="310" width="110" height="24" rx="12" fill="{t["chrome"]}" opacity=".12" stroke="{t["chrome"]}"/>'
            f'<text x="750" y="327" text-anchor="middle" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" '
            'font-weight="700">SHIP</text>',
        ]
    )

    large_columns = [
        ("Focus", "Human-centered software"),
        ("Stack", "Python • JS • React"),
        ("Infra", "Azure • AWS • Vercel"),
    ]
    for idx, (label, value) in enumerate(large_columns):
        y = 355 + idx * 42
        parts.append(
            f'<text x="490" y="{num(y)}" fill="{t["muted"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" '
            'font-weight="600">'
            f'{html.escape(label)}</text>'
        )
        parts.append(
            f'<text x="620" y="{num(y)}" fill="{t["text"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="18" '
            'font-weight="700">'
            f'{html.escape(value)}</text>'
        )

    value_right = 1127.0
    row_y = 153.0
    for label, value in ROWS:
        value_len = text_width(value, 14)
        label_len = text_width(label, 14)
        leader_start = 491 + label_len + 12
        leader_end = value_right - value_len - 12
        parts.extend(
            [
                f'<text x="491" y="{num(row_y)}" fill="{t["muted"]}" '
                'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14">'
                f"{html.escape(label)}</text>",
                f'<path d="{dotted_leader(leader_start, leader_end, row_y - 4)}" '
                f'fill="none" stroke="{t["line"]}" stroke-width="1" shape-rendering="crispEdges"/>',
                f'<text x="{num(value_right)}" y="{num(row_y)}" text-anchor="end" '
                f'fill="{t["text"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
                f'font-size="14" textLength="{num(value_len)}" lengthAdjust="spacingAndGlyphs">'
                f"{html.escape(value)}</text>",
            ]
        )
        row_y += 23

    parts.extend(
        [
            f'<path d="M490 530H1130" stroke="{t["line"]}"/>',
            f'<text x="491" y="548" fill="{t["accent"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">'
            "● BUILD WITH PURPOSE</text>",
            f'<text x="1128" y="548" text-anchor="end" fill="{t["muted"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">'
            "UTC-4 · LATAM NODE</text>",
            "</svg>",
        ]
    )
    return "".join(parts)


def main() -> None:
    ensure_source_portrait()
    ASSETS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    logos = make_logos()

    # Cache theme-specific dither points as reproducible source data.
    portraits: dict[str, np.ndarray] = {}
    for index, theme in enumerate(THEMES):
        rng = np.random.default_rng(SEED + index)
        points = portrait_points(theme, rng)
        portraits[theme] = points
        np.save(DATA / f"portrait-{theme}.npy", points)

    for index, theme in enumerate(THEMES):
        rng = np.random.default_rng(SEED + 100 + index)
        sampled = {
            name: sample_logo_points(image, rng, TRAVELLER_COUNT)
            for name, image in logos.items()
        }
        for name, points in sampled.items():
            np.save(DATA / f"{name}-{theme}.npy", points)
        svg = render_svg(theme, portraits[theme], sampled, rng)
        output = ASSETS / f"banner-{theme}.v9.svg"
        output.write_text(svg, encoding="utf-8")
        byte_size = output.stat().st_size
        print(
            f"{output.relative_to(ROOT)}: {byte_size:,} bytes "
            f"({byte_size / 1024:.1f} KiB), {len(portraits[theme]):,} portrait dots, "
            f"{TRAVELLER_COUNT} travellers"
        )

    for name in logos:
        output = LOGOS / f"{name}.png"
        print(f"{output.relative_to(ROOT)}: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
