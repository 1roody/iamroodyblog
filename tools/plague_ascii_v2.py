#!/usr/bin/env python3
"""
v2 do doutor da peste: só cinzentos, escuridão, o corpo inteiro a derreter
em bits pela borda de baixo e um fundo cheio de detalhe.

uso:  python3 tools/plague_ascii_v2.py <imagem.png> [colunas]

gera:
  plague-v2.html            (a página, com o ASCII embutido)
  img/plague-v2-hex.svg     (o tile de hexdump microscópico do fundo)

Tudo anima em CSS puro (sem JS). Só se animam transform/opacity, para o
compositor aguentar centenas de fios de bits.
"""
import math
import random
import sys
from collections import deque
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path(sys.argv[1])
COLS = int(sys.argv[2]) if len(sys.argv) > 2 else 150
LH = 1.0            # line-height em "em"
CW = 0.6            # largura de um caracter em "em" (fontes monospace)
DRIP_ROWS = 24      # linhas extra por baixo do corpo para os bits caírem
SEED = 13

ROOT = Path(__file__).resolve().parent.parent
random.seed(SEED)
np.random.seed(SEED)

# ---------- imagem + máscara do corpo ----------
img = Image.open(SRC).convert("L")
a = np.array(img).astype(np.int16)
H, W = a.shape

bg = int(np.median(np.concatenate([a[0, :], a[:, 0], a[:, -1]])))
near_bg = np.abs(a - bg) <= 14
outside = np.zeros_like(near_bg)
q = deque()
for x in range(W):
    for y in (0, H - 1):
        if near_bg[y, x] and not outside[y, x]:
            outside[y, x] = True; q.append((y, x))
for y in range(H):
    for x in (0, W - 1):
        if near_bg[y, x] and not outside[y, x]:
            outside[y, x] = True; q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and near_bg[ny, nx] and not outside[ny, nx]:
            outside[ny, nx] = True; q.append((ny, nx))
body = ~outside

# recorta à caixa do corpo
ys, xs = np.where(body)
pad = 6
y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, H - 1)
x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, W - 1)
a = a[y0:y1 + 1, x0:x1 + 1]
body = body[y0:y1 + 1, x0:x1 + 1]
H, W = a.shape

# ---------- amostragem para a grelha ----------
ROWS = round(COLS * CW * (H / W) / LH)
ys_edges = np.linspace(0, H, ROWS + 1).astype(int)
xs_edges = np.linspace(0, W, COLS + 1).astype(int)
lum = np.zeros((ROWS, COLS))
cov = np.zeros((ROWS, COLS))
for r in range(ROWS):
    for c in range(COLS):
        blk = a[ys_edges[r]:ys_edges[r + 1], xs_edges[c]:xs_edges[c + 1]]
        bm = body[ys_edges[r]:ys_edges[r + 1], xs_edges[c]:xs_edges[c + 1]]
        cov[r, c] = bm.mean()
        if bm.any():
            px = blk[bm]
            lum[r, c] = 0.5 * px.mean() + 0.5 * np.percentile(px, 85)
mask = cov > 0.5

# fronteira da silhueta (o fundo da imagem conta como "dentro": o corte
# inferior não é contorno)
pm = np.pad(mask, 1, constant_values=False)
pm[-1, 1:-1] = mask[-1, :]
edge = mask & ~(pm[:-2, 1:-1] & pm[2:, 1:-1] & pm[1:-1, :-2] & pm[1:-1, 2:])

lo, hi = np.percentile(lum[mask], [4, 99.5])
def level(v):
    return min(max((v - lo) / (hi - lo), 0), 1) ** 0.8

# ---------- óculos: os dois aglomerados mais claros da cabeça ----------
eyes = []
for side in (0, 1):
    pts = [
        (r, c) for r in range(int(ROWS * 0.45)) for c in range(COLS)
        if mask[r, c] and level(lum[r, c]) > 0.85
        and abs(c - COLS / 2) > 6 and (c >= COLS / 2) == bool(side)
    ]
    rr, cc = np.mean(pts, axis=0)
    eyes.append((rr, cc))
head_r = sum(e[0] for e in eyes) / 2
head_c = sum(e[1] for e in eyes) / 2

