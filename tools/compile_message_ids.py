#!/usr/bin/env python3
"""Validate reviewed named messages; emit deterministic C++ catalog and audit."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOC=ROOT/'localization/migration'; SRC=ROOT/'native/crawl-ref/source'
TYPES={'text':'Text','name':'Name','integer':'Integer','number':'Number','key':'Key','colour':'Colour'}
PLACE=re.compile(r'\{([a-z][a-z0-9_]*)\}')
def compile_catalog():
    messages={}
    for path in sorted(LOC.glob('luna-*-messages.json')):
        doc=json.loads(path.read_text())
        assert doc['model'] in ('Luna','gpt-6-luna'),path
        for entry in doc['messages']:
            identity=entry['id'];assert identity not in messages,identity
            assert re.fullmatch(r'[a-z][a-z0-9_.]*',identity),identity
            assert entry['context'] and entry['source'],identity
            if entry['en'] == entry['zh'] and re.search('[A-Za-z]',PLACE.sub('',entry['en'])):
                assert 'preserve source English' in entry['context'],(identity,'missing reviewed translation')
            params=entry['params'];assert all(t in TYPES for t in params.values()),identity
            for language in ('en','zh'):
                text=entry[language];assert set(PLACE.findall(text)) == set(params),(identity,language)
                assert not re.search(r'[{}]',PLACE.sub('',text)),(identity,language)
            tags=lambda s:sorted(re.findall(r'</?[a-z][^>]*>',s))
            assert tags(entry['en'])==tags(entry['zh']),(identity,'colour/style tags')
            shortcuts=lambda s:re.findall(r'\[[^\]\n]*\]',s)
            assert shortcuts(entry['en'])==shortcuts(entry['zh']),(identity,'literal shortcut tokens')
            messages[identity]=entry
    out=['// Generated from Luna-reviewed message IDs. Do not edit.','static const ZhDefinition zh_definitions[] = {']
    q=lambda s:json.dumps(s,ensure_ascii=False)
    for key,e in sorted(messages.items()):
        schema=';'.join(name+':'+kind for name,kind in e['params'].items())
        out.append('    {'+', '.join(q(x) for x in (key,e['en'],e['zh'],schema))+'},')
    out+=['};','']
    (SRC/'zh-message-catalog.inc').write_text('\n'.join(out))
    lexicon=json.loads((LOC/'luna-display-grammar.json').read_text())['lexicon']
    if isinstance(lexicon,dict): lexicon=lexicon['approved_bases']
    (SRC/'zh-display-lexicon.inc').write_text('// Reviewed semantic name atoms.\n'+ '\n'.join('    {'+q(e['en'])+', '+q(e['zh'])+'},' for e in lexicon)+'\n')
    print(f'Validated {len(messages)} stable message IDs')
    return messages
if __name__=='__main__': compile_catalog()
