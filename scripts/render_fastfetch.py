#!/usr/bin/env python3
"""Build Andrew6rant-style light/dark profile cards for sinhaparth5."""
import html, json, os, urllib.request
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "sinhaparth5")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

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
    return {"repos":len(owned), "stars":sum(r["stargazers_count"] for r in owned), "followers":user["followers"], "gists":user["public_gists"]}

def ascii_portrait():
    image = Image.open(ROOT/"assets"/"portrait.png").convert("L")
    image = ImageEnhance.Contrast(ImageOps.autocontrast(image)).enhance(1.35)
    image = ImageOps.fit(image, (26, 25))
    chars = "@%#*+=-:. "
    return ["".join(chars[image.getpixel((x,y))*(len(chars)-1)//255] for x in range(26)) for y in range(25)]

def render(theme, data):
    dark = theme == "dark"
    bg,text = (("#161b22","#c9d1d9") if dark else ("#f6f8fa","#24292f"))
    key,value,dim = (("#ffa657","#a5d6ff","#616e7f") if dark else ("#953800","#0550ae","#6e7781"))
    green,red = (("#3fb950","#f85149") if dark else ("#1a7f37","#cf222e"))
    portrait = "\n".join(f'<tspan x="15" y="{30+i*20}">{html.escape(line)}</tspan>' for i,line in enumerate(ascii_portrait()))
    def row(y, label, val, width=57):
        val = str(val)
        return f'<tspan x="390" y="{y}" fill="{dim}">. </tspan><tspan x="410" y="{y}" fill="{key}">{html.escape(label)}:</tspan><tspan x="625" y="{y}" fill="{dim}">...</tspan><tspan x="650" y="{y}" fill="{value}">{html.escape(val)}</tspan>'
    chunks = [
        '<tspan x="390" y="30">parth@sinhaparth5</tspan> -——————————————————————————————-—-',
        row(50,"OS","Linux"), row(70,"Location","United Kingdom"),
        row(90,"Host","GPU Architecture Student"), row(110,"Kernel","CUDA / Parallel Computing"),
        row(130,"IDE","VS Code, Neovim"), '<tspan x="390" y="150" fill="'+dim+'">. </tspan>',
        row(170,"Languages.Programming","C++, C, Rust, Python"),
        row(190,"Languages.Web","TypeScript, JavaScript, React"),
        row(210,"Languages.Real","English"), '<tspan x="390" y="230" fill="'+dim+'">. </tspan>',
        row(250,"Hobbies.Software","GPU kernels, systems programming"),
        row(270,"Hobbies.Hardware","GPU architecture, performance"),
        '<tspan x="390" y="310">- Contact</tspan> -——————————————————————————————————————————————-—-',
        row(330,"Email.Personal","sinhaparth555@gmail.com"), row(350,"Website","parthsinha.com"),
        row(370,"LinkedIn","parth-sinha18"), row(390,"X","@parth_sinha18"),
        '<tspan x="390" y="430">- GitHub Stats</tspan> -—————————————————————————————————————————-—-',
        row(450,"Repos",data["repos"]), row(470,"Stars",data["stars"]),
        row(490,"Followers",data["followers"]),
        f'<tspan x="390" y="510" fill="{dim}">. </tspan><tspan x="410" y="510" fill="{key}">Current mode:</tspan><tspan x="590" y="510" fill="{dim}">............</tspan><tspan x="650" y="510" fill="{green}">CUDA++</tspan><tspan x="730" y="510" fill="{red}">latency--</tspan>'
    ]
    svg=f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px" role="img" aria-labelledby="title desc">
<title id="title">Parth Sinha GitHub profile</title><desc id="desc">Terminal-style profile with ASCII portrait, technical focus, contact links, and public GitHub statistics.</desc>
<style>@font-face{{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';font-display:swap;-webkit-size-adjust:109%;size-adjust:109%}}text,tspan{{white-space:pre}}</style>
<rect width="985px" height="530px" fill="{bg}" rx="15"/>
<text x="15" y="30" fill="{text}">{portrait}</text>
<text x="390" y="30" fill="{text}">{chr(10).join(chunks)}</text>
</svg>'''
    (ROOT/f"{theme}_mode.svg").write_text(svg)

if __name__ == "__main__":
    try: data=stats()
    except Exception as exc: print(f"GitHub API unavailable ({exc}); using snapshot"); data={"repos":38,"stars":0,"followers":47,"gists":3}
    render("dark",data); render("light",data); print("Updated dark_mode.svg and light_mode.svg")
