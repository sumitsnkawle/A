#!/usr/bin/env python3
"""Build styles.css from the Tailwind-style utility classes used in index.html.

The site used to load the Tailwind *browser* build, which compiles CSS in every
visitor's browser on each page load (Tailwind marks it "not for production").
This script generates a static stylesheet instead, covering exactly the
utilities the page uses, with Tailwind v4 semantics.

Usage:  python3 tools/build_css.py          (rewrites styles.css)

Any class in a class="..." attribute that this script does not understand
makes it exit with an error, so a new utility can't silently go unstyled.
Add support for it below, or write it as custom CSS in index.html.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
OUT = ROOT / "styles.css"

# Classes defined by hand in the <style> block of index.html (or used only as
# JS hooks). They are not utilities.
CUSTOM = set("""
wrap section-pad eyebrow h2 lead kicker dark bg-grid-dark bg-soft btn btn-primary
btn-ghost btn-secondary btn-outline-light btn-white link-arrow glass card card-hover ico
icon-badge num check mock mock-bar mock-tile nav-blue nav-link tour-tab tour-num
tour-panel step-line float float-delay pulse-glow flow-line flow-chip typing-dot
avatar-ring founder-profile founder-photo fade-up bar chat-panel-h rtl-row rtl-flip
ltr-diagram group lang-option lang-option-mobile counter font-display noise-overlay
stat stat-num logo-strip section-head kpi to-top skip-link nav-scrolled is-active
""".split())

SPACING = 0.25  # rem per step

BREAKPOINTS = [("sm", "40rem"), ("md", "48rem"), ("lg", "64rem"), ("xl", "80rem")]

PALETTE = {
    "white": "#ffffff", "black": "#000000", "transparent": "transparent", "current": "currentColor",
    "slate-50": "#f8fafc", "slate-100": "#f1f5f9", "slate-200": "#e2e8f0", "slate-300": "#cbd5e1",
    "slate-400": "#94a3b8", "slate-500": "#64748b", "slate-600": "#475569", "slate-700": "#334155",
    "slate-800": "#1e293b", "slate-900": "#0f172a",
    "blue-50": "#eff6ff", "blue-100": "#dbeafe", "blue-300": "#93c5fd", "blue-400": "#60a5fa",
    "blue-600": "#2563eb", "blue-700": "#1d4ed8",
    "amber-50": "#fffbeb", "amber-200": "#fde68a", "amber-300": "#fcd34d", "amber-400": "#fbbf24",
    "amber-700": "#b45309",
    "emerald-50": "#ecfdf5", "emerald-200": "#a7f3d0", "emerald-300": "#6ee7b7",
    "emerald-400": "#34d399", "emerald-500": "#10b981", "emerald-700": "#047857",
    "red-50": "#fef2f2", "red-100": "#fee2e2", "red-200": "#fecaca", "red-300": "#fca5a5",
    "red-400": "#f87171", "red-500": "#ef4444", "red-700": "#b91c1c",
}

FONT_SIZE = {
    "xs": ("0.75rem", "1rem"), "sm": ("0.875rem", "1.25rem"), "base": ("1rem", "1.5rem"),
    "lg": ("1.125rem", "1.75rem"), "xl": ("1.25rem", "1.75rem"), "2xl": ("1.5rem", "2rem"),
    "3xl": ("1.875rem", "2.25rem"), "4xl": ("2.25rem", "2.5rem"), "5xl": ("3rem", "1"),
}
RADIUS = {"": "0.25rem", "xs": "0.125rem", "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem",
          "xl": "0.75rem", "2xl": "1rem", "3xl": "1.5rem", "full": "9999px"}
MAX_W = {"xs": "20rem", "sm": "24rem", "md": "28rem", "lg": "32rem", "xl": "36rem", "2xl": "42rem",
         "3xl": "48rem", "4xl": "56rem", "5xl": "64rem", "6xl": "72rem", "7xl": "80rem"}
SHADOW = {
    "sm": "0 1px 3px 0 rgb(0 0 0 / .1), 0 1px 2px -1px rgb(0 0 0 / .1)",
    "": "0 1px 3px 0 rgb(0 0 0 / .1), 0 1px 2px -1px rgb(0 0 0 / .1)",
    "md": "0 4px 6px -1px rgb(0 0 0 / .1), 0 2px 4px -2px rgb(0 0 0 / .1)",
    "lg": "0 10px 15px -3px rgb(0 0 0 / .1), 0 4px 6px -4px rgb(0 0 0 / .1)",
    "xl": "0 20px 25px -5px rgb(0 0 0 / .1), 0 8px 10px -6px rgb(0 0 0 / .1)",
    "2xl": "0 25px 50px -12px rgb(0 0 0 / .25)",
}
BLUR = {"sm": "8px", "": "8px", "md": "12px", "lg": "16px", "xl": "24px", "2xl": "40px", "3xl": "64px"}
LEADING = {"none": "1", "tight": "1.25", "snug": "1.375", "normal": "1.5", "relaxed": "1.625", "loose": "2"}
WEIGHT = {"normal": "400", "medium": "500", "semibold": "600", "bold": "700", "extrabold": "800"}
GRAD_DIR = {"r": "to right", "l": "to left", "b": "to bottom", "t": "to top", "br": "to bottom right",
            "bl": "to bottom left", "tr": "to top right", "tl": "to top left"}

SIDES = {
    "p": ["padding"], "px": ["padding-inline"], "py": ["padding-block"],
    "pt": ["padding-top"], "pb": ["padding-bottom"], "pl": ["padding-left"], "pr": ["padding-right"],
    "ps": ["padding-inline-start"], "pe": ["padding-inline-end"],
    "m": ["margin"], "mx": ["margin-inline"], "my": ["margin-block"],
    "mt": ["margin-top"], "mb": ["margin-bottom"], "ml": ["margin-left"], "mr": ["margin-right"],
    "ms": ["margin-inline-start"], "me": ["margin-inline-end"],
    "top": ["top"], "bottom": ["bottom"], "left": ["left"], "right": ["right"],
    "inset": ["inset"], "inset-x": ["inset-inline"], "inset-y": ["inset-block"],
    "w": ["width"], "h": ["height"], "min-h": ["min-height"], "min-w": ["min-width"],
    "max-h": ["max-height"], "size": ["width", "height"],
    "gap": ["gap"], "gap-x": ["column-gap"], "gap-y": ["row-gap"],
}

SIMPLE = {
    "block": "display:block", "inline-block": "display:inline-block", "inline": "display:inline",
    "flex": "display:flex", "inline-flex": "display:inline-flex", "grid": "display:grid",
    "hidden": "display:none", "contents": "display:contents",
    "absolute": "position:absolute", "relative": "position:relative", "fixed": "position:fixed",
    "sticky": "position:sticky", "static": "position:static",
    "flex-col": "flex-direction:column", "flex-row": "flex-direction:row",
    "flex-wrap": "flex-wrap:wrap", "flex-1": "flex:1 1 0%", "shrink-0": "flex-shrink:0", "grow": "flex-grow:1",
    "items-center": "align-items:center", "items-start": "align-items:flex-start",
    "items-end": "align-items:flex-end", "items-stretch": "align-items:stretch",
    "justify-between": "justify-content:space-between", "justify-center": "justify-content:center",
    "justify-start": "justify-content:flex-start", "justify-end": "justify-content:flex-end",
    "content-start": "align-content:flex-start", "self-start": "align-self:flex-start",
    "text-center": "text-align:center", "text-left": "text-align:left", "text-right": "text-align:right",
    "text-start": "text-align:start",
    "italic": "font-style:italic", "uppercase": "text-transform:uppercase",
    "underline": "text-decoration-line:underline", "no-underline": "text-decoration-line:none",
    "truncate": "overflow:hidden;text-overflow:ellipsis;white-space:nowrap",
    "whitespace-nowrap": "white-space:nowrap", "break-words": "overflow-wrap:break-word",
    "overflow-hidden": "overflow:hidden", "overflow-y-auto": "overflow-y:auto", "overflow-x-auto": "overflow-x:auto",
    "pointer-events-none": "pointer-events:none", "cursor-pointer": "cursor:pointer",
    "cursor-not-allowed": "cursor:not-allowed",
    "list-none": "list-style-type:none",
    "object-contain": "object-fit:contain", "object-cover": "object-fit:cover", "object-top": "object-position:top",
    "antialiased": "-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale",
    "scroll-smooth": "scroll-behavior:smooth",
    "tracking-tight": "letter-spacing:-0.025em", "tracking-tighter": "letter-spacing:-0.05em",
    "tracking-wide": "letter-spacing:0.025em",
    "outline-none": "outline-style:none",
    "aspect-auto": "aspect-ratio:auto", "aspect-square": "aspect-ratio:1/1", "aspect-video": "aspect-ratio:16/9",
    "w-auto": "width:auto", "h-auto": "height:auto", "w-full": "width:100%", "h-full": "height:100%",
    "w-px": "width:1px", "h-px": "height:1px", "w-screen": "width:100vw",
    "mx-auto": "margin-inline:auto", "ml-auto": "margin-left:auto", "mr-auto": "margin-right:auto",
    "ms-auto": "margin-inline-start:auto", "mt-auto": "margin-top:auto",
    "inset-0": "inset:0", "inset-x-0": "inset-inline:0", "top-0": "top:0", "right-0": "right:0",
    "left-0": "left:0", "bottom-0": "bottom:0",
    "right-auto": "right:auto", "left-auto": "left:auto",
    "border": "border-style:solid;border-width:1px", "border-0": "border-width:0",
    "border-2": "border-style:solid;border-width:2px",
    "border-t": "border-top-style:solid;border-top-width:1px",
    "border-b": "border-bottom-style:solid;border-bottom-width:1px",
    "border-l": "border-left-style:solid;border-left-width:1px",
    "border-r": "border-right-style:solid;border-right-width:1px",
    "border-y": "border-block-style:solid;border-block-width:1px",
    "border-l-4": "border-left-style:solid;border-left-width:4px",
    "border-t-2": "border-top-style:solid;border-top-width:2px",
    "transition": "transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,opacity,box-shadow,transform,translate,scale,rotate,filter,backdrop-filter;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:150ms",
    "transition-shadow": "transition-property:box-shadow;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:150ms",
    "transition-transform": "transition-property:transform,translate,scale,rotate;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:150ms",
    "transition-colors": "transition-property:color,background-color,border-color;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:150ms",
    "rotate-45": "rotate:45deg", "rotate-180": "rotate:180deg",
    "order-1": "order:1", "order-2": "order:2",
    "col-span-full": "grid-column:1/-1",
    "divide-y": None,  # handled specially
    "sr-only": "position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border-width:0",
    "not-sr-only": "position:static;width:auto;height:auto;padding:0;margin:0;overflow:visible;clip:auto;white-space:normal",
}

VARIANT_SELECTORS = {
    "hover": lambda s: f"{s}:hover",
    "focus": lambda s: f"{s}:focus",
    "focus-visible": lambda s: f"{s}:focus-visible",
    "disabled": lambda s: f"{s}:disabled",
    "group-hover": lambda s: f".group:hover {s}",
    "group-open": lambda s: f".group[open] {s}",
}


def esc(cls):
    return re.sub(r"([^a-zA-Z0-9_-])", r"\\\1", cls)


def hex_alpha(h, a):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgb({r} {g} {b} / {a:g})"


def color(token):
    """Resolve a colour token like 'white/10', '[#1764d1]/25', '[var(--brand)]'."""
    alpha = None
    if "/" in token and not token.startswith("[") or re.search(r"\]/", token):
        token, a = token.rsplit("/", 1)
        alpha = float(a[1:-1]) if a.startswith("[") else int(a) / 100
    if token.startswith("[") and token.endswith("]"):
        base = token[1:-1].replace("_", " ")
        if not (base.startswith("#") or base.startswith("var(") or base.startswith("rgb")):
            return None
    elif token in PALETTE:
        base = PALETTE[token]
    else:
        return None
    if alpha is None:
        return base
    if base.startswith("#"):
        return hex_alpha(base, alpha)
    return f"color-mix(in srgb, {base} {alpha * 100:g}%, transparent)"


def length(token, negative=False):
    """Resolve a spacing/size token like '4', '2.5', '[560px]', '2/3', 'px'."""
    if token.startswith("[") and token.endswith("]"):
        v = token[1:-1].replace("_", " ")
    elif token == "px":
        v = "1px"
    elif re.fullmatch(r"\d+/\d+", token):
        a, b = token.split("/")
        v = f"{int(a) / int(b) * 100:.6g}%"
    elif re.fullmatch(r"\d+(\.\d+)?", token):
        n = float(token)
        v = "0" if n == 0 else f"{n * SPACING:g}rem"
    else:
        return None
    return f"calc({v} * -1)" if negative else v


def decl(base):
    """Return the CSS declarations (and optional selector suffix) for a utility."""
    if base in SIMPLE and SIMPLE[base]:
        return SIMPLE[base], ""

    neg = base.startswith("-")
    b = base[1:] if neg else base

    # Arbitrary property: [mask-image:...]
    m = re.fullmatch(r"\[([a-z-]+):(.+)\]", b)
    if m:
        prop, val = m.group(1), m.group(2).replace("_", " ")
        out = f"{prop}:{val}"
        if prop == "mask-image":
            out = f"-webkit-mask-image:{val};{out}"
        return out, ""

    if b == "divide-y":
        return "border-top-width:0;border-bottom-style:solid;border-bottom-width:1px", " > :not(:last-child)"
    m = re.fullmatch(r"divide-(.+)", b)
    if m and color(m.group(1)):
        return f"border-color:{color(m.group(1))}", " > :not(:last-child)"

    m = re.fullmatch(r"space-([xy])-(.+)", b)
    if m:
        v = length(m.group(2), neg)
        if v is None:
            return None
        prop = "margin-inline-end" if m.group(1) == "x" else "margin-bottom"
        return f"{prop}:{v}", " > :not(:last-child)"

    m = re.fullmatch(r"(p|px|py|pt|pb|pl|pr|ps|pe|m|mx|my|mt|mb|ml|mr|ms|me|top|bottom|left|right|inset-x|inset-y|inset|w|h|min-h|min-w|max-h|size|gap-x|gap-y|gap)-(.+)", b)
    if m:
        key, val = m.groups()
        if key == "max-h" and not val.startswith("["):
            v = length(val)
        elif key in ("w", "h") and val in ("screen",):
            return None
        else:
            v = length(val, neg)
        if v is None:
            return None
        return ";".join(f"{p}:{v}" for p in SIDES[key]), ""

    m = re.fullmatch(r"max-w-(.+)", b)
    if m:
        v = MAX_W.get(m.group(1)) or length(m.group(1))
        return (f"max-width:{v}", "") if v else None

    m = re.fullmatch(r"z-(\d+|\[\d+\])", b)
    if m:
        return f"z-index:{m.group(1).strip('[]')}", ""

    m = re.fullmatch(r"(grid-cols|grid-rows)-(.+)", b)
    if m:
        prop = "grid-template-columns" if m.group(1) == "grid-cols" else "grid-template-rows"
        val = m.group(2)
        if val.isdigit():
            return f"{prop}:repeat({val},minmax(0,1fr))", ""
        if val.startswith("["):
            return f"{prop}:{val[1:-1].replace('_', ' ')}", ""
        return None

    m = re.fullmatch(r"col-span-(\d+)", b)
    if m:
        return f"grid-column:span {m.group(1)} / span {m.group(1)}", ""

    m = re.fullmatch(r"aspect-\[(.+)\]", b)
    if m:
        return f"aspect-ratio:{m.group(1)}", ""

    m = re.fullmatch(r"text-(.+)", b)
    if m:
        v = m.group(1)
        if v in FONT_SIZE:
            fs, lh = FONT_SIZE[v]
            return f"font-size:{fs};line-height:{lh}", ""
        if re.fullmatch(r"\[\d+(\.\d+)?(px|rem|em)\]", v):
            return f"font-size:{v[1:-1]}", ""
        c = color(v)
        return (f"color:{c}", "") if c else None

    m = re.fullmatch(r"font-(.+)", b)
    if m and m.group(1) in WEIGHT:
        return f"font-weight:{WEIGHT[m.group(1)]}", ""

    m = re.fullmatch(r"leading-(.+)", b)
    if m:
        v = m.group(1)
        if v in LEADING:
            return f"line-height:{LEADING[v]}", ""
        if v.startswith("["):
            return f"line-height:{v[1:-1]}", ""
        return None

    m = re.fullmatch(r"tracking-\[(.+)\]", b)
    if m:
        return f"letter-spacing:{m.group(1)}", ""

    m = re.fullmatch(r"bg-gradient-to-(\w+)", b)
    if m and m.group(1) in GRAD_DIR:
        return (f"background-image:linear-gradient({GRAD_DIR[m.group(1)]},var(--tw-gradient-from,transparent),"
                f"var(--tw-gradient-to,transparent))"), ""
    m = re.fullmatch(r"(from|to)-(.+)", b)
    if m:
        c = color(m.group(2))
        return (f"--tw-gradient-{m.group(1)}:{c}", "") if c else None

    m = re.fullmatch(r"bg-(.+)", b)
    if m:
        c = color(m.group(1))
        return (f"background-color:{c}", "") if c else None

    m = re.fullmatch(r"border-(t|b|l|r|x|y)-(.+)", b)
    if m:
        c = color(m.group(2))
        side = {"t": "top", "b": "bottom", "l": "left", "r": "right", "x": "inline", "y": "block"}[m.group(1)]
        return (f"border-{side}-color:{c}", "") if c else None
    m = re.fullmatch(r"border-(.+)", b)
    if m:
        c = color(m.group(1))
        return (f"border-color:{c}", "") if c else None

    m = re.fullmatch(r"rounded(?:-(t|b|l|r|tl|tr|bl|br))?(?:-(xs|sm|md|lg|xl|2xl|3xl|full|\[.+\]))?", b)
    if m:
        side, size = m.group(1), m.group(2) or ""
        v = size[1:-1] if size.startswith("[") else RADIUS.get(size)
        corners = {None: ["border-radius"],
                   "t": ["border-top-left-radius", "border-top-right-radius"],
                   "b": ["border-bottom-left-radius", "border-bottom-right-radius"],
                   "l": ["border-top-left-radius", "border-bottom-left-radius"],
                   "r": ["border-top-right-radius", "border-bottom-right-radius"],
                   "tl": ["border-top-left-radius"], "tr": ["border-top-right-radius"],
                   "bl": ["border-bottom-left-radius"], "br": ["border-bottom-right-radius"]}[side]
        return ";".join(f"{c}:{v}" for c in corners), ""

    m = re.fullmatch(r"shadow(?:-(.+))?", b)
    if m:
        v = m.group(1) or ""
        if v in SHADOW:
            return f"box-shadow:{SHADOW[v]}", ""
        if v.startswith("["):
            return f"box-shadow:{v[1:-1].replace('_', ' ')}", ""
        return None

    m = re.fullmatch(r"ring-(\d+)", b)
    if m:
        return f"box-shadow:0 0 0 {m.group(1)}px var(--tw-ring-color,currentColor)", ""
    m = re.fullmatch(r"ring-(.+)", b)
    if m and color(m.group(1)):
        return f"--tw-ring-color:{color(m.group(1))}", ""

    m = re.fullmatch(r"blur(?:-(.+))?", b)
    if m:
        v = m.group(1) or ""
        v = BLUR.get(v) or (v[1:-1] if v.startswith("[") else None)
        return (f"filter:blur({v})", "") if v else None

    m = re.fullmatch(r"opacity-(\d+)", b)
    if m:
        return f"opacity:{int(m.group(1)) / 100:g}", ""

    m = re.fullmatch(r"duration-(\d+)", b)
    if m:
        return f"transition-duration:{m.group(1)}ms", ""

    m = re.fullmatch(r"scale-(\[.+\]|\d+)", b)
    if m:
        v = m.group(1)
        v = v[1:-1] if v.startswith("[") else f"{int(v) / 100:g}"
        return f"scale:{v}", ""

    m = re.fullmatch(r"underline-offset-(\d+)", b)
    if m:
        return f"text-underline-offset:{m.group(1)}px", ""

    return None


def rule(cls):
    """Return (breakpoint_index, css_rule) for a class, or None if unknown."""
    parts = re.split(r":(?![^\[]*\])", cls)
    base, variants = parts[-1], parts[:-1]

    important = False
    if base.startswith("!"):
        important, base = True, base[1:]
    elif base.endswith("!"):
        important, base = True, base[:-1]

    child = ""
    # Arbitrary child variant like [&_svg]:w-6
    for v in list(variants):
        m = re.fullmatch(r"\[&_(.+)\]", v)
        if m:
            child = " " + m.group(1).replace("_", " ")
            variants.remove(v)

    d = decl(base)
    if d is None:
        return None
    body, suffix = d
    if important:
        body = ";".join(p + " !important" for p in body.split(";"))

    selector = "." + esc(cls)
    bp = 0
    for v in variants:
        if v in dict(BREAKPOINTS):
            bp = [n for n, _ in BREAKPOINTS].index(v) + 1
        elif v in VARIANT_SELECTORS:
            selector = VARIANT_SELECTORS[v](selector)
        else:
            return None
    css = f"{selector}{child}{suffix}{{{body}}}"
    if bp:
        css = f"@media (min-width:{BREAKPOINTS[bp - 1][1]}){{{css}}}"
    return bp, css


PREFLIGHT = """
*,::after,::before,::backdrop,::file-selector-button{box-sizing:border-box;margin:0;padding:0;border:0 solid}
html,:host{line-height:1.5;-webkit-text-size-adjust:100%;tab-size:4;-webkit-tap-highlight-color:transparent}
hr{height:0;color:inherit;border-top-width:1px}
h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}
a{color:inherit;-webkit-text-decoration:inherit;text-decoration:inherit}
b,strong{font-weight:bolder}
small{font-size:80%}
ol,ul,menu{list-style:none}
img,svg,video,canvas,audio,iframe,embed,object{display:block;vertical-align:middle}
img,video{max-width:100%;height:auto}
button,input,select,optgroup,textarea,::file-selector-button{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;border-radius:0;background-color:transparent;opacity:1}
::placeholder{opacity:1}
textarea{resize:vertical}
button,input:where([type=button],[type=reset],[type=submit]),::file-selector-button{appearance:button}
summary{display:list-item}
[hidden]:where(:not([hidden=until-found])){display:none!important}
/* Unlike stock Tailwind, a grid with no grid-cols-* gets one shrinkable column, so
   long content (e.g. on mobile, before an lg:grid-cols-* kicks in) can't overflow. */
