# Fetches public GitHub numbers. Used by build.py; on any failure the last good copy in state.json is used.
import json, os, re, urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
UA = {"User-Agent": "profile-readme-builder"}


def get(url, extra=None):
    req = urllib.request.Request(url, headers={**UA, **(extra or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf8")


def parse_calendar(html):
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        tips[m.group(1)] = m.group(2).strip()
    days = {}
    for m in re.finditer(r'<td[^>]*class="ContributionCalendar-day"[^>]*>', html):
        tag = m.group(0)
        d = re.search(r'data-date="([\d-]+)"', tag)
        i = re.search(r'\bid="([^"]+)"', tag)
        if not d:
            continue
        tip = tips.get(i.group(1) if i else "", "")
        n = re.match(r"(\d+|No) contribution", tip)
        days[d.group(1)] = 0 if not n or n.group(1) == "No" else int(n.group(1))
    total = re.search(r"([\d,]+)\s+contributions?\s+in", html)
    return days, int(total.group(1).replace(",", "")) if total else None


def fetch(user):
    hdr = {"X-Requested-With": "XMLHttpRequest"}
    days, last_year = parse_calendar(get(f"https://github.com/users/{user}/contributions", hdr))
    if not days or last_year is None:
        raise RuntimeError("could not read the contribution calendar")
    u = json.loads(get(f"https://api.github.com/users/{user}"))
    repos = json.loads(get(f"https://api.github.com/users/{user}/repos?per_page=100"))
    created_year = int(u["created_at"][:4])
    years = {}
    for y in range(created_year, date.today().year + 1):
        _, n = parse_calendar(get(f"https://github.com/users/{user}/contributions?from={y}-01-01&to={y}-12-31", hdr))
        years[str(y)] = n or 0
    return {
        "today": date.today().isoformat(),
        "last_year": last_year,
        "days": {k: v for k, v in sorted(days.items()) if v},
        "years": years,
        "public_repos": u["public_repos"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "followers": u["followers"],
    }


def load(user, offline=False):
    if not offline:
        try:
            data = fetch(user)
            with open(STATE, "w", encoding="utf8") as f:
                json.dump(data, f, indent=1)
            print("fetched live GitHub data")
            return data
        except Exception as e:
            print(f"live fetch failed ({e}), using state.json")
    with open(STATE, encoding="utf8") as f:
        return json.load(f)
