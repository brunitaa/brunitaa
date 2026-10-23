
from pathlib import Path
import math

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT / "assets"

WIDTH = 1200
HEIGHT = 156
SCALE = 2
FRAME_COUNT = 120
FRAME_DURATION = 60
PALETTE_COLORS = 128

RESAMPLE = Image.Resampling.LANCZOS


THEMES = {
    "dark": {
        "background": (13, 17, 23),
        "waves": [
            {
                "color": (20, 75, 125),
                "base": 0.79,
                "amplitude": 0.075,
                "cycles": 1,
                "speed": 1.0,
                "detail": 0.22,
            },
            {
                "color": (30, 105, 165),
                "base": 0.87,
                "amplitude": 0.065,
                "cycles": 2,
                "speed": -1.0,
                "detail": 0.18,
            },
            {
                "color": (55, 145, 195),
                "base": 0.96,
                "amplitude": 0.055,
                "cycles": 3,
                "speed": 1.0,
                "detail": 0.12,
            },
        ],
    },
    "light": {
        "background": (255, 255, 255),
        "waves": [
            {
                "color": (190, 225, 245),
                "base": 0.79,
                "amplitude": 0.075,
                "cycles": 1,
                "speed": 1.0,
                "detail": 0.22,
            },
            {
                "color": (115, 190, 230),
                "base": 0.87,
                "amplitude": 0.065,
                "cycles": 2,
                "speed": -1.0,
                "detail": 0.18,
            },
            {
                "color": (45, 145, 205),
                "base": 0.96,
                "amplitude": 0.055,
                "cycles": 3,
                "speed": 1.0,
                "detail": 0.12,
            },
        ],
    },
}


def create_wave_frame(theme, frame_index):
    width = WIDTH * SCALE
    height = HEIGHT * SCALE

    image = Image.new("RGB", (width, height), theme["background"])
    draw = ImageDraw.Draw(image)
    x_positions = range(0, width + 1, SCALE)

    for wave in theme["waves"]:
        points = []

        phase = (
            2 * math.pi
            * wave["cycles"]
            * wave["speed"]
            * frame_index
            / FRAME_COUNT
        )

        base_y = wave["base"] * height
        amplitude = wave["amplitude"] * height
        cycles = wave["cycles"]
        detail = wave["detail"]

        for x in x_positions:
            progress = x / width
            angle = 2 * math.pi * cycles * progress

            displacement = (
                math.sin(angle + phase)
                + detail * math.sin(2 * angle - phase * 0.65)
            )

            y = base_y - amplitude * displacement
            points.append((x, round(y)))

        polygon = points + [
            (width, height),
            (0, height),
        ]

        draw.polygon(polygon, fill=wave["color"])

    return image.resize((WIDTH, HEIGHT), RESAMPLE)


def create_shared_palette(frames):
    sample_indices = sorted({
        round(i * (len(frames) - 1) / 15)
        for i in range(16)
    })

    thumbnails = [
        frames[i].resize((150, 20), RESAMPLE)
        for i in sample_indices
    ]

    montage = Image.new("RGB", (600, 80), (0, 0, 0))

    for index, thumbnail in enumerate(thumbnails):
        x = (index % 4) * 150
        y = (index // 4) * 20
        montage.paste(thumbnail, (x, y))

    quantized = montage.quantize(colors=PALETTE_COLORS)
    return quantized.getpalette()


def convert_to_palette(image, palette):
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette)

    return image.quantize(
        palette=palette_image,
        dither=Image.Dither.NONE,
    )


def save_theme(name, theme):
    print(f"Generando tema: {name}")

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    frames = [
        create_wave_frame(theme, i)
        for i in range(FRAME_COUNT)
    ]

    palette = create_shared_palette(frames)

    indexed_frames = [
        convert_to_palette(frame, palette)
        for frame in frames
    ]

    output_path = ASSETS_DIR / f"waves-{name}.gif"

    indexed_frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=indexed_frames[1:],
        duration=FRAME_DURATION,
        loop=0,
        optimize=True,
        disposal=2,
    )

    size_kb = output_path.stat().st_size / 1024

    print(f"Archivo: {output_path}")
    print(f"Resolución: {WIDTH}x{HEIGHT}")
    print(f"Fotogramas: {FRAME_COUNT}")
    print(f"Duración por ciclo: {FRAME_COUNT * FRAME_DURATION / 1000:.1f} segundos")
    print(f"Tamaño: {size_kb:.1f} KB")
    print("-" * 45)


def main():
    for name, theme in THEMES.items():
        save_theme(name, theme)

    print("Ambas animaciones se generaron correctamente.")


if __name__ == "__main__":
    main()
