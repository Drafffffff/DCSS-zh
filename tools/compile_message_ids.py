#!/usr/bin/env python3
"""Validate reviewed named messages; emit deterministic C++ catalog and audit."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOC=ROOT/'localization/migration'; SRC=ROOT/'native/crawl-ref/source'
TYPES={'text':'Text','name':'Name','integer':'Integer','number':'Number','key':'Key','colour':'Colour','key_markup':'KeyMarkup'}
PLACE=re.compile(r'\{([a-z][a-z0-9_]*)\}')
# Literal bracket glyphs in styled examples must not consume later key tokens.
SHORTCUT=re.compile(r'\[[^\]\n<>]*\]|\((?:[A-Za-z=]|[A-Za-z]/[A-Za-z])\)')
def compile_catalog():
    messages={}
    for path in sorted(LOC.glob('luna-*-messages.json')):
        doc=json.loads(path.read_text())
        assert doc['model'] in ('Luna','gpt-6-luna'),path
        for entry in doc['messages']:
            identity=entry['id'];assert identity not in messages,identity
            assert re.fullmatch(r'[a-z][a-z0-9_.]*',identity),identity
            assert entry['context'] and entry['source'],identity
            visible = re.sub(r'</?[^>]+>', '', PLACE.sub('', entry['en']))
            if entry['en'] == entry['zh'] and re.search('[A-Za-z]',visible):
                assert 'preserve source English' in entry['context'],(identity,'missing reviewed translation')
            params=entry['params']
            assert isinstance(params,dict),(identity,'params must be an object')
            assert all(re.fullmatch(r'[a-z][a-z0-9_]*',name) for name in params),(identity,'invalid parameter name')
            assert all(t in TYPES for t in params.values()),identity
            for language in ('en','zh'):
                text=entry[language]
                slots=text.replace('{{','').replace('}}','')
                assert set(PLACE.findall(slots)) == set(params),(identity,language)
                assert not re.search(r'[{}]',PLACE.sub('',slots)),(identity,language)
            tags=lambda s:sorted(re.findall(r'</?[a-z][^>]*>',s))
            assert tags(entry['en'])==tags(entry['zh']),(identity,'colour/style tags')
            references=lambda s:sorted(re.findall(r'\[\[[^]\n]+\]\]',s))
            assert references(entry['en'])==references(entry['zh']),(identity,'internal database references')
            shortcuts=lambda s:sorted(SHORTCUT.findall(s))
            assert shortcuts(entry['en'])==shortcuts(entry['zh']),(identity,'literal shortcut tokens')
            messages[identity]=entry
    for path in sorted(LOC.glob('luna-*-messages.json')):
        for case in json.loads(path.read_text()).get('test_cases', []):
            identity=case['id']
            assert identity in messages,(path,identity,'oracle ID is missing')
            schema=messages[identity]['params']
            assert set(case['args'])==set(schema),(identity,'oracle parameter completeness')
            for key,value in case['args'].items():
                assert value['type']==schema[key],(identity,key,'oracle parameter type')
                assert isinstance(value['canonical'],str) and isinstance(value['localized'],str),(identity,key)
                if value['type'] in ('key','key_markup','colour','integer','number'):
                    assert value['canonical']==value['localized'],(identity,key,'translated structural parameter')
    out=['// Generated from Luna-reviewed message IDs. Do not edit.','static const ZhDefinition zh_definitions[] = {']
    # Escape question marks so C++11 trigraphs (e.g. ??!) never alter canonical text.
    q=lambda s:json.dumps(s,ensure_ascii=False).replace('?', r'\?')
    for key,e in sorted(messages.items()):
        schema=';'.join(name+':'+kind for name,kind in e['params'].items())
        out.append('    {'+', '.join(q(x) for x in (key,e['en'],e['zh'],schema))+'},')
    out+=['};','']
    source_keys={}
    for key,e in sorted(messages.items()):
        if 'source_context' not in e:
            continue
        assert not e['params'], (key, 'source-keyed literals cannot contain dynamic parameters')
        context=e['source_context']
        assert re.fullmatch(r'[a-z][a-z0-9_.]*',context),key
        lookup=(context,e['en'].replace('{{','{').replace('}}','}'))
        assert lookup not in source_keys,(key,'duplicate source literal in context')
        source_keys[lookup]=key
    out += ['struct ZhSourceDefinition { const char *context, *source, *id; };',
            'static const ZhSourceDefinition zh_source_definitions[] = {']
    for (context,source),key in sorted(source_keys.items()):
        out.append('    {'+', '.join(q(x) for x in (context,source,key))+'},')
    out += ['    {nullptr, nullptr, nullptr}', '};', '']
    (SRC/'zh-message-catalog.inc').write_text('\n'.join(out))
    lexicon=json.loads((LOC/'luna-display-grammar.json').read_text())['lexicon']
    if isinstance(lexicon,dict): lexicon=lexicon['approved_bases']
    (SRC/'zh-display-lexicon.inc').write_text('// Reviewed semantic name atoms.\n'+ '\n'.join('    {'+q(e['en'])+', '+q(e['zh'])+'},' for e in lexicon)+'\n')
    print(f'Validated {len(messages)} stable message IDs')
    return messages
if __name__=='__main__': compile_catalog()