.grid{grid-template-columns:minmax(0,1fr)}
"""


def collect_classes(html):
    strict, lenient = set(), set()
    for m in re.finditer(r'class="([^"]*)"', html):
        for c in m.group(1).split():
            if "${" not in c and "}" not in c:
                strict.add(c)
    # className strings set from JavaScript
    for m in re.finditer(r"'([^'\n]*)'", html):
        for c in m.group(1).split():
            lenient.add(c)
    return strict, lenient


def main():
    html = HTML.read_text(encoding="utf-8")
    strict, lenient = collect_classes(html)
    rules, unknown = {}, []
    for cls in sorted(strict | lenient):
        if cls in CUSTOM:
            continue
        r = rule(cls)
        if r is None:
            if cls in strict:
                unknown.append(cls)
            continue
        rules[cls] = r
    if unknown:
        sys.exit("Unsupported utility classes (add them to tools/build_css.py):\n  " + "\n  ".join(unknown))

    # Order: base utilities first, then each breakpoint, so wider screens win.
    # Within a group, plain utilities come before state variants (hover etc.).
    def key(item):
        cls, (bp, _) = item
        return (bp, ":" in cls.split("[")[0] and not re.match(r"(sm|md|lg|xl):[^:]+$", cls), cls)

    body = "\n".join(css for _, (_, css) in sorted(rules.items(), key=key))
    OUT.write_text(
        "/* Generated by tools/build_css.py from index.html. Do not edit by hand. */\n"
        "@layer base, utilities;\n"
        f"@layer base{{{PREFLIGHT}}}\n"
        f"@layer utilities{{\n{body}\n}}\n",
        encoding="utf-8",
    )
    print(f"styles.css: {len(rules)} utilities")


if __name__ == "__main__":
    main()
