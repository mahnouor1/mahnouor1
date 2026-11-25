# Draws every SVG in assets/ (light + dark) from profile.json and writes README.md.
# Run: python3 scripts/build.py
import base64, json, os, sys
import fetch, graphs
from svgkit import Svg, measure, wrap, HERE

ROOT = os.path.dirname(HERE)

THEMES = {
    "light": {
        "bg": "#fbf6ee", "board": "#f4ede1", "boardline": "#e4d9c6", "dot": "#d9ccb6",
        "card": "#ffffff", "text": "#22201c", "muted": "#66615a", "line": "#22201c",
        "pu": "#e7defc", "pk": "#ffd6e8", "bl": "#cfe6ff", "gr": "#d6f2dc", "am": "#ffe1b8", "tl": "#cdeff0",
        "pop": "#8b5cf6", "on-pop": "#ffffff", "go": "#2fbf71", "warn": "#ffb020", "tag": "#ffffff",
    },
    "dark": {
        "bg": "#15172b", "board": "#15172b", "boardline": "#22254a", "dot": "#2b2f57",
        "card": "#1f2240", "text": "#f3f1ff", "muted": "#cac9e1", "line": "#0a0b18",
        "pu": "#4a3a80", "pk": "#7a2f5b", "bl": "#24477a", "gr": "#1f5a3a", "am": "#7a4b1c", "tl": "#1b5560",
        "pop": "#b794ff", "on-pop": "#15172b", "go": "#4ade80", "warn": "#ffc24d", "tag": "#1f2240",
    },
}

# ---------- icons: 24x24 stroke glyphs drawn at (x, y) with scale s ----------
ICONS = {
    "mic": '<rect x="9" y="2.5" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3.5M8.5 21.5h7"/>',
    "mail": '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M3.5 6.5l8.5 6.5 8.5-6.5"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5l5.5 5.5"/>',
    "gauge": '<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="M12 17l4.5-5.5"/><circle cx="12" cy="17" r="1.3"/>',
    "db": '<ellipse cx="12" cy="5.5" rx="7.5" ry="3"/><path d="M4.5 5.5v13c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-13M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3"/>',
    "check": '<circle cx="12" cy="12" r="9.5"/><path d="M7.5 12.5l3 3 6-6.5"/>',
    "clock": '<circle cx="12" cy="12" r="9.5"/><path d="M12 6.5V12l3.5 2.5"/>',
    "bolt": '<path d="M13 2.5L4.5 13.5H11l-1 8 8.5-11H12z"/>',
    "star": '<path d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z"/>',
    "globe": '<circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c2.6 2.7 3.8 6 3.8 9.5s-1.2 6.8-3.8 9.5c-2.6-2.7-3.8-6-3.8-9.5s1.2-6.8 3.8-9.5z"/>',
    "ig": '<rect x="3" y="3" width="18" height="18" rx="5.5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.3" cy="6.7" r="0.6"/>',
    "in": '<rect x="3" y="3" width="18" height="18" rx="3.5"/><path d="M8 10.5v6M8 7.5v.1M11.5 16.5v-6M11.5 13c0-1.6 1-2.6 2.4-2.6s2.1.9 2.1 2.6v3.5"/>',
    "cal": '<rect x="3" y="4.5" width="18" height="16.5" rx="2.5"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4M8 14h3"/>',
    "arrow": '<path d="M7 17L17 7M9 7h8v8"/>',
    "site": '<rect x="2.5" y="4" width="19" height="16" rx="2.5"/><path d="M2.5 8.5h19M6 6.3v.1M8.5 6.3v.1"/>',
}


