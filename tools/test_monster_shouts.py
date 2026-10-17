#!/usr/bin/env python3
"""Run real monster_shout control paths and source bindings against frozen code."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
from test_target_notifications import block


def test_database_protocol():
    source=(SRC/'database.cc').read_text()
    code=r'''
#include "zh-localization.h"
#include <string>
#include <map>
#include <vector>
#include <cassert>
#include <cctype>
#include <iostream>
using namespace std;
struct DBM {map<string,string> rows;};
struct TextDB {DBM data;TextDB *translation=nullptr; DBM*get(){return &data;}} ShoutDB;
struct datum {const void*dptr=nullptr;int dsize=0;};
datum _database_fetch(DBM*db,const string&key){auto i=db->rows.find(key);if(i==db->rows.end())return {};return {i->second.data(),int(i->second.size())};}
void lowercase(string&s){for(char&c:s)c=tolower(c);}
int choices=0;
// Weighted selection is an engine RNG seam: assert the selected raw DB entry.
string _chooseStrByWeight(const string&s,int){++choices;return s;}
#define MAX_RECURSION_DEPTH 10
#define MAX_REPLACEMENTS 100
#define MSGCH_DIAGNOSTICS 0
void mprf(int,const char*){assert(false);}
'''
    code+=block(source,'static string _getWeightedString(')+'\n'
    code+='static void _call_recursive_replacement(string&, TextDB&, const string&, int&, int = 0);\n'
    code+=block(source,'static string _getRandomisedStr(')+'\n'
    # The first occurrence is a forward declaration; skip it for extraction.
    begin=source.index('static void _call_recursive_replacement(string &str',source.index('static string _getRandomisedStr('))
    code+=block(source[begin:],'static void _call_recursive_replacement(')+'\n'
    code+=block(source,'string getShoutString(')+'\n'
    code+=block(source,'string getShoutStringCanonical(')+'\n'
    code+=r'''
int main(){setenv("DCSS_LANG","zh",1);TextDB translated;ShoutDB.translation=&translated;
ShoutDB.data.rows={{"orc seen","@The_monster@ shouts!"},{"wolf","You hear a howl!"},{"recursive","@leaf@"},{"leaf","@The_monster@ quivers."},{"control","__NEXT"}};
translated.data.rows={{"orc seen","@The_monster@在喊叫！"},{"wolf","你听到狼嚎！"},{"recursive","@leaf@"},{"leaf","@The_monster@颤抖。"},{"control","__NONE"}};
assert(getShoutString("ORC"," seen")=="@The_monster@在喊叫！");
assert(getShoutStringCanonical("ORC"," seen")=="@The_monster@ shouts!");
assert(getShoutStringCanonical("WOLF"," unseen")=="You hear a howl!");
assert(getShoutString("WOLF"," unseen")=="你听到狼嚎！");
assert(getShoutStringCanonical("recursive","")=="@The_monster@ quivers.");
assert(getShoutString("recursive","")=="@The_monster@颤抖。");
assert(getShoutStringCanonical("control","")=="__NEXT");
assert(getShoutString("control","")=="__NONE");
assert(!zh_translation_paused());assert(getShoutStringCanonical("missing","").empty());
cout<<"PASS: real weighted translated DB, suffix fallback, recursive references, control strings and legacy caller isolation\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/'db.cc').write_text(code)
        subprocess.run(['c++','-std=c++14','-DZH_STANDALONE','-I'+str(SRC),str(root/'db.cc'),str(SRC/'zh-localization.cc'),'-o',str(root/'db')],check=True)
        subprocess.run([str(root/'db')],check=True)


def main():
    compile_catalog()
    test_database_protocol()
    source=(SRC/'shout.cc').read_text()
    fixture=json.loads((Path(__file__).parent/'fixtures/monster-shout-english.json').read_text())
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cctype>
#include <map>
#include <sstream>
#include <iostream>
#include <vector>
#include <tuple>
using namespace std;
using msg_channel_type=int;
enum {MSGCH_SOUND,MSGCH_DIAGNOSTICS,MSGCH_TALK,MSGCH_TALK_VISUAL,MSGCH_WARN,MSGCH_MONSTER_SPELL,MSGCH_MONSTER_ENCHANT};
enum {MONS_PLAYER_GHOST=1,ATT_FRIENDLY=1,DESC_YOUR=2,DESC_THE=3,PRONOUN_POSSESSIVE=4,HINT_MONSTER_SHOUT=5};
struct monster {int type=0,attitude=0,mid=99;bool seen=true,plural=false;string label="the orc";int pos()const{return 42;}const char*pronoun(int)const{return plural?"their":"its";}};
struct {bool can_see(const monster&m)const{return m.seen;}int pos()const{return 0;}}you;
bool silence=false,hints=true,arena=false,heard=true,known=true;int replacements=0,random_calls=0,noises=0;vector<int> learned,noise_args;
struct {bool game_is_hints()const{return hints;}bool game_is_arena()const{return arena;}}crawl_state;
struct mon_acting {mon_acting(monster*){}};
vector<pair<int,string>>lines;vector<string>translated;
struct Stream {int channel;string text;template<class T>Stream&operator<<(const T&value){ostringstream out;out<<value;text+=out.str();return *this;}Stream&operator<<(ostream&(*)(ostream&)){lines.emplace_back(channel,text);text.clear();return *this;}};
namespace msg {map<int,Stream>streams_by_channel;Stream&streams(int c){auto&s=streams_by_channel[c];s.channel=c;return s;}}
void mpr(const ZhMessage&m,int channel){lines.emplace_back(channel,m.canonical);translated.push_back(m.localized);}
void learned_something_new(int hint,int){learned.push_back(hint);}
bool silenced(int){return silence;}
bool mons_is_unique(int type){return type==99;}
string apostrophise(const string&s){return s+((!s.empty()&&s.back()=='s')?"'":"'s");}
string replace_all(string s,const string&a,const string&b){size_t pos=0;while((pos=s.find(a,pos))!=string::npos){s.replace(pos,a.size(),b);pos+=b.size();}return s;}
string canonical_name(const monster&m){return m.attitude==ATT_FRIENDLY&&!mons_is_unique(m.type)&&!arena&&m.seen?"your "+m.label:m.label;}
ZhArg zh_monster_arg(const string&key,const monster&m,int){auto name=canonical_name(m);return {key,ZhArgType::Name,name,known?"审校后的怪物名":name,known};}
[[noreturn]]void die(const char*){abort();}
vector<string> db_queue;size_t db_pos=0;vector<pair<string,string>>db_calls;
string getShoutStringCanonical(const string&key,const string&suffix){db_calls.emplace_back(key,suffix);return db_pos<db_queue.size()?db_queue[db_pos++]:"";}
string _shout_key(const monster&){return "test actor";}
char mons_base_char(int){return 'O';}bool isaupper(char c){return c>='A'&&c<='Z';}
template<class K,class V>V lookup(const map<K,V>&m,const K&key,const V&fallback){auto i=m.find(key);return i==m.end()?fallback:i->second;}
template<class K>string lookup(const map<K,string>&m,const K&key,const char*fallback){return lookup(m,key,string(fallback));}
void lowercase(string&s){for(char&c:s)c=tolower(c);}
int str_to_channel(const string&s){return s=="talk"?MSGCH_TALK:-1;}
'''
    code+=block((SRC/'mon-enum.h').read_text(),'enum shout_type')+';\n'
    code+=r'''
shout_type mons_shouts(int,bool){++random_calls;return S_ROAR;}
int get_shout_noise_level(int type){return type+3;}
bool noisy(int level,int pos,int mid){++noises;noise_args={level,pos,mid};return heard;}
string do_mon_str_replacements(string text,const monster&m,int){++replacements;if(text.find("@imp_taunt@")!=string::npos){++random_calls;text=replace_all(text,"@imp_taunt@","an untranslatable extension insult");}if(text.find("@demon_taunt@")!=string::npos){++random_calls;text=replace_all(text,"@demon_taunt@","an untranslatable demon insult");}text=replace_all(text,"@The_monster@",canonical_name(m));text=replace_all(text,"@The_monster_possessive@",apostrophise(canonical_name(m)));text=replace_all(text,"@possessive@",m.pronoun(PRONOUN_POSSESSIVE));return text;}
'''
    code+=block((SRC/'message.cc').read_text(),'bool strip_channel_prefix(').replace('bool silence)','bool silence = false)')+'\n'
    start=source.index('static const map<shout_type, string> default_msg_keys =');end=source.index('\n};',start)+3
    code+=source[start:end]+'\n'
    code+=block(source,'static ZhMessage _monster_shout_message(')+'\n'
    code+='string getShoutString(const string&key,const string&suffix){return getShoutStringCanonical(key,suffix);}'+'\n'
    code+=fixture['function'].replace('void monster_shout(', 'void old_monster_shout(',1)+'\n'
    code+=block(source,'void monster_shout(')+'\n'
    code+='const vector<string> fixed_sources={'+','.join(json.dumps(v['raw']) for v in fixture['fixed_sources'])+'};\n'
    code+=r'''
void reset(){lines.clear();translated.clear();learned.clear();noise_args.clear();db_calls.clear();db_pos=0;replacements=random_calls=noises=0;for(auto&entry:msg::streams_by_channel)entry.second.text.clear();}
int checks=0;
void compare(monster&mon,int kind,const vector<string>&database){
 db_queue=database;reset();old_monster_shout(mon,kind);const auto expected=lines;const auto exp_learned=learned,exp_noise_args=noise_args;const auto exp_calls=db_calls;const int exp_replacements=replacements,exp_random=random_calls,exp_noises=noises;
 reset();monster_shout(mon,kind);assert(lines==expected&&learned==exp_learned&&noise_args==exp_noise_args&&db_calls==exp_calls&&replacements==exp_replacements&&random_calls==exp_random&&noises==exp_noises);++checks;
}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.monster.shout");monster mon;
for(const string&source:fixed_sources)for(int mask=0;mask<64;++mask)for(const string&name:{string("the orc"),string("the 5-headed hydra's shadow"),string("the +9 extension (a,b; 兽)")}){
 mon.label=name;mon.seen=mask&1;silence=mask&2;hints=mask&4;heard=mask&8;mon.attitude=mask&16?ATT_FRIENDLY:0;mon.plural=mask&32;arena=mask&32;known=true;
 compare(mon,S_SHOUT,{string(mask&16?"VISUAL:":"SOUND:")+source});
}
// Every original DB fallback/control branch, silence and visual gating,
// including RNG-consuming demon verbosity and explicitly unmigrated taunts.
for(int kind:{int(S_SILENT),int(S_SHOUT),int(S_DEMON_TAUNT),int(S_CHERUB),int(S_RANDOM)})for(int mask=0;mask<32;++mask){
 mon.seen=mask&1;silence=mask&2;hints=mask&4;heard=mask&8;mon.type=mask&16?MONS_PLAYER_GHOST:0;
 for(const vector<string>&chain:vector<vector<string>>{{"__DEFAULT","SOUND:You hear a shout!"},{"__NEXT","SOUND:You hear a shout!"},{"","","SOUND:You hear a shout!"},{"__NONE"},{""},{"VISUAL:@The_monster@ quivers."},{"@The_monster@ @says@, \"@demon_taunt@\""},{"SOUND:@The_monster@ @says@, \"@imp_taunt@\""}})compare(mon,kind,chain);
}
mon.label="unknown extension actor";mon.seen=true;known=false;auto unknown=_monster_shout_message("@The_monster@ shouts!","unknown extension actor shouts!",mon);assert(unknown.localized==unknown.canonical);++checks;
// Source lookup must precede parameter substitution: a rendered sentence is
// deliberately unsupported even when it superficially resembles a known one.
known=true;auto rendered=_monster_shout_message("the orc shouts!","the orc shouts!",mon);assert(rendered.localized==rendered.canonical);++checks;
cout<<"PASS: "<<checks<<" actual monster_shout and source-template cases, frozen canonical/visibility/channel/DB-control/noise/RNG parity, explicit whole-parent fallback\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/'test.cc').write_text(code)
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(root/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(root/'test')],check=True)
        subprocess.run([str(root/'test')],check=True,timeout=180)


if __name__=='__main__':main()
