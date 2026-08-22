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
    image = ImageOps.fit(image, (38, 25))
    chars = " .:-=+*#%@"
    return ["".join(chars[image.getpixel((x,y))*(len(chars)-1)//255] for x in range(38)).rstrip() for y in range(25)]

def render(theme, data):
    dark = theme == "dark"
    bg,text = (("#161b22","#c9d1d9") if dark else ("#f6f8fa","#24292f"))
    key,value,dim = (("#ffa657","#a5d6ff","#616e7f") if dark else ("#953800","#0550ae","#6e7781"))
    green,red = (("#3fb950","#f85149") if dark else ("#1a7f37","#cf222e"))
    portrait = "".join(f'<tspan x="15" y="{30+i*20}">{html.escape(line)}</tspan>' for i,line in enumerate(ascii_portrait()))
    fields = [("OS","Linux"),("Location","United Kingdom"),("Role","GPU Architecture Student"),("Focus","CUDA, Parallel Computing"),("Editor","VS Code, Neovim"),None,("Languages.Programming","C++, C, Rust, Python, TypeScript"),("Languages.Web","JavaScript, React, Next.js, Node.js"),("Interests.Systems","GPU Kernels, Memory, Performance"),("Background","Web Architecture, Full-Stack Dev"),None,("Email","sinhaparth555@gmail.com"),("Website","parthsinha.com"),("LinkedIn","parth-sinha18"),("X","@parth_sinha18")]
    chunks = ['<tspan x="390" y="30">parth@sinhaparth5</tspan> -——————————————————————————————-—-']; y=50
    for item in fields:
        if item is None: y += 20; continue
        label,val=item; dots="."*max(2,35-len(label)-len(val)//2)
        chunks.append(f'<tspan x="390" y="{y}" fill="{dim}">. </tspan><tspan x="410" y="{y}" fill="{key}">{html.escape(label)}:</tspan><tspan x="600" y="{y}" fill="{dim}">{dots}</tspan><tspan x="650" y="{y}" fill="{value}">{html.escape(val)}</tspan>'); y+=20
    chunks += [f'<tspan x="390" y="450">- GitHub Stats -————————————————————————————-—-</tspan>',f'<tspan x="390" y="470" fill="{key}">Repos</tspan><tspan x="450" y="470" fill="{value}">{data["repos"]}</tspan><tspan x="500" y="470" fill="{key}">Stars</tspan><tspan x="560" y="470" fill="{value}">{data["stars"]}</tspan><tspan x="610" y="470" fill="{key}">Public Gists</tspan><tspan x="730" y="470" fill="{value}">{data["gists"]}</tspan>',f'<tspan x="390" y="490" fill="{key}">Followers</tspan><tspan x="490" y="490" fill="{value}">{data["followers"]}</tspan><tspan x="550" y="490" fill="{key}">Available for work</tspan><tspan x="730" y="490" fill="{green}">true</tspan>',f'<tspan x="390" y="510" fill="{key}">Current mode</tspan><tspan x="520" y="510" fill="{value}">learning</tspan><tspan x="610" y="510" fill="{green}">CUDA++</tspan><tspan x="700" y="510" fill="{red}">latency--</tspan>']
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" font-family="Consolas,Ubuntu Mono,monospace" width="985" height="530" font-size="16"><style>text,tspan{{white-space:pre}}</style><rect width="985" height="530" fill="{bg}" rx="15"/><text fill="{text}">{portrait}</text><text x="390" y="30" fill="{text}">{''.join(chunks)}</text></svg>'''
    (ROOT/f"{theme}_mode.svg").write_text(svg)

if __name__ == "__main__":
    try: data=stats()
    except Exception as exc: print(f"GitHub API unavailable ({exc}); using snapshot"); data={"repos":38,"stars":0,"followers":47,"gists":3}
    render("dark",data); render("light",data); print("Updated dark_mode.svg and light_mode.svg")
