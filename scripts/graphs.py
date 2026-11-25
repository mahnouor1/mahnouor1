# "On GitHub" board and the 6-month contribution heatmap.
from datetime import date, timedelta
from svgkit import Svg, measure, wrap

HEAT = {
    "light": ["#ebe6dc", "#e6dcff", "#c4a8ff", "#9466f5", "#6a3cd4"],
    "dark": ["#262947", "#3a2f70", "#5a40ad", "#8a62f0", "#c3a6ff"],
}
HEAT_TEXT = {"light": ["#9a948a", "#22201c", "#22201c", "#ffffff", "#ffffff"],
             "dark": ["#6f7299", "#f3f1ff", "#f3f1ff", "#15172b", "#15172b"]}


def fmt(n):
    return f"{n:,}"


def stats(data):
    today = date.fromisoformat(data["today"])
    days = data["days"]
    month = sum(v for k, v in days.items() if k.startswith(today.isoformat()[:7]))
    best = max(days.items(), key=lambda kv: kv[1]) if days else ("", 0)
    first = min(days) if days else data["today"]
    return {
        "month": month, "month_name": today.strftime("%B"),
        "best": best[1], "best_day": date.fromisoformat(best[0]).strftime("%-d %b") if best[0] else "",
        "total": sum(data["years"].values()), "since": first[:4],
    }


def github_board(t, data, T, user):
    s = stats(data)
    tiles = [
        (fmt(data["last_year"]), "contributions in the last year", "bl", "cal"),
        (fmt(s["month"]), f"contributions in {s['month_name']} so far", "gr", "bolt"),
        (fmt(s["best"]), f"best day, {s['best_day']}", "am", "star"),
        (fmt(s["total"]), f"contributions since {s['since']}", "pu", "gauge"),
    ]
    small = [(fmt(data["public_repos"]), "public repos", "tl", "site"),
             (fmt(data["stars"]), "stars earned", "pk", "star"),
             (fmt(data["followers"]), "followers", "gr", "in")]
    W, H = 880, 340
    label = "On GitHub: " + ", ".join(f"{v} {l}" for v, l, _, _ in tiles + small)
    s_ = Svg(W, H, label, T)
    return s_, tiles, small


def draw_board(svg, tiles, small, icon, today):
    T, W = svg.T, svg.w
    svg.board()
    svg.text(34, 58, "On GitHub", "display", 28, T["text"])
    d = date.fromisoformat(today).strftime("%-d %b %Y")
    svg.text(W - 34, 56, f"redrawn every night · {d}", "mono", 15, T["muted"], "end")
    tw, gap, x, y = 186, 20, 34, 82
    rots = [0.8, -0.8, 0.6, -0.6]
    ic = T["pop"] if T["bg"].startswith("#f") else T["warn"]
    for i, (v, l, tint, ico) in enumerate(tiles):
        g0 = len(svg.parts)
        svg.sticker(x, y, tw, 132, T[tint], rx=14, shadow=5)
        icon(svg, ico, x + tw - 38, y + 14, 0.95, ic, 2.4)
        svg.text(x + 16, y + 62, v, "display", 38, T["text"])
        ly = y + 88
        for ln in wrap(l, "mono", 13.5, tw - 30)[:2]:
            svg.text(x + 16, ly, ln, "mono", 13.5, T["text"])
            ly += 19
        svg.parts[g0:] = [f'<g transform="rotate({rots[i]} {x+tw/2} {y+66})">' + "".join(svg.parts[g0:]) + "</g>"]
        x += tw + gap
    x, y = 34, 244
    pw = (W - 68 - 2 * 20) / 3
    for i, (v, l, tint, ico) in enumerate(small):
        svg.sticker(x, y, pw, 62, T[tint], rx=14, rot=[-0.4, 0.4, -0.3][i], shadow=5)
        icon(svg, ico, x + 18, y + 19, 1.0, ic, 2.4)
        svg.text(x + 56, y + 43, v, "display", 30, T["text"])
        svg.text(x + 56 + measure(v, "display", 30) + 12, y + 39, l, "mono", 14.5, T["text"])
        x += pw + 20


def heatmap(t, data, T, months=6):
    today = date.fromisoformat(data["today"])
    start = today - timedelta(days=months * 30.5)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    weeks = []
    d = start
    while d <= today:
        weeks.append([d + timedelta(days=i) for i in range(7)])
        d += timedelta(days=7)
    vals = {k: v for k, v in data["days"].items()}
    shown = [vals.get(x.isoformat(), 0) for w in weeks for x in w if x <= today and x >= start]
    total = sum(shown)
    nz = sorted(v for v in shown if v)

    def level(v):
        if not v:
            return 0
        if not nz:
            return 1
        q = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75)]
        return 1 + sum(v > x for x in q)

    n = len(weeks)
    W = 880
    gap = 3.5
    cell = min(28, (W - 2 * 50 - (n - 1) * gap) / n)
    gridw = n * cell + (n - 1) * gap
    gx = (W - gridw) / 2
    H = int(118 + 7 * (cell + gap) + 54)
    svg = Svg(W, H, f"{fmt(total)} contributions in the last {months} months", T)
    svg.board()
    cx, cy, cw, ch = 24, 22, W - 52, H - 50
    svg.sticker(cx, cy, cw, ch, T["card"], rx=16, shadow=5)
    tx = gx
    svg.text(tx, cy + 44, fmt(total), "display", 24, T["text"])
    svg.text(tx + measure(fmt(total), "display", 24) + 9, cy + 43, f"contributions in the last {months} months", "mono", 16, T["text"])
    gy = cy + 92
    last_month = None
    for i, w in enumerate(weeks):
        x = gx + i * (cell + gap)
        if i > 0 and w[0].day <= 7 or (i == 0 and w[0].day <= 14):
            svg.text(x, gy - 10, w[-1].strftime("%b"), "mono", 14, T["text"])
        for j, day in enumerate(w):
            if day > today:
                continue
            v = vals.get(day.isoformat(), 0)
            lv = level(v)
            y = gy + j * (cell + gap)
            svg.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="5" fill="{HEAT[t][lv]}"/>')
            size = 12.5 if v < 100 else 10.5
            svg.text(x + cell / 2, y + cell / 2 + size * 0.36, str(v), "monob" if v else "mono", size, HEAT_TEXT[t][lv], "middle")
    by = gy + 7 * (cell + gap) + 22
    svg.text(gx, by, "contributions per day", "mono", 14, T["muted"])
    lx = gx + gridw - 5 * 20 - measure("More", "mono", 14) - 8
    svg.text(lx - 8, by, "Less", "mono", 14, T["muted"], "end")
    for k in range(5):
        svg.add(f'<rect x="{lx + k*20:.1f}" y="{by-13}" width="15" height="15" rx="4" fill="{HEAT[t][k]}"/>')
    svg.text(lx + 5 * 20 + 2, by, "More", "mono", 14, T["muted"])
    return svg
