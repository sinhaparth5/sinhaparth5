#!/usr/bin/env python3
"""Build Andrew6rant-style light/dark profile cards for sinhaparth5."""
import html, json, os, urllib.request
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "sinhaparth5")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
MARKUP = {"HTML", "CSS", "SCSS", "TeX", "Jupyter Notebook", "Dockerfile", "Makefile", "CMake"}
# Portrait box: x 15..370, y 30..510. Monospace glyphs are ~0.6em wide, so sample
# the photo at the box's real pixel aspect, not a square grid, or it renders squeezed.
P_FONT, P_LINE, P_WIDTH = 8, 10, 355
P_COLS, P_ROWS = int(P_WIDTH / (P_FONT * 0.6)), 49
EDGE = 40  # share of a cell (0-255) covered by outline before it draws as @; lower = more lines
AVATAR = ROOT/"assets"/"avatar.jpg"
WIDTH = 1025  # room for "C++ 35% Python 19% TypeScript 17% Go 10%" at the value column

def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept":"application/vnd.github+json","User-Agent":"profile-readme-card"})
    if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as response: return json.loads(response.read())

def stats():
    user, repos, page = api(f"/users/{USERNAME}"), [], 1
    while True:
        chunk = api(f"/users/{USERNAME}/repos?type=owner&per_page=100&page={page}"); repos += chunk
        if len(chunk) < 100: break
        page += 1
    owned = [r for r in repos if not r["fork"]]
    langs = {}
    for r in owned:
        for lang, size in api(f"/repos/{USERNAME}/{r['name']}/languages").items():
            if lang not in MARKUP: langs[lang] = langs.get(lang, 0) + size
    total = sum(langs.values()) or 1
    top = [(lang, round(100*langs[lang]/total)) for lang in sorted(langs, key=langs.get, reverse=True)[:4]]
    return {"repos":len(owned), "stars":sum(r["stargazers_count"] for r in owned), "followers":user["followers"], "gists":user["public_gists"], "languages":top}

