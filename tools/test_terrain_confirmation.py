#!/usr/bin/env python3
"""Compare actual shared movement confirmation producers with frozen engine code."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
from test_target_notifications import block


def main():
    compile_catalog()
    fixture=json.loads((Path(__file__).parent/'fixtures/terrain-confirmation-english.json').read_text())
    source=(SRC/'player.cc').read_text()
    spell=(SRC/'spl-other.cc').read_text()
    prompt=(SRC/'prompt.cc').read_text()
    # The normal engine flow uses typed producers; English msg is compatibility only.
    wall=block(spell,'bool passwall_path::check_moveto(')
    assert 'check_moveto_terrain_display(actual_dest, "passwall", warning)' in wall
    assert 'terrain_msg' not in wall
    assert 'confirm_prompt("yes", prompt)' in source
    yesno=block(prompt,'int yesno(const ZhMessage &message,')
    assert 'message.canonical.c_str()' in yesno and '&message' in yesno
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
using cloud_type=int;
enum {DNGN_FLOOR,DNGN_DEEP_WATER,DNGN_LAVA,DNGN_BINDING_SIGIL,DNGN_TOXIC_BOG};
enum {CLOUD_NONE,CLOUD_FIRE,CLOUD_STEAM,CLOUD_MEPHITIC};
enum {TRAP_UNASSIGNED=-1,TRAP_NONE,TRAP_ZOT,TRAP_ALARM,TRAP_PLATE,TRAP_NET};
enum {DUR_NOXIOUS_BOG,DUR_FLIGHT,DIS_CONFIRMATIONS=0,MUT_CONDENSATION_SHIELD,HINT_CLOUD_WARNING,BASELINE_DELAY=10,DESC_BASENAME,MSG_OK,MSG_UNTHINKING_ACT,MSGCH_PROMPT};
struct coord_def {int v;coord_def(int n=0):v(n){}};
bool confused=false,swim=false,air=false,immune=false,clarity=false,condensation=false,likes=false,danger=false,expire_here=false,expire_there=false,expire_flight=false,cloud_damaging=false,cloud_yours=false,trap_safe=false,trap_present=false,answer=true,cancelled=false,harmful=false;
int cloud_here=0,res_steam=0,lessons=0,cancel_calls=0;string input="yes",cloudname="blazing flames",trapname="net trap";
struct knowledge {bool known_=true;int cloud_=0,trap_=0;bool known()const{return known_;}int cloud()const{return cloud_;}int trap()const{return trap_;}};
struct world {int terrain[4]={};knowledge tiles[4];int grid(coord_def p)const{return terrain[p.v];}const knowledge&map_knowledge(coord_def p)const{return tiles[p.v];}}env;
struct Player {int duration[5]={},hp=10,time_taken=10,species=0;coord_def pos()const{return 0;}bool confused()const{return ::confused;}bool can_swim()const{return swim;}bool airborne()const{return air;}bool is_binding_sigil_immune()const{return immune;}bool clarity(bool)const{return ::clarity;}bool has_mutation(int)const{return condensation;}}you;
struct State {bool disables[1]={};}crawl_state;
namespace species {bool likes_water(int){return likes;}}
struct trap_def {int type=TRAP_NONE;bool is_safe()const{return trap_safe;}}trap;
trap_def*trap_at(coord_def){return trap_present?&trap:nullptr;}
bool feat_is_water(int t){return t==DNGN_DEEP_WATER;}bool is_feat_dangerous(int){return danger;}
bool need_expiration_warning(){return expire_here;}bool need_expiration_warning(coord_def){return expire_there;}bool need_expiration_warning(int,coord_def){return expire_flight;}
bool is_damaging_cloud(int,bool,bool){return cloud_damaging;}bool cloud_is_yours_at(coord_def){return cloud_yours;}int cloud_type_at(coord_def){return cloud_here;}int player_res_steam(bool){return res_steam;}string cloud_type_name(int){return cloudname;}
string full_trap_name(int){return trapname;}string feature_description_at(coord_def,bool,int){return trapname;}
bool excluded[4]={},stair_excluded[4]={};bool is_excluded(coord_def p){return excluded[p.v];}bool is_stair_exclusion(coord_def p){return stair_excluded[p.v];}
bool cancel_harmful_move(bool){++cancel_calls;return harmful;}void learned_something_new(int){++lessons;}
struct Record {string canonical,display,require;bool lower;int def;Record(string a,string b,string c,bool d,int e):canonical(a),display(b),require(c),lower(d),def(e){}};vector<Record> records;vector<string> outputs;vector<string> shown;
void mpr(const ZhMessage&m,int=0){outputs.push_back(m.canonical);shown.push_back(m.display());}
void mpr(const string&s){outputs.push_back(s);shown.push_back(s);}
void canned_msg(int n){outputs.push_back("canned:"+to_string(n));shown.push_back(outputs.back());}
template<class...A>string make_stringf(const char*f,A...a){char b[4096];snprintf(b,sizeof b,f,a...);return b;}
template<class...A>void mprf(int,const char*f,A...a){outputs.push_back(make_stringf(f,a...));shown.push_back(outputs.back());}
int cancellable_get_line(char*b,int n){snprintf(b,n,"%s",input.c_str());return cancelled;}
bool yesno(const char*s,bool lower,int def){records.push_back({s,s,"",lower,def});return answer;}
bool yesno(const ZhMessage&m,bool lower,int def){records.push_back({m.canonical,m.display(),"",lower,def});return answer;}

// Header declarations, including unchanged public defaults, are represented in
// the standalone harness so extracted definitions retain actual caller shape.
bool check_moveto_terrain_display(const coord_def&,const string&,const ZhArg&,bool* =nullptr);
bool check_moveto_terrain(const coord_def&,const string&,const string& ="",bool* =nullptr);
bool check_moveto_cloud(const coord_def&,const string& ="step",bool* =nullptr);
bool check_moveto_trap(const coord_def&,const string& ="step",bool* =nullptr);
bool check_moveto_exclusions(const vector<coord_def>&,const string& ="step",bool* =nullptr);
bool check_moveto_exclusion(const coord_def&,const string& ="step",bool* =nullptr);
bool old_check_moveto_terrain(const coord_def&,const string&,const string& ="",bool* =nullptr);
bool old_check_moveto_cloud(const coord_def&,const string& ="step",bool* =nullptr);
bool old_check_moveto_trap(const coord_def&,const string& ="step",bool* =nullptr);
bool old_check_moveto_exclusions(const vector<coord_def>&,const string& ="step",bool* =nullptr);
bool old_check_moveto_exclusion(const coord_def&,const string& ="step",bool* =nullptr);
'''
    # Original typed-answer code is frozen independently of the migrated overload.
    legacy_prompt=block(prompt,'bool confirm_prompt(const char* require, const char* fmt, ...)')
    # Only this legacy function is unchanged; pin its exact content alongside producers.
    expected_old=fixture.get('confirm_prompt')
    if expected_old is not None:assert legacy_prompt==expected_old
    code+=legacy_prompt+'\n'
    code+=block(prompt,'bool confirm_prompt(const char *require, const ZhMessage &prompt)')+'\n'
    funcs=list(fixture['functions'])
    mapping={q.split('(')[0].split()[-1]:'old_'+q.split('(')[0].split()[-1] for q in funcs}
    for text in fixture['functions'].values():
        for name,new in sorted(mapping.items(),key=lambda pair:-len(pair[0])):
            text=re.sub(r'\b'+re.escape(name)+r'\s*\(',new+'(',text)
        code+=text+'\n'
    for query in ['static ZhArg _movement_verb_arg(','static ZhMessage _movement_prompt(','bool check_moveto_cloud(','bool check_moveto_trap(','static bool _check_moveto_dangerous(','static bool _check_moveto_binding_sigil(','bool check_moveto_terrain_display(','bool check_moveto_terrain(','bool check_moveto_exclusions(','bool check_moveto_exclusion(','bool check_moveto(','static bool _check_move_over_terrain(','bool check_move_over(']:
        code+=block(source,query)+'\n'
    code+='struct passwall_path {coord_def actual_dest=1;vector<coord_def> possible_dests()const{return {1,2};}bool check_moveto()const;bool old_check_moveto()const;};\n'
    code+=wall+'\n'
    frozen=fixture['passwall'].replace('passwall_path::check_moveto()', 'passwall_path::old_check_moveto()',1)
    for name,new in mapping.items():
        frozen=re.sub(r'\b'+re.escape(name)+r'\s*\(',new+'(',frozen)
    code+=frozen+'\n'
    code+=r'''
void reset(){env=world();you=Player();crawl_state=State();trap=trap_def();confused=swim=air=immune=clarity=condensation=likes=danger=expire_here=expire_there=expire_flight=cloud_damaging=cloud_yours=trap_safe=trap_present=harmful=cancelled=false;answer=true;cloud_here=res_steam=0;input="yes";cloudname="blazing flames";trapname="net trap";for(int i=0;i<4;++i){excluded[i]=stair_excluded[i]=false;}}
struct Result {bool result,prompted;vector<Record> prompts;vector<string> logs,display;int hints,cancels;};
template<class F>Result run(F f,bool before=false){records.clear();outputs.clear();shown.clear();lessons=cancel_calls=0;bool prompted=before;bool r=f(&prompted);return {r,prompted,records,outputs,shown,lessons,cancel_calls};}
int cases=0;
void compare(const Result&a,const Result&b){
 assert(a.result==b.result&&a.prompted==b.prompted&&a.hints==b.hints&&a.cancels==b.cancels);assert(a.logs==b.logs);assert(a.prompts.size()==b.prompts.size());
 for(size_t i=0;i<a.prompts.size();++i){auto&x=a.prompts[i];auto&y=b.prompts[i];if(x.canonical!=y.canonical){cerr<<x.canonical<<" != "<<y.canonical<<"\n";abort();}assert(x.lower==y.lower&&x.def==y.def);}
 ++cases;
}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.movement.confirmation");
// Every early-return/priority and confirmation-enabled branch on shared terrain.
for(int mask=0;mask<4096;++mask)for(bool accept:{false,true}){
 reset();env.tiles[1].known_=mask&1;swim=mask&2;air=mask&4;danger=mask&8;likes=mask&16;immune=mask&32;you.duration[DUR_NOXIOUS_BOG]=mask&64;expire_here=mask&128;expire_there=mask&256;expire_flight=mask&512;crawl_state.disables[0]=mask&1024;env.terrain[0]=(mask&2048)?DNGN_TOXIC_BOG:DNGN_FLOOR;answer=accept;
 for(int terrain:{DNGN_DEEP_WATER,DNGN_LAVA,DNGN_BINDING_SIGIL,DNGN_TOXIC_BOG}){env.terrain[1]=terrain;
  auto a=run([&](bool*p){return old_check_moveto_terrain(1,"step","",p);});auto b=run([&](bool*p){return check_moveto_terrain_display(1,"step",zh_text("warning","",""),p);});compare(a,b);
  if(!b.prompts.empty())for(auto&x:b.prompts)assert(x.canonical!=x.display);
 }
}
// Canonical compatibility: arbitrary warnings are not fragmented or retranslated.
for(const string&warning:{string(""),string("Foreign warning: +9 dagger (cursed)!"),string("Passwall (unknown extension).")})for(int terrain:{DNGN_DEEP_WATER,DNGN_BINDING_SIGIL,DNGN_TOXIC_BOG})for(bool unsafe:{false,true}){
 reset();env.terrain[1]=terrain;danger=unsafe;compare(run([&](bool*p){return old_check_moveto_terrain(1,"step",warning,p);}),run([&](bool*p){return check_moveto_terrain(1,"step",warning,p);}));
}
// Semantic action labels + complete passwall warning parent, then unknown fallback.
const char*verbs[]={"step","stride","roll","rampage","fly","swim","slither","walk","wriggle","float","hop","blink","charge","leap","line pass","move","transfer","wall jump","passwall","potentially stumble back","a brand new mod action"};
for(const char*verb:verbs)for(const char*id:{"movement.confirm.passwall.water","movement.confirm.passwall.lava"})for(int terrain:{DNGN_BINDING_SIGIL,DNGN_TOXIC_BOG,DNGN_DEEP_WATER,DNGN_LAVA}){
 reset();env.terrain[1]=terrain;expire_there=true;expire_flight=true;auto warning=zh_message_arg("warning",id);
 auto a=run([&](bool*p){return old_check_moveto_terrain(1,verb,warning.canonical,p);});auto b=run([&](bool*p){return check_moveto_terrain_display(1,verb,warning,p);});compare(a,b);
 assert(!b.prompts.empty());for(const auto&x:b.prompts)assert(string(verb)=="a brand new mod action"?x.canonical==x.display:x.canonical!=x.display);
}
// Cloud immunity, current-cloud, steam HP thresholds, clarity and confirmation flag.
for(int mask=0;mask<1024;++mask)for(int cloud:{CLOUD_FIRE,CLOUD_STEAM,CLOUD_MEPHITIC}){
 reset();env.tiles[1].cloud_=cloud;confused=mask&1;cloud_damaging=mask&2;cloud_here=(mask&4)?cloud:CLOUD_NONE;crawl_state.disables[0]=mask&8;condensation=mask&16;clarity=mask&32;answer=mask&64;you.hp=(mask&128)?30:1;you.time_taken=(mask&256)?20:10;res_steam=(mask&512)?-1:0;
 compare(run([&](bool*p){return old_check_moveto_cloud(1,"blink",p);}),run([&](bool*p){return check_moveto_cloud(1,"blink",p);}));
}
// Trap discovery/safety, Zot typed answer, ordinary traps and accepts/cancels.
for(int mask=0;mask<128;++mask)for(int type:{TRAP_ZOT,TRAP_ALARM,TRAP_PLATE,TRAP_NET}){
 reset();env.tiles[1].trap_=(mask&1)?TRAP_NONE:TRAP_UNASSIGNED;trap_present=mask&2;trap_safe=mask&4;crawl_state.disables[0]=mask&8;answer=mask&16;input=(mask&32)?"YES":"no";cancelled=mask&64;trap.type=type;trapname=type==TRAP_ALARM?"alarm trap":type==TRAP_PLATE?"pressure plate":type==TRAP_ZOT?"Zot trap":"net trap";
 compare(run([&](bool*p){return old_check_moveto_trap(1,"hop",p);}),run([&](bool*p){return check_moveto_trap(1,"hop",p);}));
}
// Exclusion certainty, existing/stair exclusions, disabled confirmation and flag.
for(int mask=0;mask<256;++mask){reset();for(int i=0;i<3;++i){excluded[i]=mask&(1<<i);stair_excluded[i]=mask&(1<<(i+3));}crawl_state.disables[0]=mask&64;answer=mask&128;vector<coord_def> areas={1,2};for(bool flag:{false,true})compare(run([&](bool*p){return old_check_moveto_exclusions(areas,"charge",p);},flag),run([&](bool*p){return check_moveto_exclusions(areas,"charge",p);},flag));}
// Complete flow ordering: harmful movement, terrain, clouds, traps, exclusions.
for(int mask=0;mask<128;++mask){reset();harmful=mask&1;env.terrain[1]=(mask&2)?DNGN_BINDING_SIGIL:DNGN_FLOOR;env.tiles[1].cloud_=CLOUD_FIRE;cloud_damaging=mask&4;trap_present=mask&8;trap.type=TRAP_ALARM;excluded[1]=mask&16;answer=mask&32;bool physically=mask&64;
 compare(run([&](bool*){return old_check_moveto(1,"walk",physically);}),run([&](bool*){return check_moveto(1,"walk",physically);}));
 compare(run([&](bool*){return old_check_move_over(1,"walk");}),run([&](bool*){return check_move_over(1,"walk");}));
}
// Passwall uses the same typed chain, preserving uncertain destination exclusion
// confirmation, hidden terrain order, cancellation and all actual engine guards.
for(int mask=0;mask<1024;++mask){reset();env.tiles[1].known_=mask&1;env.terrain[1]=(mask&2)?DNGN_DEEP_WATER:DNGN_LAVA;swim=mask&4;air=mask&8;danger=mask&16;expire_there=mask&32;expire_flight=mask&64;excluded[1]=mask&128;excluded[2]=mask&256;answer=mask&512;passwall_path path;
 compare(run([&](bool*){return path.old_check_moveto();}),run([&](bool*){return path.check_moveto();}));
}
// Unknown display names trigger full-sentence fallback, without English/Chinese mixing.
reset();cloud_damaging=true;env.tiles[1].cloud_=CLOUD_FIRE;cloudname="not-a-catalog-cloud +9";auto cloudrun=run([&](bool*p){return check_moveto_cloud(1,"walk",p);});assert(cloudrun.prompts.size()==1&&cloudrun.prompts[0].canonical==cloudrun.prompts[0].display);++cases;
reset();trap_present=true;trap.type=TRAP_NET;trapname="not-a-catalog-trap +9";auto traprun=run([&](bool*p){return check_moveto_trap(1,"walk",p);});assert(traprun.prompts.size()==1&&traprun.prompts[0].canonical==traprun.prompts[0].display);++cases;
// New typed input path accepts canonical yes only; the entire multibyte prompt survives.
reset();string longtext;for(int n=0;n<200;++n)longtext+="中文";ZhMessage longprompt{"test.long","Long canonical prompt?",longtext};
for(const string&value:{string("yes"),string("YES"),string("no"),string("是")})for(bool abort_input:{false,true}){input=value;cancelled=abort_input;outputs.clear();shown.clear();bool ok=confirm_prompt("yes",longprompt);assert(ok==(!abort_input&&(value=="yes"||value=="YES")));assert(shown.size()==1&&shown[0].find(longtext)==0);assert(shown[0].find("yes")!=string::npos);assert(outputs[0]=="Long canonical prompt? (Confirm with \"yes\".) ");++cases;}
cout<<"PASS: "<<cases<<" real terrain/cloud/trap/exclusion confirmations, canonical Lua prompts, branch priority, acceptance, flags, typed passwall warnings and UTF-8 input prompt\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp);(p/'test.cc').write_text(code)
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
        subprocess.run([str(p/'test')],check=True,timeout=180)


if __name__=='__main__':main()
