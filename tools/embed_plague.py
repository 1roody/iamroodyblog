#!/usr/bin/env python3
"""
cola o doutor da peste do plague-v2.html no index.html.

uso:  python3 tools/embed_plague.py

o plague_ascii_v2.py gera a página inteira; daqui só se tira a figura e as
cinzas, e vão para o index entre os marcadores:
  <!-- plague:figura ... -->        <!-- /plague:figura -->
  <!-- plague:cinzas-fundo -->      <!-- /plague:cinzas-fundo -->
  <!-- plague:cinzas-frente -->     <!-- /plague:cinzas-frente -->

no index o <figure> é o invólucro (com a <figcaption> do site), por isso a
<figure class="plague"> do v2 passa a <div class="plague" role="img">.
correr outra vez sempre que se regenerar o plague-v2.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "plague-v2.html"
DST = ROOT / "index.html"

src = SRC.read_text(encoding="utf-8")
dst = DST.read_text(encoding="utf-8")


def grab(pattern):
    m = re.search(pattern, src, re.S)
    if not m:
        sys.exit("embed_plague: não encontrei %r em %s" % (pattern, SRC.name))
    return m


fig = grab(r'<figure class="plague" style="([^"]*)" aria-label="([^"]*)">\n?(.*?)\s*</figure>')
figura = '<div class="plague" style="%s" role="img" aria-label="%s">\n%s\n</div>' % fig.groups()
fundo = grab(r'<div class="ash back">(.*?)</div>').group(1)
frente = grab(r'<div class="ash front"[^>]*>(.*?)</div>').group(1)


def put(html, name, body):
    pat = re.compile(r"(<!-- plague:%s\b[^>]*-->).*?(<!-- /plague:%s -->)" % (name, name), re.S)
    if not pat.search(html):
        sys.exit("embed_plague: faltam os marcadores plague:%s em %s" % (name, DST.name))
    return pat.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(2), html, count=1)


dst = put(dst, "figura", figura)
dst = put(dst, "cinzas-fundo", fundo)
dst = put(dst, "cinzas-frente", frente)
DST.write_text(dst, encoding="utf-8")
print("ok: %s (%d KB)" % (DST.name, len(dst.encode("utf-8")) // 1024))
