"""Create the responsive image set used by the Eleventy templates.

Run from the project root with:
    python scripts/optimize_images.py

The original customer photos remain untouched. This script applies EXIF rotation,
uses deliberate component crops, strips metadata, and writes WebP plus JPEG
fallbacks at the largest dimensions each CodeStitch component needs.
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "src" / "assets" / "images"
SVGS = ROOT / "src" / "assets" / "svgs"
OUTPUT = IMAGES / "optimized"


def open_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return ImageOps.exif_transpose(source).convert("RGB")


def save_pair(
    image: Image.Image,
    name: str,
    size: tuple[int, int],
    *,
    position: tuple[float, float] = (0.5, 0.5),
    webp_quality: int = 76,
    jpeg_quality: int = 78,
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fitted = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=position)
    fitted.save(
        OUTPUT / f"{name}.webp",
        "WEBP",
        quality=webp_quality,
        method=6,
        exact=True,
    )
    fitted.save(
        OUTPUT / f"{name}.jpg",
        "JPEG",
        quality=jpeg_quality,
        optimize=True,
        progressive=True,
        subsampling="4:2:0",
    )


def extract_embedded_png(path: Path) -> Image.Image:
    encoded = re.search(
        r"data:image/(?:png|jpeg);base64,([^\"']+)",
        path.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    if not encoded:
        raise ValueError(f"No embedded raster image found in {path}")
    raw = base64.b64decode(re.sub(r"\s+", "", encoded.group(1)))
    with Image.open(io.BytesIO(raw)) as source:
        return source.copy()


def save_transparent_webp(
    image: Image.Image,
    name: str,
    width: int,
    *,
    quality: int = 78,
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rgba = image.convert("RGBA")
    height = round(rgba.height * width / rgba.width)
    resized = rgba.resize((width, height), Image.Resampling.LANCZOS)
    resized.save(
        OUTPUT / f"{name}.webp",
        "WEBP",
        quality=quality,
        method=6,
        exact=True,
    )


def main() -> None:
    # Site-wide stock backgrounds, localized from the existing CodeStitch URLs.
    backgrounds = {
        "garage": open_image(IMAGES / "stock" / "garage-source.jpg"),
        "banner": open_image(IMAGES / "stock" / "mechanic-banner-source.jpg"),
        "cta": open_image(IMAGES / "stock" / "mechanic-cta-source.jpg"),
        "footer": open_image(IMAGES / "stock" / "wheels-source.jpg"),
    }
    background_outputs = [
        ("garage-mobile", "garage", (750, 1050), (0.50, 0.50)),
        ("garage-desktop", "garage", (1920, 900), (0.50, 0.52)),
        ("banner-mobile", "banner", (750, 700), (0.50, 0.45)),
        ("banner-desktop", "banner", (1600, 560), (0.50, 0.45)),
        ("cta-mobile", "cta", (750, 650), (0.50, 0.45)),
        ("cta-desktop", "cta", (1600, 650), (0.50, 0.45)),
        ("footer-mobile", "footer", (750, 800), (0.50, 0.50)),
        ("footer-desktop", "footer", (1600, 650), (0.50, 0.50)),
    ]
    for name, source, size, position in background_outputs:
        save_pair(backgrounds[source], name, size, position=position)
    # Keep the non-lazy desktop landing background below the handbook's
    # recommended 100 KB ceiling.
    save_pair(
        backgrounds["garage"],
        "garage-desktop",
        (1920, 900),
        position=(0.50, 0.52),
        webp_quality=62,
        jpeg_quality=74,
    )

    # Component-specific crops prevent a single oversized image from serving
    # several unrelated aspect ratios.
    img1 = open_image(IMAGES / "img1.jpg")
    img2 = open_image(IMAGES / "img2.jpg")
    img5 = open_image(IMAGES / "img5.jpg")
    img8 = open_image(IMAGES / "img8.jpg")
    save_pair(img1, "shop-exterior-mobile", (560, 500))
    save_pair(img1, "shop-exterior-desktop", (680, 510))
    save_pair(img2, "engine-detail-mobile", (560, 420), webp_quality=70, jpeg_quality=74)
    save_pair(img2, "engine-detail-desktop", (680, 510))
    save_pair(img1, "about-shop-mobile", (520, 620), position=(0.52, 0.50))
    save_pair(img1, "about-shop-desktop", (680, 760), position=(0.52, 0.50))
    save_pair(img1, "contact-shop-mobile", (640, 560), position=(0.52, 0.50))
    save_pair(img1, "contact-shop-desktop", (680, 600), position=(0.52, 0.50))
    save_pair(
        img8,
        "about-engine-mobile",
        (420, 580),
        position=(0.50, 0.50),
        webp_quality=64,
        jpeg_quality=72,
    )
    save_pair(img8, "about-engine-desktop", (600, 820), position=(0.50, 0.50))
    save_pair(img5, "about-building-mobile", (420, 580), position=(0.50, 0.50))
    save_pair(img5, "about-building-desktop", (600, 820), position=(0.50, 0.50))

    # Portfolio grid: 420 px covers a two-column phone grid at 2x density;
    # 640 px covers the largest desktop cards at more than 2x density.
    for number in range(3, 13):
        suffix = "JPG" if number == 3 else "jpg"
        photo = open_image(IMAGES / f"img{number}.{suffix}")
        save_pair(
            photo,
            f"gallery-{number}-mobile",
            (420, 570),
            webp_quality=64,
            jpeg_quality=72,
        )
        save_pair(photo, f"gallery-{number}-desktop", (640, 760))

    # Service cards use a consistent 413:240 frame in the template.
    service_sources = [13, 14, 15, 16, 8, 17, 18, 19]
    for index, source_number in enumerate(service_sources, start=1):
        photo = open_image(IMAGES / f"img{source_number}.jpg")
        save_pair(
            photo,
            f"service-{index}-mobile",
            (720, 420),
            webp_quality=64,
            jpeg_quality=72,
        )
        save_pair(photo, f"service-{index}-desktop", (960, 558))

    # These two files have an SVG wrapper around a very large base64 PNG.
    # A transparent WebP keeps the same appearance at a fraction of the bytes.
    save_transparent_webp(extract_embedded_png(SVGS / "corv.svg"), "corvette", 1020)
    save_transparent_webp(extract_embedded_png(SVGS / "corv.svg"), "corvette-mobile", 640)
    save_transparent_webp(extract_embedded_png(SVGS / "cobra.svg"), "cobra", 1000)
    save_transparent_webp(extract_embedded_png(SVGS / "cobra.svg"), "cobra-mobile", 700, quality=70)

    # Absolute social image used by Open Graph and article metadata.
    save_pair(backgrounds["garage"], "full-throttle-performance-og", (1200, 630))

    files = sorted(OUTPUT.iterdir())
    total = sum(path.stat().st_size for path in files)
    print(f"Wrote {len(files)} optimized images ({total / 1024 / 1024:.2f} MiB total)")


if __name__ == "__main__":
    main()
