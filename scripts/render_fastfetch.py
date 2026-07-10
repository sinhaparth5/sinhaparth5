#!/usr/bin/env python3
"""Regenerates assets/fastfetch.svg with live public GitHub stats.

The avatar ASCII art (scripts/ascii_block.svg) and the embedded Ubuntu Mono
font (scripts/fontface.css) are static and checked in -- only the stats in
the info panel are refreshed here. Run manually with:

    GH_TOKEN=<token> python3 scripts/render_fastfetch.py

The daily GitHub Actions workflow (.github/workflows/update-fastfetch.yml)
runs this with the built-in GITHUB_TOKEN.
"""
import datetime
import json
import os
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "sinhaparth5")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

API_ROOT = "https://api.github.com"


def api_get(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "fastfetch-card-script")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def graphql(query):
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(f"{API_ROOT}/graphql", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "fastfetch-card-script")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def fetch_repos(username):
    repos = []
    page = 1
    while True:
        chunk = api_get(f"{API_ROOT}/users/{username}/repos?per_page=100&page={page}&type=owner")
        if not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return [r for r in repos if not r.get("fork")]


def fetch_language_totals(repos):
    totals = {}
    for repo in repos:
        try:
            langs = api_get(repo["languages_url"])
        except Exception:
            continue
        for lang, size in langs.items():
            totals[lang] = totals.get(lang, 0) + size
    return totals


def main():
    if not TOKEN:
        print("ERROR: no GH_TOKEN / GITHUB_TOKEN in environment", file=sys.stderr)
        sys.exit(1)

    user = api_get(f"{API_ROOT}/users/{USERNAME}")
    followers = user["followers"]

    repos = fetch_repos(USERNAME)
    repos_count = len(repos)
    stars = sum(r.get("stargazers_count", 0) for r in repos)

    lang_totals = fetch_language_totals(repos)
    total_bytes = sum(lang_totals.values()) or 1
    ranked_langs = sorted(lang_totals.items(), key=lambda kv: kv[1], reverse=True)
    top_lang_name, top_lang_bytes = ranked_langs[0] if ranked_langs else ("Unknown", 0)
    top_lang_pct = 100 * top_lang_bytes / total_bytes
    top5_names = [name for name, _ in ranked_langs[:5]]

    prs = api_get(f"{API_ROOT}/search/issues?q=author:{USERNAME}+type:pr")["total_count"]

    gql = graphql(
        f'query {{ user(login: "{USERNAME}") {{ contributionsCollection {{ '
        f"totalCommitContributions totalRepositoriesWithContributedCommits }} }} }}"
    )
    contrib = gql["user"]["contributionsCollection"]
    commits = contrib["totalCommitContributions"]
    contributed_to = contrib["totalRepositoriesWithContributedCommits"]
    year = datetime.datetime.now(datetime.timezone.utc).year

    fields = [
        ("Role", "GPU Architecture Student"),
        ("Focus", "CUDA & Parallel Computing"),
        ("Background", "Web Architecture, Full-Stack Dev"),
        ("Languages", ", ".join(top5_names) if top5_names else "n/a"),
        ("Top Language", f"{top_lang_name} — {top_lang_pct:.1f}% of public code"),
        ("Repos", f"{repos_count} public"),
        ("Stars", f"{stars} earned"),
        ("Commits", f"{commits} in {year}"),
        ("Pull Requests", f"{prs} opened"),
        ("Contributed To", f"{contributed_to} repositories"),
        ("Followers", f"{followers}"),
    ]

    render(fields)
    print("Updated assets/fastfetch.svg with live stats:")
    for label, value in fields:
        print(f"  {label}: {value}")


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(fields):
    with open(os.path.join(REPO_ROOT, "scripts", "fontface.css")) as f:
        fontface_css = f.read()
    with open(os.path.join(REPO_ROOT, "scripts", "ascii_block.svg")) as f:
        ascii_block = f.read()

    LABEL_COLOR = "#7ee787"
    VALUE_COLOR = "#c9d1d9"
    DIM_COLOR = "#30363d"
    HOST_COLOR = "#79c0ff"

    INFO_X = 320
    INFO_FONT = 13.5
    INFO_LINE_H = 21.5
    INFO_START_Y = 92
    LABEL_WIDTH_CH = 15
    INFO_CHAR_W = INFO_FONT * 0.6
    HEADER_FONT = 16

    info_lines = []
    y = INFO_START_Y
    info_lines.append(
        f'<text x="{INFO_X}" y="{y:.2f}" font-family="Ubuntu Mono, monospace" '
        f'font-size="{HEADER_FONT}" font-weight="700" fill="{HOST_COLOR}">parth@sinhaparth5</text>'
    )
    y += INFO_LINE_H + 2
    info_lines.append(
        f'<text x="{INFO_X}" y="{y:.2f}" font-family="Ubuntu Mono, monospace" '
        f'font-size="{INFO_FONT}" fill="{DIM_COLOR}">' + ("─" * 30) + "</text>"
    )
    y += INFO_LINE_H + 4

    for label, value in fields:
        label_txt = esc((label + ":").ljust(LABEL_WIDTH_CH))
        value_esc = esc(value)
        value_x = INFO_X + LABEL_WIDTH_CH * INFO_CHAR_W
        info_lines.append(
            f'<text x="{INFO_X}" y="{y:.2f}" font-family="Ubuntu Mono, monospace" '
            f'font-size="{INFO_FONT}" xml:space="preserve">'
            f'<tspan fill="{LABEL_COLOR}">{label_txt}</tspan>'
            f'<tspan x="{value_x:.2f}" fill="{VALUE_COLOR}">{value_esc}</tspan></text>'
        )
        y += INFO_LINE_H

    y += 10
    swatch_colors = ["#ff5f56", "#ffbd2e", "#27c93f", "#79c0ff", "#a371f7", "#f778ba", "#76b900", "#c9d1d9"]
    swatches = []
    sx = INFO_X
    for c in swatch_colors:
        swatches.append(f'<rect x="{sx}" y="{y - 11:.2f}" width="16" height="12" rx="2" fill="{c}"/>')
        sx += 22

    info_block = "\n      ".join(info_lines)
    swatch_block = "\n      ".join(swatches)

    canvas_w = 780
    canvas_h = int(y + 30)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}">
  <defs>
    <style>
{fontface_css}
    </style>
    <clipPath id="cardClip">
      <rect x="0.5" y="0.5" width="{canvas_w - 1}" height="{canvas_h - 1}" rx="12"/>
    </clipPath>
  </defs>
  <g clip-path="url(#cardClip)">
    <rect x="0.5" y="0.5" width="{canvas_w - 1}" height="{canvas_h - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
    <rect x="0" y="0" width="{canvas_w}" height="34" fill="#161b22"/>
    <circle cx="20" cy="17" r="6" fill="#ff5f56"/>
    <circle cx="40" cy="17" r="6" fill="#ffbd2e"/>
    <circle cx="60" cy="17" r="6" fill="#27c93f"/>
    <text x="{canvas_w / 2}" y="21.5" text-anchor="middle" font-family="Ubuntu Mono, monospace" font-size="12.5" fill="#8b949e">parth@sinhaparth5: ~</text>
    <line x1="0" y1="34" x2="{canvas_w}" y2="34" stroke="#30363d"/>
    {ascii_block}
    {info_block}
    {swatch_block}
  </g>
</svg>
'''

    with open(os.path.join(REPO_ROOT, "assets", "fastfetch.svg"), "w") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
