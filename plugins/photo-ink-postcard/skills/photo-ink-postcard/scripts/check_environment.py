#!/usr/bin/env python3
"""Check the portable runtime requirements for photo-ink-postcard."""

from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path


TITLE_FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\FRSCRIPT.TTF"),
    Path(r"C:\Windows\Fonts\segoesc.ttf"),
    Path(r"C:\Windows\Fonts\LHANDW.TTF"),
    Path("/System/Library/Fonts/Supplemental/Apple Chancery.ttf"),
    Path("/Library/Fonts/Allura-Regular.ttf"),
    Path("/usr/share/fonts/truetype/googlefonts/Allura-Regular.ttf"),
    Path("/usr/share/fonts/opentype/urw-base35/Z003-MediumItalic.otf"),
]


def main() -> None:
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")

    if sys.version_info < (3, 10):
        raise SystemExit("FAIL: Python 3.10 or newer is required")

    if importlib.util.find_spec("PIL") is None:
        raise SystemExit("FAIL: Pillow is missing; run: python -m pip install Pillow")
    print("Pillow: available")

    fonts = [path for path in TITLE_FONT_CANDIDATES if path.exists()]
    if fonts:
        print(f"Handwriting font: {fonts[0]}")
    else:
        print("WARN: no known handwriting font found; pass --title-font /path/to/font.ttf")

    print("PASS: core environment is ready")


if __name__ == "__main__":
    main()
