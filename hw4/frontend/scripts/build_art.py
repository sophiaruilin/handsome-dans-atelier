"""Draw the Campus Customs engravings (Problem 10).

Writes Victorian line-engraving SVGs of Yale landmarks to public/art/, plus a seamless toile
wallpaper tile (public/art/toile.svg) that repeats them in Yale blue on cream, Trader Joe's style.
All original drawings. Run:  python scripts/build_art.py
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public" / "art"
INK = "#00356b"

# Shared defs: diagonal and cross hatching used as engraved "shading".
DEFS = f"""<defs>
  <pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="5" stroke="{INK}" stroke-width="1"/>
  </pattern>
  <pattern id="hatch-fine" width="3.4" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">
    <line x1="0" y1="0" x2="0" y2="3.4" stroke="{INK}" stroke-width="0.7"/>
  </pattern>
  <pattern id="cross" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <path d="M0 0V5M0 0H5" stroke="{INK}" stroke-width="0.8"/>
  </pattern>
</defs>"""


def lancet(x: float, y: float, w: float, h: float, fill: str = "none") -> str:
    """A pointed Gothic window/arch whose bottom-left corner is (x, y+h)."""
    r = w * 0.85
    return (
        f'<path d="M{x} {y + h} V{y + w * 0.55} '
        f'A{r} {r} 0 0 1 {x + w / 2} {y} A{r} {r} 0 0 1 {x + w} {y + w * 0.55} V{y + h} Z" fill="{fill}"/>'
    )


def windows_grid(x0, y0, cols, rows, w, h, gx, gy, muntins=True) -> str:
    out = []
    for r in range(rows):
        for c in range(cols):
            x, y = x0 + c * (w + gx), y0 + r * (h + gy)
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>')
            if muntins:
                out.append(f'<path d="M{x + w / 2} {y}V{y + h}M{x} {y + h / 2}H{x + w}" stroke-width="0.6"/>')
    return "".join(out)


def crenellation(x0, x1, y, step=6, h=5) -> str:
    d = [f"M{x0} {y}"]
    x, up = x0, True
    while x < x1 - 0.01:
        nx = min(x + step, x1)
        if up:
            d.append(f"V{y - h}H{nx}V{y}")
        else:
            d.append(f"H{nx}")
        x, up = nx, not up
    return f'<path d="{"".join(d)}"/>'


def pinnacle(x, y, h=14, w=6) -> str:
    return f'<path d="M{x - w / 2} {y}L{x} {y - h}L{x + w / 2} {y}Z" fill="url(#hatch-fine)"/><path d="M{x} {y - h}V{y - h - 4}"/>'


# ---------------------------------------------------------------- landmarks (each in its own box)

def harkness() -> tuple[str, int, int]:
    W, H = 130, 330
    s = []
    # base
    s.append('<rect x="28" y="215" width="74" height="110"/>')
    s.append('<rect x="80" y="215" width="22" height="110" fill="url(#hatch)" stroke="none"/>')
    s.append(lancet(52, 262, 26, 63, "url(#cross)"))
    s.append('<path d="M28 240H102M28 300H102" stroke-width="0.6"/>')
    s.append("".join(pinnacle(x, 215, 16) for x in (30, 100)))
    # tier 1
    s.append('<rect x="33" y="140" width="64" height="75"/>')
    s.append('<rect x="79" y="140" width="18" height="75" fill="url(#hatch)" stroke="none"/>')
    s.append(lancet(41, 152, 14, 52, "url(#hatch-fine)") + lancet(75, 152, 14, 52, "url(#hatch-fine)"))
    s.append("".join(pinnacle(x, 140, 18) for x in (35, 95)))
    # tier 2 with clock
    s.append('<rect x="40" y="88" width="50" height="52"/>')
    s.append('<rect x="76" y="88" width="14" height="52" fill="url(#hatch)" stroke="none"/>')
    s.append('<circle cx="65" cy="114" r="12"/><circle cx="65" cy="114" r="9" stroke-width="0.5"/>')
    s.append('<path d="M65 114V106M65 114L71 117"/>')
    s.append("".join(f'<path d="M{65 + 10.5 * math.cos(a)} {114 + 10.5 * math.sin(a)}l{1.2 * math.cos(a)} {1.2 * math.sin(a)}" stroke-width="0.6"/>'
                     for a in [i * math.pi / 6 for i in range(12)]))
    s.append("".join(pinnacle(x, 88, 20) for x in (42, 88)))
    # lantern
    s.append('<rect x="47" y="46" width="36" height="42"/>')
    s.append(lancet(51, 52, 8, 32, "url(#hatch-fine)") + lancet(61, 52, 8, 32, "url(#hatch-fine)") + lancet(71, 52, 8, 32, "url(#hatch-fine)"))
    s.append(crenellation(45, 85, 46, step=5, h=4))
    s.append("".join(pinnacle(x, 42, 22, 5) for x in (47, 65, 83)))
    s.append('<path d="M65 20V6M61 10H69" stroke-width="1.1"/>')
    return "".join(s), W, H


def sterling() -> tuple[str, int, int]:
    W, H = 280, 210
    s = []
    # wings
    for x0 in (14, 176):
        s.append(f'<rect x="{x0}" y="100" width="90" height="100"/>')
        s.append(f'<path d="M{x0} 100L{x0 + 45} 72L{x0 + 90} 100"/>')
        s.append(windows_grid(x0 + 10, 118, 4, 2, 12, 22, 9, 14))
        s.append(pinnacle(x0 + 2, 100, 14) + pinnacle(x0 + 88, 100, 14))
    s.append('<rect x="176" y="100" width="90" height="100" fill="url(#hatch-fine)" stroke="none" opacity="0.6"/>')
    # central nave/tower
    s.append('<rect x="104" y="58" width="72" height="142"/>')
    s.append('<path d="M104 58L140 18L176 58"/>')
    s.append('<path d="M112 58L140 28L168 58" stroke-width="0.6"/>')
    s.append(lancet(119, 78, 42, 92, "url(#cross)"))
    s.append('<path d="M140 78V170M119 125H161" stroke-width="0.7"/>')
    s.append(lancet(126, 176, 28, 24, "none"))
    s.append(pinnacle(104, 58, 26, 7) + pinnacle(176, 58, 26, 7) + '<path d="M140 18V6"/>')
    s.append('<circle cx="140" cy="44" r="6"/>')
    s.append('<path d="M6 200H274" stroke-width="1.4"/>')
    return "".join(s), W, H


def beinecke() -> tuple[str, int, int]:
    W, H = 240, 160
    s = ['<path d="M8 148H232" stroke-width="1.4"/>']
    s.append('<rect x="28" y="28" width="184" height="88"/>')
    cols, rows = 9, 4
    cw, rh = 184 / cols, 88 / rows
    for r in range(rows):
        for c in range(cols):
            x, y = 28 + c * cw, 28 + r * rh
            s.append(f'<rect x="{x + 2:.1f}" y="{y + 2:.1f}" width="{cw - 4:.1f}" height="{rh - 4:.1f}" stroke-width="0.6"/>')
            s.append(f'<path d="M{x + cw / 2:.1f} {y + 4:.1f}L{x + cw - 4:.1f} {y + rh / 2:.1f}L{x + cw / 2:.1f} {y + rh - 4:.1f}L{x + 4:.1f} {y + rh / 2:.1f}Z" stroke-width="0.5"/>')
    for x in (30, 196):
        s.append(f'<path d="M{x} 116L{x + 4} 148H{x + 10}L{x + 14} 116"/>')
    s.append('<rect x="60" y="120" width="120" height="28" fill="url(#hatch)" stroke="none"/>')
    s.append('<rect x="70" y="124" width="100" height="24" fill="none"/>')
    return "".join(s), W, H


def connecticut_hall() -> tuple[str, int, int]:
    W, H = 230, 180
    s = ['<rect x="18" y="64" width="194" height="106"/>']
    s.append('<path d="M14 64L34 34H196L216 64Z" fill="url(#hatch-fine)"/>')
    s.append('<path d="M34 34L48 22H182L196 34"/>')
    for x in (60, 160):
        s.append(f'<rect x="{x}" y="6" width="12" height="18" fill="url(#hatch)"/><path d="M{x - 2} 6H{x + 14}"/>')
    s.append("".join(f'<rect x="{x}" y="40" width="9" height="12" stroke-width="0.7"/>' for x in (70, 100, 130, 154)))
    s.append(windows_grid(30, 74, 8, 3, 14, 18, 8.6, 10))
    s.append('<rect x="104" y="140" width="22" height="30" fill="url(#hatch)"/><path d="M100 140H130L115 132Z"/>')
    s.append('<path d="M10 170H220" stroke-width="1.4"/>')
    return "".join(s), W, H


def rotunda() -> tuple[str, int, int]:
    W, H = 210, 200
    s = ['<rect x="22" y="120" width="166" height="68"/>', '<path d="M16 120H194M16 114H194L194 120M16 114V120"/>']
    s.append("".join(f'<path d="M{x} 124V184M{x + 4} 124V184" stroke-width="0.8"/>' for x in range(32, 182, 16)))
    s.append('<path d="M14 188H196" stroke-width="1.4"/>')
    s.append('<rect x="56" y="84" width="98" height="30"/>')
    s.append("".join(f'<rect x="{x}" y="90" width="7" height="18" stroke-width="0.6"/>' for x in range(64, 150, 14)))
    s.append('<path d="M50 84Q50 30 105 26Q160 30 160 84Z" fill="url(#hatch-fine)"/>')
    s.append("".join(f'<path d="M{105 + dx} 27Q{105 + dx * 1.6} 50 {105 + dx * 2.1} 84" stroke-width="0.6"/>' for dx in (-20, -8, 8, 20)))
    s.append('<rect x="97" y="10" width="16" height="16"/><path d="M95 10H115L105 2Z"/>')
    return "".join(s), W, H


def phelps_gate() -> tuple[str, int, int]:
    W, H = 170, 240
    s = ['<rect x="30" y="60" width="110" height="170"/>']
    s.append('<rect x="110" y="60" width="30" height="170" fill="url(#hatch)" stroke="none"/>')
    s.append(lancet(58, 150, 54, 80, "url(#cross)"))
    s.append(lancet(66, 160, 38, 70, "none"))
    s.append(crenellation(26, 144, 60, step=8, h=7))
    s.append('<rect x="70" y="84" width="30" height="40"/>' + lancet(76, 90, 8, 30, "url(#hatch-fine)") + lancet(86, 90, 8, 30, "url(#hatch-fine)"))
    s.append('<path d="M30 140H140" stroke-width="0.6"/>')
    s.append('<path d="M85 53V8"/><path d="M85 9L118 16L85 24Z" fill="#fff"/><text x="96" y="21" font-family="Georgia,serif" font-size="9" font-weight="700" fill="' + INK + '" stroke="none">Y</text>')
    s.append('<path d="M18 230H152" stroke-width="1.4"/>')
    return "".join(s), W, H


def yale_bowl() -> tuple[str, int, int]:
    """The Yale Bowl: an elliptical earthwork stadium ringed with portal arches."""
    W, H = 250, 120
    s = ['<ellipse cx="125" cy="62" rx="115" ry="40"/>', '<ellipse cx="125" cy="58" rx="92" ry="28" fill="url(#hatch-fine)"/>']
    s.append('<ellipse cx="125" cy="56" rx="60" ry="15" fill="#fffdf7"/>')
    s.append('<path d="M85 56H165M125 42V70" stroke-width="0.6"/>')
    for i in range(13):
        a = math.pi * (0.12 + 0.76 * i / 12)
        x, y = 125 - 112 * math.cos(a), 62 + 38 * math.sin(a)
        s.append(f'<path d="M{x - 4:.1f} {y + 10:.1f}V{y + 3:.1f}A4 4 0 0 1 {x + 4:.1f} {y + 3:.1f}V{y + 10:.1f}" stroke-width="0.8"/>')
    s.append('<path d="M10 70V92Q125 128 240 92V70" />')
    s.append('<path d="M6 112H244" stroke-width="1.4"/>')
    return "".join(s), W, H


def college_courtyard() -> tuple[str, int, int]:
    """A Gothic residential college: gate tower between gabled wings, with an ivy-hatched base."""
    W, H = 260, 190
    s = []
    for x0 in (12, 158):
        s.append(f'<rect x="{x0}" y="92" width="90" height="88"/>')
        s.append(f'<path d="M{x0} 92L{x0 + 22} 70L{x0 + 44} 92M{x0 + 46} 92L{x0 + 68} 70L{x0 + 90} 92"/>')
        s.append(windows_grid(x0 + 10, 104, 4, 2, 11, 18, 9, 12))
        s.append(f'<path d="M{x0} 160H{x0 + 90}V180H{x0}Z" fill="url(#cross)" stroke="none" opacity="0.7"/>')
    s.append('<rect x="102" y="46" width="56" height="134"/>')
    s.append(crenellation(98, 162, 46, step=7, h=6))
    s.append(lancet(114, 120, 32, 60, "url(#cross)"))
    s.append('<rect x="118" y="66" width="24" height="30"/>' + lancet(122, 70, 7, 22, "url(#hatch-fine)") + lancet(131, 70, 7, 22, "url(#hatch-fine)"))
    s.append(pinnacle(102, 42, 16) + pinnacle(158, 42, 16))
    s.append('<path d="M4 180H256" stroke-width="1.4"/>')
    return "".join(s), W, H


def payne_whitney() -> tuple[str, int, int]:
    """Payne Whitney Gym, the 'cathedral of sweat': a stepped Gothic tower."""
    W, H = 150, 260
    s = []
    for (x, y, w, h) in ((15, 170, 120, 82), (30, 110, 90, 60), (44, 62, 62, 48), (56, 28, 38, 34)):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>')
        s.append(f'<rect x="{x + w * 0.72:.1f}" y="{y}" width="{w * 0.28:.1f}" height="{h}" fill="url(#hatch)" stroke="none"/>')
        for k in range(max(1, int(w // 22))):
            wx = x + 8 + k * (w - 16) / max(1, int(w // 22))
            s.append(lancet(wx, y + 8, 8, h - 16, "url(#hatch-fine)"))
        s.append(pinnacle(x + 2, y, 12, 5) + pinnacle(x + w - 2, y, 12, 5))
    s.append('<path d="M75 28V10M71 14H79"/>')
    s.append('<path d="M6 252H144" stroke-width="1.4"/>')
    return "".join(s), W, H


def elm(scale: float = 1.0) -> tuple[str, int, int]:
    """An engraved elm (New Haven is the Elm City): vase-shaped trunk and scalloped canopy."""
    W, H = 150, 180
    s = ['<path d="M70 178C72 150 68 130 60 110M80 178C78 150 84 128 94 108M75 150C75 128 76 112 76 92" stroke-width="1.3"/>']
    s.append('<path d="M68 178H84" stroke-width="1.3"/>')
    # canopy: ring of bumps
    cx, cy, rx, ry = 75, 70, 62, 52
    pts = []
    n = 22
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        r = 1 + 0.12 * math.sin(i * 2.7)
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ox, oy = (mx - cx) * 0.18, (my - cy) * 0.18
        d += f"Q{mx + ox:.1f} {my + oy:.1f} {x1:.1f} {y1:.1f}"
    s.append(f'<path d="{d}Z" fill="url(#hatch-fine)"/>')
    s.append('<path d="M40 64Q55 50 70 58M82 46Q98 40 108 54M52 88Q66 80 80 90" stroke-width="0.8"/>')
    return "".join(s), W, H


def sprig(flip: bool = False) -> tuple[str, int, int]:
    """Toile foliage: a curling stem with leaves and a small flower."""
    W, H = 110, 90
    s = ['<path d="M8 82C30 70 46 52 58 30C66 16 80 10 96 12" stroke-width="1.1"/>']
    for (x, y, a) in ((26, 70, -30), (40, 56, 20), (52, 40, -40), (66, 24, 10), (80, 14, -20)):
        s.append(f'<path d="M{x} {y}q8 -14 20 -12q-6 12 -20 12z" transform="rotate({a} {x} {y})" fill="url(#hatch-fine)"/>')
    s.append('<circle cx="98" cy="12" r="4"/>' + "".join(
        f'<ellipse cx="{98 + 7 * math.cos(a):.1f}" cy="{12 + 7 * math.sin(a):.1f}" rx="4" ry="2.4" transform="rotate({math.degrees(a):.0f} {98 + 7 * math.cos(a):.1f} {12 + 7 * math.sin(a):.1f})" stroke-width="0.7"/>'
        for a in [i * 2 * math.pi / 6 for i in range(6)]))
    body = "".join(s)
    if flip:
        body = f'<g transform="translate({W} 0) scale(-1 1)">{body}</g>'
    return body, W, H


def pennant() -> tuple[str, int, int]:
    W, H = 90, 50
    s = '<path d="M6 6V44" stroke-width="1.4"/><path d="M6 8L84 24L6 40Z" fill="url(#hatch-fine)"/>'
    s += f'<text x="22" y="30" font-family="Georgia,serif" font-size="14" font-weight="700" fill="#fffdf7" stroke="none">YALE</text>'
    return s, W, H


def svg_doc(body: str, w: int, h: int, stroke_opacity: float = 1.0) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{DEFS}'
        f'<g fill="none" stroke="{INK}" stroke-width="1" stroke-linejoin="round" stroke-linecap="round" '
        f'stroke-opacity="{stroke_opacity}" fill-opacity="{stroke_opacity}">{body}</g></svg>'
    )


def place(art: tuple[str, int, int], x: float, y: float, scale: float = 1.0) -> str:
    body, _, _ = art
    return f'<g transform="translate({x} {y}) scale({scale})">{body}</g>'


def toile_tile() -> str:
    """A 960x960 repeating tile. Motifs that cross an edge are drawn again on the opposite edge."""
    T = 960
    items = [
        (harkness(), 40, 20, 0.9),
        (sterling(), 300, 40, 0.85),
        (elm(), 560, 10, 0.8),
        (payne_whitney(), 760, 30, 0.75),
        (sprig(), 200, 290, 0.9),
        (beinecke(), 560, 250, 0.85),
        (college_courtyard(), 20, 360, 0.85),
        (pennant(), 820, 270, 0.8),
        (elm(), 330, 330, 0.75),
        (sprig(True), 470, 400, 0.85),
        (connecticut_hall(), 260, 520, 0.85),
        (rotunda(), 720, 470, 0.8),
        (yale_bowl(), 40, 600, 0.85),
        (sprig(), 520, 600, 0.85),
        (phelps_gate(), 560, 690, 0.8),
        (elm(), 800, 690, 0.75),
        (pennant(), 250, 720, 0.8),
        (sprig(True), 60, 790, 0.85),
        (sprig(), 360, 860, 0.8),
        (elm(), 160, 840, 0.6),
    ]
    parts = []
    for art, x, y, sc in items:
        _, w, h = art
        for dx in (0, -T, T):
            for dy in (0, -T, T):
                if x + dx < T and x + dx + w * sc > 0 and y + dy < T and y + dy + h * sc > 0:
                    parts.append(place(art, x + dx, y + dy, sc))
    # Scattered toile dots and tiny stars to fill gaps.
    for (x, y) in ((260, 20), (520, 230), (190, 260), (930, 200), (20, 560), (480, 560), (740, 930), (300, 950), (940, 620), (680, 380), (430, 300), (150, 520), (900, 420), (640, 860)):
        parts.append(f'<path d="M{x} {y - 5}V{y + 5}M{x - 5} {y}H{x + 5}M{x - 3} {y - 3}L{x + 3} {y + 3}M{x - 3} {y + 3}L{x + 3} {y - 3}" stroke-width="0.8"/>')
    return svg_doc("".join(parts), T, T, stroke_opacity=1.0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    singles = {
        "harkness": harkness(), "sterling": sterling(), "beinecke": beinecke(),
        "connecticut-hall": connecticut_hall(), "rotunda": rotunda(), "phelps-gate": phelps_gate(), "elm": elm(),
        "yale-bowl": yale_bowl(), "college": college_courtyard(), "payne-whitney": payne_whitney(),
    }
    for name, (body, w, h) in singles.items():
        (OUT / f"{name}.svg").write_text(svg_doc(body, w, h), encoding="utf-8")
    (OUT / "toile.svg").write_text(toile_tile(), encoding="utf-8")
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.svg"))))


if __name__ == "__main__":
    main()
