#!/usr/bin/env python3
"""Generate smooth, looping ocean-wave GIFs for the profile README."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
WIDTH, HEIGHT = 1200, 156
SCALE = 3
FRAME_COUNT = 48
FRAME_DURATION_MS = 60
LAYERS = (
    (65, 12, 5, 470, 185, 1.0, 0.1, "#2F81F7"),
    (91, 11, 4, 390, 155, -0.72, 1.8, "#1F6FEB"),
    (117, 8, 3, 330, 125, 0.52, 3.1, "#0B4FA8"),
)
THEMES = {
    "dark": {
        "background": "#0D1117",
        "crests": ("#A5D6FF", "#79C0FF", "#58A6FF"),
    },
    "light": {
        "background": "#FFFFFF",
        "crests": ("#0969DA", "#218BFF", "#54AEFF"),
    },
}


def wave_points(
    baseline: float,
    amplitude: float,
    secondary_amplitude: float,
    wavelength: float,
    secondary_wavelength: float,
    speed: float,
    offset: float,
    phase: float,
) -> list[tuple[int, int]]:
    points = []
    for x in range(-4, WIDTH + 5, 2):
        primary = math.sin(2 * math.pi * x / wavelength - phase * speed + offset)
        secondary = math.sin(
            2 * math.pi * x / secondary_wavelength - phase * speed * 1.37 + offset * 1.6
        )
        y = baseline + amplitude * primary + secondary_amplitude * secondary
        points.append((x * SCALE, round(y * SCALE)))
    return points


def render_frame(theme: dict[str, object], frame_number: int) -> Image.Image:
    image = Image.new(
        "RGB",
        (WIDTH * SCALE, HEIGHT * SCALE),
        str(theme["background"]),
    )
    draw = ImageDraw.Draw(image)
    phase = 2 * math.pi * frame_number / FRAME_COUNT
    crests = theme["crests"]

    for index, layer in enumerate(LAYERS):
        baseline, amplitude, secondary, wavelength, short_wavelength, speed, offset, color = layer
        points = wave_points(
            baseline,
            amplitude,
            secondary,
            wavelength,
            short_wavelength,
            speed,
            offset,
            phase,
        )
        draw.polygon(
            points + [(WIDTH * SCALE, HEIGHT * SCALE), (0, HEIGHT * SCALE)],
            fill=color,
        )
        crest = [(x, y - 2 * SCALE) for x, y in points]
        draw.line(crest, fill=crests[index], width=2 * SCALE, joint="curve")

    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def save_theme(name: str, theme: dict[str, object]) -> None:
    frames = [render_frame(theme, index) for index in range(FRAME_COUNT)]

    sample = Image.new("RGB", (WIDTH, HEIGHT))
    for index, frame in enumerate(frames[::4]):
        thumbnail = frame.resize((WIDTH // 4, HEIGHT // 4), Image.Resampling.LANCZOS)
        sample.paste(thumbnail, ((index % 4) * (WIDTH // 4), (index // 4) * (HEIGHT // 4)))
    palette = sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed_frames = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames
    ]
    destination = ROOT / "assets" / f"waves-{name}.gif"
    indexed_frames[0].save(
        destination,
        save_all=True,
        append_images=indexed_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=False,
        disposal=2,
    )
    print(f"Wrote {destination.relative_to(ROOT)}")


def main() -> None:
    for name, theme in THEMES.items():
        save_theme(name, theme)


if __name__ == "__main__":
    main()
