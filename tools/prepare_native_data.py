#!/usr/bin/env python3
"""Merge existing data translations into a separate native build, idempotently."""
from pathlib import Path
from dcss_parse import keyed_entries
ROOT=Path(__file__).resolve().parents[1]
DAT=ROOT/'native/crawl-ref/source/dat'
n=0
for kind in ('database','descript'):
    for f in sorted((ROOT/'translations/zh'/kind).glob('*.txt')):
        stem=f.name.split('.part')[0]
        name=stem if stem.endswith('.txt') else stem+'.txt'
        target=DAT/kind/'zh'/name
        existing={k for k,b in keyed_entries(target.read_text())} if target.exists() else set()
        additions=[]
        for k,b in keyed_entries(f.read_text()):
            if k not in existing:
                additions.append(f'%%%%\n{k}\n\n{b}\n%%%%\n');existing.add(k);n+=1
        if additions:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('a') as out: out.write('\n'+''.join(additions))
print('Merged data entries:',n)
