#!/usr/bin/env python3
"""Exercise actual scroll, quiver, god ability and healing target callbacks."""
import json,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(s,name):
 p=s.index(name);a=s.rfind('\n',0,p)+1;b=s.index('{',p);depth=0
 for e in range(b,len(s)):
  if s[e]=='{':depth+=1
  elif s[e]=='}':
   depth-=1
   if not depth:return s[a:e+1]
 raise AssertionError(name)

compile_catalog()
refs=json.loads((ROOT/'tools/fixtures/target-monster-callbacks-english.json').read_text())['functions']
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
enum {WILL_INVULN=999,MR_RES_TORMENT=1,MB_CANT_SEE_YOU=2,MB_SHADOWLESS=3,MB_SUMMONED=4,ATT_HOSTILE=0,I_BRAINLESS=1};
const char*DITHMENOS_MARIONETTE_SPELLS_KEY="spells";
struct Value {int value;int get_int()const{return value;}};
struct Props {int usable;Value operator[](const char*)const{return {usable};}};
struct monster{Props props;};monster mon;
int test_will=0,test_res=0,test_speed=0,test_hp=1,test_total=1,test_intel=2,test_sides=5,test_max_hp=3,test_success=0;
bool test_see=false,test_cant=false,test_backlit=false,test_visible=true,test_exists=true,test_slouch=true,test_bound=true,test_shadowless=false,test_summoned=false,test_reason=false;
struct item_def{};
struct monster_info {int pos=0,type=0,attitude=ATT_HOSTILE;int willpower()const{return test_will;}int resists()const{return test_res;}bool can_see_invisible()const{return test_see;}bool is(int f)const{return f==MB_CANT_SEE_YOU?test_cant:f==MB_SHADOWLESS?test_shadowless:test_summoned;}int intel()const{return test_intel;}};
struct Player {bool backlit()const{return test_backlit;}bool can_see(const monster&)const{return test_visible;}item_def*weapon()const{return nullptr;}}you;
monster*monster_at(int){return test_exists?&mon:nullptr;}
bool is_slouchable(int){return test_slouch;}int slouch_damage(monster*){return test_speed;}bool yred_can_bind_soul(monster*){return test_bound;}int yred_get_bound_soul_hp(int,bool){return test_hp;}
struct mon_spell_slot{};vector<mon_spell_slot>get_unique_spells(const monster_info&){return vector<mon_spell_slot>(test_total);}
string unpacifiable_reason(const monster_info&){return test_reason?"reason":"";}int _pacification_sides(int,int){return test_sides;}int _pacification_hp(int){return test_max_hp;}int _pacify_chance(const monster_info&,int,int){return test_success;}
template<class...A>string make_stringf(const char*f,A...a){char b[4096];snprintf(b,sizeof b,f,a...);return b;}
bool test_empty=false;void describe_to_hit(const monster_info&,ostringstream&r,const item_def*){if(!test_empty)r<<"hit chance";}
ZhArg describe_to_hit_message(const monster_info&,const item_def*){return ZhArg("effect",ZhArgType::Text,test_empty?"":"hit chance",test_empty?"":"命中率");}
'''
for name,ref in refs.items():
 old=ref['body'].replace(name+'(', 'old'+name+'(')
 code+=old+'\n'
 src=(SRC/ref['file']).read_text()
 assert 'args.get_desc_func =' not in src,ref['file']
 code+=block(src,'static vector<ZhArg> '+name+'(')+'\n'
code+=r'''
int checked=0;
void compare(const vector<string>&old,const vector<ZhArg>&now){assert(old.size()==now.size());for(size_t i=0;i<old.size();++i){assert(old[i]==now[i].canonical);assert(now[i].supported);assert(now[i].localized!=now[i].canonical||now[i].canonical.empty());}++checked;}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.target-monster.callbacks");monster_info mi;
 for(int wl:{0,1,100,999}){test_will=wl;compare(old_desc_finite_wl(mi),_desc_finite_wl(mi));}
 for(int res:{0,1,4,5}){test_res=res;compare(old_desc_res_torment(mi),_desc_res_torment(mi));}
 for(bool see:{false,true})for(bool cant:{false,true})for(bool backlit:{false,true}){test_see=see;test_cant=cant;test_backlit=backlit;compare(old_desc_see_invis(mi),_desc_see_invis(mi));}
 for(bool exists:{false,true})for(bool visible:{false,true})for(bool susceptible:{false,true})for(int dice:{0,1,9,100,999}){test_exists=exists;test_visible=visible;test_slouch=susceptible;test_speed=dice;compare(old_desc_slouch_damage(mi),_desc_slouch_damage(mi));}
 for(bool exists:{false,true})for(bool bound:{false,true})for(int hp:{0,1,20,999}){test_exists=exists;test_bound=bound;test_hp=hp;compare(old_desc_bind_soul_hp(mi),_desc_bind_soul_hp(mi));}
 test_exists=true;for(bool shadowless:{false,true})for(bool summoned:{false,true})for(int attitude:{0,1,2})for(int total:{0,1,10,99})for(int usable:{0,1,9,99}){test_shadowless=shadowless;test_summoned=summoned;mi.attitude=attitude;test_total=total;mon.props.usable=usable;compare(old_desc_marionette_spells(mi),_desc_marionette_spells(mi));}
 for(int intel:{0,1,2,3})for(bool reason:{false,true})for(int sides:{0,3,4,5,99})for(int hp:{0,1,3,99})for(int chance:{0,1,50,99,100})for(int pow:{0,1,100}){test_intel=intel;test_reason=reason;test_sides=sides;test_max_hp=hp;test_success=chance;compare(old_desc_pacify_chance(mi,pow),_desc_pacify_chance(mi,pow));}
 for(bool empty:{false,true}){test_empty=empty;compare(old_desc_hit_chance(mi),_desc_hit_chance(mi));}
 cout<<checked<<" actual custom target callback canonical/localized comparisons passed\n";
}
'''
with tempfile.TemporaryDirectory(prefix='dcss-target-callback-') as td:
 p=Path(td);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++17','-O2','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=60)
