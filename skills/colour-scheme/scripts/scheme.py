#!/usr/bin/env python3
"""Build light and dark UI colour schemes from A Dictionary of Colour Combinations.

Commands:

  show ID...        print combinations
  random            print random combinations
  near HEX          combinations that hold the colours nearest to HEX
  search TEXT       combinations that hold a colour whose name contains TEXT
  chain ID          combinations that share a colour with ID, for nested schemes
  build ID          print the scheme tokens as CSS or JSON
  preview SPEC...   write an HTML sheet that shows schemes in light and dark
  contrast FG BG    print the WCAG contrast ratio of two colours

Each of the 348 combinations makes a light and a dark scheme. Hue stays fixed:
the dark scheme flips lightness in OKLCH, so a pink stays pink. Lightness (and
chroma, to stay in sRGB) changes only as needed to meet the contrast targets.

Usage: scheme.py COMMAND [options]
"""

import argparse
import html
import json
import math
import random
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "colors.json"

# WCAG 2 contrast targets. EDGE is decorative: the tinted panel already marks a card.
TEXT = 4.5
UI = 3.0
EDGE = 1.5

# OKLCH lightness of the derived neutrals. A chained scheme sits on a more
# tinted, slightly darker (light mode) or lighter (dark mode) panel.
LEVELS = {
    "page": {
        "light": {"bg": 0.975, "surface": 0.995, "surface-2": 0.945, "border": 0.87, "fg": 0.24, "fg-muted": 0.46},
        "dark": {"bg": 0.19, "surface": 0.235, "surface-2": 0.275, "border": 0.36, "fg": 0.94, "fg-muted": 0.74},
    },
    "card": {
        "light": {"bg": 0.95, "surface": 0.98, "surface-2": 0.92, "border": 0.84, "fg": 0.24, "fg-muted": 0.46},
        "dark": {"bg": 0.25, "surface": 0.29, "surface-2": 0.33, "border": 0.42, "fg": 0.94, "fg-muted": 0.74},
    },
}
# Neutral tint: fraction of the ground colour's chroma, and a cap.
TINT = {"page": (0.12, 0.012), "card": (0.3, 0.035)}
# Set by --swatches, or when stdout is a terminal.
SWATCHES = False
STATUS_HUES = {"success": 150, "warning": 70, "error": 27}

# (foreground, background, target) pairs that a scheme must pass.
CHECKS = [
    ("fg", "surface-2", TEXT), ("fg-muted", "surface-2", TEXT), ("heading", "surface-2", TEXT),
    ("link", "surface-2", TEXT), ("on-primary", "primary", TEXT), ("on-secondary", "secondary", TEXT),
    ("on-accent", "accent", TEXT), ("primary", "bg", UI), ("success", "surface-2", TEXT),
    ("warning", "surface-2", TEXT), ("error", "surface-2", TEXT),
]


# Colour maths: sRGB, OKLab/OKLCH, WCAG contrast.

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_rgb(value):
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    try:
        if len(value) == 6:
            return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        pass
    raise SystemExit(f"error: not a hex colour: {value!r}")


def rgb_to_hex(rgb):
    return "#" + "".join(f"{round(min(max(c, 0), 1) * 255):02x}" for c in rgb)


def cbrt(x):
    return math.copysign(abs(x) ** (1 / 3), x)


