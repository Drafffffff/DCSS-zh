#!/usr/bin/env python3
"""Test real first-monster hint producers and state changes against frozen code."""
import json
import subprocess
import tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
from test_target_notifications import block


def main():
    compile_catalog()
    source=(SRC/'hints.cc').read_text()
    old=json.loads((Path(__file__).parent/'fixtures/first-encounter-hints-english.json').read_text())['function']
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdio>
#include <algorithm>
#include <sstream>
#include <iostream>
#include <vector>
using namespace std;
enum {HINT_SEEN_ZERO_EXP_MON,HINT_SEEN_MONSTER,HINT_MONSTER_FRIENDLY,HINT_CAN_BERSERK,HINT_MONSTER_UNUSUAL,EVENT_COUNT};
enum {GOD_TROG,DESC_A,HINT_RANGER_CHAR,HINT_MAGIC_CHAR,HINT_BERSERK_CHAR,OBJ_WEAPONS,WPN_SHORTBOW,MSGCH_TUTORIAL,CURSOR_TUTORIAL,TAG_TUTORIAL};
using command_type=int;enum {CMD_LOOK_AROUND,CMD_SHOUT};
struct coord_def {int x=0;};
struct item_def {int base_type=OBJ_WEAPONS,sub_type=WPN_SHORTBOW;};
struct Player {bool trog=false,berserk=false;item_def item;bool wielded=false;const item_def*weapon()const{return wielded?&item:nullptr;}bool can_go_berserk()const{return berserk;}}you;
bool you_worship(int){return you.trog;}
bool tiles_mode=false,random_result=false,known=true;
bool is_tiles(){return tiles_mode;}
int stops=0,random_calls=0,cursors=0,tags=0;vector<int>learned;vector<string>canonical,localized;
void stop_running(){++stops;}bool one_chance_in(int){++random_calls;return random_result;}
void learned_something_new(int event,coord_def=coord_def()){learned.push_back(event);}
struct HintsState {bool hints_events[EVENT_COUNT];bool hints_just_triggered=false;int hints_type=HINT_BERSERK_CHAR;}Hints;
struct {struct{int y=0;}mlistsz;}crawl_view;
struct monster {bool wood=false,friendly_flag=false,unusual=false;string label="an orc";bool is_firewood()const{return wood;}bool friendly()const{return friendly_flag;}coord_def pos()const{return {};}string name(int)const{return label;}};
struct monster_info {const monster*mon;monster_info(const monster*m):mon(m){}bool has_unusual_items()const{return mon->unusual;}};
struct Tiles {void place_cursor(int,coord_def){++cursors;}void add_text_tag(int,const monster_info&){++tags;}void add_text_tag(int,const string&,coord_def,bool=false){++tags;}}tiles;
struct cglyph_t {char32_t ch='o';int col=0;};cglyph_t current_glyph;
cglyph_t get_mons_glyph(const monster_info&){return current_glyph;}
string colour_to_str(int n){return n?"lightgrey":"brown";}
string stringize_glyph(char32_t c){return c=='<'?"<":c==U'兽'?"兽":string(1,char(c));}
string glyph_to_tagstr(const cglyph_t&g){string v=stringize_glyph(g.ch);if(g.ch=='<')v+="<";string c=colour_to_str(g.col);return "<"+c+">"+v+"</"+c+">";}
string replace_all(string s,const string&a,const string&b){size_t pos=0;while((pos=s.find(a,pos))!=string::npos){s.replace(pos,a.size(),b);pos+=b.size();}return s;}
string command_to_string(int c){return c==CMD_LOOK_AROUND?"x":"t";}
[[noreturn]]void die(const char*){abort();}
ZhArg zh_monster_arg(const string&key,const monster&m,int){return {key,ZhArgType::Name,m.label,known?"已审校怪物名":m.label,known};}
string zh_monster_display(const monster&m,int){return known?"已审校怪物名":m.label;}
void mprf(int ch,const char*,const char*message){assert(ch==MSGCH_TUTORIAL);canonical.push_back(message);}
void mpr(const ZhMessage&message,int ch){assert(ch==MSGCH_TUTORIAL);canonical.push_back(message.canonical);localized.push_back(message.localized);}
'''
    lib=(SRC/'libutil.cc').read_text()
    code+=block(lib,'static void inline _untag(')+'\n'+block(lib,'string untag_tiles_console(')+'\n'
    for query in ['static ZhMessage _prepare_encounter_hint(',
                  'static ZhArg _encounter_hint_key(',
                  'static ZhArg _encounter_monster_glyph(',
                  'static ZhMessage _encounter_database_hint_message(',
                  'static ZhMessage _first_monster_hint_message(',
                  'static ZhMessage _first_monster_followup_message(']:
        code+=block(source,query)+'\n'
    code+=old.replace('void hints_monster_seen(', 'void old_hints_monster_seen(',1)+'\n'
    code+=block(source,'void hints_monster_seen(')+'\n'
    code+=r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.hints.first_encounter");int cases=0;monster mon;
for(int mask=0;mask<512;++mask)for(int job:{int(HINT_BERSERK_CHAR),int(HINT_MAGIC_CHAR),int(HINT_RANGER_CHAR)})for(int weapon=0;weapon<4;++weapon){
 tiles_mode=mask&1;crawl_view.mlistsz.y=mask&2;mon.wood=mask&4;mon.friendly_flag=mask&8;mon.unusual=mask&16;HintsState initial;fill(begin(initial.hints_events),end(initial.hints_events),true);initial.hints_events[HINT_SEEN_MONSTER]=!(mask&32);initial.hints_events[HINT_SEEN_ZERO_EXP_MON]=!(mask&64);initial.hints_just_triggered=mask&128;initial.hints_type=job;you.trog=mask&256;you.berserk=!(mask&128);random_result=mask&64;you.wielded=weapon!=0;you.item.base_type=weapon==2?999:OBJ_WEAPONS;you.item.sub_type=weapon==3?999:WPN_SHORTBOW;
 Hints=initial;canonical.clear();localized.clear();learned.clear();stops=random_calls=cursors=tags=0;old_hints_monster_seen(mon);auto expected=canonical;auto expected_learned=learned;auto expected_hints=Hints;const int expected_stops=stops,expected_random=random_calls,expected_cursors=cursors,expected_tags=tags;
 Hints=initial;canonical.clear();localized.clear();learned.clear();stops=random_calls=cursors=tags=0;hints_monster_seen(mon);
 if(canonical!=expected){cerr<<"Mismatch mask "<<mask<<" job "<<job<<" weapon "<<weapon<<"\n";for(auto&m:expected)cerr<<"OLD:"<<m<<"\n";for(auto&m:canonical)cerr<<"NEW:"<<m<<"\n";abort();}
 assert(learned==expected_learned&&stops==expected_stops&&random_calls==expected_random&&cursors==expected_cursors&&tags==expected_tags);assert(equal(begin(Hints.hints_events),end(Hints.hints_events),begin(expected_hints.hints_events)));assert(Hints.hints_just_triggered==expected_hints.hints_just_triggered);assert(localized.size()==canonical.size());for(size_t i=0;i<localized.size();++i)assert(localized[i]!=canonical[i]);++cases;
}
// Real glyph producer preserves colour, '<' escaping and Unicode as structure.
for(char32_t glyph:{U'o',U'<',U'兽'})for(int colour:{0,1}){current_glyph.ch=glyph;current_glyph.col=colour;monster_info info(&mon);auto arg=_encounter_monster_glyph(info);assert(arg.supported&&arg.canonical==glyph_to_tagstr(current_glyph)&&arg.localized==arg.canonical);++cases;}
// Unknown names cause a complete first popup fallback, never mixed prose.
tiles_mode=true;known=false;monster_info info(&mon);auto unknown=_first_monster_hint_message(mon,info);assert(unknown.localized==unknown.canonical);known=true;
for(const char*key:{"HINT_MONSTER_UNUSUAL","HINT_MONSTER_FRIENDLY","HINT_TEMPORARILY_FRIENDLY","HINT_MONSTER_SHOUTED_UNSEEN","HINT_MONSTER_SHOUTED_SEEN","HINT_MONSTER_NO_SHOUT"}){auto message=_encounter_database_hint_message(key);assert(!message.canonical.empty()&&message.localized!=message.canonical);assert(message.localized.find("$cmd[")==string::npos);++cases;}
cout<<"PASS: "<<cases<<" actual first encounter hint cases, canonical full-function parity, tutorial flags, RNG calls, channels, Tiles/console markup and semantic glyph/name/key arguments\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/'test.cc').write_text(code)
        for variant,flags in [('console',[]),('localtiles',['-DUSE_TILE','-DUSE_TILE_LOCAL'])]:
            subprocess.run(['c++','-std=c++11','-DZH_STANDALONE',*flags,'-I'+str(SRC),str(root/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(root/variant)],check=True)
            subprocess.run([str(root/variant)],check=True,timeout=180)


if __name__=='__main__':main()
