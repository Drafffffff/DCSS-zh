#!/usr/bin/env python3
"""Exercise actual C++ translator: templates, markup, fallback, suspension, language toggle."""
import json,re,subprocess,tempfile,time
from pathlib import Path
from native_catalog import ROOT,SRC,LOC,PRINTF,formats,tags,reviewed_entries,review_files
entries=json.loads((LOC/'source.json').read_text())
for path in sorted(LOC.glob('source-*.json')): entries+=json.loads(path.read_text())
raw={}
for f in sorted((LOC/'pi').glob('*batch-*.json')): raw.update(json.loads(f.read_text())['translations'])
review_entries = reviewed_entries()
review_targets = {entry['en']: entry['zh'] for entry in review_entries}
pairs=[]
for e in entries:
    en=e['en']; zh=review_targets.get(en,raw.get(e['id']))
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
    en=entry['en']; zh=review_targets.get(en,raw[entry['id']])
    if en.startswith(("This weapon's minimum attack delay", '    At ', 'Damage rating:')): continue # reviewed templates below
    if '<' in en or not formats(en) or any(t!='%d' for t in formats(en)): continue
    def expanded(text):
        values=iter(str(n) for n in range(1,30))
        return re.sub(r'%d',lambda m:next(values),text)
    tests.append((expanded(en),expanded(zh)));item_cases+=1

# Screenshot regressions: reviewed full sentences, including level/floor context.
for entry in review_entries:
    en, zh = entry['en'], entry['zh']
    zh = re.match(r'^\s*',en)[0]+zh.strip()+re.search(r'\s*$',en)[0]
    def expand(text):
        index = [0]
        def value(match):
            index[0] += 1
            token = match.group()
            if token == '%%':
                index[0] -= 1
                return '%'
            if token.endswith('s'):
                if en == 'The %s %s %s%s%s%s' and index[0] == 2: return 'hits'
                return 'ZYBQ'+str(index[0])
            if token.endswith('c'): return 'Q'
            if token.endswith(('f','g')): return str(index[0])+'.5'
            return str(index[0]+4)
        return PRINTF.sub(value, text)
    src = expand(en)
    dst = expand(zh).replace('hits', review_targets.get('hits', dict(pairs).get('hits', 'hits')))
    tests.append((src, dst))
    if src.endswith('\n'):
        tests.append((src.rstrip('\n'), dst.rstrip('\n')))
    if '<white>' in src:
        tests.append((re.sub(r'</?white>', '', src), dst))

# Runtime sentence/name oracles now exercise their real named-message producers
# via test_message_ids.py and isolated game scenarios. The legacy layer no
# longer promises word-by-word reconstruction of names or arbitrary sentences.
assert len(tests)>=100
enc=lambda s:json.dumps(s,ensure_ascii=False)
code='#include "zh-localization.h"\n#include <cassert>\n#include <cstdlib>\n#include <iostream>\nint main() { int failures=0; setenv("DCSS_LANG","zh",1);\n'
for s,t in tests: code+='if (zh_translate('+enc(s)+') != '+enc(t)+') { std::cerr << '+enc(s+' => ')+ ' << zh_translate('+enc(s)+') << std::endl; ++failures; }\n'
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
# An unmigrated item list must not regain the removed generic word fallback.
code+='assert(zh_translate("a) +0 short sword") == "a) +0 short sword");\n'

# A real printf phrase may be concatenated with other text before rendering.
fragment_cases=0
for en,zh in pairs:
    if formats(en)==['%s'] and len(en.split('%s')[0])>=4 and en.split('%s')[-1].strip() and '<' not in en and '\n' not in en:
        src='XQZ_VJKT ['+en.replace('%s','ZYBQ')+'] UVQP'
        dst='XQZ_VJKT ['+zh.replace('%s','ZYBQ')+'] UVQP'
        code+='if (zh_translate('+enc(src)+') != '+enc(dst)+') { std::cerr << '+enc(src+' => ')+ ' << zh_translate('+enc(src)+') << '+enc(' EXPECTED '+dst)+' << std::endl; ++failures; }\n'
        fragment_cases+=1
    if fragment_cases==30:break
