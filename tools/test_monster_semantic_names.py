#!/usr/bin/env python3
"""Actual visible-name producers: head counts, unique articles, qualifier guards."""
import subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(s,name):
 p=s.index(name);a=s.rfind('\n',0,p)+1;b=s.index('{',p);d=0
 for e in range(b,len(s)):
  if s[e]=='{':d+=1
  elif s[e]=='}':
   d-=1
   if not d:return s[a:e+1]
 raise AssertionError(name)

compile_catalog();s=(SRC/'zh-display-name.cc').read_text()
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
using monster_type=int;using description_level_type=int;
enum {MONS_HYDRA,MONS_ROYAL_JELLY,MONS_ORC,MONS_SENSED,MONS_REMNANT,MONS_UNKNOWN};
enum {DESC_PLAIN,DESC_A,DESC_THE,DESC_YOUR,DESC_ITS,DESC_DBNAME,DESC_NONE,ATT_HOSTILE,ATT_FRIENDLY,MILEV_NAME};
struct monsterentry{const char*name;};monsterentry monster_data[]={{"hydra"},{"Royal Jelly"},{"orc"},{"sensed monster"},{"remnant"},{"future-unknown-monster"}};
monsterentry*get_monster_data(int t){return &monster_data[t];}bool mons_is_the(int t){return t==MONS_ROYAL_JELLY;}bool mons_class_is_remnant(int t){return t==MONS_REMNANT;}
string mons_type_name(int t,int){return string(mons_is_the(t)?"the ":"")+monster_data[t].name;}
string number_in_words(unsigned n){const char*words[]={"zero","one","two","three","four","five","six","seven","eight","nine","ten"};return n<11?words[n]:to_string(n);}
vector<string>missing;void audit_name_fallback(const string&domain,const string&name){missing.push_back(domain+":"+name);}
struct monster;
struct monster_info{int type=MONS_HYDRA,num_heads=8,attitude=ATT_HOSTILE;bool multi=true,proper=false;string qualifier,proper_text;
 monster_info(){}monster_info(const monster*,int);
 bool has_hydra_multi_attack()const{return multi;}bool has_proper_name()const{return proper;}string proper_name(int)const{return proper_text;}
 string common_name(int)const{string name=monster_data[type].name;if(multi&&type!=MONS_SENSED&&type!=MONS_REMNANT)name=(num_heads<11?number_in_words(num_heads):to_string(num_heads))+"-headed "+name;return qualifier+name;}
 string full_name(int d)const{if(d==DESC_NONE)return "";string name=proper?proper_text+" the "+common_name(0):common_name(0);if(d==DESC_A)name=type==MONS_ROYAL_JELLY?"the "+name:"a "+name;else if(d==DESC_THE||d==DESC_ITS)name="the "+name;else if(d==DESC_YOUR)name="your "+name;return d==DESC_ITS?name+"'s":name;}
};
struct monster{monster_info info;int type;bool visible=true;monster(monster_info m):info(m),type(m.type){}bool observable()const{return visible;}bool friendly()const{return info.attitude==ATT_FRIENDLY;}string name(int d)const{return info.full_name(d);}};
monster_info::monster_info(const monster*m,int){*this=m->info;}
'''
for name in ['std::string exact_component(', 'std::string description_prefix(', 'std::string possessive_suffix(', 'std::string _monster_type_component(', 'ZhArg _monster_visible_species_arg(', 'ZhArg zh_monster_type_arg(', 'ZhArg zh_monster_arg(', 'ZhArg zh_monster_info_arg(']:code+=block(s,name)+'\n'
code+=r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.monster.semantic-name");int checked=0;
for(int heads:{1,2,8,10,11,27,256})for(bool friendly:{false,true})for(int desc:{DESC_PLAIN,DESC_A,DESC_THE,DESC_YOUR,DESC_ITS,DESC_DBNAME,DESC_NONE}){
 monster_info info;info.num_heads=heads;info.attitude=friendly?ATT_FRIENDLY:ATT_HOSTILE;monster live(info);missing.clear();auto snapshot=zh_monster_info_arg("monster",info,desc);auto actual=zh_monster_arg("monster",live,desc);assert(snapshot.canonical==info.full_name(desc));assert(actual.canonical==live.name(desc));
 if(desc!=DESC_DBNAME&&desc!=DESC_NONE){assert(snapshot.supported&&actual.supported);assert(snapshot.localized==actual.localized);assert(snapshot.localized.find(to_string(heads))!=string::npos);assert(snapshot.localized!=snapshot.canonical);assert(missing.empty());}++checked;
}
for(int type:{MONS_ROYAL_JELLY,MONS_ORC})for(int desc:{DESC_PLAIN,DESC_A,DESC_THE,DESC_YOUR,DESC_ITS})for(bool friendly:{false,true}){
 monster_info info;info.type=type;info.multi=false;info.attitude=friendly?ATT_FRIENDLY:ATT_HOSTILE;monster live(info);missing.clear();auto a=zh_monster_info_arg("monster",info,desc);auto b=zh_monster_arg("monster",live,desc);assert(a.supported&&b.supported&&a.canonical==info.full_name(desc)&&b.canonical==live.name(desc));assert(a.localized==b.localized&&missing.empty());auto type_arg=zh_monster_type_arg("monster",type);assert(type_arg.supported&&type_arg.canonical==mons_type_name(type,DESC_PLAIN));++checked;
}
for(int type:{MONS_HYDRA,MONS_ROYAL_JELLY,MONS_ORC})for(const char*q:{"ghostly ","bound ","helpless ","vampire ","custom-adjective ","renamed ","shaped shifter "})for(int heads:{1,8,12}){
 monster_info info;info.type=type;info.multi=type==MONS_HYDRA;info.num_heads=heads;info.qualifier=q;monster live(info);for(int desc:{DESC_A,DESC_THE,DESC_ITS}){auto a=zh_monster_info_arg("monster",info,desc);auto b=zh_monster_arg("monster",live,desc);assert(!a.supported&&!b.supported);assert(a.localized==a.canonical&&b.localized==b.canonical);++checked;}
}
monster_info info;monster hidden(info);hidden.visible=false;auto hidden_name=zh_monster_arg("monster",hidden,DESC_THE);assert(!hidden_name.supported&&hidden_name.localized==hidden_name.canonical);++checked;
info.type=MONS_UNKNOWN;info.multi=false;auto unknown=zh_monster_info_arg("monster",info,DESC_A);assert(!unknown.supported&&unknown.localized==unknown.canonical);++checked;
info.type=MONS_HYDRA;info.multi=true;info.num_heads=0;auto invalid=zh_monster_info_arg("monster",info,DESC_A);assert(!invalid.supported&&invalid.localized==invalid.canonical);++checked;
cout<<checked<<" actual monster name cases passed; visible head-count/unique article, canonical/qualifier/visibility guards\n";
}
'''
with tempfile.TemporaryDirectory(prefix='dcss-monster-name-') as td:
 p=Path(td);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++17','-O2','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=60)
