#!/usr/bin/env python3
"""Actual special monster detail prose/energy producers vs frozen engine English."""
import json,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(s,name):
 p=s.index(name);a=s.rfind('\n',0,p)+1;b=s.index('{',p);d=0
 for end in range(b,len(s)):
  if s[end]=='{':d+=1
  elif s[end]=='}':
   d-=1
   if not d:return s[a:end+1]
 raise AssertionError(name)

compile_catalog()
s=(SRC/'describe.cc').read_text();refs=json.loads((ROOT/'tools/fixtures/special-monster-detail-english.json').read_text())
stat=block(s,'static string _monster_stat_description(')
assert 'mi.speed_description()' not in stat
assert '_monster_intrinsic_prose(mi, resist)' in stat
assert 'zh_integer("rate", mi.regen_rate(1))' in stat
assert 'zh_message("monster.special.program_bug")' in s
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <array>
#include <cassert>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
#define ASSERT(x) assert(x)
[[noreturn]]void die(const char*){abort();}
using monster_type=int;using mon_resist_flags=int;using resists_t=array<int,10>;
enum {MR_RES_STEAM,MR_RES_CORR,MR_RES_DAMNATION,MR_RES_MIASMA,MR_RES_TORMENT,MR_RES_COLD};
enum {MB_UNBLINDABLE,MB_RES_DROWN,MB_CHAOTIC};
enum {M_STATIONARY,M_COLD_BLOOD,M_BURROWS,M_ACID_SPLASH,M_INSUBSTANTIAL,M_AMORPHOUS};
enum {MONS_NORMAL,MONS_SHADOWGHAST,MONS_ROYAL_JELLY,MONS_STAR_JELLY,MONS_BATTLESPHERE,MONS_LURKING_HORROR,MONS_ORC_APOSTLE,MONS_SIXFIRHY,MONS_JIANGSHI,MONS_ANIMATED};
enum {PRONOUN_SUBJECTIVE,DESC_A,MSLOT_LAST_VISIBLE_SLOT=3,GOD_ZIN=1,RE_INELIGIBLE=0,RE_TOO_STRONG,RE_ELIGIBLE,RE_RECITE_TIMER,HT_NONE=0,HT_AMPHIBIOUS,HT_AMPHIBIOUS_LAVA,ZAP_SHOOTING_STAR};
const char*CLOUD_IMMUNE_MB_KEY="immune";
unsigned int test_class_flags=0;bool test_see=false,test_air=false,test_priest=false,test_draconian=false,test_tentacle=false,test_god=false,test_monster=true,test_explode=false;int test_habitat=0,test_eligibility=0,test_player_delay=10,test_dice=1,test_sides=3,test_power=1;vector<string>calls;
struct Value {bool flag=false;operator bool()const{return flag;}};
struct Props {bool immune=false;bool exists(const char*)const{return immune;}Value operator[](const char*)const{return {immune};}};
struct Pos {bool zero=false;bool origin()const{return zero;}};
struct item_def {string text="a long sword";bool known=true,unusual=true;string name(int,bool=false,bool=false,bool=false,bool=false)const{return text;}};
bool item_is_unusual(const item_def&i){return i.unusual;}
struct mon_energy_usage{int attack=10,missile=10,move=10,swim=10,spell=10;bool operator==(const mon_energy_usage&o)const{return attack==o.attack&&missile==o.missile&&move==o.move&&swim==o.swim&&spell==o.spell;}};
#define DEFAULT_ENERGY mon_energy_usage{}
struct monster_info {int type=0,base_type=0,hd=1,attitude=0,speed=10;unsigned int flags=0;bool plural=false;string subject="it";Props props;Pos pos;mon_energy_usage menergy;shared_ptr<item_def>inv[4];
 bool is(int f)const{return flags&(1u<<f);}const char*pronoun(int)const{return subject.c_str();}bool pronoun_plurality()const{return plural;}bool can_see_invisible()const{return test_see;}bool airborne()const{return test_air;}int draconian_subspecies()const{return MONS_NORMAL;}int base_speed()const{return speed;}bool is_priest()const{return test_priest;}
 vector<string>get_unusual_items()const{vector<string>r;for(auto&i:inv)if(i&&item_is_unusual(*i))r.push_back(i->name(DESC_A,false,false,true,false));return r;}bool has_unusual_items()const{return attitude==0&&!get_unusual_items().empty();}
 string speed_description()const;
};
struct Player {bool wizard=false;}you;
struct monster{};monster current;
struct recite_counts{};
bool mons_class_flag(int,int f){return test_class_flags&(1u<<f);}bool mons_class_is_stationary(int t){return mons_class_flag(t,M_STATIONARY);}bool mons_is_tentacle_or_tentacle_segment(int){return test_tentacle;}bool mons_class_is_animated_weapon(int t){return t==MONS_ANIMATED;}bool mons_is_draconian_job(int){return test_draconian;}int mons_habitat_type(int,int){return test_habitat;}
monster*monster_at(Pos){return test_monster?&current:nullptr;}bool in_good_standing(int,int){return test_god;}int zin_check_recite_to_single_monster(monster*,recite_counts&){calls.push_back("eligibility");return test_eligibility;}int zin_recite_power(){calls.push_back("power");return test_power;}int player_movement_speed(bool,bool){return test_player_delay;}
struct dice_def {int num,size;};dice_def zap_damage(int,int,bool,bool){calls.push_back("zap");return {test_dice,test_sides};}dice_def mon_explode_dam(int,int){calls.push_back("explode");return {test_dice,test_sides};}dice_def battlesphere_damage_from_hd(int){calls.push_back("sphere");return {test_dice,test_sides};}bool mon_explodes_on_death(int){return test_explode;}
int get_resist(resists_t r,int f){return r[f];}
const char*_get_resist_name(int f){switch(f){case MR_RES_STEAM:return "steam";case MR_RES_CORR:return "acid and corrosion";case MR_RES_DAMNATION:return "damnation";case MR_RES_MIASMA:return "miasma";case MR_RES_TORMENT:return "torment";default:return "cold";}}
string uppercase_first(string s){if(!s.empty())s[0]=toupper(s[0]);return s;}
string conjugate_verb(const string&s,bool p){if(p)return s;if(s=="are")return "is";if(s=="have")return "has";return s+"s";}
template<class...A>string make_stringf(const char*f,A...a){char b[4096];snprintf(b,sizeof b,f,a...);return b;}
template<class I>string comma_separated_line(I a,I b,const string&last=" and ",const string&comma=", "){string s;for(auto i=a;i!=b;++i){if(i!=a)s+=next(i)==b?last:comma;s+=*i;}return s;}
template<class I>string join_strings(I a,I b,const string&sep=" "){return comma_separated_line(a,b,sep,sep);}
ZhArg zh_item_arg(const string&key,const item_def&i,int d){return {key,ZhArgType::Name,i.name(d),i.known?"长剑":i.name(d),i.known};}
'''
code+=refs['habitat']+'\n'
code+=refs['death'].replace('_desc_mon_death_explosion(', '_old_death(')+'\n'
code+=refs['intrinsic'].replace('_desc_mon_death_explosion(', '_old_death(')+'\n'
code+=refs['energy']+'\n'+refs['speed']+'\n'
for name in ['static string _special_detail_display(', 'static ZhArg _special_monster_subject(', 'static ZhArg _special_resist_atom(', 'static ZhArg _special_resist_list(', 'static ZhArg _monster_habitat_message(', 'static ZhArg _monster_speed_message(', 'static void _desc_mon_death_explosion(', 'static string _monster_intrinsic_prose(']:code+=block(s,name)+'\n'
code+=r'''
int checked=0;
void check(const monster_info&mi,resists_t resist){calls.clear();auto before=old_intrinsic(mi,resist);auto before_calls=calls;calls.clear();string now;{ZhTranslationPause english;now=_monster_intrinsic_prose(mi,resist);}if(now!=before){cerr<<"type="<<mi.type<<" flags="<<mi.flags<<" class="<<test_class_flags<<"\n"<<before<<"\n---\n"<<now;abort();}assert(calls==before_calls);calls.clear();auto zh=_monster_intrinsic_prose(mi,resist);assert(calls==before_calls);if(!before.empty())assert(zh!=before);++checked;}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.monster.special");resists_t resist{};monster_info mi;
 for(int type=0;type<10;++type)for(unsigned int mb=0;mb<8;++mb)for(unsigned int cls=0;cls<64;++cls)for(bool plural:{false,true}){mi.type=type;mi.flags=mb;test_class_flags=cls;mi.plural=plural;mi.subject=plural?"they":"it";test_habitat=type%3;test_air=mb&1;test_see=mb&2;mi.props.immune=mb&4;check(mi,resist);}
 test_class_flags=0;mi.type=MONS_NORMAL;mi.flags=0;test_air=false;test_see=false;mi.props.immune=false;
 for(int a=-2;a<=4;++a)for(int b=-2;b<=4;++b)for(int c=-2;c<=4;++c){resist[0]=a;resist[1]=b;resist[2]=c;resist[3]=a;resist[4]=b;check(mi,resist);}
 resist={};test_god=true;for(const char*pronoun:{"he","she","it","they","you"})for(bool plural:{false,true})for(bool wizard:{false,true})for(bool exists:{false,true})for(bool origin:{false,true})for(int eligibility=0;eligibility<4;++eligibility){mi.subject=pronoun;mi.plural=plural;you.wizard=wizard;test_monster=exists;mi.pos.zero=origin;test_eligibility=eligibility;test_power=321;mi.hd=27;check(mi,resist);}
 test_god=false;test_monster=true;mi.pos.zero=false;mi.subject="it";mi.plural=false;
 for(int type:{MONS_NORMAL,MONS_ANIMATED})for(int mask=1;mask<16;++mask){mi.type=type;for(int i=0;i<4;++i){mi.inv[i].reset();if(mask&(1<<i)){mi.inv[i]=make_shared<item_def>();mi.inv[i]->unusual=!(i&1);}}check(mi,resist);}
 mi.type=MONS_NORMAL;for(auto&i:mi.inv)i.reset();mi.inv[0]=make_shared<item_def>();mi.inv[0]->known=false;auto en=old_intrinsic(mi,resist);auto zh=_monster_intrinsic_prose(mi,resist);assert(en==zh);++checked;mi.inv[0].reset();
 for(int type:{MONS_STAR_JELLY,MONS_BATTLESPHERE,MONS_LURKING_HORROR,MONS_NORMAL})for(bool explode:{false,true})for(int dice:{0,1,33})for(int sides:{1,5,100}){mi.type=type;test_explode=explode;test_dice=dice;test_sides=sides;check(mi,resist);}test_explode=false;
 for(int type:{MONS_NORMAL,MONS_SIXFIRHY,MONS_JIANGSHI})for(int speed:{0,5,10,15,30})for(int energy:{5,10,12,20})for(int travel:{5,10,20})for(int flags:{0,1})for(bool priest:{false,true}){mi.type=type;mi.speed=speed;mi.menergy={energy,10,energy,energy+2,energy};test_player_delay=travel;test_class_flags=flags;test_priest=priest;auto old=mi.speed_description();auto now=_monster_speed_message(mi);assert(old==now.canonical);assert(now.supported);if(!old.empty())assert(old!=now.localized);++checked;}
 cout<<checked<<" actual special monster prose/energy cases, canonical and effect-call order passed\n";
}
'''
with tempfile.TemporaryDirectory(prefix='dcss-special-monster-') as td:
 p=Path(td);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++17','-O2','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=120)