# Real message_line joins must retain independently translated sentence boundaries.
for separator in ('<lightgrey> </lightgrey>', '<lightgrey>; </lightgrey>'):
    first = '<lightgrey>You hit the rat.'
    second = '<lightgrey>You shoot an arrow.'
    code += 'assert(zh_translate('+enc(first+separator+second)+') == zh_translate('+enc(first)+') + '+enc(separator)+' + zh_translate('+enc(second)+'));\n'

# Colour names passed through printf belong to markup, not translated prose.
# Exercise the real shopping format in every stock/key colour combination.
shop_source = ' <%s>%c %c </%s><%s>%4d gold   %s%s</%s>'
shop_target = dict(pairs)[shop_source]
for key_colour in ('red','lightred','lightgreen','lightcyan'):
    for item_colour in ('yellow','lightgrey','white','lightblue'):
        values = [key_colour,'a','-',key_colour,item_colour,'  54','ZYBQ','',item_colour]
        def render_template(text):
            it=iter(values)
            return PRINTF.sub(lambda m: '%' if m.group()=='%%' else next(it),text)
        src,dst=render_template(shop_source),render_template(shop_target)
        code += 'assert(zh_translate('+enc(src)+') == '+enc(dst)+');\n'
        code += 'assert(zh_translate(zh_translate('+enc(src)+')) == '+enc(dst)+');\n'

# Large histories must not exhaust the recursion budget. Alternate the two
# real separators, colours, punctuation and message types as storage does.
code += r'''{
 const std::string messages[] = {"<lightgrey>You hit the rat.", "<red>You bludgeon the rat!",
  "<lightgrey>You kill the rat!", "<white>You shoot an arrow.", "You have reached level 5!"};
 const std::string separators[] = {"<lightgrey> </lightgrey>", "<lightgrey>; </lightgrey>"};
 for(int count : {1,2,12,13,24,64}) {
  std::string source, expected;
  for(int i=0;i<count;i++) {
   if(i) {source+=separators[i%2];expected+=separators[i%2];}
   source+=messages[i%5];expected+=zh_translate(messages[i%5]);
  }
  assert(zh_translate(source)==expected);
 }
}'''

for colour in ('white','black','yellow','lightgrey'):
    tag='<'+colour+'>'
    code+='assert(zh_translate('+enc(tag)+') == '+enc(tag)+');\n'
    text=tag+tests[0][1]+'<lightgrey>'
    code+='assert(zh_translate('+enc(text)+') == '+enc(text)+');\n'
# Regression cases use Pi's wording as the oracle, not hand-authored translations.
translated=dict(pairs)
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
code+='assert(zh_translate("/source/items.txt") == "/source/items.txt");\n'
code+='assert(zh_translate("https://example.com/items/scrolls") == "https://example.com/items/scrolls");\n'
code+='assert(zh_translate("a - XQZ_VJKT") == "a - XQZ_VJKT");\n'
code+='''assert(zh_translate("XQZ_VJKT ZYBQ 12938") == "XQZ_VJKT ZYBQ 12938");
{ ZhTranslationPause pause; assert(zh_translate("'''+tests[0][0].replace('"','\\"')+'''") == "'''+tests[0][0].replace('"','\\"')+'''"); }
setenv("DCSS_LANG","en",1);
'''
code+='assert(zh_translate('+enc(tests[0][0])+') == '+enc(tests[0][0])+');\n'
code+='setenv("DCSS_LANG","zh",1); for (int i=0;i<100;i++) zh_translate(std::string(2048,\'x\'));\n'
code+='if (failures) return 1; std::cout << "PASS: '+str(len(tests))+' catalog/template cases, '+str(fragment_cases)+' composed template cases, canonical colour tags, no word fallback, pause, English mode, long input\\n"; }\n'
with tempfile.TemporaryDirectory() as td:
    p=Path(td);(p/'test.cc').write_text(code)
    subprocess.run(['c++','-std=c++11','-O2','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,timeout=15)
