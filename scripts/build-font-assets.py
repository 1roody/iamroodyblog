"""Rebuild static font assets; no build step is needed to serve the site.

Requires: pip install fonttools brotli
Usage: python scripts/build-font-assets.py /path/to/DejaVuSansMono.ttf
The editable ASCII artwork remains in img/plague-v2.svg.
"""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("font", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
font = TTFont(args.font)
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
units = font["head"].unitsPerEm
ns = {"svg": "http://www.w3.org/2000/svg"}
source = ET.parse(root / "img/plague-v2.svg").getroot()
rows = source.findall("svg:text", ns)
characters = sorted(set("".join("".join(row.itertext()) for row in rows)) - {" "})


def number(value):
    return f"{value:.8f}".rstrip("0").rstrip(".") or "0"


parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 100">',
    '<title>Doutor da peste em ASCII</title>',
    '<!-- Outlined from plague-v2.svg using DejaVu Sans Mono. See fonts/LICENSE-DejaVu.txt. -->',
    '<style>' + source.find("svg:style", ns).text.split("}", 1)[1] + '</style>',
    '<defs>',
]
for character in characters:
    pen = SVGPathPen(glyphs, ntos=number)
    glyphs[cmap[ord(character)]].draw(TransformPen(pen, (1 / units, 0, 0, -1 / units, 0, 0)))
    parts.append(f'<path id="g{ord(character)}" d="{pen.getCommands()}"/>')
parts.append('</defs>')

for row in rows:
    x = float(row.get("x", 0))
    parts.append(f'<g transform="translate(0 {row.get("y")})" fill="#777">')
    runs = [(row.text or "", None)]
    for span in row:
        runs.extend(((span.text or "", span.get("class")), (span.tail or "", None)))
    for content, css_class in runs:
        if css_class:
            parts.append(f'<g class="{css_class}">')
        for character in content:
            glyph_name = cmap[ord(character)]
            if character != " ":
                parts.append(f'<use href="#g{ord(character)}" x="{number(x)}"/>')
            x += font["hmtx"][glyph_name][0] / units
        if css_class:
            parts.append('</g>')
    parts.append('</g>')
parts.append('</svg>')
(root / "img/plague-outlined.svg").write_text("\n".join(parts) + "\n")

options = subset.Options()
options.flavor = "woff2"
subsetter = subset.Subsetter(options=options)
subsetter.populate(unicodes=set(range(0x20, 0x250)) | set(range(0x2000, 0x2070)))
subsetter.subset(font)
font.flavor = "woff2"
(root / "fonts").mkdir(exist_ok=True)
font.save(root / "fonts/dejavu-sans-mono-latin.woff2")
