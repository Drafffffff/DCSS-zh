#!/usr/bin/env python3
"""Execute real semantic speech argument producer with actor/world seams."""
import subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC
from test_speech_protocol import block
code=r'''
#include "zh-speech.h"
#include <cassert>
#include <cctype>
#include <iostream>
using namespace std;
enum {DESC_THE,DESC_YOUR,DESC_PLAIN,ATT_FRIENDLY,GOD_NO_GOD,GOD_NAMELESS};
struct monster;
struct actor {bool player=false;int god=GOD_NO_GOD;bool is_player()const{return player;}int deity()const{return god;}const monster*as_monster()const;};
struct monster:actor {int attitude=0,type=1,foe=1;const actor*enemy=nullptr;bool wont_attack()const{return attitude==ATT_FRIENDLY;}const actor*get_foe()const{return enemy;}};
const monster*actor::as_monster()const{return static_cast<const monster*>(this);}
struct:actor {string your_name="A +9 name's 兽";int species=1;}you;
struct{bool game_is_arena()const{return false;}}crawl_state;
bool mons_is_unique(int t){return t==99;}
bool invalid_monster_index(int i){return i<0;}
void lowercase(string&s){for(char&c:s)c=tolower(c);}
namespace species {enum name_type{SPNAME_PLAIN,SPNAME_GENUS};string name(int,name_type=SPNAME_PLAIN){return "human";}}
int mons_species(int t){return t;}int mons_genus(int t){return t;}
string mons_type_name(int,int){return "orc";}
string god_name(int){return "Zin";}
ZhArg zh_monster_arg(const string&key,const monster&,int desc){return {key,ZhArgType::Name,"the orc",desc==DESC_YOUR?"你的兽人":"兽人"};}
ZhArg zh_actor_arg(const string&key,const actor*,int){return {key,ZhArgType::Name,"the rat","老鼠"};}
'''
code+=block((SRC/'mon-util.cc').read_text(),'ZhArg zh_speech_actor_arg(')+'\n'
code+=r'''
int main(){setenv("DCSS_LANG","zh",1);monster mon,foe;you.player=true;mon.enemy=&you;ZhSpeechFacts facts;int cases=0;
for(const string&tag:{string("The_monster"),string("the_something"),string("the_monster_possessive")})for(int ally=0;ally<2;++ally){
 mon.attitude=ally?ATT_FRIENDLY:0;facts.values["@"+tag+"@"]="forged assembled English";auto a=zh_speech_actor_arg("value",tag,mon,facts);assert(a.supported&&a.localized.find(ally?"你的兽人":"兽人")==0);++cases;
}
auto name=zh_speech_actor_arg("value","player_name",mon,facts);assert(name.supported&&name.canonical==you.your_name&&name.localized==you.your_name);++cases;
for(const string&tag:{string("foe"),string("foe_possessive"),string("foe,")}){auto a=zh_speech_actor_arg("value",tag,mon,facts);assert(a.supported&&a.localized.find("你")==0);++cases;}
mon.enemy=&foe;
for(const string&tag:{string("foe"),string("foe_possessive"),string("to_foe"),string("at_foe")}){auto a=zh_speech_actor_arg("value",tag,mon,facts);assert(a.supported&&a.localized.find("老鼠")!=string::npos);++cases;}
for(const string&tag:{string("player_only"),string("CAPS"),string("NOCAPS")}){auto a=zh_speech_actor_arg("value",tag,mon,facts);assert(a.supported&&a.localized.empty());++cases;}
for(const string&sound:{string("shouts"),string("hisses"),string("whispers"),string("roars")}){facts.values["@says@"]=sound;auto a=zh_speech_actor_arg("value","says",mon,facts);assert(a.supported&&a.localized!=sound);++cases;}
for(const string&tag:{string("player_genus"),string("player_genus_plural"),string("foe_genus_plural")}){auto a=zh_speech_actor_arg("value",tag,mon,facts);assert(a.supported&&a.localized.find('@')==string::npos);++cases;}
auto unknown=zh_speech_actor_arg("value","new_extension",mon,facts);assert(!unknown.supported);++cases;
cout<<"PASS: "<<cases<<" actual speech semantic arguments, player/foe/friendly/possessive/genus/sound/control/custom-name/unknown paths\n";}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++14','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