# ---------- luminância -> caracter (com luz a cair para a escuridão) ----------
RAMP = " .:-=+*#%@"
def light(r, c):
    # luz fraca na cara, o resto do corpo afunda no escuro
    dx = (c - head_c) * CW / (COLS * CW)
    dy = (r - (head_r + 6)) * LH / (COLS * CW)
    d = math.hypot(dx, dy * 1.15)
    return min(max(1.12 - 1.1 * d, 0.34), 1.0)

grid = []   # (texto, classe)
for r in range(ROWS):
    row = []
    for c in range(COLS):
        if not mask[r, c]:
            row.append((" ", ""))
            continue
        t = level(lum[r, c])
        bright = t > 0.86 and r < ROWS * 0.7       # óculos e bico ficam vivos
        if not bright:
            t *= light(r, c)
        if edge[r, c]:
            # contraluz: o contorno apanha a luz que vem de trás da cabeça
            rim = min(max(1.1 - r / ROWS * 0.9, 0.4), 1.0)
            ch = RAMP[2 + int(rim * 4)]
            row.append((ch, "rim" if rim > 0.55 else "l2"))
            continue
        if t < 0.07:
            ch, cls = "░", "l0"
        else:
            ch = RAMP[1 + int(min(t, 0.999) * (len(RAMP) - 2))]
            cls = "l1" if t < 0.3 else "l2" if t < 0.6 else "l3"
        if bright:
            cls = "l4"
        row.append((ch, cls))
    grid.append(row)

# ---------- borda de baixo: todo o contorno inferior derrete ----------
bottom = {}
for c in range(COLS):
    rs = np.where(mask[:, c])[0]
    if len(rs) and rs.max() >= ROWS * 0.5:
        bottom[c] = int(rs.max())

FADE = 9
FLICK = "\x00"      # marcador: bit que pisca (vira <i class="fl">)
for c, rb in bottom.items():
    for r in range(max(rb - FADE, 0), rb + 1):
        if not mask[r, c]:
            continue
        k = (r - (rb - FADE)) / FADE                # 0 em cima, 1 na borda
        if r >= rb - 1 and random.random() < 0.22 * k:
            grid[r][c] = (" ", "gap")               # buracos: já se foi
        elif random.random() < k ** 1.3 * 0.95:
            if random.random() < 0.28:
                grid[r][c] = (FLICK + random.choice("ab"), "bit")
            else:
                grid[r][c] = (random.choice("01"), "bit")

# ---------- HTML do desenho ----------
def cell_html(text):
    if text.startswith(FLICK):
        return f'<i class="fl {text[1]}" style="--d:{-random.uniform(0, 3):.2f}s"></i>'
    return escape(text)

def line(row):
    out, cur, buf = [], None, []
    for text, cls in row:
        if cls != cur:
            if buf:
                out.append((cur, "".join(buf)))
            cur, buf = cls, []
        buf.append(cell_html(text))
    out.append((cur, "".join(buf)))
    s = ""
    for cls, text in out:
        s += f'<span class="{cls}">{text}</span>' if cls else text
    return s.rstrip()

art = "\n".join(line(r) for r in grid)

# ---------- sombra: silhueta preta (dilatada) que tapa o fundo ----------
dil = mask.copy()
dil[1:, :] |= mask[:-1, :]
dil[:-1, :] |= mask[1:, :]
dil[:, 1:] |= mask[:, :-1]
dil[:, :-1] |= mask[:, 1:]
runs = []
for r in range(ROWS):
    c = 0
    while c < COLS:
        if dil[r, c]:
            s = c
            while c < COLS and dil[r, c]:
                c += 1
            runs.append(f"M{s} {r}h{c - s}v1h{s - c}z")
        c += 1
shade_d = "".join(runs)

# ---------- fios de bits ----------
def bitcol(n):
    # cada linha tem 3 variantes; o .s desliza entre elas para os bits trocarem
    lines = ["".join(random.choice("01") for _ in range(3)) for _ in range(n)]
    lines[-1] = f"<b>{lines[-1]}</b>"
    return "\n".join(lines)

