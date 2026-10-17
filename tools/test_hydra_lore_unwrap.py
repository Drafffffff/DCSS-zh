#!/usr/bin/env python3
"""Verify monster lore/quote keys match native unwrap_desc representations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'native/crawl-ref/source/dat/descript'


def unwrap_entry(path, key):
    source = path.read_text()
    body = source.split('\n' + key + '\n', 1)[1].split('\n%%%%', 1)[0]
    # Database parsing removes the blank separator around each keyed record.
    body = body.strip('\n').rstrip()
    # Mirror unwrap_desc substitutions from native/crawl-ref/source/libutil.cc.
    body = body.replace('\n\n', r'\n\n').replace('\n ', r'\n ')
    body = body.replace('>\n<', '><').replace('\n', ' ')
    body = body.replace(r'\n', '\n')
    # _monster_db_source/_monster_quote_source apply trimmed_string afterwards.
    return body.strip()


catalog = json.loads((ROOT / 'localization/migration/luna-monster-events-messages.json').read_text())
messages = {m['id']: m for m in catalog['messages']}
cases = {c['id']: c for c in catalog['test_cases']}

hydra = unwrap_entry(DATA / 'monsters.txt', 'hydra')
message = messages['monster.detail.lore.hydra_current']
assert message['en'] == hydra
assert cases[message['id']]['canonical'] == hydra
assert '\n\n' in hydra and 'more!\n\nHitting' in hydra

quote_key = '__cap-D_suffix'
quote_en = unwrap_entry(DATA / 'quotes.txt', quote_key)
quote_zh = unwrap_entry(DATA / 'zh/quotes.txt', quote_key)
message = messages['monster.quote.cap_d_suffix']
assert message['en'] == quote_en
assert message['zh'] == quote_zh
assert cases[message['id']]['canonical'] == quote_en
assert cases[message['id']]['zh'] == quote_zh
assert '\n    -Life of Confucius\n\n' in quote_en
assert '\n   Each one upon each Shoulder;' in quote_en
print('PASS: hydra lore and shared dragon quote match native unwrap_desc outputs')

royal = unwrap_entry(DATA / 'monsters.txt', 'Royal Jelly')
message = messages['monster.lore.royal_jelly']
assert message['en'] == royal
assert cases[message['id']]['canonical'] == royal
print('PASS: Royal Jelly lore matches native unwrap_desc output')
