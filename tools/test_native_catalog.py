#!/usr/bin/env python3
"""Exercise actual C++ translator: templates, markup, fallback, suspension, language toggle."""
import json,re,subprocess,tempfile,time
from pathlib import Path
from native_catalog import ROOT,SRC,LOC,PRINTF,formats,tags
entries=json.loads((LOC/'source.json').read_text())
for path in sorted(LOC.glob('source-*.json')): entries+=json.loads(path.read_text())
raw={}
for f in sorted((LOC/'pi').glob('*batch-*.json')): raw.update(json.loads(f.read_text())['translations'])
pairs=[]
for e in entries:
    en=e['en']; zh=raw.get(e['id'])
    if zh is not None: zh=re.match(r'^\s*',en)[0]+zh.strip()+re.search(r'\s*$',en)[0]
    if zh and en!=zh and formats(en)==formats(zh) and tags(en)==tags(zh) and re.search('[\u3400-\u9fff]',zh): pairs.append((en,zh))
# Only assert known strings present in the generated catalog.
cpp=(SRC/'zh-catalog.inc').read_text()
pairs=[(s,t) for s,t in pairs if json.dumps(s,ensure_ascii=False) in cpp]
tests=[]
for s,t in pairs[:100]: tests.append((s,t))
n=0
for s,t in pairs:
    tokens=PRINTF.findall(s)
    if tokens==['%s'] and len(PRINTF.sub('',s))>=8 and '<' not in s:
        tests.append((s.replace('%s','XQZ_TEST'),t.replace('%s','XQZ_TEST')));n+=1
    if n>=30: break
# Real assembled item lines caught by the final PTY audit; distinct numbers
# make accidental capture changes visible.
item_cases=0
for entry in json.loads((LOC/'source-zzzzzzzz-itemlines.json').read_text()):
    en=entry['en']; zh=raw[entry['id']]
    if '<' in en or not formats(en) or any(t!='%d' for t in formats(en)): continue
    def expanded(text):
        values=iter(str(n) for n in range(1,30))
        return re.sub(r'%d',lambda m:next(values),text)
    tests.append((expanded(en),expanded(zh)));item_cases+=1

# The item window joins translated prose, numeric templates, and hotkey tags.
for entry in json.loads((LOC/'source-zzzzzzzz-itemlines.json').read_text()):
    en=entry['en']; zh=raw[entry['id']]
    if 'Your skill:' not in en: continue
    def numbers(text):
        values=iter(str(n) for n in range(1,20))
        return re.sub(r'%d',lambda m:next(values),text)
    tests.append(('測試\n'+numbers(en)+'\n測試', '測試\n'+numbers(zh)+'\n測試'))

assert len(tests)>=100
enc=lambda s:json.dumps(s,ensure_ascii=False)
code='#include "zh-localization.h"\n#include <cassert>\n#include <cstdlib>\n#include <iostream>\nint main() { setenv("DCSS_LANG","zh",1);\n'
for s,t in tests: code+='assert(zh_translate('+enc(s)+') == '+enc(t)+');\n'
# Native mutation menu entries contain a selector before the colour run.
for en in ("You have very sharp teeth.", "You have an uncanny knack for detecting items."):
    zh=next(t for candidate,t in pairs if candidate==en)
    code+='assert(zh_translate('+enc(' a - <lightblue>'+en+'</lightblue>')+') == '+enc(' a - <lightblue>'+zh+'</lightblue>')+');\n'

# Message storage expands shorthand tags; test the rendering input actually produced by DCSS.
for s,t in pairs:
    if '<w>' in s and not s.startswith('<') and not formats(s) and '\n' not in s:
        normalized='<lightgrey>'+s.replace('<w>','<white>').replace('</w>','</white>')
        code+='assert(zh_translate('+enc(normalized)+') == '+enc('<lightgrey>'+t)+');\n'
        break
term=dict(pairs).get('short sword')
if term:
    code+='assert(zh_translate("a) +0 short sword") == '+enc('a) +0 '+term)+');\n'

# A real printf phrase may be concatenated with other text before rendering.
fragment_cases=0
for en,zh in pairs:
    if formats(en)==['%s'] and len(en.split('%s')[0])>=4 and en.split('%s')[-1].strip() and '<' not in en and '\n' not in en:
        src='XQZ_VJKT ['+en.replace('%s','ZYBQ')+'] UVQP'
        dst='XQZ_VJKT ['+zh.replace('%s','ZYBQ')+'] UVQP'
        code+='assert(zh_translate('+enc(src)+') == '+enc(dst)+');\n'
        fragment_cases+=1
    if fragment_cases==30:break