def oklab(hex_value):
    r, g, b = (srgb_to_linear(c) for c in hex_to_rgb(hex_value))
    l = cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklch(hex_value):
    L, a, b = oklab(hex_value)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def oklch_to_linear(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def in_gamut(L, C, h):
    return all(-1e-4 <= c <= 1 + 1e-4 for c in oklch_to_linear(L, C, h))


def oklch_hex(L, C, h):
    """Convert OKLCH to hex. Out-of-gamut colours lose chroma, not hue or lightness."""
    L = min(max(L, 0.0), 1.0)
    if not in_gamut(L, C, h):
        low, high = 0.0, C
        while high - low > 1e-4:
            mid = (low + high) / 2
            low, high = (mid, high) if in_gamut(L, mid, h) else (low, mid)
        C = low
    return rgb_to_hex(linear_to_srgb(min(max(c, 0.0), 1.0)) for c in oklch_to_linear(L, C, h))


def luminance(hex_value):
    r, g, b = (srgb_to_linear(c) for c in hex_to_rgb(hex_value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def fit(lch, bg, target):
    """Move lightness away from bg until contrast reaches target. Hue stays."""
    L, C, h = lch
    # 0.18 is the luminance where black and white text have equal contrast.
    step = -0.005 if luminance(bg) > 0.18 else 0.005
    while True:
        value = oklch_hex(L, C, h)
        if contrast(value, bg) >= target or L <= 0 or L >= 1:
            return value
        L += step


def soften(lch, hue):
    """Keep a colour off pure black and white. A near-grey takes the ground hue."""
    L, C, h = lch
    return (min(max(L, 0.18), 0.97), *((C, h) if C >= 0.005 else (0.006, hue)))


# Dataset.

def load():
    colours = json.loads(DATA.read_text())
    combos = {}
    for index, colour in enumerate(colours):
        colour["id"] = index
        colour["oklch"] = oklch(colour["hex"])
        colour["oklab"] = oklab(colour["hex"])
        for combo in colour["combinations"]:
            combos.setdefault(combo, []).append(colour)
    return colours, combos


def palette(combos, cid):
    if cid not in combos:
        raise SystemExit(f"error: no combination {cid} (valid: 1-{max(combos)})")
    return combos[cid]


def swatch(hex_value):
    """A 24-bit colour block for terminals that show ANSI colour."""
    if not SWATCHES:
        return ""
    r, g, b = (round(c * 255) for c in hex_to_rgb(hex_value))
    return f"\033[48;2;{r};{g};{b}m   \033[0m "


def describe(cid, colours, mark=()):
    names = [f"{swatch(c['hex'])}{'*' if c in mark else ''}{c['name']} {c['hex']}" for c in colours]
    return f"{cid:>3}  " + " · ".join(names)


def neighbours(combos, cid):
    """Combinations that share a colour with cid and add one, ordered subtle to bold.

    Each entry is (novelty, id, bridge, added). Novelty is the mean OKLab
    distance from each added colour to the nearest page colour.
    """
    page = palette(combos, cid)
    result = []
    for other, members in combos.items():
        shared = [c for c in members if c in page]
        added = [c for c in members if c not in page]
        if other == cid or not shared or not added:
            continue
        novelty = sum(min(math.dist(a["oklab"], p["oklab"]) for p in page) for a in added) / len(added)
        # The most chromatic shared colour is the most recognisable bridge.
        bridge = max(shared, key=lambda c: c["oklch"][1])
        result.append((novelty, other, bridge, added))
    return sorted(result, key=lambda item: item[0])


def strength(rank, total):
    return ("subtle", "moderate", "bold")[min(3 * rank // max(total, 1), 2)]


# Schemes.

def make_scheme(colours, mode, bridge=None):
    """Assign roles to one combination for one mode. bridge marks a chained scheme."""
    kind = "card" if bridge else "page"
    levels = LEVELS[kind][mode]
    others = [c for c in colours if c is not bridge]
    by_chroma = sorted(others, key=lambda c: c["oklch"][1], reverse=True)
    primary = by_chroma[0]
    secondary = by_chroma[1] if len(by_chroma) > 1 else (bridge or primary)
    accent = by_chroma[2] if len(by_chroma) > 2 else (bridge or secondary)
    _, ground_c, ground_h = by_chroma[-1]["oklch"]

    share, cap = TINT[kind]
    tint = min(ground_c * share, cap)
    text_c = min(ground_c * 0.25, 0.03)
    s = {role: oklch_hex(levels[role], tint, ground_h) for role in ("bg", "surface", "surface-2", "border")}
    worst = s["surface-2"]  # closest in lightness to the text, in both modes
    s["fg"] = fit((levels["fg"], text_c, ground_h), worst, TEXT)
    s["fg-muted"] = fit((levels["fg-muted"], text_c, ground_h), worst, TEXT)
    s["heading"] = fit(soften(bridge["oklch"], ground_h), worst, TEXT) if bridge else s["fg"]
    s["edge"] = fit((bridge or primary)["oklch"], s["bg"], EDGE)

    # Text on fills is a tinted near-white or near-black, never pure #fff or #000.
    light_text, dark_text = oklch_hex(0.985, 0.006, ground_h), oklch_hex(0.2, text_c, ground_h)
    for name, colour in (("primary", primary), ("secondary", secondary), ("accent", accent)):
        fill = fit(soften(colour["oklch"], ground_h), s["bg"], UI)
        on = max((light_text, dark_text), key=lambda t: contrast(t, fill))
        if contrast(on, fill) < TEXT:
            fill = fit(oklch(fill), on, TEXT)
        s[name], s[f"on-{name}"] = fill, on
    s["link"] = fit(soften(primary["oklch"], ground_h), worst, TEXT)

    chroma = min(max(sum(c["oklch"][1] for c in colours) / len(colours), 0.11), 0.16)
    for name, hue in STATUS_HUES.items():
        s[name] = fit((0.65, chroma, hue), worst, TEXT)
    for index, colour in enumerate(colours, 1):
        s[f"c{index}"] = colour["hex"]
    return s


def problems(scheme):
    found = []
    for fg, bg, target in CHECKS:
        ratio = contrast(scheme[fg], scheme[bg])
        if ratio < target - 0.005:
            found.append(f"{fg} on {bg}: {ratio:.2f}:1, needs {target}:1")
    return found


def build(combos, cid, card_ids):
    page = palette(combos, cid)
    result = {
        "source": "A Dictionary of Colour Combinations (Sanzo Wada)",
        "combination": cid,
        "colours": [{"name": c["name"], "hex": c["hex"]} for c in page],
        "light": make_scheme(page, "light"),
        "dark": make_scheme(page, "dark"),
        "cards": {},
    }
    for index, card_id in enumerate(card_ids):
        card = palette(combos, card_id)
        shared = [c for c in card if c in page]
        if not shared or len(shared) == len(card):
            raise SystemExit(f"error: {card_id} must share a colour with {cid} and add one. "
                             f"Run: scheme.py chain {cid}")
        bridge = max(shared, key=lambda c: c["oklch"][1])
        result["cards"]["card" if index == 0 else f"card-{index + 1}"] = {
            "combination": card_id,
            "bridge": {"name": bridge["name"], "hex": bridge["hex"]},
            "colours": [{"name": c["name"], "hex": c["hex"]} for c in card],
            "light": make_scheme(card, "light", bridge),
            "dark": make_scheme(card, "dark", bridge),
        }
    return result


def all_schemes(result):
    yield "page", result
    yield from result["cards"].items()


def to_css(result, prefix):
    def block(selector, tokens, mode, indent=""):
        lines = [f"{indent}{selector} {{", f"{indent}  color-scheme: {mode};"]
        lines += [f"{indent}  --{prefix}{key}: {value};" for key, value in tokens.items()]
        return "\n".join(lines + [f"{indent}}}"])

    names = ", ".join(c["name"] for c in result["colours"])
    out = [f"/* Colour scheme from A Dictionary of Colour Combinations #{result['combination']}: {names}.",
           "   Dark mode follows the OS unless <html data-theme=\"light|dark\"> overrides it. */"]
    auto_root, forced_root = ':root:not([data-theme="light"])', ':root[data-theme="dark"]'
    for name, scheme in all_schemes(result):
        if name == "page":
            light, dark_auto, dark_forced = ":root", auto_root, forced_root
        else:
            out.append(f"/* {name}: #{scheme['combination']}, bridge {scheme['bridge']['name']}. "
                       f"Put data-scheme=\"{name}\" on the element where it starts. */")
            light = f'[data-scheme="{name}"]'
            dark_auto, dark_forced = f"{auto_root} {light}", f"{forced_root} {light}"
        out.append(block(light, scheme["light"], "light"))
        out.append("@media (prefers-color-scheme: dark) {\n"
                   + block(dark_auto, scheme["dark"], "dark", "  ") + "\n}")
        out.append(block(dark_forced, scheme["dark"], "dark"))
    out.append(f"body, [data-scheme] {{ background: var(--{prefix}bg); color: var(--{prefix}fg); }}")
    return "\n".join(out)


# Preview.

PREVIEW_CSS = """
:root { --chrome-bg: #f4f4f2; --chrome-fg: #222; --chrome-muted: #666; color-scheme: light dark; }
@media (prefers-color-scheme: dark) { :root { --chrome-bg: #161616; --chrome-fg: #e8e8e8; --chrome-muted: #999; } }
* { box-sizing: border-box; }
body { margin: 0; padding: 24px 16px; background: var(--chrome-bg); color: var(--chrome-fg);
       font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1200px; margin: 0 auto; }
section.candidate { margin: 0 0 48px; }
.meta { color: var(--chrome-muted); font-size: 13px; margin: 2px 0 10px; }
.swatches { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.swatch { display: flex; align-items: center; gap: 6px; font-size: 12px; padding-right: 8px; }
.swatch i { width: 28px; height: 28px; border-radius: 4px; display: inline-block; border: 1px solid #8884; }
.swatch.bridge i { outline: 2px solid var(--chrome-fg); outline-offset: 1px; }
.modes { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 480px), 1fr)); gap: 16px; }
.panel { background: var(--bg); color: var(--fg); border-radius: 10px; padding: 20px; border: 1px solid var(--border); }
.panel .bar { display: flex; justify-content: space-between; align-items: center; gap: 12px;
              padding-bottom: 12px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
.panel .bar span { color: var(--fg-muted); font-size: 13px; }
.panel h2, .panel h3 { color: var(--heading); margin: 0 0 6px; }
.panel h2 { font-size: 22px; } .panel h3 { font-size: 16px; }
.panel p { margin: 0 0 12px; }
.panel a { color: var(--link); }
.muted { color: var(--fg-muted); }
.row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 14px; }
button { font: inherit; font-size: 14px; border-radius: 6px; padding: 6px 14px; border: 1px solid transparent; }
.primary { background: var(--primary); color: var(--on-primary); }
.secondary { background: var(--secondary); color: var(--on-secondary); }
.accent { background: var(--accent); color: var(--on-accent); }
.ghost { background: var(--surface); color: var(--fg); border-color: var(--border); }
.badge { font-size: 12px; border: 1px solid currentColor; border-radius: 99px; padding: 1px 10px; }
.success { color: var(--success); } .warning { color: var(--warning); } .error { color: var(--error); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
.card { background: var(--bg); color: var(--fg); border: 1px solid var(--border);
        border-top: 4px solid var(--edge); border-radius: 8px; padding: 14px; }
.card.plain { background: var(--surface); border-top-color: var(--border); }
.inner { background: var(--surface-2); border-radius: 6px; padding: 8px 10px; margin: 0 0 10px; font-size: 13px; }
.chip { font-size: 12px; background: var(--surface-2); border: 1px solid var(--border); border-radius: 99px; padding: 1px 10px; }
details { margin-top: 10px; font-size: 12px; }
table { border-collapse: collapse; margin-top: 6px; }
td, th { padding: 2px 10px 2px 0; text-align: left; font-family: ui-monospace, monospace; }
td i { display: inline-block; width: 12px; height: 12px; border-radius: 2px; vertical-align: middle; margin-right: 4px; }
.warn { color: #c0392b; font-size: 12px; margin-top: 6px; }
"""


def style(tokens):
    return ";".join(f"--{key}:{value}" for key, value in tokens.items())


def preview_section(result):
    cards = result["cards"]
    card = next(iter(cards.values()), None)
    bridge_hex = card["bridge"]["hex"] if card else None
    title = f"#{result['combination']}" + (f" → card #{card['combination']}" if card else "")
    meta = (f"bridge: {card['bridge']['name']} {bridge_hex}" if card else "no chained scheme")
    swatches = [(c, c["hex"] == bridge_hex) for c in result["colours"]]
    if card:
        swatches += [(c, False) for c in card["colours"] if c["hex"] != bridge_hex]
    out = [f'<section class="candidate"><h2>{html.escape(title)}</h2>',
           f'<div class="meta">{html.escape(meta)}</div><div class="swatches">']
    out += [f'<span class="swatch{" bridge" if is_bridge else ""}"><i style="background:{c["hex"]}"></i>'
            f'{html.escape(c["name"])} {c["hex"]}</span>' for c, is_bridge in swatches]
    out.append('</div><div class="modes">')
    for mode in ("light", "dark"):
        card_html = ""
        if card:
            card_html = (f'<div class="card" style="{style(card[mode])}"><h3>Chained card</h3>'
                         f'<p>Scheme #{card["combination"]} starts here. <a href="#">Link</a> '
                         f'<span class="muted">and muted text.</span></p>'
                         f'<div class="inner">Inner surface</div><div class="row">'
                         f'<button class="primary">Action</button><span class="chip">chip</span></div></div>')
        out.append(
            f'<div class="panel" style="{style(result[mode])}">'
            f'<div class="bar"><strong>{mode.title()}</strong><span>Docs · Pricing · About</span></div>'
            f'<h2>Page heading</h2><p>Body text with <a href="#">a link</a> and '
            f'<span class="muted">some muted secondary text</span>.</p>'
            f'<div class="row"><button class="primary">Primary</button>'
            f'<button class="secondary">Secondary</button><button class="accent">Accent</button>'
            f'<button class="ghost">Ghost</button></div>'
            f'<div class="row"><span class="badge success">Success</span>'
            f'<span class="badge warning">Warning</span><span class="badge error">Error</span></div>'
            f'<div class="cards"><div class="card plain"><h3>Page card</h3>'
            f'<p>Uses the page scheme.</p><div class="inner">Inner surface</div></div>{card_html}</div></div>')
    out.append("</div>")
    issues = [f"{name} {mode}: {p}" for name, s in all_schemes(result) for mode in ("light", "dark")
              for p in problems(s[mode])]
    out += [f'<div class="warn">{html.escape(issue)}</div>' for issue in issues]
    out.append("<details><summary>Tokens</summary>")
    for name, s in all_schemes(result):
        rows = "".join(f'<tr><th>--{key}</th>' + "".join(
            f'<td><i style="background:{s[mode][key]}"></i>{s[mode][key]}</td>' for mode in ("light", "dark"))
            + "</tr>" for key in s["light"])
        out.append(f"<table><tr><th>{name}</th><th>light</th><th>dark</th></tr>{rows}</table>")
    out.append("</details></section>")
    return "".join(out)


def preview_html(results):
    body = "".join(preview_section(r) for r in results)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Colour scheme preview</title><style>{PREVIEW_CSS}</style></head>'
            f'<body><main><h1>Colour scheme preview</h1>{body}</main></body></html>')


# Commands.

def parse_specs(combos, specs):
    """Turn "176" or "176:43" into (page, [card]). A bare id picks a moderate card."""
    pairs = []
    for spec in specs:
        page, _, card = spec.partition(":")
        cid = int(page)
        if card:
            cards = [int(card)] if card != "none" else []
        else:
            options = neighbours(combos, cid)
            cards = [options[len(options) // 2][1]] if options else []
        pairs.append((cid, cards))
    return pairs


def main(argv):
    global SWATCHES
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--swatches", action="store_true",
                        help="print colour blocks even when output is not a terminal")
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("show", help="print combinations")
    show.add_argument("ids", type=int, nargs="+")
    pick = commands.add_parser("random", help="print random combinations")
    near = commands.add_parser("near", help="combinations near a hex colour")
    near.add_argument("hex")
    search = commands.add_parser("search", help="combinations by colour name")
    search.add_argument("text")
    for command in (pick, near, search):
        command.add_argument("--size", type=int, choices=(2, 3, 4), help="only combinations of this many colours")
        command.add_argument("--count", type=int, default=8, help="how many to print (default 8)")
    pick.add_argument("--seed", type=int, help="seed, for repeatable picks")
    chain = commands.add_parser("chain", help="combinations that share a colour with ID")
    chain.add_argument("id", type=int)
    chain.add_argument("--count", type=int, default=12, help="how many to print (default 12)")
    make = commands.add_parser("build", help="print scheme tokens")
    make.add_argument("id", type=int)
    make.add_argument("--card", type=int, action="append", default=[],
                      help="chained scheme; repeat for card, card-2, ...")
    make.add_argument("--format", choices=("css", "json"), default="css")
    make.add_argument("--prefix", default="", help="token name prefix, for example 'cs-'")
    view = commands.add_parser("preview", help="write an HTML preview sheet")
    view.add_argument("specs", nargs="*", help="ID, ID:CARD, or ID:none")
    view.add_argument("--random", type=int, default=0, help="add N random combinations")
    view.add_argument("--size", type=int, choices=(2, 3, 4))
    view.add_argument("--seed", type=int)
    view.add_argument("-o", "--output", default="colour-scheme-preview.html")
    ratio = commands.add_parser("contrast", help="WCAG contrast of two colours")
    ratio.add_argument("fg")
    ratio.add_argument("bg")
    args = parser.parse_args(argv)

    SWATCHES = args.swatches or sys.stdout.isatty()
    colours, combos = load()
    if args.command == "show":
        for cid in args.ids:
            print(describe(cid, palette(combos, cid)))
    elif args.command in ("random", "near", "search"):
        ids = [cid for cid in combos if not args.size or len(combos[cid]) == args.size]
        mark = ()
        if args.command == "random":
            ids = random.Random(args.seed).sample(ids, min(args.count, len(ids)))
        elif args.command == "near":
            target = oklab(args.hex)
            nearest = sorted(colours, key=lambda c: math.dist(c["oklab"], target))[:3]
            print("nearest: " + " · ".join(
                f"{c['name']} {c['hex']} (ΔE {math.dist(c['oklab'], target) * 100:.1f})" for c in nearest))
            rank = {c["id"]: i for i, c in enumerate(nearest)}
            ids = sorted((cid for cid in ids if any(c["id"] in rank for c in combos[cid])),
                         key=lambda cid: min(rank.get(c["id"], 9) for c in combos[cid]))
            mark = nearest
        else:
            mark = [c for c in colours if args.text.lower() in c["name"].lower()]
            ids = [cid for cid in ids if any(c in mark for c in combos[cid])]
        for cid in ids[:args.count]:
            print(describe(cid, combos[cid], mark))
        if not ids:
            print("no matches")
    elif args.command == "chain":
        options = neighbours(combos, args.id)
        print(describe(args.id, palette(combos, args.id)) + f"   ({len(options)} chained options)")
        # Spread the sample across the range so it shows subtle to bold.
        step = max(len(options) / args.count, 1)
        for i in sorted({int(k * step) for k in range(min(args.count, len(options)))}):
            novelty, cid, bridge, added = options[i]
            new = ", ".join(f"{swatch(c['hex'])}{c['name']} {c['hex']}" for c in added)
            print(f"{cid:>3}  {strength(i, len(options)):<8}  bridge {swatch(bridge['hex'])}{bridge['name']} {bridge['hex']}  adds {new}")
    elif args.command == "build":
        result = build(combos, args.id, args.card)
        print(to_css(result, args.prefix) if args.format == "css" else json.dumps(result, indent=2))
        for name, scheme in all_schemes(result):
            for mode in ("light", "dark"):
                for issue in problems(scheme[mode]):
                    print(f"warning: {name} {mode}: {issue}", file=sys.stderr)
    elif args.command == "preview":
        specs = list(args.specs)
        if args.random:
            ids = [cid for cid in combos if not args.size or len(combos[cid]) == args.size]
            specs += [str(cid) for cid in random.Random(args.seed).sample(ids, args.random)]
        if not specs:
            raise SystemExit("error: give combination ids or --random N")
        results = [build(combos, cid, cards) for cid, cards in parse_specs(combos, specs)]
        Path(args.output).write_text(preview_html(results))
        print(f"wrote {Path(args.output).resolve()} ({', '.join(specs)})")
    elif args.command == "contrast":
        value = contrast(args.fg, args.bg)
        verdict = "text OK" if value >= TEXT else "UI only" if value >= UI else "fails"
        print(f"{value:.2f}:1  {verdict}")
        if value < TEXT:
            print(f"nearest passing text colour, same hue: {fit(oklch(args.fg), args.bg, TEXT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
