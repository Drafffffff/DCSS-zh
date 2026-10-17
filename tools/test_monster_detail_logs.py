#!/usr/bin/env python3
"""Run actual wound/encounter producers against frozen canonical functions."""
import json, re, subprocess, tempfile
from pathlib import Path
from compile_message_ids import SRC, compile_catalog
from test_target_notifications import block

FIX = Path(__file__).parent / 'fixtures/monster-detail-logs-english.json'


def main():
    compile_catalog()
    source = (SRC / 'player-notices.cc').read_text()
    frozen = json.loads(FIX.read_text())
    code = r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <algorithm>
#include <sstream>
#include <iostream>
#include <set>
#include <cstdio>
#include <unordered_set>
using namespace std;
using special_missile_type=int;using monster_type=int;using mon_dam_level_type=int;using mon_holy_type=int;using msg_channel_type=int;using description_level_type=int;
enum {MDAM_OKAY,MDAM_LIGHTLY_DAMAGED,MDAM_MODERATELY_DAMAGED,MDAM_HEAVILY_DAMAGED,MDAM_SEVERELY_DAMAGED,MDAM_ALMOST_DEAD,MSGCH_MONSTER_DAMAGE,MSGCH_PLAIN,MSGCH_MONSTER_SPELL,MSGCH_FRIEND_SPELL,MSGCH_FRIEND_ACTION};
enum {MONS_DANCING_WEAPON=2,MONS_SPECTRAL_WEAPON,MONS_ARMOUR_ECHO,MONS_DEATH_COB, DESC_THE=1,DESC_A,DESC_NONE,DESC_PLAIN,DESC_DBNAME,PRONOUN_SUBJECTIVE,PRONOUN_REFLEXIVE, DESC_WEAPON,DESC_NOTEWORTHY,DESC_NOTEWORTHY_AND_WEAPON};
using mons_equip_desc_level_type=int;
string uppercase_first(string s){if(!s.empty())s[0]=toupper(s[0]);return s;}
string conjugate_verb(const string&s,bool plural){return plural?s:"is";}
string pluralise(const string&s){return s+"s";}
string apply_description(int,const string&s,int count){return count>1?to_string(count)+s:"an "+s;}
template<class... A>string make_stringf(const char*f,A...args){char out[2048];snprintf(out,sizeof out,f,args...);return out;}
string title;string getMiscString(const string&){return title;}
int mons_genus(int type){return type+100;}bool mons_is_unique(int type){return type==99;}
bool known=true;int selection=0;bool quiet=false,coin=false;
struct monster {int type=1,base_monster=1,hit_points=5,max_hit_points=10,holy=0;bool living=true,visible=true;bool plural=false,named=false,worth=true;string label="orc";
 string pronoun(int p)const{return p==PRONOUN_REFLEXIVE?(plural?"themselves":"itself"):(plural?"they":"it");}
 bool pronoun_plurality()const{return plural;}string full_name(int d)const{return d==DESC_THE?"the "+label:"an "+label;}string name(int d)const{return named?"NamedProper":full_name(d);}bool is_named()const{return named;}bool alive()const{return living;}int pos()const{return 0;}bool visible_to(const void*)const{return visible;}bool wont_attack()const{return false;}int holiness()const{return holy;}
};
bool mons_is_zombified(const monster&){return false;}
string mons_type_name(int,int){return "orc";}
int mons_get_damage_level(const monster&);
enum {MB_CHAOTIC=1,MH_UNDEAD=2,MH_NONLIVING=4,OBJ_MISSILES=1,MI_THROWING_NET=1,MI_DART=2,SPMSL_SILVER=1,SPMSL_FRENZY=2,SPMSL_BLINDING=3};
struct monster_info {const monster*mon;int hd=10,flags=0;bool immune=false,escape=false,can_go_frenzy=true;bool is(int flag)const{return flags&flag;}bool net_immune()const{return immune;}bool net_escape_capable()const{return escape;}int dam,holi;monster_info(const monster*m):mon(m),dam(mons_get_damage_level(*m)),holi(m->holy){}ZhArg wounds_description_message(bool use_colour=false)const;string full_name(int d)const{return mon->full_name(d);}};
struct details {const monster*mon;string name;int count;bool genus;};
struct Player {bool sees=true;int pos()const{return 0;}bool see_cell(int)const{return sees;}}you;
bool silenced(int){return quiet;}bool coinflip(){return coin;}
template<class T>const T*random_choose_weighted(const vector<pair<T,int>>&items){return &items[selection%items.size()].first;}
bool _is_mon_equipment_worth_listing(const monster_info&mi,bool){return mi.mon->worth;}
bool _does_core_name_include_inventory(const monster*mon){return mon->type==MONS_DANCING_WEAPON||mon->type==MONS_SPECTRAL_WEAPON||mon->type==MONS_ARMOUR_ECHO;}
string get_monster_equipment_desc(const monster_info&mi,int,int){return mi.mon->type==MONS_DANCING_WEAPON?"a sword":"wielding a sword";}
ZhArg get_monster_equipment_desc_message(const monster_info&mi,int a,int b){return {"equipment",ZhArgType::Text,get_monster_equipment_desc(mi,a,b),"持剑",known};}
ZhArg zh_monster_arg(const string&key,const monster&mon,int d){return {key,ZhArgType::Name,d==DESC_PLAIN?mon.label:mon.name(d),"兽",known};}
ZhArg zh_monster_type_arg(const string&key,int){return {key,ZhArgType::Name,"orc","兽族",known};}
ZhArg zh_glossary_name(const string&key,const string&,const string&value){return {key,ZhArgType::Name,value,known?"称号":value,known};}
template<class I,class F>string comma_separated_fn(I a,I b,F fn){string out;for(auto i=a;i!=b;++i){if(i!=a)out+=i+1==b?" and ":", ";out+=fn(*i);}return out;}
'''
    code+=r'''
