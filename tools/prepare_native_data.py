#!/usr/bin/env python3
"""Merge existing data translations into a separate native build, idempotently."""
from pathlib import Path
import json
import re
from collections import Counter
from dcss_parse import keyed_entries
from native_catalog import review_files
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

# Reviewed prose overrides are source-checked so upstream edits cannot silently
# inherit a translation for an obsolete paragraph.
grouped = {}
for review in review_files():
    for entry in json.loads(review.read_text()).get('data_entries', []):
        source = dict(keyed_entries((DAT/entry['kind']/entry['file']).read_text()))
        body = '\n'.join(line for line in source[entry['key']].splitlines()
                         if not line.startswith('#')).strip()
        assert body == entry['en'].strip(), entry['key']
        for pattern in (r'</?[a-z][a-z0-9_ -]*>', r'\$cmd\[[^]]+\]'):
            assert Counter(re.findall(pattern, entry['en'])) == Counter(re.findall(pattern, entry['zh'])), entry['key']
        target = DAT/entry['kind']/'zh'/entry['file']
        grouped.setdefault(target, {})[entry['key']] = entry['zh']
if grouped:
    for target, overrides in grouped.items():
        text = target.read_text()
        assert set(overrides) <= {key for key, body in keyed_entries(text)}
        blocks = re.split(r'(^%{4,}[^\S\n]*$)', text, flags=re.M)
        for i in range(0, len(blocks), 2):
            entries = keyed_entries(blocks[i])
            if entries and entries[0][0] in overrides:
                key = entries[0][0]
                start = blocks[i].index(key)
                blocks[i] = blocks[i][:start]+key+'\n\n'+overrides[key]+'\n'
        target.write_text(''.join(blocks))
    print('Applied reviewed prose:', sum(map(len, grouped.values())))

from prepare_native_docs import prepare_docs
prepare_docs()
