#!/usr/bin/env python3
"""Compare real spell/talisman restriction producers to frozen canonical code.
Only world queries and already-tested child restriction producers are seams.
The portable fixture is frozen from native aa75645, before this migration.
"""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(s,needle):
    p=s.index(needle);begin=s.rfind('\n',0,p)+1;brace=s.index('{',p);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[begin:end+1]
    raise AssertionError(needle)

compile_catalog()
refs=json.loads((ROOT/'tools/fixtures/spell-talisman-reasons-english.json').read_text())
files={f:(SRC/f).read_text() for f in refs}
old='\n'.join(sum(refs.values(),[]))
symbols=sorted(set(re.findall(r'\b(?:SPELL|DUR|MUT|UNRAND|BRANCH|LSTATE|SLOT|MONS|GRAVE|PARAGON|OBJ|TALISMAN|SK|GOD)_[A-Z_]+\b',old)))
spells=sorted(s for s in symbols if s.startswith('SPELL_'))
fixed_reasons=set()
for match in re.finditer(r'return\s+((?:"(?:[^"\\]|\\.)*"\s*)+);',old):
    text=''.join(json.loads(literal) for literal in re.findall(r'"(?:[^"\\]|\\.)*"',match[1]))
    if text:fixed_reasons.add(text)
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
#include <vector>
using namespace std;
#define ASSERT assert
const int FASTEST_PLAYER_MOVE_SPEED=6, UNUSABLE_SKILL=-99;
'''
code+='enum {'+','.join(symbols)+',SPELL_TEST_UNKNOWN};\nusing spell_type=int;\n'
code+=r'''
enum class transformation {none,walking_scroll,hive,tree,flux};
enum class passive_t {goldify_corpses,reaping};
namespace spschool {const int summoning=1;}
enum class spret {success,abort};
struct Prop {int n=0;int get_int()const{return n;}};
struct Props {bool paragon=true;Prop charge;bool exists(int)const{return paragon;}Prop operator[](int)const{return charge;}};
struct item_def {int base_type=OBJ_TALISMANS,sub_type=0;};
struct monster {};monster mon;
struct World {
 bool bounds=true,hostile=false,hp=true,mp=true,banned=false,no_grasp=false,hp_cast=false,allies=false;
 bool stasis=false,move=true,undead=false,blood=true,salamander=false,gateway=true,gateway_room=true,forest_room=true;
 bool wall=true,constricted=false,gold=false,reap=false,gauntlet=false,armour_allowed=true,armour=true,pile=true,sigil=true;
 bool diamond=true,stationary=false,habitable=true,croc=false,paragon_deployed=false,paragon_charged=true,oka=false,nolove=false;
 int movement=10,aptitude=0;double skill=8;transformation talisman_form=transformation::none;
 ZhArg tele={"reason",ZhArgType::Text,"","",true};
 ZhArg electric={"reason",ZhArgType::Text,"","",true};
 ZhArg transform={"reason",ZhArgType::Text,"","",true};
} world;
struct Player {
 int duration[1024]={};int experience_level=27,magic_points=8,max_magic_points=10,hp=40,hp_max=50,current_vision=8;
 bool on_current_level=true;transformation form=transformation::none,default_form=transformation::none;Props props;
 int pos()const{return 0;}bool has_mutation(int m)const{return m==MUT_HP_CASTING?world.hp_cast:world.no_grasp;}
 bool allies_forbidden()const{return world.allies;}bool stasis()const{return world.stasis;}
 bool no_tele(bool)const{return !world.tele.canonical.empty();}string no_tele_reason(bool)const{return world.tele.canonical;}
 ZhArg no_tele_display_reason(bool)const{return world.tele;}
 bool cannot_move()const{return !world.move;}bool undead_state(bool)const{return world.undead;}
 bool unrand_equipped(int)const{return world.salamander;}bool has_blood(bool)const{return world.blood;}
 bool is_constricted()const{return world.constricted;}bool body_armour()const{return world.armour;}
 bool is_stationary()const{return world.stationary;}double skill(int)const{return world.skill;}
 int get_mutation_level(int)const{return world.nolove;}
}you;
struct {int level_state=0;int grid(int)const{return world.wall;}}env;
struct adjacent_iterator {int i=0;adjacent_iterator(int){}operator bool()const{return i<8;}void operator++(){++i;}int operator*()const{return i;}};
bool in_bounds(int){return world.bounds;}
int spell_difficulty(int){return 5;}int spell_mana(int){return 3;}
bool enough_hp(int,bool,bool){return world.hp;}bool enough_mp(int,bool,bool){return world.mp;}
int get_spell_disciplines(int s){return s==SPELL_TEST_UNKNOWN?spschool::summoning:0;}
bool cannot_use_schools(int){return world.banned;}bool spell_no_hostile_in_range(int){return world.hostile;}
int player_movement_speed(bool){return world.movement;}
bool can_cast_malign_gateway(){return world.gateway;}
spret cast_malign_gateway(Player*,int,bool,bool){return world.gateway_room?spret::success:spret::abort;}
spret cast_summon_forest(Player*,int,bool,bool){return world.forest_room?spret::success:spret::abort;}
bool passwall_simplified_check(Player&){return world.wall;}
bool have_passive(passive_t p){return p==passive_t::goldify_corpses?world.gold:world.reap;}
bool player_in_branch(int){return world.gauntlet;}bool you_can_wear(int,bool){return world.armour_allowed;}
bool piledriver_target_exists(){return world.pile;}
string electric_charge_impossible_reason(bool){return world.electric.canonical;}
ZhArg electric_charge_impossible_display_reason(bool){return world.electric;}
spret cast_sigil_of_binding(int,bool,bool){return world.sigil?spret::success:spret::abort;}
bool feat_is_wall(int f){return f;}
vector<int> diamond_sawblade_spots(bool){return world.diamond?vector<int>{1}:vector<int>{};}
bool monster_habitable_grid(int,int){return world.habitable;}
int count_summons(Player*,int){return world.croc;}
monster* find_player_paragon(){return world.paragon_deployed?&mon:nullptr;}
int paragon_charge_level(monster&){return world.paragon_charged;}
int species_apt(int){return world.aptitude;}transformation form_for_talisman(const item_def&){return world.talisman_form;}
string cant_transform_reason(transformation,bool,bool){return world.transform.canonical;}
ZhArg cant_transform_display_reason(transformation,bool,bool){return world.transform;}
bool you_worship(int){return world.oka;}
string lowercase_first(string s){if(!s.empty())s[0]=tolower(static_cast<unsigned char>(s[0]));return s;}
'''
for f,blocks in refs.items():
    for s in blocks:
        for name in ('casting_uselessness_reason','spell_uselessness_reason','cannot_put_on_talisman_reason'):
            s=s.replace(name+'(', 'old_'+name+'(')
        code+=s+'\n'
for f,needle in [('spl-util.cc','ZhArg casting_uselessness_display_reason('),('spl-util.cc','ZhArg spell_uselessness_display_reason('),('item-use.cc','ZhArg cannot_put_on_talisman_display_reason(')]:
    code+=block(files[f],needle)+'\n'
code+=r'''
int checks=0;map<string,int> reached;
void compare(ZhArg actual,const string&old){
 if(actual.canonical!=old){cerr<<"Canonical drift: ["<<actual.canonical<<"] != ["<<old<<"]\n";abort();}
 if(!old.empty()&&actual.supported)assert(actual.localized!=old);
 if(!actual.supported)assert(actual.localized==old);
 if(!old.empty())++reached[old];++checks;
}
void fresh(){world=World();you=Player();env.level_state=0;}
// Deterministic world scenarios isolate every predicate, then combine selected conflicts
// to detect accidental priority changes without a Cartesian world matrix. Integer boundaries use exact values.
void state(int id){
 if(id==0)return;
 if(id>=100){you.duration[id-100]=1;return;}
 switch(id){
 case 1:world.bounds=false;break;case 2:you.on_current_level=false;break;
 case 3:you.experience_level=4;break;case 4:world.hp_cast=true;break;
 case 5:world.hp=false;world.hp_cast=true;break;case 6:world.mp=false;break;
 case 7:you.magic_points=you.max_magic_points;break;case 8:you.form=transformation::walking_scroll;break;
 case 9:world.banned=true;break;case 10:world.allies=true;break;case 11:world.hostile=true;break;
 case 12:world.stasis=true;break;case 13:world.tele={"reason",ZhArgType::Text,"You cannot blink because you are wielding a named weapon.","【T】",true};break;
 case 14:world.move=false;break;case 15:world.movement=FASTEST_PLAYER_MOVE_SPEED;break;
 case 16:world.no_grasp=true;break;case 17:you.hp=you.hp_max;break;case 18:you.hp_max=20;break;
 case 19:world.undead=true;break;case 20:world.salamander=true;break;case 21:world.blood=false;break;
 case 22:world.gateway=false;break;case 23:world.gateway_room=false;break;case 24:world.forest_room=false;break;
 case 25:world.wall=false;break;case 26:world.constricted=true;break;case 27:world.gold=true;break;case 28:world.reap=true;break;
 case 29:env.level_state=LSTATE_STILL_WINDS;break;case 30:world.gauntlet=true;break;
 case 31:world.armour_allowed=false;break;case 32:world.armour=false;break;case 33:world.pile=false;break;
 case 34:world.electric={"reason",ZhArgType::Text,"there is a wall between you and your target.","【E】",true};break;
 case 35:world.sigil=false;break;case 36:you.current_vision=0;break;case 37:world.diamond=false;break;
 case 38:world.stationary=true;break;case 39:world.habitable=false;break;case 40:world.croc=true;break;
 case 41:you.props.paragon=false;break;case 42:world.paragon_deployed=true;world.paragon_charged=false;break;
 case 43:you.props.charge.n=1;break;
 }
}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.spell.talisman.reasons");
'''
code+='vector<int> spells={'+','.join(spells+['SPELL_TEST_UNKNOWN'])+'};\n'
code+='vector<int> states={'+','.join(['0']+[str(i) for i in range(1,44)]+['100+'+s for s in symbols if s.startswith('DUR_')])+'};\n'
code+=r'''
 vector<pair<int,int>> scenarios;
 for(auto state_id:states)scenarios.emplace_back(state_id,0);
 for(auto pair:vector<pair<int,int>>{{1,2},{3,6},{4,7},{5,6},{9,10},{11,12},{12,13},{13,34},{14,33},{17,19},{27,28},{38,39},{39,40}})scenarios.push_back(pair);
 scenarios.emplace_back(100+DUR_CONF,3);
 scenarios.emplace_back(100+DUR_DEATHS_DOOR,5);
 for(auto spell:spells)for(auto scenario:scenarios){
  fresh();state(scenario.first);state(scenario.second);
  for(bool temp:{false,true}){
   compare(casting_uselessness_display_reason(spell,temp),old_casting_uselessness_reason(spell,temp));
   for(bool prevent:{false,true})for(bool skip:{false,true})
    compare(spell_uselessness_display_reason(spell,temp,prevent,skip),old_spell_uselessness_reason(spell,temp,prevent,skip));
  }
 }
 // The detail caller selects its complete parent by stable semantic ID.
 fresh();world.hostile=true;
 assert(spell_uselessness_display_reason(SPELL_TEST_UNKNOWN,true,false,true).message_id=="spell.reason.no_hostiles");
 assert(spell_uselessness_display_reason(SPELL_TEST_UNKNOWN,true,true,true).canonical.empty());
 ++checks;
 // Semantic child failures must survive nesting without partial translation.
 for(bool supported:{false,true})for(int child:{0,1})for(int spell:{SPELL_BLINK,SPELL_PILEDRIVER,SPELL_ELECTRIC_CHARGE}){
  fresh();auto&reason=child?world.electric:world.tele;
  reason={"reason",ZhArgType::Text,"A missing child reason with 5, names & punctuation!",supported?"【S】":"A missing child reason with 5, names & punctuation!",supported};
  auto result=spell_uselessness_display_reason(spell,true,true,true);
  compare(result,old_spell_uselessness_reason(spell,true,true,true));
  if(!result.canonical.empty()){
   assert(result.supported==supported);
   auto parent=zh_message("spell.player.useless_reason",{result});
   if(!supported)assert(parent.localized==parent.canonical);
  }
 }
 item_def talisman;
 for(bool protean:{false,true})for(double skill:{0.,5.99,6.,6.01,27.})for(int apt:{0,UNUSABLE_SKILL})
 for(bool temporary:{false,true})for(bool hive:{false,true})for(bool oka:{false,true})for(bool love:{false,true})for(int reason_case:{0,1,2})for(bool temp:{false,true}){
  fresh();talisman.sub_type=protean?TALISMAN_PROTEAN:-1;world.skill=skill;world.aptitude=apt;
  if(temporary)you.form=transformation::tree;
  world.talisman_form=hive?transformation::hive:transformation::none;world.oka=oka;world.nolove=love;
  if(reason_case)world.transform={"reason",ZhArgType::Text,"A full transformation restriction.",reason_case==1?"【F】":"A full transformation restriction.",reason_case==1};
  compare(cannot_put_on_talisman_display_reason(talisman,temp),old_cannot_put_on_talisman_reason(talisman,temp));
 }
'''+''.join(' assert(reached.count('+json.dumps(reason)+'));\n' for reason in sorted(fixed_reasons))+r'''
 cout<<"PASS: "<<checks<<" real spell/talisman producer cases; "<<reached.size()<<" distinct canonical restrictions, priority, temp/prevent/skip, skill boundaries and child fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
    source=Path(tmp)/'test.cc';source.write_text(code);exe=Path(tmp)/'test'
    subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(source),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=90)