string captured,translated;int channel=-1,parameter=-1;
void mpr(const ZhMessage&m,int ch,int p=0){captured=m.canonical;translated=m.localized;channel=ch;parameter=p;}
void mprf(int ch,int p,const char*,const char*text){captured=text;channel=ch;parameter=p;}
string apostrophise(const string&s){return s+"'s";}
bool old_simple_monster_message(const monster&,const char*,bool=false,int=MSGCH_PLAIN,int=0,int=DESC_THE);
bool wounded_damaged(int holi){return holi!=0;}
string colour_to_str(int){return "red";}int channel_to_colour(int,int){return 1;}
'''
    util=(SRC/'mon-util.cc').read_text()
    code+=block(util,'mon_dam_level_type mons_get_damage_level(')+'\n'
    code+=block(util,'string get_damage_level_string(')+'\n'
    code+=r'''
struct item_def {int base_type=OBJ_MISSILES,subtype=0,brand=0;bool ranged=false;bool is_type(int base,int sub)const{return base_type==base&&subtype==sub;}};
int get_ammo_brand(const item_def&i){return i.brand;}bool is_range_weapon(const item_def&i){return i.ranged;}int _get_dart_chance(int hd){return 100-hd;}
void describe_to_hit(const monster_info&,ostringstream&out,const item_def*){out<<"chance to hit: 50%";}
ZhArg describe_to_hit_message(const monster_info&,const item_def*){return {"effect",ZhArgType::Text,"chance to hit: 50%","命中率：50%"};}
struct FireAction {const item_def*launcher=nullptr;const item_def*get_launcher()const{return launcher;}};
class fire_target_behaviour {public:FireAction action;item_def*item=nullptr;bool target=true;bool targeted()const{return target;}item_def*active_item(){return item;}vector<ZhArg>get_monster_desc_messages(const monster_info&);vector<string>old_get_monster_desc(const monster_info&);};
'''
    for query, text in frozen.items():
        # These are independent pre-migration bodies, never generated from the
        # implementation being checked during a test run.
        if query=='void print_wounds(':
            text=text.replace('simple_monster_message(', 'old_simple_monster_message(')
        oldname = query.split('(')[0].split()[-1]
        if '::' in oldname:
            oldname = oldname.split('::')[-1]
        code += text.replace(oldname+'(', 'old_'+oldname+'(', 1) + '\n'
    for query in ['static ZhArg _monster_headsup_message(',
                  'static ZhArg _monster_species_message(',
                  'static ZhArg _describe_monsters_message(',
                  'static ZhArg _abyss_monster_creation_message(']:
        code += block(source, query) + '\n'
    code += block((SRC/'mon-info.cc').read_text(),'ZhArg monster_info::wounds_description_message(')+'\n'
    code += block(util,'void print_wounds(')+'\n'
    code += block((SRC/'throw.cc').read_text(),'vector<ZhArg> fire_target_behaviour::get_monster_desc_messages(')+'\n'
    code += r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.monster.logs");int cases=0;
for(int type:{1,int(MONS_DANCING_WEAPON),int(MONS_SPECTRAL_WEAPON)})for(int mask=0;mask<32;++mask)for(int count:{1,2,4}){
 monster a;a.type=type;a.plural=mask&1;a.worth=!(mask&2);monster b;b.label="ogre";b.worth=!(mask&4);vector<monster*> mons{&a};if(count>1)mons.push_back(&b);unordered_set<const monster*> single;if(mask&8)single.insert(&a);if(mask&16)single.insert(&b);
 for(const string&prefix:{string(),string("You encounter an orc.")}){
  ostringstream old;old<<prefix;old__monster_headsup(mons,single,old);
  auto actual=_monster_headsup_message(mons,single,{"encounter",ZhArgType::Text,prefix,prefix});if(actual.canonical!=old.str()){cerr<<"TYPE "<<type<<" MASK "<<mask<<" count "<<count<<" old:["<<old.str()<<"] actual:["<<actual.canonical<<"]\n";abort();}assert(actual.supported);++cases;
  known=false;actual=_monster_headsup_message(mons,single,{"encounter",ZhArgType::Text,prefix,prefix});if(actual.canonical!=prefix)assert(!actual.supported&&actual.localized==actual.canonical);known=true;++cases;
 }
}
monster mon;
for(int hp:{0,1,2,3,4,5,6,7,8,9,10})for(bool sees:{false,true})for(bool visible:{false,true})for(bool alive:{false,true})for(int holi:{0,1}){
 mon.hit_points=hp;mon.visible=visible;mon.living=alive;mon.holy=holi;you.sees=sees;captured="";channel=parameter=-1;old_print_wounds(mon);const auto oldtext=captured;const int oldch=channel,oldparam=parameter;captured="";channel=parameter=-1;print_wounds(mon);assert(captured==oldtext&&channel==oldch&&parameter==oldparam);++cases;
}
for(bool named:{false,true})for(bool genus:{false,true})for(int count:{1,2,4})for(bool titled:{false,true}){
 mon.named=named;title=titled?"The Champion":"";vector<details> species{{&mon,"orc",count,genus}};auto actual=_describe_monsters_message(species);auto canonical=old__describe_monsters_from_species(species);assert(actual.canonical==canonical);assert(actual.supported);++cases;
}
for(int type:{1,int(MONS_DEATH_COB)})for(int pick=0;pick<15;++pick)for(bool quieted:{false,true})for(bool coinval:{false,true}){
 mon.type=type;selection=pick;quiet=quieted;coin=coinval;auto actual=_abyss_monster_creation_message(&mon);auto canonical=mon.name(DESC_A)+old__abyss_monster_creation_message(&mon);assert(actual.canonical==canonical);assert(actual.supported&&actual.localized!=canonical);++cases;
 known=false;actual=_abyss_monster_creation_message(&mon);assert(!actual.supported&&actual.localized==canonical);known=true;++cases;
}
mon=monster();monster_info mi(&mon);fire_target_behaviour beh;item_def item,launcher;
for(int type:{0,int(MI_THROWING_NET),int(MI_DART)})for(int brand:{0,int(SPMSL_SILVER),int(SPMSL_FRENZY),int(SPMSL_BLINDING)})for(int mask=0;mask<64;++mask){
 item.subtype=type;item.brand=brand;beh.item=&item;beh.target=mask&1;launcher.ranged=mask&2;beh.action.launcher=mask&4?&launcher:nullptr;mi.flags=mask&8?MB_CHAOTIC:0;mi.immune=mask&16;mi.escape=mask&32;mi.can_go_frenzy=!(mask&16);mi.holi=mask&32?MH_UNDEAD:0;
 auto old=beh.old_get_monster_desc(mi);auto actual=beh.get_monster_desc_messages(mi);assert(old.size()==actual.size());for(size_t i=0;i<old.size();++i)assert(old[i]==actual[i].canonical&&actual[i].supported);++cases;
}
cout<<"PASS: "<<cases<<" actual encounter equipment, species/genus/title, abyss weights/grammar and full-parent fallback cases\n";
}
'''
    code=code.replace("zh_glossary_name(", "test_glossary_name(")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root/'test.cc').write_text(code)
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),
                        str(root/'test.cc'),str(SRC/'zh-message.cc'),
                        str(SRC/'zh-localization.cc'),'-o',str(root/'test')],check=True)
        subprocess.run([str(root/'test')],check=True)


if __name__ == '__main__':
    main()
