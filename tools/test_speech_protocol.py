#!/usr/bin/env python3
"""Compare real legacy/new DB generators, RNG state and typed recursive rendering."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
def block(source, needle):
 start=source.index(needle);start=source.rfind("\n",0,start)+1
 return source[start:source.index("\n}",start)+2]
ROOT=Path(__file__).resolve().parents[1]

def main():
 compile_catalog();db=(SRC/'database.cc').read_text()
 prefix=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include "zh-speech.h"
#include <string>
#include <map>
#include <vector>
#include <cassert>
#include <cctype>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <regex>
#include <algorithm>
using namespace std;
vector<string> split_string(const string&sep,const string&s,bool trim=true,bool empty=false){vector<string>r;size_t p=0;for(;;){auto e=s.find(sep,p);auto v=s.substr(p,e==string::npos?e:e-p);if(trim){auto a=v.find_first_not_of(" \t\r\n"),b=v.find_last_not_of(" \t\r\n");v=a==string::npos?"":v.substr(a,b-a+1);}if(empty||!v.empty())r.push_back(v);if(e==string::npos)break;p=e+sep.size();}return r;}
string replace_all(string s,const string&a,const string&b){size_t p=0;while((p=s.find(a,p))!=string::npos){s.replace(p,a.size(),b);p+=b.size();}return s;}
void trim_string(string&s){auto a=s.find_first_not_of(" \t\r\n"),b=s.find_last_not_of(" \t\r\n");s=a==string::npos?"":s.substr(a,b-a+1);}
struct DBM {map<string,string> rows;};
struct TextDB {DBM data;TextDB *translation=nullptr; DBM*get(){return &data;}} ShoutDB,SpeakDB;
struct datum{const void*dptr=nullptr;int dsize=0;datum(){}datum(const void*p,int n):dptr(p),dsize(n){}};
datum _database_fetch(DBM*db,const string&key){auto i=db->rows.find(key);return i==db->rows.end()?datum():datum(i->second.data(),int(i->second.size()));}
string &lowercase(string&s){for(char&c:s)c=tolower(static_cast<unsigned char>(c));return s;}
unsigned rng=1;int draws=0,diagnostics=0;
int random2(int n){++draws;rng=rng*1664525U+1013904223U;return n>0?(rng>>1)%n:0;}
#define MAX_RECURSION_DEPTH 10
#define MAX_REPLACEMENTS 100
#define MSGCH_DIAGNOSTICS 0
void mprf(int,const char*){++diagnostics;}
void _execute_embedded_lua(string&){}
struct monster{};
ZhArg zh_speech_actor_arg(const string&key,const string&tag,const monster&,const ZhSpeechFacts&){return {key,ZhArgType::Text,"actor("+tag+")","参数（"+tag+"）"};}
'''
 code=prefix+block(db,'static string _chooseStrByWeight(')+'\n'
 code+=block(db,'static string _getWeightedString(')+'\n'
 code+='static void _call_recursive_replacement(string&,TextDB&,const string&,int&,int=0);\n'
 code+=block(db,'static string _getRandomisedStr(')+'\n'
 begin=db.index('static void _call_recursive_replacement(string &str',db.index('static string _getRandomisedStr('))
 code+=block(db[begin:],'static void _call_recursive_replacement(')+'\n'
 code+=block(db,'static ZhSpeech _getWeightedSpeech(')+'\n'
 code+=block(db,'static ZhSpeech _getRandomisedSpeech(')+'\n'
 render=(SRC/'zh-speech.cc').read_text()
 render='\n'.join(line for line in render.splitlines() if not line.startswith('#include') or 'zh-speech-catalog.inc' in line)
 code+=render+'\n'
 code+='int main(){setenv("DCSS_LANG","zh",1);\n'
 # Read actual canonical DB rows including original weights.
 for file in ('insult','monspeak','shout'):
  for section in re.split(r'^%%%%.*$',(SRC/'dat/database'/f'{file}.txt').read_text(),flags=re.M)[1:]:
   lines=[x.rstrip() for x in section.splitlines() if not x.startswith('#')]
   while lines and not lines[0].strip():lines.pop(0)
   if not lines:continue
   key=lines.pop(0).strip().lower();value='\n'.join(lines).strip()
   if value:code+='SpeakDB.data.rows['+json.dumps(key)+']='+json.dumps(value)+';\n'
 code+=r'''
int cases=0;
for(const auto&entry:SpeakDB.data.rows)for(unsigned seed=1;seed<=8;++seed){
 for(const string&suffix:{string(""),string(" seen"),string(" unseen")}){
 rng=seed;draws=diagnostics=0;int n=0;string old;
 {ZhTranslationPause pause;old=_getRandomisedStr(SpeakDB,entry.first,suffix,n);}
 const auto oldrng=rng;const int olddraws=draws,olddiag=diagnostics;
 rng=seed;draws=diagnostics=0;n=0;auto tree=_getRandomisedSpeech(SpeakDB,entry.first,suffix,n);
 if(old!=tree.canonical||oldrng!=rng||olddraws!=draws||olddiag!=diagnostics){cerr<<entry.first<<" seed "<<seed<<"\n";abort();}
 ++cases;
 }}
// Source identities, translated DB isolation, repeated recursive children,
// alternatives and unknown whole-parent fallback are exercised independently.
monster mon;ZhSpeechFacts facts;
'''
 doc=json.loads((ROOT/'localization/migration/luna-speech-insults-raw.json').read_text())
 rows={r['key']:r for r in doc['rows'] if not re.search(r'[@\[\]]',r['raw']) and r['zh']!=r['raw']}
 # Real parent template + two actual independently selected child templates.
 parent=next(r for r in doc['rows'] if r['key']=='imp_taunt' and r['raw']=='@run_or_give_up@, thou @generic_insult@!')
 q=lambda s:json.dumps(s,ensure_ascii=False)
 index={}
 for row in doc['rows']:index.setdefault(row['key'],[]).append(row)
 serial=[0]
 def tree(row,depth=0):
  nonlocal code
  assert depth<10,row['key']
  name='n'+str(serial[0]);serial[0]+=1
  code+=f'ZhSpeech {name};{name}.key={q(row["key"])};{name}.source={q(row["raw"])};{name}.canonical={name}.source;\n'
  zh=row['zh']
  for m in re.finditer(r'@([^@]+)@',row['raw']):
   candidates=[r for r in index.get(m[1],[]) if '@species_insult_' not in r['raw']]
   assert candidates,m[1]
   child,translated=tree(candidates[0],depth+1)
   code+=f'{name}.children.push_back({child});{name}.child_markers.push_back({q(m[0])});{name}.child_positions.push_back({m.start()});\n'
   zh=zh.replace(m[0],translated,1)
  return name,zh
 name,expected=tree(parent)
 code+='auto m=zh_render_speech('+name+',mon,facts,"frozen parent");assert(m.localized=='+q(expected)+');\n'
 # Real random-branch source with expected authored words and semantic actor.
 docs=json.loads((ROOT/'localization/migration/luna-speech-monsters-a-raw.json').read_text())
 r=next(r for r in docs['rows'] if r['raw']=='VISUAL:@The_monster@ [almost|nearly] stumbles in trying to escape.')
 for i in (0,1):
  z=r['zh'].replace('@The_monster@','参数（The_monster）');z=re.sub(r'\[([^]]*)\]',lambda m:m[1].split('|')[i],z)
  code+='{ZhSpeech n;n.key='+q(r['key'])+';n.source='+q(r['raw'])+';n.canonical=n.source;facts.choices={'+str(i)+'};auto m=zh_render_speech(n,mon,facts,"canonical branch");assert(m.localized=='+q(z)+');}\n'
 code+='facts.choices.clear();ZhSpeech unknown;unknown.key="extension";unknown.source="a new extension sentence";auto fallback=zh_render_speech(unknown,mon,facts,"unknown whole sentence");assert(fallback.localized=="unknown whole sentence");\n'
 code+='cout<<"PASS: "<<cases<<" real weighted/recursive source selections, suffix/control/RNG/diagnostic parity, actual nested taunt/branch/actor/channel rendering and whole-parent fallback\\n";}\n'
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);(root/'test.cc').write_text(code)
  subprocess.run(['c++','-std=c++14','-DZH_STANDALONE','-I'+str(SRC),str(root/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(root/'test')],check=True)
  subprocess.run([str(root/'test')],check=True,timeout=180)
if __name__=='__main__':main()
