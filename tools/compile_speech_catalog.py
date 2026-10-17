#!/usr/bin/env python3
"""Compile Luna-reviewed raw speech grammar into named full message templates.
Channels, protocol tags and branch indices are structural; no rendered text lookup.
"""
import collections,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];LOC=ROOT/'localization/migration';SRC=ROOT/'native/crawl-ref/source'
TOKEN=re.compile(r'(^|\n)([A-Z_]+(?: [A-Z_]+)*:)|\[([^\[\]]*)\]|@([^@\n]+)@',re.M)
def name_kind(tag):
 tag=tag.lower()
 return 'name' if any(x in tag for x in ('monster','something','_name','genus','species','_god')) and tag not in ('species_insult_adj1','species_insult_adj2','species_insult_noun') else 'text'
def slots(text):
 counts=collections.Counter();out=[]
 for m in TOKEN.finditer(text):
  kind='channel' if m[2] else 'choice' if m[3] is not None else 'tag'
  label=kind if kind!='tag' else re.sub('[^a-z0-9_]+','_',m[4].lower()).strip('_')
  if not label or not label[0].isalpha():label='tag_'+label
  counts[label]+=1
  out.append((m,kind,label+'_'+str(counts[label])))
 return out

def compile_speech():
 messages=[];bindings=[];cases=[];seen={}
 def compile_pattern(identity,en,zh,key):
  es,zs=slots(en),slots(zh)
  em={n:(m,k) for m,k,n in es};zm={n:(m,k) for m,k,n in zs}
  assert set(em)==set(zm),(identity,'protocol completeness',set(em)^set(zm))
  schema={}
  for param,(e,kind) in em.items():
   z,zkind=zm[param];assert kind==zkind
   if kind=='channel':
    assert e[2]==z[2],(identity,'channel changed');schema[param]='key'
   elif kind=='tag':
    assert e[4]==z[4],(identity,'actor/DB tag changed');schema[param]=name_kind(e[4])
   else:
    ev=e[3].split('|');zv=z[3].split('|');assert len(ev)==len(zv),(identity,'branch count')
    schema[param]='text'
    for i,(a,b) in enumerate(zip(ev,zv)):compile_pattern(identity+'.'+param+'.alt_'+str(i),a,b,key)
  def transform(text,found):
   out=[];last=0
   for m,kind,param in found:
    out.append(text[last:m.start()].replace('{','{{').replace('}','}}'))
    if kind=='channel':out.append(m[1])
    out.append('{'+param+'}');last=m.end()
   out.append(text[last:].replace('{','{{').replace('}','}}'));return ''.join(out)
  et,zt=transform(en,es),transform(zh,zs)
  # Literal brackets outside speech variants are not translated as shortcuts.
  messages.append({'id':identity,'context':'Selected raw monster speech grammar, before recursive children and semantic actor parameters; preserve source English only for reviewed proper names/onomatopoeia/protocol-only entries','en':et,'zh':zt,'params':schema,'source':{'file':key,'anchor':'raw speech leaf / '+identity}})
  args={k:{'type':typ,'canonical':('TALK:' if typ=='key' else 'orc' if typ=='name' else 'voice'),'localized':('TALK:' if typ=='key' else '兽人' if typ=='name' else '声音')} for k,typ in schema.items()}
  def render(t,which):
   return re.sub(r'\{([a-z][a-z0-9_]*)\}',lambda m:args[m[1]][which],t).replace('{{','{').replace('}}','}')
  cases.append({'id':identity,'args':args,'canonical':render(et,'canonical'),'zh':render(zt,'localized')})
 for path in sorted(LOC.glob('luna-speech-*-raw.json')):
  doc=json.loads(path.read_text());assert doc['model']=='Luna'
  for row in doc['rows']:
   raw,zh=row['raw'],row['zh'];key=row['key'];identity=row['id']
   if key=='imp' and row['file']=='shout.txt':raw='SOUND:'+raw;zh='SOUND:'+zh
   assert '{{' not in raw,(identity,'embedded Lua must remain a protocol')
   pair=(key,raw)
   if pair in seen:
    assert seen[pair][1]==zh,(key,'conflicting review');continue
   seen[pair]=(identity,zh)
   # Unknown untranslated ordinary text is explicitly deferred, never treated
   # as a translation merely because protocol markers themselves are valid.
   visible=TOKEN.sub('',raw)
   if raw==zh and re.search('[A-Za-z]',visible) and not row.get('preserve_english',False):
    continue
   compile_pattern(identity,raw,zh,row['file']+':'+key)
   bindings.append((key,raw,identity))
  messages.extend(doc.get('messages', []))
  for atom in doc.get('atoms',[]):
   identity='speech.atom.'+hashlib.sha256(atom['en'].encode()).hexdigest()[:12]
   messages.append({'id':identity,'context':'Semantic speech enum label; preserve source English for intentional diagnostic/proper-name tokens','en':atom['en'],'zh':atom['zh'],'params':{},'source':{'file':'mon-util.cc','anchor':'speech actor facts'}})
 q=lambda s:json.dumps(s,ensure_ascii=False).replace('?',r'\?')
 (SRC/'zh-speech-catalog.inc').write_text('// Generated from Luna-reviewed raw speech templates.\nstatic const SpeechDefinition speech_definitions[] = {\n'+''.join('    {'+', '.join(map(q,row))+'},\n' for row in bindings)+'};\n')
 (LOC/'luna-speech-generated-messages.json').write_text(json.dumps({'model':'Luna','purpose':'机械转换已审校的完整源模板为命名参数；分支与频道保持独立结构','messages':messages,'test_cases':cases},ensure_ascii=False,indent=2)+'\n')
 print('Compiled speech grammar:',len(bindings),'raw templates,',len(messages),'message IDs')
 return messages
if __name__=='__main__':compile_speech()
