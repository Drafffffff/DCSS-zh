#!/usr/bin/env python3
"""Exercise actual casting/channel producers against pre-migration code."""
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
s=(SRC/'spl-cast.cc').read_text()
assert 'mpr(_casting_spell_log("spell.cast.miscast", spell));' in s
assert 'mpr(_casting_spell_log("spell.channel.insufficient_magic", spell));' in s
assert 'string reminder_msg' not in s
for name in ['spl-damage.cc','spl-summoning.cc']:
 assert not re.search(r'start_channelling_spell\([^;]*"',(SRC/name).read_text())
refs=json.loads((ROOT/'tools/fixtures/casting-logs-english.json').read_text())['functions']
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using namespace std;using spell_type=int;
enum {SPELL_FLAME_WAVE=1,SPELL_SEARING_RAY,SPELL_MAXWELLS_COUPLING,SPELL_CLOCKWORK_BEE,SPELL_UNKNOWN};
enum {ATTR_CHANNELLED_SPELL,ATTR_CHANNEL_DURATION,CMD_WAIT};
struct Player {int attribute[8]={};}you;
int effects=0;string key=".";vector<ZhMessage> logs;
void handle_channelled_spell(){++effects;++you.attribute[ATTR_CHANNEL_DURATION];}
void mpr(const ZhMessage&m){logs.push_back(m);}
void mpr(const string&s){logs.push_back({"",s,s});}
template<class...A>void mprf(const char*f,A...a){char b[2048];snprintf(b,sizeof b,f,a...);mpr(string(b));}
string article_a(const string&s){return (s[0]=='e'?"an ":"a ")+s;}
void insert_commands(string&s,initializer_list<int>){auto p=s.find('%');if(p!=string::npos)s.replace(p,1,key);}
const char*spell_title(int n){return n==1?"Flame Wave":n==2?"Searing Ray":n==3?"Maxwell's Capacitive Coupling":n==4?"Launch Clockwork Bee":"Unknown wizard spell!";}
'''
for name,text in refs.items():
 func=name.split('(')[0].split()[-1]
 code+=text.replace(func+'(', 'old_'+func+'(')+'\n'
for name in ['static ZhMessage _surge_power_message(','void surge_power(','void surge_power_wand(','static ZhMessage _casting_spell_log(','static ZhMessage _channel_reminder_message(','void start_channelling_spell(','void stop_channelling_spells(']:code+=block(s,name)+'\n'
code+=r'''
struct Result {vector<ZhMessage> messages;int spell,duration,effects;};
template<class F>Result run(F f){logs.clear();you.attribute[0]=17;you.attribute[1]=23;effects=0;f();return {logs,you.attribute[0],you.attribute[1],effects};}
int checked=0;
void check(const Result&old,const Result&now){
 assert(old.messages.size()==now.messages.size());
 for(size_t i=0;i<old.messages.size();++i){auto&m=now.messages[i];assert(m.canonical==old.messages[i].canonical);assert(m.localized!=m.canonical);assert(m.display()==m.localized);{ZhTranslationPause pause;assert(m.display()==m.canonical);}}
 assert(old.spell==now.spell&&old.duration==now.duration&&old.effects==now.effects);++checked;
}
int main(){
 setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.casting");
 for(int n:{-999,-3,-2,-1,0,1,2,3,999})check(run([&]{old_surge_power(n);}),run([&]{surge_power(n);}));
 for(int n:{-9,0,1,2,3,99})check(run([&]{old_surge_power_wand(n);}),run([&]{surge_power_wand(n);}));
 const char*reminders[]={"", "intensify the flame waves","maintain the ray","continue charging","continue winding your bee",""};
 for(const char*bind:{".","s","5"})for(int spell=1;spell<=5;++spell)for(bool effect:{false,true}){
  key=bind;auto a=run([&]{old_start_channelling_spell(spell,reminders[spell],effect);});auto b=run([&]{start_channelling_spell(spell,effect);});check(a,b);
 }
 for(int spell=0;spell<=5;++spell)for(bool quiet:{false,true}){
  auto a=run([&]{you.attribute[0]=spell;old_stop_channelling_spells(quiet);});auto b=run([&]{you.attribute[0]=spell;stop_channelling_spells(quiet);});check(a,b);
 }
 for(int spell=1;spell<=5;++spell)for(const char*id:{"spell.cast.miscast","spell.channel.insufficient_magic"}){
  auto m=_casting_spell_log(id,spell);string name=spell_title(spell);string expected=string(id)=="spell.cast.miscast"?"You miscast "+name+".":"Without enough magic to sustain it, your "+name+" dissipates.";
  assert(m.canonical==expected);if(!(spell==5?m.localized==expected:m.localized!=expected)){cerr<<spell<<" "<<id<<" "<<m.localized<<"\n";return 1;}++checked;
 }
 cout<<"PASS: "<<checked<<" actual casting/channel producer cases, canonical text, state, quiet branches, remapped keys and unknown-name fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=30)
