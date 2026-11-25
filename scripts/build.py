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


# ---------- hero ----------
def hero(t, P):
    T = THEMES[t]
    W = 880
    lines = wrap(P["tagline"], "body", 19, 640)
    H = 214 + 26 * len(lines)
    s = Svg(W, H, f"Hi, I'm {P['name']}. {P['tagline']}", T)
    s.board()
    # logo tile
    s.sticker(40, 40, 96, 96, "#fbf6ee", rx=22, shadow=7, stroke=3, shadow_fill=T["pop"])
    s.text(88, 115, P["name"][0], "display", 72, "#22201c", "middle")
    # title + highlighted name
    x0, ty = 168, 104
    s.text(x0, ty, "Hi, I'm", "display", 52, T["text"])
    nx = x0 + measure("Hi, I'm ", "display", 52)
    nw = measure(P["name"], "display", 52) + 24
    s.sticker(nx - 10, ty - 50, nw, 66, T["pu"], rx=10, rot=-1.5, shadow=4)
    s.text(nx + 2, ty, P["name"], "display", 52, T["text"], extra=' transform="rotate(-1.5 %d %d)"' % (nx + nw / 2, ty - 17))
    y = ty + 40
    for ln in lines:
        s.text(x0, y, ln, "body", 19, T["muted"])
        y += 26
    s.text(x0, y + 4, P["role"], "mono", 14, T["muted"])
    y += 24
    cx = x0
    for text, fill in P["chips"]:
        cx += chip(s, cx, y, text, fill, kind="body", size=14, padx=11, h=30, shadow=3) + 12
    # corner sticker
    cw = measure(P["corner"], "display", 18) + 28
    s.sticker(W - cw - 34, 28, cw, 40, T["pop"], rx=10, rot=4, shadow=4)
    s.text(W - cw / 2 - 34, 54, P["corner"], "display", 18, T["on-pop"], "middle", extra=' transform="rotate(4 %d 48)"' % (W - cw / 2 - 34))
    return s


# ---------- badges ----------
BADGE = {"instagram": ("pk", "ig"), "linkedin": ("bl", "in"), "site": ("pu", "site"), "email": ("gr", "mail"), "call": ("am", "cal")}


def badge(t, key, L):
    T = THEMES[t]
    fill, ic = BADGE[key]
    lw = measure(L["label"], "display", 16)
    hw = measure(L["handle"], "mono", 14) + 10 if L["handle"] else 0
    W, H = int(14 + 22 + 8 + lw + hw + 16 + 6), 48
    s = Svg(W, H, f"{L['label']} {L['handle']}".strip(), T)
    s.sticker(2, 2, W - 8, H - 8, T[fill], rx=10, shadow=4, stroke=2.2)
    icon(s, ic, 13, 12.5, 0.85, T["text"], 2.3)
    s.text(44, 29, L["label"], "display", 16, T["text"])
    if L["handle"]:
        s.text(44 + lw + 10, 28.5, L["handle"], "mono", 14, T["text"])
    return s