def icon(svg, name, x, y, s, color, sw=2.2):
    svg.add(f'<g transform="translate({x:.1f} {y:.1f}) scale({s})" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


def chip(svg, x, y, text, fill, kind="mono", size=12.5, padx=9, h=24, rot=0, shadow=2):
    T = svg.T
    w = measure(text, kind, size) + padx * 2
    svg.sticker(x, y, w, h, T[fill], rx=7, rot=rot, shadow=shadow, stroke=2)
    svg.text(x + w / 2, y + h / 2 + size * 0.36, text, kind, size, T["text"], "middle")
    return w


# ---------- hero (compact) ----------
def hero(t, P):
    T = THEMES[t]
    W, H = 880, 172
    s = Svg(W, H, f"Hi, I'm {P['name']}. {P['tagline']}", T)
    s.board()
    s.sticker(30, 30, 72, 72, "#fbf6ee", rx=17, shadow=5, stroke=2.5, shadow_fill=T["pop"])
    s.text(66, 88, P["name"][0], "display", 54, "#22201c", "middle")
    x0, ty = 126, 70
    s.text(x0, ty, "Hi, I'm", "display", 38, T["text"])
    nx = x0 + measure("Hi, I'm ", "display", 38)
    nw = measure(P["name"], "display", 38) + 18
    s.sticker(nx - 8, ty - 37, nw, 48, T["pu"], rx=9, rot=-1.5, shadow=3)
    s.text(nx + 1, ty, P["name"], "display", 38, T["text"], extra=' transform="rotate(-1.5 %d %d)"' % (nx + nw / 2, ty - 13))
    s.text(x0, ty + 28, P["tagline"], "body", 15.5, T["muted"])
    cx, y = x0, ty + 44
    for text, fill in P["chips"]:
        cx += chip(s, cx, y, text, fill, kind="body", size=12.5, padx=9, h=25, shadow=2) + 9
    cw = measure(P["corner"], "display", 15) + 22
    s.sticker(W - cw - 28, 24, cw, 32, T["pop"], rx=8, rot=4, shadow=3)
    s.text(W - cw / 2 - 28, 45, P["corner"], "display", 15, T["on-pop"], "middle", extra=' transform="rotate(4 %d 40)"' % (W - cw / 2 - 28))
    return s


# ---------- section label (compact) ----------
def label(t, title, tag, fill):
    T = THEMES[t]
    W, H = 880, 52
    s = Svg(W, H, title, T)
    lw = measure(title, "display", 21) + 26
    s.sticker(6, 8, lw, 36, T[fill], rx=10, rot=-2, shadow=4, stroke=2.2)
    s.text(6 + lw / 2, 33, title, "display", 21, T["text"], "middle", extra=' transform="rotate(-2 %d 26)"' % (6 + lw / 2))
    tw = measure(tag, "mono", 13) + 20
    s.add(f'<rect x="{lw + 24}" y="12" width="{tw:.1f}" height="27" rx="6" fill="{T["tag"]}" stroke="{T["boardline"]}" stroke-width="1.5"/>')
    s.text(lw + 34, 30.5, tag, "mono", 13, T["text"])
    return s


# ---------- app card (compact) ----------
def app(t, a):
    T = THEMES[t]
    W, H = 440, 172
    s = Svg(W, H, f"{a['name']}: {a['line']} {a['status']}. {a['fact']}", T)
    s.board()
    x, y, w, h = 12, 12, W - 28, H - 28
    s.sticker(x, y, w, h, T["card"], rx=14, shadow=4)
    s.sticker(x + 16, y + 16, 40, 40, T[a["tint"]], rx=10, shadow=2, stroke=2)
    icon(s, a["icon"], x + 24, y + 24, 1.0, T["text"], 2.2)
    s.text(x + 68, y + 42, a["name"], "display", 20, T["text"])
    st = a["status"]
    sx = x + 68 + measure(a["name"], "display", 20) + 10
    stw = measure(st, "monob", 11.5) + 16
    s.add(f'<rect x="{sx:.1f}" y="{y+27}" width="{stw:.1f}" height="20" rx="10" fill="{T["go"] if st == "live" else T["warn"]}" stroke="{T["line"]}" stroke-width="1.8"/>')
    s.text(sx + stw / 2, y + 41, st, "monob", 11.5, "#15172b", "middle")
    s.sticker(x + w - 34, y + 14, 22, 22, T["pop"], rx=6, shadow=2, stroke=1.8)
    icon(s, "arrow", x + w - 31, y + 17, 0.68, T["on-pop"], 3)
    ly = y + 82
    for ln in wrap(a["line"], "body", 14.5, w - 34)[:2]:
        s.text(x + 16, ly, ln, "body", 14.5, T["text"])
        ly += 20
    s.text(x + 16, y + h - 14, a["fact"], "mono", 12, T["muted"])
    return s


# ---------- reel card (compact) ----------
def reel(t, r, thumb_b64):
    T = THEMES[t]
    W, H = 220, 300
    s = Svg(W, H, f"{r['title']} ({r['date']}, Instagram)", T)
    s.board()
    x, y, w, h = 8, 8, W - 22, H - 22
    s.sticker(x, y, w, h, T["card"], rx=12, shadow=4)
    tx, ty, tw = x + 10, y + 10, w - 20
    th = tw * 1.0
    cid = f"clip{r['id'].replace('_', '')}"
    s.defs.append(f'<clipPath id="{cid}"><rect x="{tx}" y="{ty}" width="{tw}" height="{th:.1f}" rx="8"/></clipPath>')
    s.add(f'<image x="{tx}" y="{ty}" width="{tw}" height="{th:.1f}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})" '
          f'href="data:image/jpeg;base64,{thumb_b64}" xlink:href="data:image/jpeg;base64,{thumb_b64}"/>')
    s.add(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th:.1f}" rx="8" fill="none" stroke="{T["line"]}" stroke-width="2.2"/>')
    vw = measure(r["views"], "monob", 11) + 30
    s.add(f'<rect x="{tx+7}" y="{ty+7}" width="{vw:.1f}" height="20" rx="10" fill="#15172b" fill-opacity="0.82"/>')
    s.add(f'<path d="M{tx+15} {ty+12}l6.5 5-6.5 5z" fill="#ffffff"/>')
    s.text(tx + 26, ty + 21, r["views"], "monob", 11, "#ffffff")
    px, py = tx + tw - 18, ty + th - 18
    s.add(f'<circle cx="{px+2}" cy="{py+2}" r="12" fill="{T["line"]}"/><circle cx="{px}" cy="{py}" r="12" fill="{T["pop"]}" stroke="{T["line"]}" stroke-width="2"/>'
          f'<path d="M{px-3.5} {py-5.5}l9 5.5-9 5.5z" fill="{T["on-pop"]}"/>')
    ly = ty + th + 22
    for ln in wrap(r["title"], "body", 13.5, tw)[:2]:
        s.text(tx, ly, ln, "body", 13.5, T["text"])
        ly += 18
    s.text(tx, y + h - 11, r["date"], "mono", 10.5, T["muted"])
    return s


# ---------- README ----------
def pic(name, alt, width=None, height=None, href=None):
    size = f' width="{width}"' if width else f' height="{height}"'
    p = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
         f'<img src="assets/{name}-light.svg"{size} alt="{alt}"></picture>')
    return f'<a href="{href}">{p}</a>' if href else p


