#!/usr/bin/env python3
"""Extract presentation candidates, delegate translations to Pi, validate, generate C++ catalog."""
import argparse, ast, collections, concurrent.futures, hashlib, json, os, re, subprocess, time
from pathlib import Path
from english_inflections import pluralise
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'native/crawl-ref/source'
LOC = ROOT / 'localization'
MODEL = os.environ.get('DCSS_PI_MODEL', 'cc-switch-deep-seek/deepseek-flash')
TOKEN = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[^\s]', re.S)
PRINTF = re.compile(r'%(?:[-+#0]*)(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|ll|[hljztL])?[diuoxXfFeEgGaAcspn%]')
def formats(s): return PRINTF.findall(s)
def tags(s): return collections.Counter(re.findall(r'</?[a-z][a-z0-9_: -]*>', s))
def extract():
    found = {}
    for path in sorted(list(SRC.glob('*.cc')) + list(SRC.glob('*.h'))):
        if path.name.startswith(('zh-', 'tiledef-', 'levcomp', 'lang-', 'l-')): continue
        text = path.read_text(errors='replace')
        parts=[]; start=0
        def flush():
            nonlocal parts
            if not parts: return
            s=''.join(parts); parts=[]
            # Candidates only. Pi may preserve technical strings verbatim.
            if len(s) < 3 or not re.search(r'[A-Za-z]{3}',s) or len(s)>6000: return
            if '\x00' in s or s.startswith(('#include', 'http:', 'https:')): return
            if re.fullmatch(r'[\w./\\:-]+',s) and not re.fullmatch(r'[A-Za-z][a-z]+',s): return
            found.setdefault(s,[]).append(f'{path.name}:{text.count(chr(10),0,start)+1}')
        for m in TOKEN.finditer(text):
            tok=m.group()
            if tok.startswith(('//','/*')): continue
            if tok.startswith('"'):
                try: value=ast.literal_eval(tok)
                except (SyntaxError,ValueError): flush(); continue
                if not parts: start=m.start()
                parts.append(value)
            else: flush()
        flush()
    entries=[{'id':hashlib.sha256(s.encode()).hexdigest()[:16],'en':s,'locations':v} for s,v in found.items()]
    LOC.mkdir(exist_ok=True)
    (LOC/'source.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
    print(f'Extracted {len(entries)} candidates')
    return entries
PROMPT='''You are the sole Simplified Chinese translator for Dungeon Crawl Stone Soup stable 0.34. Translate every player-facing English string in the supplied JSON into natural, concise roguelike Chinese. Return ONLY a JSON object mapping each supplied id to its translation. Preserve all printf format specifiers in EXACT original order and spelling (including %% and widths), all colour tags with identical counts, all newlines, leading/trailing whitespace, hotkey letters and key sequences. Do NOT translate code, filenames, regexes, Lua expressions, enum identifiers, machine-readable keys or technical debug text: return those unchanged. Preserve quoted names or translate game terms consistently. Goblin/monster/species/item names may be translated. Do not invent content. All entries must be returned. Do not use tools. Do not explain.\n'''
def translate(batch_size=150, workers=3, start_batch=0, extra=False, lines=False, catalog=None):
    prefix=(catalog+'-' if catalog else 'lines-' if lines else 'extra-' if extra else '')
    entries=json.loads((LOC/('source-'+catalog+'.json' if catalog else 'source-lines.json' if lines else 'source-extra.json' if extra else 'source.json')).read_text()); batches=[entries[i:i+batch_size] for i in range(0,len(entries),batch_size)]
    outdir=LOC/'pi'; outdir.mkdir(exist_ok=True)
    def work(pair):
        n, batch=pair; dest=outdir/f'{prefix}batch-{n:04d}.json'
        fingerprint=hashlib.sha256(json.dumps(batch,ensure_ascii=False).encode()).hexdigest()
        if dest.exists() and json.loads(dest.read_text()).get('fingerprint')==fingerprint: return
        context='\nUI constraints: '+json.dumps({e['id']:e['context'] for e in batch if e.get('context')},ensure_ascii=False)+'\n' if any(e.get('context') for e in batch) else ''
        prompt=PROMPT+context+json.dumps({e['id']:e['en'] for e in batch},ensure_ascii=False)
        log=outdir/f'{prefix}batch-{n:04d}.log'
        for attempt in range(3):
            p=subprocess.run(['pi','--print','--model',MODEL,'--no-tools','--no-extensions','--no-mcp','--no-skills','--no-context-files','--no-prompt-templates','--no-session',prompt],capture_output=True,text=True,timeout=600)
            log.write_text(p.stdout+'\nSTDERR:\n'+p.stderr)
            try:
                raw=p.stdout.strip(); raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw)
                result=json.loads(raw[raw.index('{'):raw.rindex('}')+1])
                assert p.returncode==0 and all(isinstance(result[e['id']],str) for e in batch)
                dest.write_text(json.dumps({'fingerprint':fingerprint,'model':MODEL,'translations':result},ensure_ascii=False,indent=2)+'\n')
                print(f'Pi batch {n+1}/{len(batches)} complete',flush=True); return
            except (ValueError,KeyError,AssertionError):
                print(f'Pi batch {n} retry {attempt+1}',flush=True)
        raise RuntimeError(f'Pi translation failed: {log}')
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(work,((n,b) for n,b in enumerate(batches) if n>=start_batch)))
def compile_catalog():
    entries=json.loads((LOC/'source.json').read_text()); translated={}; provenance={}
    for path in sorted(LOC.glob('source-*.json')):
        entries += json.loads(path.read_text())
    unique={}
    for e in entries:
        if e['id'] in unique:
            locs=unique[e['id']]['locations']+e['locations']
            unique[e['id']].update(e); unique[e['id']]['locations']=locs
        else: unique[e['id']]={**e,'locations':list(e['locations'])}
    entries=list(unique.values())
    for f in sorted((LOC/'pi').glob('*batch-*.json')):
        record=json.loads(f.read_text()); translated.update(record['translations'])
        provenance.update({key:record.get('model','unknown') for key in record['translations']})
    good=[]; bad=[]; missing=[]; padded=0
    for e in entries:
        s=e['en']; t=translated.get(e['id'])
        if t is None: missing.append(e['id']); continue
        lead=re.match(r'^\s*',s)[0]; tail=re.search(r'\s*$',s)[0]
        adjusted=lead+t.strip()+tail if s.strip() else s
        if adjusted!=t: padded+=1; t=adjusted
        reasons=[]
        if formats(s)!=formats(t) or s.count('%')!=t.count('%'): reasons.append('printf')
        if tags(s)!=tags(t): reasons.append('tags')
        if s.count('\n')!=t.count('\n'): reasons.append('newlines')
        if re.match(r'^\s*',s)[0]!=re.match(r'^\s*',t)[0] or re.search(r'\s*$',s)[0]!=re.search(r'\s*$',t)[0]: reasons.append('whitespace')
        if reasons: bad.append({**e,'zh':t,'errors':reasons}); continue
        if s!=t and (re.search('[\u3400-\u9fff]',t) or e.get('presentation')): good.append((s,t))
    (LOC/'rejected.json').write_text(json.dumps(bad,ensure_ascii=False,indent=2)+'\n')
    # UTF-8 literals; JSON escaping is C++ compatible for these input strings.
    enc=lambda s: re.sub(r'\\u00([01][0-9a-f])',lambda m: '\\'+format(int(m[1],16),'03o'),json.dumps(s,ensure_ascii=False))
    body='// Generated by native_catalog.py; translations by Pi / DeepSeek Flash.\n'
    body+='static const ZhEntry zh_entries[] = {\n'+''.join('    {'+enc(s)+', '+enc(t)+'},\n' for s,t in good)+'};\n'
    name_files=('item-prop.cc:', 'item-name.cc:', 'spl-data.h:', 'skills.cc:', 'branch-data.h:', 'god-data.h:', 'newgame.cc:', 'english.cc:', 'mon-data.h:', 'species-data.h:', 'job-data.h:', 'religion.cc:')
    names={e['en'] for e in entries if any('/dat/' in loc or loc.startswith(name_files) for loc in e['locations'])}
    # Exact sentences/templates take priority. These Pi-authored fragments
    # cover engine concatenation, adjective prefixes and generated noun plurals.
    plain=lambda s:re.sub(r'</?[a-z][a-z0-9_: -]*>','',s).strip()
    terms={plain(s):plain(t) for s,t in good if 2<=len(plain(s))<=1024
           and '\n' not in s and not formats(s) and not re.search(r'(?<![0-9])%',s)
           and re.search('[A-Za-z]{2}',plain(s)) and re.search('[\u3400-\u9fff]',t)}
    aliases={}
    for s,t in good:
        if s not in names or not 3<=len(s)<=60 or not re.fullmatch(r"[A-Za-z][A-Za-z '\-]*",s): continue
        for alias in (pluralise(s),pluralise(s,monster=True)):
            if alias!=s and alias not in terms: aliases[alias]=t
        if s[0].islower(): aliases.setdefault(s[0].upper()+s[1:],t)
    terms.update({s:t for s,t in aliases.items() if s not in terms})
    body+='static const ZhEntry zh_terms[] = {\n'+''.join('    {'+enc(s)+', '+enc(t)+'},\n' for s,t in sorted(terms.items(),key=lambda pair:-len(pair[0])))+'};\n'
    (SRC/'zh-catalog.inc').write_text(body)
    report={'candidates':len(entries),'received':len(translated),'translated_valid':len(good),'rejected':len(bad),'whitespace_restored':padded,'missing':len(missing),'default_model':MODEL,'translation_models':dict(collections.Counter(provenance.values()))}
    (LOC/'coverage.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['extract','translate','compile']);p.add_argument('--batch-size',type=int,default=150);p.add_argument('--workers',type=int,default=3);p.add_argument('--start-batch',type=int,default=0);p.add_argument('--extra',action='store_true');p.add_argument('--lines',action='store_true');p.add_argument('--catalog');a=p.parse_args()
    if a.action=='extract': extract()
    elif a.action=='translate': translate(a.batch_size,a.workers,a.start_batch,a.extra,a.lines,a.catalog)
    else: compile_catalog()