# ---------- numbers board ----------
def numbers(t, P):
    T = THEMES[t]
    rows = (len(P["pills"]) + 1) // 2
    W, H = 880, 242 + rows * 80
    s = Svg(W, H, f"{P['numbers_title']}: " + "; ".join(f"{n['value']} {n['label']}" for n in P["numbers"] + P["pills"]), T)
    s.board()
    s.text(34, 58, P["numbers_title"], "display", 28, T["text"])
    s.text(W - 34, 56, P["numbers_note"], "mono", 15, T["muted"], "end")
    tw, gap, x, y = 186, 16, 34, 82
    rots = [0.8, -0.8, 0.6, -0.6]
    for i, n in enumerate(P["numbers"]):
        s.sticker(x, y, tw, 132, T[n["tint"]], rx=14, rot=rots[i], shadow=5)
        g0 = len(s.parts)
        icon(s, n["icon"], x + tw - 38, y + 14, 0.95, T["pop"] if t == "light" else T["warn"], 2.4)
        size = 38 if measure(n["value"], "display", 38) < tw - 70 else 31
        s.text(x + 16, y + 62, n["value"], "display", size, T["text"])
        ly = y + 88
        for ln in wrap(n["label"], "mono", 13.5, tw - 30)[:2]:
            s.text(x + 16, ly, ln, "mono", 13.5, T["text"])
            ly += 19
        cx, cy = x + tw / 2, y + 66
        s.parts[g0:] = [f'<g transform="rotate({rots[i]} {cx} {cy})">' + "".join(s.parts[g0:]) + "</g>"]
        x += tw + gap + 4
    pw = (W - 68 - 24) / 2
    for i, p in enumerate(P["pills"]):
        x, y = 34 + (i % 2) * (pw + 24), 240 + (i // 2) * 80
        s.sticker(x, y, pw, 62, T[p["tint"]], rx=14, rot=[-0.4, 0.4, 0.3, -0.3][i % 4], shadow=5)
        icon(s, p["icon"], x + 18, y + 19, 1.0, T["pop"] if t == "light" else T["warn"], 2.4)
        s.text(x + 56, y + 43, p["value"], "display", 30, T["text"])
        s.text(x + 56 + measure(p["value"], "display", 30) + 12, y + 39, p["label"], "mono", 14.5, T["text"])
    return s


# ---------- section label ----------
def label(t, title, tag, fill):
    T = THEMES[t]
    W, H = 880, 70
    s = Svg(W, H, title, T)
    lw = measure(title, "display", 28) + 34
    s.sticker(8, 10, lw, 48, T[fill], rx=12, rot=-2, shadow=5, stroke=2.5)
    s.text(8 + lw / 2, 44, title, "display", 28, T["text"], "middle", extra=' transform="rotate(-2 %d 34)"' % (8 + lw / 2))
    tw = measure(tag, "mono", 15) + 24
    s.add(f'<rect x="{lw + 30}" y="18" width="{tw:.1f}" height="32" rx="7" fill="{T["tag"]}" stroke="{T["boardline"]}" stroke-width="1.5"/>')
    s.text(lw + 30 + 12, 39, tag, "mono", 15, T["text"])
    return s


# ---------- app card ----------
def app(t, a):
    T = THEMES[t]
    W, H = 440, 304
    s = Svg(W, H, f"{a['name']}: {a['line']} {a['status']}. {a['fact']}", T)
    s.board()
    x, y, w, h = 16, 16, W - 36, H - 36
    s.sticker(x, y, w, h, T["card"], rx=16, shadow=5)
    # icon tile
    s.sticker(x + 20, y + 20, 62, 62, T[a["tint"]], rx=14, shadow=3)
    icon(s, a["icon"], x + 34, y + 34, 1.42, T["text"], 2.1)
    s.text(x + 100, y + 50, a["name"], "display", 25, T["text"])
    st = a["status"]
    stw = measure(st, "monob", 12.5) + 20
    s.add(f'<rect x="{x+100}" y="{y+60}" width="{stw:.1f}" height="22" rx="11" fill="{T["go"] if st == "live" else T["warn"]}" stroke="{T["line"]}" stroke-width="2"/>')
    s.text(x + 100 + stw / 2, y + 75.5, st, "monob", 12.5, "#15172b", "middle")
    # arrow corner
    s.sticker(x + w - 44, y + 16, 28, 28, T["pop"], rx=7, shadow=2, stroke=2)
    icon(s, "arrow", x + w - 40.5, y + 19.5, 0.88, T["on-pop"], 2.8)
    ly = y + 122
    for ln in wrap(a["line"], "body", 17.5, w - 44)[:3]:
        s.text(x + 20, ly, ln, "body", 17.5, T["text"])
        ly += 25
    cx = x + 20
    for text, fill in a["chips"]:
        cx += chip(s, cx, y + 190, text, fill, size=12.5, shadow=0) + 8
    s.text(x + 20, y + 245, a["fact"], "mono", 13.5, T["muted"])
    return s


# ---------- reel card ----------
def reel(t, r, thumb_b64):
    T = THEMES[t]
    W, H = 220, 414
    s = Svg(W, H, f"{r['title']} ({r['date']}, Instagram)", T)
    s.board()
    x, y, w, h = 10, 10, W - 26, H - 26
    s.sticker(x, y, w, h, T["card"], rx=14, shadow=5)
    tx, ty, tw, th = x + 12, y + 12, w - 24, (w - 24) / 0.704
    cid = f"clip{r['id'].replace('_', '')}"
    s.defs.append(f'<clipPath id="{cid}"><rect x="{tx}" y="{ty}" width="{tw}" height="{th:.1f}" rx="9"/></clipPath>')
    s.add(f'<image x="{tx}" y="{ty}" width="{tw}" height="{th:.1f}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})" '
          f'href="data:image/jpeg;base64,{thumb_b64}" xlink:href="data:image/jpeg;base64,{thumb_b64}"/>')
    s.add(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th:.1f}" rx="9" fill="none" stroke="{T["line"]}" stroke-width="2.5"/>')
    # views chip
    vw = measure(r["views"], "monob", 12) + 34
    s.add(f'<rect x="{tx+8}" y="{ty+8}" width="{vw:.1f}" height="22" rx="11" fill="#15172b" fill-opacity="0.82"/>')
    s.add(f'<path d="M{tx+17} {ty+13.5}l7.5 5.5-7.5 5.5z" fill="#ffffff"/>')
    s.text(tx + 30, ty + 23.5, r["views"], "monob", 12, "#ffffff")
    # play button
    px, py = tx + tw - 22, ty + th - 22
    s.add(f'<circle cx="{px+2}" cy="{py+2}" r="15" fill="{T["line"]}"/><circle cx="{px}" cy="{py}" r="15" fill="{T["pop"]}" stroke="{T["line"]}" stroke-width="2.2"/>'
          f'<path d="M{px-4} {py-6.5}l10.5 6.5-10.5 6.5z" fill="{T["on-pop"]}"/>')
    ly = ty + th + 28
    for ln in wrap(r["title"], "body", 15.5, tw)[:3]:
        s.text(tx, ly, ln, "body", 15.5, T["text"])
        ly += 21
    s.text(tx, y + h - 16, f"{r['date']} · Instagram", "mono", 11.5, T["muted"])
    return s


# ---------- README ----------
def pic(name, alt, width=None, height=None, href=None):
    size = f' width="{width}"' if width else f' height="{height}"'
    p = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
         f'<img src="assets/{name}-light.svg"{size} alt="{alt}"></picture>')
    return f'<a href="{href}">{p}</a>' if href else p


