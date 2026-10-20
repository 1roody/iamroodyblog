#!/usr/bin/env python3
"""
Converte a imagem do doutor da peste em ASCII e gera plague.html.

uso:  python3 tools/plague_ascii.py <imagem.png> [colunas]

- O fundo cinzento é removido por flood-fill a partir das bordas.
- A luminância vira caracteres; 4 níveis de brilho -> classes CSS (l0..l3).
- As últimas linhas do corpo "digitalizam": caracteres viram 0/1.
- Fios de bits (<div class="drip">) saem da borda inferior do peito e
  caem em CSS puro (sem JS).
"""
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
DRIP_ROWS = 22      # linhas extra por baixo do corpo para os bits caírem
SEED = 7

ROOT = Path(__file__).resolve().parent.parent
random.seed(SEED)

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

# equalização por percentis, só dentro do corpo
lo, hi = np.percentile(lum[mask], [4, 99.5])
def level(v):
    return min(max((v - lo) / (hi - lo), 0), 1) ** 0.8

RAMP = " .:-=+*#%@"                 # do vazio ao denso
grid = []   # (char, classe)
for r in range(ROWS):
    row = []
    for c in range(COLS):
        if not mask[r, c]:
            row.append((" ", ""))
            continue
        t = level(lum[r, c])
        if edge[r, c]:
            t = max(t, 0.28)                       # contorno sempre visível
        if t < 0.06:
            ch, cls = "░", "l0"                     # vazio do capuz: só um fumo
        else:
            ch = RAMP[1 + int(t * (len(RAMP) - 2))]
            cls = "l1" if t < 0.3 else "l2" if t < 0.65 else "l3"
        if t > 0.88:
            cls += " hi"
        row.append((ch, cls))
    grid.append(row)

# ---------- borda inferior: onde o corpo é "cortado" ----------
bottom = {}
for c in range(COLS):
    rs = [r for r in range(ROWS) if mask[r, c]]
    if rs and max(rs) >= ROWS - 3:
        bottom[c] = max(rs)

# digitalização: as últimas linhas passam a bits, mais denso para baixo
FADE = 7
for c, rb in bottom.items():
    for r in range(max(rb - FADE, 0), rb + 1):
        if not mask[r, c]:
            continue
        p = ((r - (rb - FADE)) / FADE) ** 1.4 * 0.9
        if random.random() < p:
            ch, cls = grid[r][c]
            grid[r][c] = (random.choice("01"), "bit " + (cls.replace(" hi", "") or "l1"))

# ---------- HTML ----------
def line(row):
    out, cur, buf = [], None, []
    for ch, cls in row:
        if cls != cur:
            if buf:
                out.append((cur, "".join(buf)))
            cur, buf = cls, []
        buf.append(ch)
    out.append((cur, "".join(buf)))
    s = ""
    for cls, text in out:
        text = escape(text)
        s += f'<span class="{cls}">{text}</span>' if cls else text
    return s.rstrip()

art = "\n".join(line(r) for r in grid)

# fios de bits
cols = sorted(bottom)
streams = []
if cols:
    picks = random.sample(cols, k=min(len(cols), 46))
    for c in picks:
        rb = bottom[c]
        length = random.randint(5, 14)
        fall = random.randint(8, DRIP_ROWS)
        dur = random.uniform(3.2, 7.5)
        delay = -random.uniform(0, dur)
        bits = "".join(
            f'<i class="{random.choice("ab")}" style="--n:{n}"></i>'
            for n in range(length)
        )
        streams.append(
            f'<div class="drip" style="--x:{c};--y:{rb + 1};--len:{length};'
            f'--fall:{fall};--dur:{dur:.2f}s;--del:{delay:.2f}s">{bits}</div>'
        )
drips = "\n".join(streams)

html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>plague.exe :: experiência</title>
  <link rel="stylesheet" href="css/plague.css">
</head>
<body>
  <main class="stage">
    <figure class="plague" style="--cols:{COLS};--rows:{ROWS};--drip-rows:{DRIP_ROWS}" aria-label="Doutor da peste em ASCII, com bits a escorrer do peito">
<pre class="art" aria-hidden="true">
{art}
</pre>
<div class="drips" aria-hidden="true">
{drips}
</div>
    </figure>
    <p class="caption">&gt; plague.exe<span class="cursor">_</span></p>
  </main>
</body>
</html>
"""
(ROOT / "plague.html").write_text(html, encoding="utf-8")
print(f"ok: {COLS}x{ROWS} chars, {len(streams)} fios, plague.html")