floor = ROWS + DRIP_ROWS
streams = []
for c, rb in sorted(bottom.items()):
    # pingo: a borda estica e encolhe devagar, como cera a derreter
    if random.random() < 0.55:
        reach = random.randint(1, 4)
        length = reach + random.randint(1, 3)
        dur = random.uniform(4, 9)
        streams.append(
            f'<div class="drip ooze" style="--x:{c};--y:{rb + 1};--fall:{reach};'
            f'--dur:{dur:.2f}s;--del:{-random.uniform(0, dur):.2f}s">'
            f'<div class="f"><div class="s">{bitcol(length)}</div></div></div>'
        )
    # fios que caem: 1 a 3 por coluna
    for _ in range(random.choice((1, 1, 2, 2, 3))):
        length = random.choice((2, 3, 4, 6, 8, 10, 13, 16))
        fall = floor - (rb + 1) - random.randint(0, 6)
        dur = random.uniform(0.8, 1.3) * (1.4 + fall * 0.11)
        cls = "drip" + (" w" if random.random() < 0.18 else "") \
                     + (" still" if random.random() < 0.45 else "")
        streams.append(
            f'<div class="{cls}" style="--x:{c};--y:{rb + 1};--fall:{fall};'
            f'--dur:{dur:.2f}s;--del:{-random.uniform(0, dur * 1.6):.2f}s;'
            f'--fl:{random.uniform(0.35, 1.4):.2f}s">'
            f'<div class="f"><div class="s">{bitcol(length)}</div></div></div>'
        )
drips = "\n".join(streams)

# ---------- anéis atrás da cabeça ----------
def binary(msg):
    return " ".join(f"{ord(ch):08b}" for ch in msg)

R_TEXT = 67.5
ring_text = binary("MEMENTO MORI · BETA_SITE_ME · ")
ring_text = (ring_text + " ") * 3
circ = 2 * math.pi * R_TEXT
n_chars = int(circ / (2.4 * 0.6))      # font-size 2.4 no CSS
ring_text = ring_text[:n_chars]

def dash(r, n, on):
    # n traços iguais à volta do círculo, sem costura
    return f"{on} {2 * math.pi * r / n - on:.4f}"

labels = "".join(
    f'<text x="0" y="-97" transform="rotate({deg})" text-anchor="middle">'
    f'0x{int(deg / 360 * 255):02X}</text>'
    for deg in range(0, 360, 30)
)

rings = f"""<svg class="ring ring-a" viewBox="-100 -100 200 200" aria-hidden="true">
  <circle r="95" class="hair"/>
  <circle r="81.25" class="ticks" stroke-dasharray="{dash(81.25, 180, 0.3)}"/>
  <circle r="81.75" class="ticks-big" stroke-dasharray="{dash(81.75, 36, 0.7)}"/>
  <circle r="79" class="hair"/>
  <g class="lab">{labels}</g>
</svg>
<svg class="ring ring-b" viewBox="-100 -100 200 200" aria-hidden="true">
  <defs><path id="rp" d="M 0 -{R_TEXT} a {R_TEXT} {R_TEXT} 0 1 1 0 {2 * R_TEXT} a {R_TEXT} {R_TEXT} 0 1 1 0 -{2 * R_TEXT}"/></defs>
  <text class="bin"><textPath href="#rp" textLength="{circ:.2f}" lengthAdjust="spacingAndGlyphs">{ring_text}</textPath></text>
  <circle r="72" class="dash"/>
</svg>
<svg class="ring ring-c" viewBox="-100 -100 200 200" aria-hidden="true">
  <circle r="88" class="arc arc-1"/>
  <circle r="90.5" class="arc arc-2"/>
  <circle r="62" class="arc arc-3"/>
</svg>"""

# ---------- cinzas a flutuar ----------
def ash(n, front=False):
    out = []
    for _ in range(n):
        ch = random.choice("··..˙01" if not front else "·.01")
        size = random.uniform(5, 9) if not front else random.uniform(10, 16)
        out.append(
            f'<i style="--l:{random.uniform(0, 100):.1f}vw;--s:{size:.1f}px;'
            f'--o:{random.uniform(0.15, 0.55) if not front else random.uniform(0.1, 0.3):.2f};'
            f'--dx:{random.uniform(-12, 12):.1f}vw;--t:{random.uniform(18, 45):.1f}s;'
            f'--dl:{-random.uniform(0, 45):.1f}s">{ch}</i>'
        )
    return "".join(out)

