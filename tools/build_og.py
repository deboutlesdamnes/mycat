"""Renders the social link-preview image and the raster icons.

The site has no build step (amplify.yml publishes site/ as-is), so the PNGs
this writes are committed alongside the HTML. Run it again after editing
tools/og-card.html:

    python tools/build_og.py

The preview image is versioned (og-v1.png). CloudFront holds assets at the
edge for a year and social platforms cache preview images per URL, so new
artwork should ship as og-v2.png with the meta tags updated to match, rather
than overwriting the old file.

Needs playwright (already used by the screenshot harness) and Pillow:
    python -m playwright install chromium
"""
import io
import pathlib
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARD = ROOT / "tools" / "og-card.html"
SITE = ROOT / "site"

# The cat mark on a solid background, for the raster icons. Same paths as
# mycatMark() in site/icons.js, minus the whiskers and mouth, which blur at
# icon sizes (that function drops them below 20px too). The background is
# opaque on purpose: iOS composites a transparent touch icon onto black.
ICON_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  html, body { margin: 0; }
  body { width: 100vw; height: 100vh; background: #ffffff; display: grid; place-items: center; }
  svg { width: %(pct)d%%; height: %(pct)d%%; }
</style></head><body>
<svg viewBox="0 0 64 64" fill="none" color="#16212b">
  <path d="M13 10 C15.5 15.2 20 18.6 25.5 20.2 C29.4 18 34.6 18 38.5 20.2 C44 18.6 48.5 15.2 51 10 C54 17.5 54.2 28 51.5 35.2 C49 44 41 48.6 32 48.6 C23 48.6 15 44 12.5 35.2 C9.8 28 10 17.5 13 10 Z" fill="#ffffff" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="13" cy="9" r="4.5" fill="currentColor"/>
  <circle cx="51" cy="9" r="4.5" fill="currentColor"/>
  <path d="M32 48.5 C32 54 36 56.5 40 57" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
  <circle cx="46.5" cy="57" r="5.5" stroke="currentColor" stroke-width="4.5"/>
  <circle cx="24.5" cy="30.5" r="2.8" fill="currentColor"/>
  <circle cx="39.5" cy="30.5" r="2.8" fill="currentColor"/>
  <ellipse cx="32" cy="35.6" rx="2.7" ry="2.2" fill="#f0879e"/>
</svg></body></html>"""

# name, width, height, page source
TARGETS = [
    ("og-v1.png", 1200, 630, {"url": CARD.as_uri()}),
    ("apple-touch-icon.png", 180, 180, {"html": ICON_HTML % {"pct": 84}}),
    ("favicon-32.png", 32, 32, {"html": ICON_HTML % {"pct": 94}}),
]


def shoot(browser, width, height, out, url=None, html=None):
    # Render at 2x and downsample: noticeably cleaner curves on the cat mark
    # and the serif heading than shooting at 1x.
    page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
    if url:
        page.goto(url, wait_until="networkidle")
    else:
        page.set_content(html, wait_until="load")
    # document.fonts.ready alone can resolve before a face that nothing has
    # requested yet starts loading, which silently bakes in the fallback font.
    # Request the faces explicitly, then wait, then assert they really landed.
    page.evaluate("""async () => {
      await Promise.all([
        document.fonts.load('600 62px "IBM Plex Sans"'),
        document.fonts.load('600 66px "IBM Plex Serif"'),
      ]);
      await document.fonts.ready;
    }""")
    if url:
        for spec in ('600 62px "IBM Plex Sans"', '600 66px "IBM Plex Serif"'):
            if not page.evaluate(f"document.fonts.check('{spec}')"):
                sys.exit(f"font not loaded: {spec} (network needed to build the card)")
    shot = page.screenshot()
    page.close()

    img = Image.open(io.BytesIO(shot)).convert("RGB").resize((width, height), Image.LANCZOS)
    img.save(out, optimize=True)
    print(f"{out.relative_to(ROOT)}  {width}x{height}  {out.stat().st_size / 1024:.0f} KB")


def main():
    if not CARD.exists():
        sys.exit(f"missing template: {CARD}")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, w, h, src in TARGETS:
            shoot(browser, w, h, SITE / name, **src)
        browser.close()


if __name__ == "__main__":
    main()
