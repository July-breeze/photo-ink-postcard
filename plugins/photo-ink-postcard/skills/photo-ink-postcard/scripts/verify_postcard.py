#!/usr/bin/env python3
"""Verify adaptive canvas geometry and exact photo embedding."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops

from PIL import ImageOps

from compose_postcard import PANEL_GAP, TOP_Y, contain, layout_geometry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photo", required=True, type=Path)
    parser.add_argument("--postcard", required=True, type=Path)
    parser.add_argument(
        "--layout",
        choices=("auto", "vertical", "horizontal"),
        default="auto",
    )
    args = parser.parse_args()

    with Image.open(args.postcard) as source:
        postcard = source.convert("RGB")
    with Image.open(args.photo) as source:
        source_size = ImageOps.exif_transpose(source).size
        layout, canvas_size, max_frame_size, _ = layout_geometry(source_size, args.layout)
        expected = contain(source, max_frame_size)
    if postcard.size != canvas_size:
        raise SystemExit(
            f"FAIL: expected {canvas_size[0]}x{canvas_size[1]} for {layout} layout, "
            f"got {postcard.width}x{postcard.height}"
        )

    safe = 64
    expected_core = expected.crop((safe, safe, expected.width - safe, expected.height - safe))
    if layout == "horizontal":
        pair_width = expected.width * 2 + PANEL_GAP
        x = (canvas_size[0] - pair_width) // 2 + safe
    else:
        x = (canvas_size[0] - expected.width) // 2 + safe
    y = TOP_Y + safe
    embedded_core = postcard.crop((x, y, x + expected_core.width, y + expected_core.height))
    if ImageChops.difference(expected_core, embedded_core).getbbox() is not None:
        raise SystemExit("FAIL: the embedded photo core differs from the expected resize")

    print(
        f"PASS: {args.postcard} is {canvas_size[0]}x{canvas_size[1]} ({layout}) "
        "and its central photo safe area is pixel-exact"
    )


if __name__ == "__main__":
    main()