# ---------- tile de hexdump microscópico ----------
HX_COLS, HX_ROWS, CWU, LHU = 96, 48, 6, 10
lines_svg = []
addr = random.randint(0x7f0000, 0x7fff00) & ~0xF
for r in range(HX_ROWS):
    parts = [f"{addr:08x}  "]
    addr += 24
    while sum(len(p) for p in parts) < HX_COLS - 2:
        byte = f"{random.randint(0, 255):02x} "
        if random.random() < 0.08:
            byte = f'<tspan class="h">{byte[:2]}</tspan> '
        parts.append(byte)
    raw = "".join(parts)
    visible = len(raw.replace('<tspan class="h">', "").replace("</tspan>", ""))
    raw += " " * (HX_COLS - visible)
    lines_svg.append(
        f'<text x="0" y="{r * LHU + 8}" textLength="{HX_COLS * CWU}" '
        f'lengthAdjust="spacingAndGlyphs" fill-opacity="{random.uniform(0.35, 0.8):.2f}">{raw}</text>'
    )
hex_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{HX_COLS * CWU}" height="{HX_ROWS * LHU}" viewBox="0 0 {HX_COLS * CWU} {HX_ROWS * LHU}">
<style>text{{font:8px "DejaVu Sans Mono","Fira Code",monospace;fill:#fff;white-space:pre}} .h{{fill-opacity:1;font-weight:bold}}</style>
{chr(10).join(lines_svg)}
</svg>
"""
(ROOT / "img").mkdir(exist_ok=True)
(ROOT / "img" / "plague-v2-hex.svg").write_text(hex_svg, encoding="utf-8")

# ---------- página ----------
eye_html = "".join(
    f'<span class="eye" style="--ex:{c + 0.5:.1f};--ey:{r + 0.5:.1f};--ed:{i * -1.7:.1f}s"></span>'
    for i, (r, c) in enumerate(eyes)
)

html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>plague.exe v2 :: experiência</title>
  <link rel="stylesheet" href="css/plague-v2.css">
</head>
<body>
  <div class="bg" aria-hidden="true">
    <div class="hex"></div>
    <div class="scan"><div class="hex"></div></div>
    <div class="fog back"></div>
    <div class="ash back">{ash(80)}</div>
  </div>

  <main class="stage">
    <figure class="plague" style="--cols:{COLS};--rows:{ROWS};--drip-rows:{DRIP_ROWS};--hx:{head_c + 0.5:.1f};--hy:{head_r:.1f}" aria-label="Doutor da peste em ASCII, a derreter em bits pela borda de baixo do corpo">
<div class="halo" aria-hidden="true"></div>
{rings}
<svg class="shade" viewBox="0 0 {COLS} {ROWS}" preserveAspectRatio="none" aria-hidden="true">
  <defs><filter id="soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.2 1.3"/></filter></defs>
  <path d="{shade_d}" filter="url(#soft)" opacity="0.9"/>
  <path d="{shade_d}"/>
</svg>
<pre class="art" aria-hidden="true">
{art}
</pre>
<div class="eyes" aria-hidden="true">{eye_html}</div>
<div class="drips" aria-hidden="true">
{drips}
</div>
<div class="tear" aria-hidden="true"></div>
    </figure>
  </main>

  <div class="fog front" aria-hidden="true"></div>
  <div class="ash front" aria-hidden="true">{ash(14, front=True)}</div>
  <div class="grain" aria-hidden="true"></div>
  <div class="vignette" aria-hidden="true"></div>

  <div class="hud" aria-hidden="true">
    <p class="tl">plague.exe <span class="dim">v2.0</span><br><span class="dim">proc 0x1347 ·</span> <span class="blink">a corromper</span></p>
    <p class="tr">mem 0x7f3a·0000 → 0x7f3a·ffff<br><span class="dim">integridade</span> <span class="integ"></span></p>
    <p class="bl"><span class="dim">bits perdidos</span> <span class="leak"></span></p>
    <p class="br">// memento mori<span class="cursor">_</span></p>
  </div>
</body>
</html>
"""
(ROOT / "plague-v2.html").write_text(html, encoding="utf-8")
print(f"ok: {COLS}x{ROWS} chars, {len(streams)} fios, {len(bottom)} colunas a derreter, "
      f"olhos em {[(round(r), round(c)) for r, c in eyes]}")
