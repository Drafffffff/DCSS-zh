#!/usr/bin/env python3
"""Real mon-info semantic producers vs frozen pre-migration English functions."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(s,name):
 p=s.index(name);a=s.rfind('\n',0,p)+1;b=s.index('{',p);depth=0
 for end in range(b,len(s)):
  if s[end]=='{':depth+=1
  elif s[end]=='}':
   depth-=1
   if not depth:return s[a:end+1]
 raise AssertionError(name)

compile_catalog()
s=(SRC/'mon-info.cc').read_text()
refs=json.loads((ROOT/'tools/fixtures/monster-info-english.json').read_text())
flags=refs['flags']
current_flags={m[0]:list(m[1:]) for m in re.findall(r'\{ (MB_\w+),\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"',(SRC/'mon-info-flag-name.h').read_text())}
assert current_flags==flags, 'Flag table changed: review IDs, templates and frozen compatibility baseline'
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <functional>
#include <cassert>
#define ASSERT assert
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <set>
#include <string>
#include <vector>
using namespace std;
'''
code+='enum monster_info_flags {'+','.join(flags)+',NUM_MB_FLAGS};\n'
code+=r'''
enum {MONS_ORC,MONS_NAMELESS_REVENANT,NOBODY_MEMORIES_KEY,NOBODY_MAX_MEMORIES=7,PRONOUN_POSSESSIVE=9,MSGCH_MONSTER_DAMAGE=10};
enum {MDAM_OKAY,MDAM_LIGHTLY_DAMAGED,MDAM_MODERATELY_DAMAGED,MDAM_HEAVILY_DAMAGED,MDAM_SEVERELY_DAMAGED,MDAM_ALMOST_DEAD};
struct FlagName {monster_info_flags flag;string short_singular,long_singular,plural;};
vector<FlagName> monster_info_flag_names={
'''
for f,values in flags.items():code+='{'+f+','+','.join(json.dumps(v) for v in values)+'},\n'
code+=r'''};
set<int> hidden;
bool _hide_moninfo_flag(int f){return hidden.count(f);}
string replace_all(string s,const string&a,const string&b){size_t p;while((p=s.find(a))!=string::npos)s.replace(p,a.size(),b);return s;}
string make_stringf(const char*f,int n,const char*s){char b[1024];snprintf(b,sizeof b,f,n,s);return b;}
template<class A,class B>void _append_container(A&a,const B&b){a.insert(a.end(),b.begin(),b.end());}
template<class It>string comma_separated_line(It b,It e){string s;for(auto i=b;i!=e;++i){if(i!=b){auto n=i;++n;s+=n==e?" and ":", ";}s+=*i;}return s;}
struct Value{int count=0;vector<int> get_vector()const{return vector<int>(count);}};
struct Props{bool has=false;Value value;bool exists(int)const{return has;}const Value&operator[](int)const{return value;}};
struct Base {set<int> bits;int type=MONS_ORC,holi=0,dam=MDAM_OKAY;Props props;string poss="its",constrictor_name;vector<string> constricting_name;vector<ZhArg> constriction_messages;bool is(int f)const{return bits.count(f);}string pronoun(int)const{return poss;}};
struct monster_info:Base {vector<ZhArg> attributes_messages()const;ZhArg wounds_description_message(bool)const;ZhArg constriction_description_message()const;string constriction_description()const;};
struct OldInfo:Base {vector<string> attributes()const;string wounds_description(bool)const;string constriction_description()const;};
bool wounded_damaged(int holi){return holi!=0;}
int channel_to_colour(int,int d){return d%2?1:2;}
string colour_to_str(int c){return c==1?"red":"yellow";}
string colour_string(const string&s,int c){return "<"+colour_to_str(c)+">"+s+"</"+colour_to_str(c)+">";}
string get_damage_level_string(int h,int d){const char*adjs[]={"not","lightly","moderately","heavily","severely","almost"};return string(adjs[d])+(d==MDAM_ALMOST_DEAD?(h?" destroyed":" dead"):(h?" damaged":" wounded"));}
'''
for name,body in refs['functions'].items():code+=body.replace('monster_info::','OldInfo::')+'\n'
for name in ('_monster_flag_message_id','monster_info::attributes_messages','monster_info::wounds_description_message','monster_info::constriction_description_message','monster_info::constriction_description()'):
 code+=block(s,name)+'\n'
code+=r'''
struct targeting_behaviour {function<vector<ZhArg>(const monster_info&)> get_desc_messages_func;function<vector<string>(const monster_info&)> get_desc_func;vector<string>get_monster_desc(const monster_info&);vector<ZhArg>get_monster_desc_messages(const monster_info&);};
'''
directn=(SRC/'directn.cc').read_text()
code+=block(directn,'vector<string> targeting_behaviour::get_monster_desc(')+'\n'
code+=block(directn,'vector<ZhArg> targeting_behaviour::get_monster_desc_messages(')+'\n'
code+=r'''
int main(){setenv("DCSS_LANG","zh",1);size_t checked=0;
 for(bool typed:{false,true})for(bool legacy:{false,true}){monster_info mi;targeting_behaviour b;if(typed)b.get_desc_messages_func=[](const monster_info&){return vector<ZhArg>{zh_message_arg("status","target.monster.flag.hasted")};};if(legacy)b.get_desc_func=[](const monster_info&){return vector<string>{"future canonical callback"};};auto en=b.get_monster_desc(mi);auto ui=b.get_monster_desc_messages(mi);assert(en.size()==ui.size());if(!en.empty()){assert(en[0]==ui[0].canonical);assert(ui[0].supported==typed);if(typed)assert(en[0]=="fast");else assert(ui[0].localized==en[0]);}++checked;}

 for(int mask=0;mask<NUM_MB_FLAGS+4;++mask)for(const char*poss:{"his","her","its","their","your"})for(bool hide:{false,true})for(bool terror:{false,true}){
  monster_info n;OldInfo o;n.poss=o.poss=poss;hidden.clear();
  if(mask<NUM_MB_FLAGS)n.bits.insert(mask);else for(int i=0;i<NUM_MB_FLAGS;++i)if(i%4==mask-NUM_MB_FLAGS)n.bits.insert(i);
  if(terror)n.bits.insert(MB_FROZEN_IN_TERROR);
  if(hide)for(int i=0;i<NUM_MB_FLAGS;i+=3)hidden.insert(i);
  o.bits=n.bits;auto old=o.attributes();auto now=n.attributes_messages();assert(old.size()==now.size());
  for(size_t i=0;i<old.size();++i){assert(old[i]==now[i].canonical);assert(now[i].supported);assert(now[i].localized!=old[i]);++checked;}
 }
 hidden.clear();
 for(int count=0;count<20;++count)for(bool has:{false,true}){monster_info n;OldInfo o;n.type=o.type=MONS_NAMELESS_REVENANT;n.props.has=o.props.has=has;n.props.value.count=o.props.value.count=count;auto now=n.attributes_messages();assert(now[0].canonical==o.attributes()[0]);assert(now[0].supported);++checked;}
 for(int h=0;h<2;++h)for(int d=0;d<=MDAM_ALMOST_DEAD;++d)for(bool colour:{false,true}){monster_info n;OldInfo o;n.holi=o.holi=h;n.dam=o.dam=d;auto now=n.wounds_description_message(colour);assert(now.canonical==o.wounds_description(colour));assert(now.supported);if(d)assert(now.localized!=now.canonical);++checked;}
 for(bool known:{false,true})for(int count=0;count<5;++count){monster_info n;OldInfo o;
  for(int i=0;i<count;++i){ZhArg actor("actor",ZhArgType::Name,"the orc's echo",known?"已审校名称":"the orc's echo",known);auto child=zh_message_arg("constriction",i?"target.monster.constriction.holding":"target.monster.constriction.by",{actor});n.constriction_messages.push_back(child);if(i)n.constricting_name.push_back(child.canonical);else n.constrictor_name=child.canonical;}
  o.constrictor_name=n.constrictor_name;o.constricting_name=n.constricting_name;auto now=n.constriction_description_message();assert(now.canonical==o.constriction_description());assert(now.supported==(known||count==0));if(!known&&count)assert(now.localized==now.canonical);++checked;
 }
 monster_info incomplete;incomplete.constrictor_name="constricted by unknown actor";auto fallback=incomplete.constriction_description_message();assert(!fallback.supported&&fallback.localized==fallback.canonical);
 cout<<"PASS: "<<checked<<" real monster status/wound/constriction producer cases; flag priorities, possessives, hidden flags, memory plural, colours, canonical compatibility and unsupported actor fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=30)