def readme(P, gh_alt):
    L = P["links"]
    out = [pic("hero", f"Hi, I'm {P['name']}. {P['tagline']}", "100%", href=L["site"]["url"]), "",
           pic("github", gh_alt, "100%"), "",
           pic("label-ship", "What I ship", "100%"), "", '<p align="center">']
    for a in P["apps"]:
        out.append(pic(f"app-{a['id']}", f"{a['name']}: {a['line']}", "49%", href=a["url"]))
    more = " · ".join(f'<a href="{u}">{n}</a>' for n, u in P["more"])
    out += ["</p>", "", f'<p align="center"><sub>Company and client repos are private · more: {more}</sub></p>', "",
            pic("label-reels", "Latest reels", "100%"), "", '<p align="center">']
    for r in P["reels"]:
        out.append(pic(f"reel-{r['id']}", r["title"], "24%", href=f"https://www.instagram.com/mahnoor.ships/reel/{r['id']}/"))
    out += ["</p>", "",
            f'<p align="center"><sub><a href="{L["site"]["url"]}">Portfolio</a> · <a href="{L["linkedin"]["url"]}">LinkedIn</a> · '
            f'<a href="{L["email"]["url"]}">Email</a> · <a href="{L["call"]["url"]}">Book a call</a> · '
            f'design inspired by <a href="https://github.com/ZazaGdev">ZazaGdev</a></sub></p>', ""]
    return "\n".join(out)


def main():
    P = json.load(open(os.path.join(ROOT, "profile.json"), encoding="utf8"))
    A = os.path.join(ROOT, "assets")
    os.makedirs(A, exist_ok=True)
    for f in os.listdir(A):
        if f.endswith(".svg"):
            os.remove(os.path.join(A, f))
    thumbs = {r["id"]: base64.b64encode(open(os.path.join(HERE, "thumbs", r["id"] + ".jpg"), "rb").read()).decode() for r in P["reels"]}
    data = fetch.load(P["user"], offline="--offline" in sys.argv)
    out = {}
    for t in THEMES:
        out[f"hero-{t}"] = hero(t, P)
        g = graphs.github_card(t, data, THEMES[t], icon)
        out[f"github-{t}"] = g
        out[f"label-ship-{t}"] = label(t, "What I ship", f"{len(P['apps'])} systems I built", "am")
        out[f"label-reels-{t}"] = label(t, "Latest reels", f"Instagram {P['links']['instagram']['handle']}", "pk")
        for a in P["apps"]:
            out[f"app-{a['id']}-{t}"] = app(t, a)
        for r in P["reels"]:
            out[f"reel-{r['id']}-{t}"] = reel(t, r, thumbs[r["id"]])
    for name, svg in out.items():
        with open(os.path.join(A, name + ".svg"), "w", encoding="utf8") as f:
            f.write(svg.render())
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf8") as f:
        f.write(readme(P, out["github-light"].label))
    print(f"wrote {len(out)} svgs + README.md")


if __name__ == "__main__":
    main()