def ascii_portrait(dark):
    try:  # live GitHub avatar, cached so offline runs still render
        req = urllib.request.Request(api(f"/users/{USERNAME}")["avatar_url"] + "&s=460", headers={"User-Agent":"profile-readme-card"})
        AVATAR.write_bytes(urllib.request.urlopen(req, timeout=30).read())
    except Exception as exc: print(f"Avatar fetch failed ({exc}); using cached {AVATAR.name}")
    # Pad (not crop) the square avatar into the tall panel; cells are ~2x taller than wide.
    src = Image.open(AVATAR).convert("RGB")
    bg = src.getpixel((2, 2))
    big = ImageOps.pad(src, (P_COLS*6, P_ROWS*12), color=bg)  # 6x detail per cell for edge finding
    rgb = big.resize((P_COLS, P_ROWS), Image.BOX)
    grey = rgb.convert("L")
    # cartoon outlines (snout, eyes, ears, tail): edges found at full detail, kept if they touch the cell at all
    # FIND_EDGES flags the image border, so pad with backdrop first and crop it back off
    # per colour channel, since pink-on-blue is nearly flat in grey
    r, g, b = (ch.filter(ImageFilter.FIND_EDGES) for ch in ImageOps.expand(big, 2, fill=bg).split())
    edges = ImageChops.lighter(ImageChops.lighter(r, g), b).crop((2, 2, big.width+2, big.height+2))
    edges = edges.point(lambda v: 255 if v > 30 else 0).resize((P_COLS, P_ROWS), Image.BOX)  # share of each cell that is line
    # the flat backdrop (corner colour) stays blank; contrast is stretched over the subject only
    subject = {(x, y) for y in range(P_ROWS) for x in range(P_COLS) if sum((c-b)**2 for c,b in zip(rgb.getpixel((x, y)), bg)) >= 70**2}
    vals = sorted(grey.getpixel(xy) for xy in subject) or [0, 255]
    lo, hi = vals[len(vals)//50], vals[-len(vals)//50 - 1]
    fill = ".:-=+" if dark else "+=-:."  # fills stay light so outlines stand out; dark theme: bright = denser
    def glyph(x, y):
        if edges.getpixel((x, y)) > EDGE: return "@"
        if (x, y) not in subject: return " "
        v = grey.getpixel((x, y))
        return fill[max(0, min(len(fill)-1, (v-lo)*len(fill)//max(1, hi-lo+1)))]
    return ["".join(glyph(x, y) for x in range(P_COLS)) for y in range(P_ROWS)]

def render(theme, data):
    dark = theme == "dark"
    bg,text = (("#161b22","#c9d1d9") if dark else ("#f6f8fa","#24292f"))
    key,value,dim = (("#ffa657","#a5d6ff","#616e7f") if dark else ("#953800","#0550ae","#6e7781"))
    green,red = (("#3fb950","#f85149") if dark else ("#1a7f37","#cf222e"))
    # textLength pins each line to the box width whatever monospace font the viewer has
    portrait = "\n".join(f'<text x="15" y="{30+i*P_LINE}" textLength="{P_WIDTH}" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text>' for i,line in enumerate(ascii_portrait(dark)))
    def row(y, label, val, width=57):
        val = str(val)
        return f'<tspan x="390" y="{y}" fill="{dim}">. </tspan><tspan x="410" y="{y}" fill="{key}">{html.escape(label)}:</tspan><tspan x="585" y="{y}" fill="{dim}">...</tspan><tspan x="615" y="{y}" fill="{value}">{html.escape(val)}</tspan>'
    chunks = [
        '<tspan x="390" y="30">parth@sinhaparth5</tspan> -——————————————————————————————————-—-',
        row(50,"OS","Linux"), row(70,"Location","United Kingdom"),
        row(90,"Host","GPU Architecture Student"), row(110,"Kernel","CUDA / Parallel Computing"),
        row(130,"IDE","VS Code, Neovim"), '<tspan x="390" y="150" fill="'+dim+'">. </tspan>',
        row(170,"Languages.Top","") + "".join(f'<tspan fill="{value}">{html.escape(l)} </tspan><tspan fill="{dim}">{pct}% </tspan>' for l,pct in data["languages"]),
        row(190,"Languages.Web","Astro, React"),
        row(210,"Languages.Real","English"), '<tspan x="390" y="230" fill="'+dim+'">. </tspan>',
        row(250,"Hobbies.Software","GPU kernels, systems programming"),
        row(270,"Hobbies.Hardware","GPU architecture, performance"),
        '<tspan x="390" y="310">- Contact</tspan> -——————————————————————————————————————————————————-—-',
        row(330,"Email.Personal","sinhaparth555@gmail.com"), row(350,"Website","parthsinha.com"),
        row(370,"LinkedIn","parth-sinha18"), row(390,"X","@parth_sinha18"),
        '<tspan x="390" y="430">- GitHub Stats</tspan> -—————————————————————————————————————————————-—-',
        row(450,"Repos",data["repos"]), row(470,"Stars",data["stars"]),
        row(490,"Followers",data["followers"]),
        f'<tspan x="390" y="510" fill="{dim}">. </tspan><tspan x="410" y="510" fill="{key}">Current mode:</tspan><tspan x="585" y="510" fill="{dim}">...</tspan><tspan x="615" y="510" fill="{green}">CUDA++</tspan><tspan x="695" y="510" fill="{red}">latency--</tspan>'
    ]
    svg=f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="{WIDTH}px" height="530px" font-size="16px" role="img" aria-labelledby="title desc">
<title id="title">Parth Sinha GitHub profile</title><desc id="desc">Terminal-style profile with ASCII portrait, technical focus, contact links, and public GitHub statistics.</desc>
<style>@font-face{{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';font-display:swap;-webkit-size-adjust:109%;size-adjust:109%}}text,tspan{{white-space:pre}}</style>
<rect width="{WIDTH}px" height="530px" fill="{bg}" rx="15"/>
<g fill="{text}" font-size="{P_FONT}px">{portrait}</g>
<text x="390" y="30" fill="{text}">{chr(10).join(chunks)}</text>
</svg>'''
    (ROOT/f"{theme}_mode.svg").write_text(svg)

if __name__ == "__main__":
    try: data=stats()
    except Exception as exc: print(f"GitHub API unavailable ({exc}); using snapshot"); data={"repos":38,"stars":0,"followers":47,"gists":3,"languages":[("C++",35),("Python",19),("TypeScript",17),("Go",10)]}
    render("dark",data); render("light",data); print("Updated dark_mode.svg and light_mode.svg")
