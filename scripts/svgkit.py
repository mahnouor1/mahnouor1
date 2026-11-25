# Tiny SVG toolkit: text measuring, sticker shapes, and per-file font subsetting.
import base64, io, os
from fontTools.ttLib import TTFont
from fontTools import subset

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILES = {
    "display": ("Fredoka-700.ttf", "MF", 700),
    "body": ("Fredoka-600.ttf", "MB", 600),
    "mono": ("DMMono-400.ttf", "MM", 400),
    "monob": ("DMMono-500.ttf", "MN", 500),
}
_fonts = {}


def font(kind):
    if kind not in _fonts:
        _fonts[kind] = TTFont(os.path.join(HERE, "fonts", FONT_FILES[kind][0]))
    return _fonts[kind]


def measure(s, kind, size):
    f = font(kind)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = 0
    for ch in s:
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        w += hmtx[g][0]
    return w * size / upm


def wrap(s, kind, size, width):
    lines, cur = [], ""
    for word in s.split():
        t = (cur + " " + word).strip()
        if measure(t, kind, size) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


class Svg:
    def __init__(self, w, h, label, T):
        self.w, self.h, self.label, self.T = w, h, label, T
        self.parts, self.defs, self.used = [], [], {}

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, kind, size, fill, anchor="start", extra=""):
        self.used.setdefault(kind, set()).update(s)
        fam, w = FONT_FILES[kind][1], FONT_FILES[kind][2]
        a = "" if anchor == "start" else f' text-anchor="{anchor}"'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{w}" font-size="{size}" fill="{fill}"{a}{extra}>{esc(s)}</text>')

    def sticker(self, x, y, w, h, fill, rx=12, rot=0, shadow=4, stroke=2.5, shadow_fill=None):
        T = self.T
        cx, cy = x + w / 2, y + h / 2
        g = f'<g transform="rotate({rot} {cx:.1f} {cy:.1f})">' if rot else "<g>"
        sh = f'<rect x="{x+shadow:.1f}" y="{y+shadow:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{shadow_fill or T["line"]}"/>' if shadow else ""
        self.add(f'{g}{sh}<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{T["line"]}" stroke-width="{stroke}"/></g>')

    def board(self, x=0, y=0, w=None, h=None):
        T = self.T
        w, h = w or self.w, h or self.h
        pid = "dots"
        if not any(pid in d for d in self.defs):
            self.defs.append(f'<pattern id="{pid}" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{T["dot"]}"/></pattern>')
        self.add(f'<rect x="{x+1}" y="{y+1}" width="{w-2}" height="{h-2}" rx="22" fill="{T["board"]}" stroke="{T["boardline"]}" stroke-width="1.5"/>')
        self.add(f'<rect x="{x+1}" y="{y+1}" width="{w-2}" height="{h-2}" rx="22" fill="url(#{pid})"/>')

    def _fontface(self):
        css = []
        for kind, chars in self.used.items():
            fname, fam, wt = FONT_FILES[kind]
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga"]
            opts.name_IDs = []
            opts.notdef_outline = True
            sub = subset.Subsetter(opts)
            f = TTFont(os.path.join(HERE, "fonts", fname))
            sub.populate(text="".join(sorted(chars)) + " ")
            sub.subset(f)
            buf = io.BytesIO()
            f.flavor = "woff2"
            f.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            css.append(f"@font-face{{font-family:{fam};font-weight:{wt};src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
        return "".join(css)

    def render(self):
        lab = esc(self.label)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{lab}"><title>{lab}</title>'
                f'<defs><style>{self._fontface()}</style>{"".join(self.defs)}</defs>{"".join(self.parts)}</svg>')
