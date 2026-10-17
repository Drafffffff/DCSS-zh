#!/usr/bin/env python3
"""Check fixed production log bindings against pre-migration text and channels."""
import ast,json,re,subprocess
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog
from migrate_message_sources import calls
messages=compile_catalog()
def literal(arg):
    if not re.fullmatch(r'\s*(?:"(?:\\.|[^"\\])*"\s*)+',arg):return None
    return ''.join(ast.literal_eval(s) for s in re.findall(r'"(?:\\.|[^"\\])*"',arg))
def fixed(text):
    rows=[]
    for _,_,fn,args in calls(text):
        if fn not in ('mpr','mprf'):continue
        args=list(args);channel=args.pop(0).strip() if args and args[0].strip().startswith('MSGCH_') else 'MSGCH_PLAIN'
        if len(args)!=1:continue
        value=literal(args[0])
        if value is not None:rows.append([value,channel])
    return rows
fixture=ROOT/'tools/fixtures/shared-logs-english.json'
if not fixture.exists():
    fixture.write_text(json.dumps({f:fixed(subprocess.check_output(['git','show','7648b0b:crawl-ref/source/'+f],cwd=ROOT/'native',text=True)) for f in ['spl-transloc.cc','player-act.cc']},indent=2)+'\n')
old=json.loads(fixture.read_text());checks=0
for file,original in old.items():
    text=(SRC/file).read_text();reached=set()
    for _,_,fn,args in calls(text):
        if fn!='mpr' or not args:continue
        match=re.fullmatch(r'zh_message\("([a-z0-9_.]+)"\)',args[0].strip())
        if not match:continue
        identity=match[1]
        if not identity.startswith('shared.log.'):continue
        channel=args[1].strip() if len(args)>1 else 'MSGCH_PLAIN'
        assert [messages[identity]['en'],channel] in original,(file,identity,'canonical/channel drift')
        reached.add(identity);checks+=1
    required={e['id'] for e in json.loads((ROOT/'localization/migration/luna-shared-restrictions-messages.json').read_text())['messages'] if e['id'].startswith('shared.log.') and e['source']['file']==file}
    assert required<=reached,(file,required-reached)
print(f'PASS: {checks} fixed production log bindings retain original canonical text and channels')