for colour in ('white','black','yellow','lightgrey'):
    tag='<'+colour+'>'
    code+='assert(zh_translate('+enc(tag)+') == '+enc(tag)+');\n'
    text=tag+tests[0][1]+'<lightgrey>'
    code+='assert(zh_translate('+enc(text)+') == '+enc(text)+');\n'
# Regression cases use Pi's wording as the oracle, not hand-authored translations.
translated=dict(pairs)
for noun in ('goblin','staff','larva','hippogriff'):
    if noun in translated:
        from english_inflections import pluralise
        code+='assert(zh_translate('+enc('3 '+pluralise(noun))+') == '+enc('3 '+translated.get(pluralise(noun),translated[noun]))+');\n'
if '(%+d apt)' in translated:
    code+='assert(zh_translate("(+2 apt)") == '+enc(translated['(%+d apt)'].replace('%+d','+2'))+');\n'
if 'Fugue of the Fallen' in translated:
    code+='assert(zh_translate("a - Fugue of the Fallen") == '+enc('a - '+translated['Fugue of the Fallen'])+');\n'
for prefix in ('Stash search prefixes: ','\nMenu/colouring prefixes: '):
    if prefix in translated:
        en=prefix+'identified melee weapon {inventory}'
        zh=translated[prefix]+'identified melee weapon {inventory}'
        code+='assert(zh_translate('+enc(en)+') == '+enc(zh)+');\n'
        code+='assert(zh_translate(zh_translate('+enc(en)+')) == '+enc(zh)+');\n'
# Skill menu regressions: raw tile labels, switches, and composed descriptions.
for en in ('     Skill', 'Level', 'Cost', 'training', 'cost'):
    if en in translated:
        code+='assert(zh_translate('+enc(en)+') == '+enc(translated[en])+');\n'
for en in ('Skills enhanced by %s are in <green>green</green>.',
           'Skills reduced by %s are in <magenta>magenta</magenta>.'):
    assert en in translated
    code+='assert(zh_translate('+enc(en.replace('%s','ZYBQ'))+') == '+enc(translated[en].replace('%s','ZYBQ'))+');\n'
for en in translated:
    if en.startswith('The relative cost of raising each skill') and en.endswith('.\n'):
        code+='assert(zh_translate('+enc(en)+') == '+enc(translated[en])+');\n'
        code+='assert(zh_translate('+enc(en+'ZYBQ')+') == '+enc(translated[en]+'ZYBQ')+');\n'
for en in ('Welcome back, %s the %s.', 'Welcome, %s the %s.'):
    assert en in translated
    src=en.replace('%s','ZYBQ',1).replace('%s','Gnoll Fighter',1)
    zh=translated[en].replace('%s','ZYBQ',1).replace('%s','豺狼人 战士',1)
    code+='assert(zh_translate('+enc(src)+') == '+enc(zh)+');\n'
code+='assert(zh_translate("/source/items.txt") == "/source/items.txt");\n'
code+='assert(zh_translate("https://example.com/items/scrolls") == "https://example.com/items/scrolls");\n'
code+='assert(zh_translate("a - XQZ_VJKT") == "a - XQZ_VJKT");\n'
code+='''assert(zh_translate("XQZ_VJKT ZYBQ 12938") == "XQZ_VJKT ZYBQ 12938");
{ ZhTranslationPause pause; assert(zh_translate("'''+tests[0][0].replace('"','\\"')+'''") == "'''+tests[0][0].replace('"','\\"')+'''"); }
setenv("DCSS_LANG","en",1);
'''
code+='assert(zh_translate('+enc(tests[0][0])+') == '+enc(tests[0][0])+');\n'
code+='setenv("DCSS_LANG","zh",1); for (int i=0;i<100;i++) zh_translate(std::string(2048,\'x\'));\n'
code+='std::cout << "PASS: '+str(len(tests))+' catalog/template cases, '+str(fragment_cases)+' composed template cases, canonical colour tags, compound item names, fallback, pause, English mode, long input\\n"; }\n'
with tempfile.TemporaryDirectory() as td:
    p=Path(td);(p/'test.cc').write_text(code)
    subprocess.run(['c++','-std=c++11','-O2','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,timeout=15)
