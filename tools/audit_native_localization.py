#!/usr/bin/env python3
"""Auditable data-key coverage and residual-English evidence, not a gameplay %.

Paths, parser tokens, copyright holder names and key names intentionally remain
canonical. Keep unexpected traces for inspection rather than declaring success
from a CJK-character count.
"""
import argparse,json,re
from pathlib import Path
from native_catalog import ROOT,SRC,LOC
from dcss_parse import parse
p=argparse.ArgumentParser();p.add_argument('--player-name',action='append',default=[]);p.add_argument('traces',nargs='*');p.add_argument('--out',default=str(ROOT/'verification/native/localization-audit.json'));a=p.parse_args()
files={};missing=[];unchanged=[]
for kind in ('database','descript'):
    for f in sorted(SRC.joinpath('dat',kind).glob('*.txt')):
        en=parse(f);zh=parse(f.parent/'zh'/f.name);gaps=sorted(en.keys()-zh.keys())
        files[f'{kind}/{f.name}']={'keys':len(en),'localized_keys':len(en)-len(gaps)}
        missing += [f'{kind}/{f.name}#{k}' for k in gaps]
        for key,body in en.items():
            if body!=zh.get(key):continue
            text=re.sub(r'@[^@]+@|\[\[.*?\]\]|<[^>]+>','',body)
            text=re.sub(r'^\s*(?:#.*|[wW]:.*|__NONE)\s*$','',text,flags=re.M)
            if re.search('[A-Za-z]{3}',text):unchanged.append(f'{kind}/{f.name}#{key}')
allowed=set('Up Down Left Right Tab Esc PgDn PgUp Ctrl Shift Alt Del Numlock Home End Enter Return Insert Delete Backspace Space Spacebar Numpad numpad DCSS HP MP AC EV SH XL STR INT DEX XXX'.split())
residual={};records=0
for filename in a.traces:
    for line in Path(filename).read_text().splitlines():
        e=json.loads(line)
        if 'rendered' not in e:continue
        records+=1
        text=re.sub(r'</?[a-z][a-z0-9_: -]*>','',e['rendered'])
        lines=[]
        for part in text.splitlines():
            if re.search(r'Copyright|版权所有|search prefixes|colouring prefixes|搜索前缀|储藏检索前缀|颜色前缀|着色前缀',part):continue
            part=re.sub(r'https?://[^\s<>]+|(?:/|~/)[^\s<>"\']+(?:/|\.)[^\s<>"\']*','',part)
            part=re.sub(r'ZH_[A-Z_]+|ZhSmoke','',part)
            lines.append(part)
        words=sorted({w for w in re.findall('[A-Za-z]{3,}', '\n'.join(lines)) if w not in allowed and w not in a.player_name})
        if words:residual[e['en']]={'en':e['en'],'rendered':e['rendered'],'words':words}
report={'data_keys':sum(v['keys'] for v in files.values()),'localized_data_keys':sum(v['localized_keys'] for v in files.values()),'missing_data_keys':missing,'unchanged_prose_bodies':unchanged,'files':files,'catalog':json.loads(LOC.joinpath('coverage.json').read_text()),'trace_records':records,'unclassified_english_records':len(residual),'residual_english':list(residual.values()),'preserved_player_names':a.player_name,'scope':'Data-key coverage is exhaustive for dat/database and dat/descript. Traces cover only the exercised UI paths; they are not a percentage of every game state.'}
Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('files','catalog','residual_english')},ensure_ascii=False))
assert not missing and not unchanged
