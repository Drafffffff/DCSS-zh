#!/usr/bin/env python3
"""Check shipped quote outlines against the terminal's one-cell layout."""
from pathlib import Path
from fontTools.ttLib import TTFont

root = Path(__file__).resolve().parents[1]
font = TTFont(root / 'fonts/DCSSPixelSC-Regular.ttf')
cmap = font.getBestCmap()
cell = font['hmtx'][cmap[ord('a')]][0]
for char in '‘’“”':
    name = cmap[ord(char)]
    glyph = font['glyf'][name]
    advance, bearing = font['hmtx'][name]
    assert advance == cell, (char, advance, cell)
    assert 0 <= glyph.xMin < glyph.xMax <= cell, (char, glyph.xMin, glyph.xMax)
    assert bearing == glyph.xMin
    coords, _, _ = glyph.getCoordinates(font['glyf'])
    assert all(x % 100 == 0 and y % 100 == 0 for x, y in coords), char
    for size in (24, 36, 48):
        scale = size / font['head'].unitsPerEm
        assert all((x * scale).is_integer() and (y * scale).is_integer()
                   for x, y in coords), (char, size)
print('PASS: four shipped curly quotes fit one cell on the pixel grid at 24/36/48 px')
