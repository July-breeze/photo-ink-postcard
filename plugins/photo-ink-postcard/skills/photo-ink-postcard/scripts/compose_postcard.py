#!/usr/bin/env python3
"""Compose an untouched photo and a generated ink illustration into an adaptive postcard."""

from __future__ import annotations

import argparse
from pathlib import Path
from random import Random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


OFF_WHITE = "#F5F5F1"
PANEL_PAPER = "#F3F4F2"
INK = "#292824"
SUB_INK = "#69665E"
VERTICAL_CANVAS_SIZE = (1536, 2048)
HORIZONTAL_CANVAS_SIZE = (2048, 1536)
VERTICAL_MAX_FRAME_SIZE = (1400, 788)
HORIZONTAL_MAX_FRAME_SIZE = (900, 1180)
# Backward-compatible alias for callers that imported the original constant.
MAX_FRAME_SIZE = VERTICAL_MAX_FRAME_SIZE
TOP_Y = 64
PANEL_GAP = 18
BOTTOM_TEXT_MARGIN = 128
HORIZONTAL_BOTTOM_TEXT_MARGIN = 80
TITLE_TO_SUBTITLE = 104


def resample() -> int:
    return getattr(Image.Resampling, "LANCZOS", Image.LANCZOS)


def contain(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    copy = ImageOps.exif_transpose(image).convert("RGB")
    copy.thumbnail(box, resample())
    return copy


def cover(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    return ImageOps.fit(image, box, method=resample(), centering=(0.5, 0.5))


def painted_edge_mask(size: tuple[int, int], band: int, softness: int, seed: int) -> Image.Image:
    """Create a deterministic irregular edge resembling diluted oil-paint bleed."""
    width, height = size
    rng = Random(seed)
    coarse_size = (max(8, width // 34), max(8, height // 34))
    fine_size = (max(8, width // 11), max(8, height // 11))
    coarse = Image.new("L", coarse_size)
    coarse.putdata([rng.randrange(256) for _ in range(coarse_size[0] * coarse_size[1])])
    coarse = coarse.resize(size, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(5))
    fine = Image.new("L", fine_size)
    fine.putdata([rng.randrange(256) for _ in range(fine_size[0] * fine_size[1])])
    fine = fine.resize(size, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(1.5))
    noise = Image.blend(coarse, fine, 0.32)

    noise_pixels = noise.load()
    output = Image.new("L", size, 0)
    output_pixels = output.load()
    for y in range(height):
        for x in range(width):
            distance = min(x, y, width - 1 - x, height - 1 - y)
            threshold = band + (noise_pixels[x, y] - 128) * 0.075
            value = int((distance - threshold + softness) * 255 / (2 * softness))
            output_pixels[x, y] = max(0, min(255, value))
    return output.filter(ImageFilter.GaussianBlur(0.7))


def normalize_paper(image: Image.Image, background: str) -> Image.Image:
    """Blend bright low-chroma paper pixels toward the shared neutral canvas color."""
    image = image.convert("RGB")
    red, green, blue = image.split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    minimum = ImageChops.darker(ImageChops.darker(red, green), blue)
    chroma = ImageChops.subtract(maximum, minimum)
    light_mask = maximum.point(lambda value: max(0, min(255, (value - 205) * 7)))
    neutral_mask = chroma.point(lambda value: max(0, min(255, 255 - (value - 8) * 9)))
    mask = ImageChops.multiply(light_mask, neutral_mask)
    return Image.composite(Image.new("RGB", image.size, background), image, mask)


def first_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for item in candidates:
        path = Path(item)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def center_text(draw: ImageDraw.ImageDraw, canvas_width: int, y: int, text: str, font, fill: str) -> None:
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    draw.text(((canvas_width - width) // 2, y), text, font=font, fill=fill)


def tracked_text(
    draw: ImageDraw.ImageDraw,
    canvas_width: int,
    y: int,
    text: str,
    font,
    fill: str,
    tracking: int,
) -> None:
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = (canvas_width - total) / 2
    for ch, width in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += width + tracking


def choose_layout(photo_size: tuple[int, int], requested: str = "auto") -> str:
    """Route portrait sources to a horizontal card and all others to a vertical card."""
    if requested != "auto":
        return requested
    width, height = photo_size
    return "horizontal" if width < height else "vertical"


def layout_geometry(
    photo_size: tuple[int, int], requested: str = "auto"
) -> tuple[str, tuple[int, int], tuple[int, int], int]:
    layout = choose_layout(photo_size, requested)
    if layout == "horizontal":
        return layout, HORIZONTAL_CANVAS_SIZE, HORIZONTAL_MAX_FRAME_SIZE, HORIZONTAL_BOTTOM_TEXT_MARGIN
    return layout, VERTICAL_CANVAS_SIZE, VERTICAL_MAX_FRAME_SIZE, BOTTOM_TEXT_MARGIN


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photo", required=True, type=Path)
    parser.add_argument("--illustration", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--background", default=OFF_WHITE)
    parser.add_argument(
        "--layout",
        choices=("auto", "vertical", "horizontal"),
        default="auto",
        help="auto uses a 4:3 left-right card for portrait photos and a 3:4 top-bottom card otherwise",
    )
    parser.add_argument("--title-font", type=Path)
    parser.add_argument("--subtitle-font", type=Path)
    args = parser.parse_args()

    with Image.open(args.photo) as source:
        source_size = ImageOps.exif_transpose(source).size
        layout, canvas_size, max_frame_size, text_bottom_margin = layout_geometry(source_size, args.layout)
        photo = contain(source, max_frame_size)

    canvas = Image.new("RGB", canvas_size, args.background)

    # Both adaptive layouts preserve the source aspect ratio. Nothing is generated
    # or blurred outside the source bounds; only its own outer edge dissolves softly.
    frame_size = photo.size
    if layout == "horizontal":
        pair_width = frame_size[0] * 2 + PANEL_GAP
        frame_x = (canvas_size[0] - pair_width) // 2
        frame_y = TOP_Y
        art_x = frame_x + frame_size[0] + PANEL_GAP
        art_y = frame_y
    else:
        frame_x = (canvas_size[0] - frame_size[0]) // 2
        frame_y = TOP_Y
        art_x = frame_x
        art_y = frame_y + frame_size[1] + PANEL_GAP
    shared_mask = painted_edge_mask(frame_size, band=8, softness=9, seed=41)
    canvas.paste(photo, (frame_x, frame_y), shared_mask)

    # The lower panel has exactly the same displayed dimensions and aspect ratio.
    # A barely perceptible cool-gray paper difference makes its true box legible
    # without introducing a border; the shared mask keeps both boxes optically aligned.
    with Image.open(args.illustration) as source:
        art = normalize_paper(cover(source, frame_size), PANEL_PAPER)
    canvas.paste(art, (art_x, art_y), shared_mask)

    title_font = first_font(
        [str(args.title_font)] if args.title_font else [
            r"C:\Windows\Fonts\FRSCRIPT.TTF",
            r"C:\Windows\Fonts\segoesc.ttf",
            r"C:\Windows\Fonts\LHANDW.TTF",
        ],
        92,
    )
    subtitle_font = first_font(
        [str(args.subtitle_font)] if args.subtitle_font else [
            r"C:\Windows\Fonts\aptos.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ],
        27,
    )

    draw = ImageDraw.Draw(canvas)
    # Anchor the text group from the bottom edge so its final visible margin is
    # stable across captions, rather than leaving an accidental empty lower field.
    subtitle_bounds = draw.textbbox((0, 0), args.subtitle.upper(), font=subtitle_font)
    subtitle_y = canvas_size[1] - text_bottom_margin - subtitle_bounds[3]
    title_y = subtitle_y - TITLE_TO_SUBTITLE
    center_text(draw, canvas_size[0], title_y, args.title, title_font, INK)
    tracked_text(draw, canvas_size[0], subtitle_y, args.subtitle.upper(), subtitle_font, SUB_INK, 2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, format="PNG", optimize=True, dpi=(300, 300))


if __name__ == "__main__":
    main()
