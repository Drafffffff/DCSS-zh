#!/usr/bin/env python3
"""Run actual charge parents/target checks, transform safety, and dynamic logs.
Only world/name queries are seams. Canonical oracles reproduce the original
printf expressions, independently of the translated catalog.
"""
import subprocess
import tempfile
from pathlib import Path
from compile_message_ids import ROOT, SRC, compile_catalog


def block(source, needle):
    start = source.index(needle)
    start = source.rfind('\n', 0, start) + 1
    brace = source.index('{', start)
    depth = 0
    for end in range(brace, len(source)):
        if source[end] == '{':
            depth += 1
        elif source[end] == '}':
            depth -= 1
            if not depth:
                return source[start:end + 1]
    raise AssertionError(needle)


compile_catalog()
source = (SRC / 'spl-transloc.cc').read_text()
transform = (SRC / 'transform.cc').read_text()
code = r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
enum {DESC_THE, DESC_YOUR, MSGCH_PROMPT, DNGN_LAVA, ARTP_FRAGILE, SPELL_ELECTRIC_CHARGE};
enum class transformation {none, tree};
struct coord_def {int x=0,y=0;coord_def(int a=0,int b=0):x(a),y(b){}bool origin()const{return !x&&!y;}bool operator==(coord_def b)const{return x==b.x&&y==b.y;}};
struct actor {bool player=true,visible=true,wood=false,aligned=false;coord_def pos()const{return {10,10};}bool can_see(const actor&)const{return visible;}bool is_player()const{return player;}bool is_monster()const{return !player;}const actor*as_monster()const{return this;}bool is_firewood()const{return wood;}};
struct monster:actor {string english,localized;bool known=true,safe=false,test=false,blocked=false;int type=0;ZhArg reason;monster(string e,string z,bool k):english(e),localized(z),known(k){player=false;}string name(int,bool=false)const{return english;}};
vector<monster> monsters;
struct monster_near_iterator {size_t i=0;monster_near_iterator(actor*){}operator bool()const{return i<monsters.size();}void operator++(){++i;}monster*operator->(){return &monsters[i];}monster*operator*(){return &monsters[i];}};
struct item_def {bool curse=false,fragile=false,artefact=false,known=true;string english="your +3 armour",localized="甲";bool cursed()const{return curse;}};
vector<item_def*> equipment;
struct player_equip_set {int marker=1;void unmeld_all_equipment(bool){marker=2;}void meld_equipment(int,bool){marker=3;}vector<item_def*>get_forced_removal_list(bool){return equipment;}};
const monster *beholder=nullptr,*fearmonger=nullptr;
struct Player:actor {const monster*get_beholder(coord_def)const{return beholder;}const monster*get_fearmonger(coord_def)const{return fearmonger;}player_equip_set equipment;transformation form=transformation::none,default_form=transformation::none;}you;
struct Form {int blocked_slots=1;} form;
Form*get_form(transformation){return &form;}
template<typename T>struct unwind_var {T&value;T original;unwind_var(T&v):value(v),original(v){}~unwind_var(){value=original;}};
struct {int terrain=0;int grid(coord_def)const{return terrain;}}env;
bool dangerous=false, passthrough=false;
bool feat_dangerous_for_form(transformation,int){return dangerous;}
bool is_artefact(const item_def&i){return i.artefact;}bool artefact_property(const item_def&i,int){return i.fragile;}
ZhArg zh_item_arg(const string&key,const item_def&i,int){return {key,ZhArgType::Name,i.english,i.known?i.localized:i.english,i.known};}
ZhArg zh_monster_arg(const string&key,const monster&m,int=DESC_THE){return {key,ZhArgType::Name,m.english,m.known?m.localized:m.english,m.known};}
string lowercase_string(string s){transform(s.begin(),s.end(),s.begin(),[](unsigned char c){return tolower(c);});return s;}
bool mons_is_safe(const monster*m,bool){return m->safe;}bool mons_class_is_test(int t){return t==1;}
coord_def get_electric_charge_landing_spot(const actor&,coord_def,string*,ZhArg*);
int spell_range(int,const actor*){return 6;}
int grid_distance(coord_def a,coord_def b){return max(abs(a.x-b.x),abs(a.y-b.y));}
bool adjacent(coord_def a,coord_def b){return grid_distance(a,b)<=1;}
const actor*target_actor=nullptr;const actor*actor_at(coord_def){return target_actor;}
bool fedhas_passthrough(const actor*){return passthrough;}
bool mons_aligned(const actor*a,const actor*){return a->aligned;}
vector<ZhMessage> emitted;vector<int> channels;
void mpr(const ZhMessage&m,int channel=0){emitted.push_back(m);channels.push_back(channel);}
'''
code += block(source, 'static void _charge_failure(') + '\n'
code += block(source, 'bool valid_electric_charge_target(') + '\n'
code += r'''
coord_def get_electric_charge_landing_spot(const actor&,coord_def,string*,ZhArg*out){
 // Parent aggregation sees actual typed child messages, with only landing world
 // query replaced. The target decision function itself is tested separately.
 static size_t cursor=0;
 monster&m=monsters[cursor++%monsters.size()];
 if(m.blocked){*out=m.reason;return {};}
 return {3,3};
}
'''
code += block(source, 'ZhArg electric_charge_impossible_display_reason(') + '\n'
code += r'''
enum {NUM_TRAPS,DESC_PLAIN,opc_solid};
bool ray_exists=true,terrain_bad=false,habitable=true;const monster*stationary_mon=nullptr;
struct ray_def {int step=0;bool advance(){return step++==0;}coord_def pos()const{return {12,10};}};
bool find_ray(coord_def,coord_def,ray_def&,int){return ray_exists;}
bool is_feat_dangerous(int){return terrain_bad;}
bool monster_habitable_grid(const actor*,coord_def){return habitable;}
const monster*monster_at(coord_def){return stationary_mon;}
bool mons_class_is_stationary(int){return true;}
string feature_description_at(coord_def){return "a rock wall";}
string feature_description(int,int,const string&,int){return "rock wall";}
'''
code += block(source, 'coord_def get_electric_charge_landing_spot(').replace(
    'coord_def get_electric_charge_landing_spot(', 'coord_def actual_landing_spot(') + '\n'
code += block(transform, 'bool transforming_is_unsafe(') + '\n'

# These production statement regions remain bound inside the actual spell paths.
start = source.index('    // Select a complete message from the direction')
end = source.index('\n\n    if (you.stasis())', start)
code += 'void gavotte_log(coord_def dir){\n' + source[start:end] + '\n}\n'
start = source.index('    mpr(zh_message(item.quantity > 1 ? "transloc.apport.many"')
end = source.index(';', start) + 1
code += 'void apport_log(int quantity){struct {int quantity;}item{quantity};\n' + source[start:end] + '\n}\n'
code += r'''
int checks=0;
void check(const ZhMessage&m,const string&en,bool known=true){
 if(m.canonical!=en){cerr<<"Canonical drift ["<<m.canonical<<"] != ["<<en<<"]\n";abort();}
 if(known)assert(m.localized!=en);else assert(m.localized==en);
 assert(m.localized.find('{')==string::npos);++checks;
}
void check(const ZhArg&a,const string&en,bool known=true){assert(a.supported==known);check(ZhMessage{"",a.canonical,a.localized},en,known);}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.transloc.remaining");
 check(electric_charge_impossible_display_reason(false),"you can't see anything to charge at.");
 for(string en:{"Sigmund","the Wizard's ghost","the two-headed ogre","something"})for(bool known:{false,true}){
  monsters.clear();monster m(en,"乙",known);m.blocked=true;
  for(string id:{"transloc.charge.reason.blocked","transloc.charge.reason.self","transloc.charge.reason.unseen"}){
   m.reason=zh_message_arg("reason",id);monsters={m};
   check(electric_charge_impossible_display_reason(false),lowercase_string("you can't charge at "+en+" because "+m.reason.canonical),known);
  }
 }
 for(bool known:{false,true}){
  monster blocker("The Wizard's Ghost","己",known);
  monster target("Sigmund","庚",true);target.blocked=true;
  target.reason=zh_message_arg("reason","transloc.charge.reason.stationary",{zh_monster_arg("monster",blocker)});
  monsters={target};
  check(electric_charge_impossible_display_reason(false),"you can't charge at sigmund because the wizard's ghost is immovably fixed in your path.",known);
 }
 for(int count:{1,2,3,12})for(bool blocked:{false,true})for(bool safe:{false,true})for(bool allow:{false,true})for(bool test:{false,true}){
  monsters.clear();for(int i=0;i<count;++i){monster m("the orc","丙",true);m.blocked=blocked;m.safe=safe;m.type=test?1:0;m.reason=zh_message_arg("reason","transloc.charge.reason.blocked");monsters.push_back(m);}
  auto a=electric_charge_impossible_display_reason(allow);
  if(!blocked&&(allow||!safe||test)){assert(a.canonical.empty()&&a.localized.empty());++checks;}
  else if(count==1&&!blocked){assert(a.canonical.empty());++checks;}
  else if(count==1)check(a,"you can't charge at the orc because there's something in the way.");
  else check(a,"there's one issue or another keeping you from charging at any nearby foe.");
 }
 monster victim("the orc","丁",true);target_actor=&victim;
 for(int state=0;state<6;++state){
  actor caster;coord_def target{13,10};victim.aligned=false;victim.wood=false;passthrough=false;
  string expected;
  if(state==0){target={10,10};expected="You can't charge at yourself.";}
  if(state==1){target={11,10};expected="You're already next to there.";}
  if(state==2){target={20,10};expected="That's out of range!";}
  if(state==3){caster.visible=false;expected="You can't see anything there to charge at.";}
  if(state==4){victim.aligned=true;expected="Why would you want to do that?";}
  string english;ZhArg display;bool valid=valid_electric_charge_target(caster,target,&english,&display);
  assert(valid==(state==5));if(!valid){assert(english==expected);check(display,expected);}
 }
 for(int state=0;state<7;++state)for(bool known:{false,true}){
  actor caster;victim.known=known;victim.aligned=false;victim.wood=false;target_actor=&victim;passthrough=false;
  monster blocker("the stationary orc","戊",known);
  ray_exists=state!=0;terrain_bad=state==1;stationary_mon=state==2?&blocker:nullptr;
  beholder=state==3?&blocker:nullptr;fearmonger=state==4?&blocker:nullptr;
  string canonical;ZhArg display;auto landing=actual_landing_spot(caster,{13,10},&canonical,&display);
  const char*expected[]={"There's something in the way.","There's a rock wall in the way.","the stationary orc is immovably fixed in your path.","You cannot charge away from the stationary orc!","You cannot charge closer to the stationary orc!"};
  if(state<5){assert(landing.origin());assert(canonical==expected[state]);check(display,expected[state],state<2||known);}
  else{assert(!landing.origin()&&canonical.empty());++checks;}
 }
 beholder=nullptr;fearmonger=nullptr;stationary_mon=nullptr;
 for(bool ending:{false,true})for(bool lava:{false,true}){
  dangerous=true;env.terrain=lava?DNGN_LAVA:0;emitted.clear();channels.clear();
  assert(transforming_is_unsafe(ending?transformation::none:transformation::tree));
  check(emitted.at(0),string(ending?"Untransforming":"Transforming")+" right now would cause you to "+(lava?"burn":"drown")+"!");assert(channels.at(0)==MSGCH_PROMPT);
 }
 dangerous=false;
 for(bool ending:{false,true})for(bool curse:{false,true})for(bool artefact:{false,true})for(bool fragile:{false,true})for(bool known:{false,true}){
  item_def item;item.curse=curse;item.artefact=artefact;item.fragile=fragile;item.known=known;equipment={&item};emitted.clear();channels.clear();
  auto old_form=you.form,old_default=you.default_form;int old_equipment=you.equipment.marker;
  bool unsafe=transforming_is_unsafe(ending?transformation::none:transformation::tree);
  assert(unsafe==(curse||(artefact&&fragile)));
  assert(you.form==old_form&&you.default_form==old_default&&you.equipment.marker==old_equipment);
  if(unsafe){check(emitted.at(0),string(ending?"Untransforming":"Transforming")+" right now would shatter "+item.english+"!",known);assert(channels.at(0)==MSGCH_PROMPT);}else{assert(emitted.empty());++checks;}
 }
 const char*dirs[]={"northwest","north","northeast","west","???","east","southwest","south","southeast"};
 for(int y=-1;y<=1;++y)for(int x=-1;x<=1;++x){emitted.clear();gavotte_log({x,y});check(emitted.at(0),string("Gravity reorients to the ")+dirs[(y+1)*3+x+1]+"!");}
 for(int n:{1,2,3,12,999}){emitted.clear();apport_log(n);check(emitted.at(0),string("Yoink! You pull the item")+(n>1?"s":"")+" towards yourself.");}
 cout<<"PASS: "<<checks<<" actual translocation/transform production branches, canonical oracles and fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / 'test.cc'
    path.write_text(code)
    exe = Path(tmp) / 'test'
    subprocess.run(['c++', '-std=c++11', '-DZH_STANDALONE', '-I' + str(SRC), str(path),
                    str(SRC / 'zh-localization.cc'), str(SRC / 'zh-message.cc'), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=30)
