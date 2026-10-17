#!/usr/bin/env python3
"""Exercise source-generated entity logs with world/name queries as seams.
Canonical expectations freeze the original 7648b0b spl-transloc.cc printf
expressions. This deliberately tests production branch helpers, not just IDs.
"""
import subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(s,needle):
    p=s.index(needle);begin=s.rfind('\n',0,p)+1;brace=s.index('{',p);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[begin:end+1]
    raise AssertionError(needle)

compile_catalog()
source=(SRC/'spl-transloc.cc').read_text()
names=['_transloc_pull_message','_transloc_gravity_message','_transloc_beckon_message','_transloc_contract_message']
for name in names:
    assert source.count(name+'(')>=2,(name,'producer is not bound to a real call site')
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
enum {DESC_THE,DESC_PLAIN,NUM_TRAPS};
using dungeon_feature_type=int;
struct actor {
 string english,localized,verb;bool supported;
 actor(string e,string z,string v,bool s=true):english(e),localized(z),verb(v),supported(s){}
 string name(int)const{return english;}string conj_verb(const string&)const{return verb;}
 bool is_player()const{return english=="you";}
};
struct monster:actor{using actor::actor;};
ZhArg zh_actor_arg(const string&key,const actor*who,int=DESC_THE){return {key,ZhArgType::Name,who->english,who->supported?who->localized:who->english,who->supported};}
ZhArg zh_monster_arg(const string&key,const monster&m,int d=DESC_THE){return zh_actor_arg(key,&m,d);}
bool feat_is_solid(int feat){return feat!=0;}
string feature_description(int feat,int=NUM_TRAPS,const string&="",int desc=DESC_THE){string base=feat==1?"rock wall":feat==2?"stone wall":feat==3?"crystal wall":"unknown feature";return desc==DESC_THE?"the "+base:base;}
string make_stringf(const char*fmt,...){char b[4096];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);return b;}
string number_in_words(int n){const char*words[]={"zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"};return n>=0&&n<13?words[n]:to_string(n);}
'''
for name in names:code+=block(source,'static ZhMessage '+name+'(')+'\n'
code+=r'''
int checks=0,failures=0;
void check(const ZhMessage&m,const string&en,bool supported=true){
 if(m.canonical!=en){cerr<<"Canonical drift: ["<<m.canonical<<"] != ["<<en<<"]\n";++failures;}
 if(supported){if(!(m.localized!=en&&m.display()==m.localized)){cerr<<"Missing localization: "<<m.id<<" ["<<en<<"]\n";++failures;}}
 else assert(m.localized==en&&m.display()==en);
 assert(m.localized.find('{')==string::npos&&m.localized.find('}')==string::npos);
 ++checks;
}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.transloc.entity");
 for(int count:{0,1,2,3,12,99,10000})check(_transloc_pull_message(count),string("You are hurled through space towards ")+(count>1?"some monsters":"a monster")+"!");
 vector<monster> creatures;
 for(string name:{"the orc","Sigmund","the Wizard's ghost","the +7 spectral blade","the two-headed ogre","the player illusion (confused)","the unseen horror","something"})
  for(string verb:{"hurl","hurls"})for(bool known:{false,true}){
   monster mon(name,"甲",verb,known);creatures.push_back(mon);
   for(int feat:{0,1,2,3,99})check(_transloc_gravity_message(&mon,feat),"Waves of gravity draw inward around "+name+".",known);
   check(_transloc_beckon_message(mon),name+" "+verb+" suddenly forward!",known);
   vector<monster*>one{&mon};check(_transloc_contract_message(one),"Space contracts around you and "+name+" and then re-expands violently!",known);
  }
 for(string name:{"you","You"}){
  actor player(name,"乙","hurl");
  check(_transloc_beckon_message(player),name+" hurl suddenly forward!");
 }
 // A null monster selects a terrain sentence or a complete untargeted sentence.
 for(int feat:{0,1,2,3,99})check(_transloc_gravity_message(nullptr,feat),"Waves of gravity draw inward"+(feat_is_solid(feat)?" around "+feature_description(feat):string())+".",feat!=99);
 for(int count:{0,2,3,12,31,64}){
  vector<monster*>many;for(int i=0;i<count;++i)many.push_back(&creatures[i%creatures.size()]);
  check(_transloc_contract_message(many),"Space contracts around you and "+number_in_words(count)+" other creatures and then re-expands violently!");
 }
 if(failures){cerr<<failures<<" message failures\n";return 1;}
 cout<<"PASS: "<<checks<<" source-generated translocation entity log cases, complete canonical sentences and fallback\n";
}
'''
# The feature seam takes the same argument defaults as the engine query.
code=code.replace('const string&=""','const string &unused=""')
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'test.cc';path.write_text(code);exe=Path(tmp)/'test'
    subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(path),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=30)
