#!/usr/bin/env python3
"""Run actual equipment producers against frozen canonical engine functions."""
import json, subprocess, tempfile
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
s=(SRC/'directn.cc').read_text()
assert 'zh_translate(' not in s
assert 'get_desc_messages_func = args.get_desc_messages_func' in s
assert 'parse_string_to_multiple_raw(str, fss)' in s
assert 'me->pretranslated = true' in s
refs=json.loads((ROOT/'tools/fixtures/target-monster-equipment-english.json').read_text())['functions']
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>
#include <vector>
using namespace std;
using mons_equip_desc_level_type=int;using description_level_type=int;using brand_type=int;
enum {DESC_NONE,DESC_A,DESC_PLAIN,DESC_WEAPON=10,DESC_NOTEWORTHY,DESC_NOTEWORTHY_AND_WEAPON,DESC_FULL};
enum {MONS_NORMAL,MONS_PANDEMONIUM_LORD,MONS_DANCING_WEAPON,MONS_PLAYER_GHOST,MONS_ARMOUR_ECHO,MONS_HAUNTED_ARMOUR};
enum {MSLOT_WEAPON,MSLOT_ARMOUR,MSLOT_SHIELD,MSLOT_MISSILE,MSLOT_ALT_WEAPON,MSLOT_WAND,MSLOT_JEWELLERY};
enum {ATT_HOSTILE,ATT_FRIENDLY,ATT_GOOD_NEUTRAL,ATT_NEUTRAL,MB_FRENZIED,MB_ARMED,MI_THROWING_NET};
const char* SPECIAL_WEAPON_KEY="special";
struct Value {int get_int()const{return 1;}};
struct Props {bool special=false;bool exists(const char*)const{return special;}Value operator[](const char*)const{return {};}};
struct item_def {string label="club";int quantity=1,sub_type=0;bool interesting=true,known=true;
 string name(int d,bool=false,bool=false,bool=false,bool=false)const{return (d==DESC_A?"a ":"")+to_string(quantity)+" "+label;}};
struct monster_info {int type=MONS_NORMAL,attitude=ATT_HOSTILE;bool dual=false,armed=false,frenzied=false,known=true;Props props;shared_ptr<item_def> inv[7];
 bool wields_two_weapons()const{return dual;}bool is(int f)const{return f==MB_ARMED?armed:frenzied;}
 string full_name(int)const{return "an orc";}vector<string>attributes()const{return {};}
 vector<ZhArg>attributes_messages()const{return {};}};
bool mons_is_pghost(int t){return t==MONS_PLAYER_GHOST;}
bool mons_class_is_animated_weapon(int t){return t==MONS_DANCING_WEAPON;}
bool item_is_worth_listing(const item_def&i){return i.interesting;}
string get_ghost_description(const monster_info&){return "ghost biography";}
string ghost_brand_name(int,int){return "fiery weapon";}
string article_a(const string&s){return "a "+s;}
string pluralise(const string&s){return s+"s";}
template<class...A>string make_stringf(const char*f,A...a){char b[4096];snprintf(b,sizeof b,f,a...);return b;}
template<class A,class B>void _append_container(A&a,const B&b){a.insert(a.end(),b.begin(),b.end());}
template<class I>string comma_separated_line(I a,I b,const string&last=" and ",const string&comma=", "){string s;for(auto i=a;i!=b;++i){if(i!=a)s+=next(i)==b?last:comma;s+=*i;}return s;}
ZhArg zh_item_arg(const string&key,const item_def&i,int d=DESC_A){return ZhArg(key,ZhArgType::Name,i.name(d),"物品"+to_string(i.quantity),i.known);}
ZhArg zh_monster_info_arg(const string&key,const monster_info&i,int d){return ZhArg(key,ZhArgType::Name,i.full_name(d),"兽人",i.known);}
'''
code+=refs['static string _describe_monster_weapon(']+'\n'
code+=refs['string get_monster_equipment_desc('].replace('get_monster_equipment_desc(', 'old_equipment(')+'\n'
for name in ['static ZhArg _target_detail_join(', 'static ZhArg _target_item_arg(', 'static ZhArg _target_weapon_message(', 'ZhArg get_monster_equipment_desc_message(']:
 # first helper has forward declaration near top; find actual definition after marker
 code+=block(s[s.index('// UI-only semantic producers.'):],name)+'\n'
code+=r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.target-monster");int n=0;
 for(int t=0;t<6;++t)for(int attitude=0;attitude<4;++attitude)for(int level:{DESC_WEAPON,DESC_NOTEWORTHY,DESC_NOTEWORTHY_AND_WEAPON,DESC_FULL})for(int mask=0;mask<128;++mask)for(bool print:{false,true}){
 monster_info mi;mi.type=t;mi.attitude=attitude;mi.dual=mask&1;mi.armed=mask&2;mi.frenzied=mask&4;
 for(int slot=0;slot<7;++slot)if(mask&(1<<slot)){mi.inv[slot]=make_shared<item_def>();mi.inv[slot]->label=slot==4?"axe":"club";mi.inv[slot]->interesting=mask&8;}
 for(int dtype:{DESC_NONE,DESC_A}){auto now=get_monster_equipment_desc_message(mi,level,dtype,print);auto old=old_equipment(mi,level,dtype,print);if(now.canonical!=old){cerr<<t<<" "<<attitude<<" "<<level<<" "<<mask<<" "<<print<<" "<<dtype<<"\n"<<now.canonical<<"\n"<<old<<"\n";return 1;}
 if(print&&t==MONS_PLAYER_GHOST&&dtype!=DESC_NONE)assert(!now.supported);
 if(!now.supported)assert(now.localized==now.canonical);++n;}
 }
 monster_info unknown;unknown.known=false;unknown.inv[0]=make_shared<item_def>();auto whole=get_monster_equipment_desc_message(unknown,DESC_FULL,DESC_A,false);assert(!whole.supported&&whole.localized==whole.canonical);
 unknown.known=true;unknown.inv[0]->known=false;whole=get_monster_equipment_desc_message(unknown,DESC_FULL,DESC_A,false);assert(!whole.supported&&whole.localized==whole.canonical);
 for(bool special:{false,true})for(bool duplicate:{false,true})for(bool armed:{false,true})for(int quantity:{1,2,19})for(int t:{MONS_NORMAL,MONS_PANDEMONIUM_LORD,MONS_DANCING_WEAPON}){
 monster_info mi;mi.type=t;mi.dual=true;mi.armed=armed;mi.props.special=special;mi.inv[0]=make_shared<item_def>();mi.inv[4]=make_shared<item_def>();mi.inv[0]->quantity=mi.inv[4]->quantity=quantity;if(!duplicate)mi.inv[4]->label="axe";
 for(int level:{DESC_WEAPON,DESC_NOTEWORTHY,DESC_NOTEWORTHY_AND_WEAPON,DESC_FULL})for(int dtype:{DESC_NONE,DESC_A}){
 auto now=get_monster_equipment_desc_message(mi,level,dtype,false);assert(now.canonical==old_equipment(mi,level,dtype,false));if(!now.supported)assert(now.localized==now.canonical);++n;}
 }
 cout<<n+2<<" equipment canonical/fallback comparisons passed\n";
}
'''
with tempfile.TemporaryDirectory(prefix='dcss-target-monster-') as td:
 p=Path(td);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++17','-DZH_STANDALONE','-O0','-I',str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
