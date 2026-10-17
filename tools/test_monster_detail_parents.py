#!/usr/bin/env python3
"""Exercise actual monster-detail parents with independently frozen English."""
import json
import subprocess
import tempfile
from pathlib import Path
from compile_message_ids import SRC, compile_catalog
from test_target_notifications import block


def main():
    compile_catalog()
    source=(SRC/'describe.cc').read_text()
    old=json.loads((Path(__file__).parent/'fixtures/monster-detail-parents-english.json').read_text())
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <sstream>
#include <iostream>
#include <vector>
using namespace std;
using size_type=int;
enum {SIZE_TINY,SIZE_LITTLE,SIZE_SMALL,SIZE_MEDIUM,SIZE_LARGE,SIZE_GIANT,NUM_SIZE_LEVELS};
enum {MONUSE_NOTHING,MONUSE_WEAPON,NUM_MONUSE,PRONOUN_SUBJECTIVE,PRONOUN_POSSESSIVE,DESC_A};
enum {M_CRASH_DOORS=1,M_EAT_DOORS=2};
struct monster_info {int type=0,use=0,flags=0,base_ev=10,ev=10;bool unable=false,human=false,fixed=false,plural=false;string name="an orc warrior";
 bool incapacitated()const{return unable;}int itemuse()const{return use;}const char*pronoun(int p)const{return p==PRONOUN_POSSESSIVE?(plural?"their":"its"):(plural?"they":"it");}string full_name(int)const{return name;}};
const monster_info*current=nullptr;
bool mons_class_is_stationary(int){return current->fixed;}bool mon_shape_is_humanoid(int){return current->human;}int get_mon_shape(int){return 0;}bool mons_class_flag(int,int flag){return current->flags&flag;}
string uppercase_first(string s){if(!s.empty())s[0]=toupper(s[0]);return s;}
[[noreturn]]void die(const char*){abort();}
int child=0;bool known=true;string chance_en,chance_zh;
struct Player {const void*weapon()const{return child?this:nullptr;}}you;
ZhArg describe_to_hit_message(const monster_info&,const void*,bool){return {"chance",ZhArgType::Text,chance_en,chance_zh,known};}
void describe_to_hit(const monster_info&,ostringstream&result,const void*,bool){result<<chance_en;}
ZhArg zh_monster_info_arg(const string&key,const monster_info&mi,int){return {key,ZhArgType::Name,mi.name,known?"兽人战士":mi.name,known};}
ZhArg parent_test_glossary_name(const string&key,const string&,const string&name){return {key,ZhArgType::Name,name,known?"兽人队长":name,known};}
'''
    for query in ['static ZhArg _monster_player_hit_message(',
                  'static ZhArg _monster_detail_size_message(',
                  'static ZhArg _monster_door_message(',
                  'static ZhArg _monster_detail_title_message(']:
        code+=block(source,query).replace('zh_glossary_name(', 'parent_test_glossary_name(')+'\n'
    code+='string old_hit(const monster_info&mi){ostringstream result;'+old['hit_block']+'return result.str();}\n'
    code+='string old_door(const monster_info&mi){ostringstream result;const string pronoun=mi.pronoun(PRONOUN_SUBJECTIVE);'+old['door_block']+'return result.str();}\n'
    code+=r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.monster.detail.parents");monster_info mi;current=&mi;int cases=0;
for(int mask=0;mask<16;++mask)for(const string&chance:{string(),string("about 0% chance to hit with your hands"),string("about 100% chance to hit with your +9 hand axe (range 8)"),string("about 73% chance to hit with your claws and 8% to hit with your bite, kick, and headbutt")}){
 mi.unable=mask&1;mi.ev=mask&2?4:mi.base_ev;child=mask&4;known=mask&8;chance_en=chance;chance_zh=known?"审校过的完整命中率子句":chance;const auto actual=_monster_player_hit_message(mi);assert(actual.canonical==old_hit(mi));assert(actual.supported==known);assert(known?actual.localized!=actual.canonical:actual.localized==actual.canonical);++cases;
}
for(int use:{int(MONUSE_NOTHING),int(MONUSE_WEAPON),int(NUM_MONUSE)})for(int mask=0;mask<64;++mask){
 mi.use=use;mi.fixed=mask&1;mi.human=mask&2;mi.flags=(mask&4?M_CRASH_DOORS:0)|(mask&8?M_EAT_DOORS:0);mi.plural=mask&16;known=true;const auto actual=_monster_door_message(mi);assert(actual.canonical==old_door(mi));assert(actual.supported);if(!actual.canonical.empty())assert(actual.localized!=actual.canonical);++cases;
}
// English labels are frozen from the old get_size_adj presentation expression.
const vector<string> labels={"Tiny","V. Small","Small","Medium","Large","Giant"};
for(int size=0;size<NUM_SIZE_LEVELS;++size){auto actual=_monster_detail_size_message(size);assert(actual.canonical==labels[size]);assert(actual.supported&&actual.localized!=actual.canonical);++cases;}
for(const string&name:{string("an orc warrior"),string("an orc's +2 spectre"),string("a 5-headed hydra")})for(const string&title:{string(),string("The Captain."),string("The \"Hero\"")})for(bool supported:{false,true}){
 mi.name=name;known=supported;const auto actual=_monster_detail_title_message(mi,title);const string expected=title.empty()?uppercase_first(mi.full_name(DESC_A))+".":title;assert(actual.canonical==expected);assert(actual.supported==supported);assert(supported?actual.localized!=actual.canonical:actual.localized==actual.canonical);++cases;
}
cout<<"PASS: "<<cases<<" actual hit/title/size/door parent cases, frozen English parity, typed child support, semantic enum branches and canonical names\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/'test.cc').write_text(code)
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(root/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(root/'test')],check=True)
        subprocess.run([str(root/'test')],check=True)


if __name__=='__main__':
    main()
