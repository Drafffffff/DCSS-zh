#!/usr/bin/env python3
"""Build an OFL-compatible, renamed pixel font with missing display glyphs."""
from pathlib import Path
import json
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
ROOT = Path(__file__).resolve().parents[1]
base = TTFont(ROOT/'fonts/fusion-pixel-12px-monospaced-zh_hans.ttf')
fallback = TTFont(ROOT/'fonts/NotoSansSC-Regular.ttf')
text = (ROOT/'native/crawl-ref/source/zh-catalog.inc').read_text()
for kind in ('database', 'descript'):
    for path in (ROOT/f'native/crawl-ref/source/dat/{kind}/zh').glob('*.txt'):
        text += path.read_text()
for path in (ROOT/'native/crawl-ref/docs/zh').glob('*.txt'):
    text += path.read_text()
for name in ('zh-message-catalog.inc', 'zh-display-lexicon.inc'):
    path = ROOT/'native/crawl-ref/source'/name
    if path.exists(): text += path.read_text()
cmap = base.getBestCmap()
missing = sorted({ord(c) for c in text if not c.isspace() and ord(c)>127 and ord(c) not in cmap})
source = fallback.getGlyphSet()
order = list(base.getGlyphOrder())
scale = base['head'].unitsPerEm/fallback['head'].unitsPerEm
for cp in missing:
    original = fallback.getBestCmap().get(cp)
    if original is None:
        raise ValueError(f'No fallback glyph for U+{cp:04X}')
    name = f'dcssFallback{cp:05X}'
    pen = TTGlyphPen(None)
    source[original].draw(TransformPen(pen, (scale,0,0,scale,0,-60)))
    glyph = pen.glyph()
    base['glyf'][name] = glyph
    base['hmtx'][name] = (1200, 0)
    if 'vmtx' in base: base['vmtx'][name] = (1200, 0)
    order.append(name)
    for table in base['cmap'].tables:
        if table.isUnicode() and (cp<65536 or table.format in (12,13)):
            table.cmap[cp] = name
# DCSS treats East Asian Ambiguous punctuation as one terminal cell. Fusion's
# zh-Hans curly quotes occupy two cells; their right-hand ink overlaps the next
# glyph in TextRegion. Keep the original integer-grid outlines, translate only,
# and give these four characters the same advance as ASCII.
quote_adjustments = {0x2018: -700, 0x2019: 0, 0x201C: -500, 0x201D: 0}
quote_metrics = {}
for cp, dx in quote_adjustments.items():
    original = base.getBestCmap()[cp]
    name = f'dcssNarrowQuote{cp:04X}'
    pen = TTGlyphPen(base.getGlyphSet())
    base.getGlyphSet()[original].draw(TransformPen(pen, (1, 0, 0, 1, dx, 0)))
    glyph = pen.glyph()
    base['glyf'][name] = glyph
    glyph.recalcBounds(base['glyf'])
    base['hmtx'][name] = (600, glyph.xMin)
    if 'vmtx' in base:
        base['vmtx'][name] = base['vmtx'][original]
    order.append(name)
    for table in base['cmap'].tables:
        if table.isUnicode():
            table.cmap[cp] = name
    quote_metrics[chr(cp)] = {'advance': 600, 'bounds': [glyph.xMin, glyph.xMax]}
base.setGlyphOrder(order)
# Both upstream font licenses reserve names; this modified font has its own name.
values={1:'DCSS Pixel SC',2:'Regular',3:'DCSS Pixel SC 1.0',4:'DCSS Pixel SC',6:'DCSSPixelSC-Regular',16:'DCSS Pixel SC',17:'Regular'}
for record in base['name'].names:
    if record.nameID in values:
        record.string=values[record.nameID].encode(record.getEncoding(),errors='replace')
base.save(ROOT/'fonts/DCSSPixelSC-Regular.ttf')
report={'font':'DCSSPixelSC-Regular.ttf','base':'Fusion Pixel 12px monospaced zh-Hans 2026.09.25','fallback':'Noto Sans SC Regular','fallback_characters':[chr(cp) for cp in missing],'missing_visible_characters':[], 'single_cell_quote_metrics':quote_metrics,'base_pixel_size':12,'recommended_pixel_sizes':[24,36,48]}
(ROOT/'verification/native/pixel-font-composite.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
