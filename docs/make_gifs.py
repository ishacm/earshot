"""Regenerate the README / Pages animation (original artwork, no third-party media).
Usage: python docs/make_gifs.py  ->  docs/listen.gif and docs/listen.webp
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BG, PANEL, LINE = (12, 13, 14), (24, 26, 28), (45, 48, 51)
INK, MUTED, ORANGE, GREEN, RED = (236, 231, 221), (150, 145, 136), (240, 138, 75), (140, 203, 143), (242, 120, 105)
W, H = 760, 340
f = lambda p, s: ImageFont.truetype(p, s)

QUOTES = [  # (source, text, verified)
    ("HN", "setup took six weeks", True),
    ("App Store", "crashes on every upload", True),
    ("Reddit", "per-seat pricing hurts", True),
    ("HN", "it's basically perfect™", False),
    ("App Store", "love how fast it is", True),
    ("Reddit", "we left after the price hike", True),
]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ear(d, cx, cy, s, wiggle):
    """A friendly cartoon ear (side view, listening to the left), plus sound waves."""
    w = int(wiggle)
    d.arc([cx - 38, cy - 78, cx + 52, cy + 44], 195, 430, fill=ORANGE, width=9)       # outer rim (helix)
    d.arc([cx - 30, cy + 8, cx + 22, cy + 72], 0, 180, fill=ORANGE, width=9)          # lobe
    d.line([cx - 32, cy - 40, cx - 30, cy + 34], fill=ORANGE, width=9)                # front edge
    d.arc([cx - 14, cy - 50, cx + 30, cy + 10], 200, 420, fill=ORANGE, width=6)       # inner fold
    d.ellipse([cx - 14, cy + 2, cx + 2, cy + 18], fill=ORANGE)                         # ear canal
    for i in range(3):
        r = 30 + i * 18 + w
        d.arc([cx - 70 - r, cy - r, cx - 70 + r, cy + r], 140, 220, fill=LINE, width=3)


def bubble(d, x, y, src, text, col, alpha_ok=True):
    font = f(SANS, 15)
    tw = d.textlength(text, font=font)
    pad = 10
    d.rounded_rectangle([x, y, x + tw + 2 * pad, y + 46], 12, fill=PANEL, outline=col, width=2)
    d.polygon([(x + 18, y + 46), (x + 30, y + 46), (x + 20, y + 56)], fill=PANEL)
    d.text((x + pad, y + 5), src, font=f(MONO, 11), fill=MUTED)
    d.text((x + pad, y + 21), text, font=font, fill=INK if alpha_ok else MUTED)
    return tw + 2 * pad


def frame(i, n):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((28, 22), "earshot", font=f(BOLD, 26), fill=INK)
    d.text((150, 30), "hears what customers actually say", font=f(SANS, 16), fill=MUTED)
    ex, ey = 470, 175
    ear(d, ex, ey, 1.0, 3 * math.sin(i / 3))
    verified = 0
    for k, (src, text, ok) in enumerate(QUOTES):
        start = k * 6
        t = (i - start) / 14
        if t < 0:
            continue
        lane = 70 + (k % 3) * 82
        if ok:
            p = ease(t)
            x = 20 + p * (ex - 170)
            y = lane + p * (ey - 30 - lane) * 0.6
            if t < 1:
                bubble(d, int(x), int(y), src, text, LINE)
            else:
                verified += 1
        else:
            p = ease(min(t, 0.6) / 0.6)
            x = 20 + p * 180
            y = lane
            if t < 1.6:
                bubble(d, int(x), int(y + max(0, t - 0.8) * 160), src, text, RED, alpha_ok=False)
                if t > 0.55:
                    d.text((int(x) + 4, int(y) - 22), "✗ not verbatim → dropped", font=f(MONO, 13), fill=RED)
    d.text((28, H - 38), f"verified quotes: {verified * 8 + (3 if verified else 0)}", font=f(MONO, 14), fill=GREEN if verified else MUTED)
    if i > n - 20:  # the messaging card slides in
        p = ease((i - (n - 20)) / 10)
        x = int(W - p * 250)
        d.rounded_rectangle([x, 92, x + 236, 262], 14, fill=PANEL, outline=ORANGE, width=2)
        d.text((x + 16, 104), "MESSAGING", font=f(MONO, 12), fill=ORANGE)
        d.text((x + 16, 126), "Pay for spenders,", font=f(BOLD, 18), fill=INK)
        d.text((x + 16, 150), "not for everyone.", font=f(BOLD, 18), fill=INK)
        d.text((x + 16, 184), "#1 pain: per-seat pricing", font=f(SANS, 13), fill=MUTED)
        d.text((x + 16, 204), "every line cites a quote", font=f(SANS, 13), fill=MUTED)
        d.text((x + 16, 228), "✓ [E4] [E5] [E6]", font=f(MONO, 13), fill=GREEN)
    return im


def main():
    n = 62
    frames = [frame(i, n) for i in range(n)]
    dur = [70] * n
    dur[-1] = 2800
    frames = [fr.quantize(colors=48, method=Image.Quantize.MEDIANCUT) for fr in frames]
    frames[0].save(OUT / "listen.gif", save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True)
    rgb = [fr.convert("RGB") for fr in frames]
    rgb[0].save(OUT / "listen.webp", save_all=True, append_images=rgb[1:], duration=dur, loop=0, quality=70, method=6)
    for p in ("listen.gif", "listen.webp"):
        print(p, (OUT / p).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