def readme(P):
    L = P["links"]
    out = [pic("hero", f"Hi, I'm {P['name']}. {P['tagline']}", "100%", href=L["site"]["url"]), "",
            pic("github", "On GitHub", "100%"), "",
            pic("graph-6m", "Contributions in the last 6 months", "100%"), "",
            pic("label-ship", "What I ship", "100%"), "", '<p align="center">']
    for a in P["apps"]:
        out.append(pic(f"app-{a['id']}", f"{a['name']}: {a['line']}", "49%", href=a["url"]))
    more = " · ".join(f'<a href="{u}">{n}</a>' for n, u in P["more"])
    out += ["</p>", "", f'<p align="center"><sub>Company and client repos are private. Demos on request · more ships: {more}</sub></p>', "",
            pic("label-reels", "Latest reels", "100%"), "", '<p align="center">']
    for r in P["reels"]:
        out.append(pic(f"reel-{r['id']}", r["title"], "24%", href=f"https://www.instagram.com/mahnoor.ships/reel/{r['id']}/"))
    out += ["</p>", "",
            f'<p align="center"><sub>Karachi, Pakistan · building <a href="https://skimmy.ai">Skimmy AI</a> · '
            f'<a href="{L["site"]["url"]}">mahnoor.cloudordinate.com</a> · '
            f'design inspired by <a href="https://github.com/ZazaGdev">ZazaGdev</a></sub></p>', ""]
    return "\n".join(out)


def main():
    P = json.load(open(os.path.join(ROOT, "profile.json"), encoding="utf8"))
    A = os.path.join(ROOT, "assets")
    os.makedirs(A, exist_ok=True)
    thumbs = {r["id"]: base64.b64encode(open(os.path.join(HERE, "thumbs", r["id"] + ".jpg"), "rb").read()).decode() for r in P["reels"]}
    data = fetch.load(P["user"], offline="--offline" in sys.argv)
    out = {}
    for t in THEMES:
        b, tiles, small = graphs.github_board(t, data, THEMES[t], P["user"])
        graphs.draw_board(b, tiles, small, icon, data["today"])
        b.label = "On GitHub: " + ", ".join(f"{v} {l}" for v, l, _, _ in tiles + small)
        out[f"github-{t}"] = b
        out[f"graph-6m-{t}"] = graphs.heatmap(t, data, THEMES[t])
        out[f"hero-{t}"] = hero(t, P)
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
        f.write(readme(P))
    print(f"wrote {len(out)} svgs + README.md")


if __name__ == "__main__":
    main()
