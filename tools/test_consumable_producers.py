#!/usr/bin/env python3
"""Exercise production restriction and noise generators, keeping English snapshots.
Only world-state queries are stubs; selected methods and the ID runtime are real.
"""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog
compile_catalog()
def block(s,needle,start=0):
 pos=s.index(needle,start);begin=s.rfind('\n',0,pos)+1;brace=s.index('{',pos);depth=0
 for end in range(brace,len(s)):
  if s[end]=='{':depth+=1
  elif s[end]=='}':
   depth-=1
   if not depth:return s[begin:end+1]
 raise AssertionError(needle)
files={f:(SRC/f).read_text() for f in ('item-name.cc','potion.cc','spl-cast.cc','evoke.cc')}
needles={'item-name.cc':['static string _no_items_reason(','static string _general_cannot_read_reason(','string cannot_read_item_reason(','string cannot_drink_item_reason('], 'potion.cc':[], 'spl-cast.cc':['string spell_noise_string(']}
classes=['PotionCuring','PotionHealWounds','PotionHaste','PotionBrilliance','PotionCancellation','PotionMagic','PotionMutation']
snapshot=ROOT/'tools/fixtures/consumable-english.json'
if not snapshot.exists():
 originals={f:subprocess.check_output(['git','show','5fa2fbf:crawl-ref/source/'+f],cwd=ROOT/'native',text=True) for f in needles}
 ref={f:[block(originals[f],n) for n in ns] for f,ns in needles.items()}
 ref['potions']={c:block(originals['potion.cc'],'bool can_quaff(',originals['potion.cc'].index('class '+c+' ')) for c in classes}
 ref['mutation']=block(originals['potion.cc'],'static bool _can_mutate(')
 snapshot.write_text(json.dumps(ref,indent=2)+'\n')
ref=json.loads(snapshot.read_text())
if 'evoke.cc' not in ref:
 original=subprocess.check_output(['git','show','5fa2fbf:crawl-ref/source/evoke.cc'],cwd=ROOT/'native',text=True)
 ref['evoke.cc']=[block(original,'string cannot_evoke_item_reason(')]
 snapshot.write_text(json.dumps(ref,indent=2)+'\n')
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
using namespace std;
#define WIZARD
#define TAG_MAJOR_VERSION 34
#define ARRAYSZ(a) (sizeof(a)/sizeof(*(a)))
#define COMPILE_CHECK(x) static_assert(x,"size")
using object_selector=int;using potion_type=int;using spell_type=int;
'''
symbols=set(re.findall(r'\b(?:OBJ|SCR|POT|DUR|MUT|BRANCH|OSEL|SPELL|MISC)_[A-Z_]+\b','\n'.join(ref['item-name.cc']+list(ref['potions'].values())+[ref['mutation']]+ref['spl-cast.cc'])))
symbols|=set(re.findall(r'\b(?:OBJ|SPELL|MISC)_[A-Z_]+\b',block(files['evoke.cc'],'static spell_type _evoke_noise_spell(')))
symbols|=set(re.findall(r'\b(?:OBJ|MISC|BAUBLE|MUT)_[A-Z_]+\b',ref['evoke.cc'][0]))
symbols|={'NUM_POTIONS','GOD_TROG','UNRAND_FOLLY','RENOUNCE_SCROLLS_TIMER_KEY','RENOUNCE_POTIONS_TIMER_KEY','IDENTIFIED_ALL_KEY','LSTATE_STILL_WINDS','SPELL_NO_SPELL','DUR_FLOODED','OBJ_WEAPONS','DESC_DBNAME'}
code+='enum {'+','.join(sorted(symbols))+'};\n'
code+=r'''
namespace passive_t {enum {identify_items,no_haste};}
struct Props {map<int,bool> values;bool exists(int k)const{auto i=values.find(k);return i!=values.end()&&i->second;}};
namespace transformation {enum {flux};}
struct Player {
 int form=-1;int get_mutation_level(int m)const{return has_mutation(m);}
 int branch=0;bool rage=false,conf=false,silent=false,flood=false,drink_perm=true,drink_temp=true,allies=false,stasis_flag=false,trog=false,identify=false,no_haste=false,heal_perm=true,heal_temp=true,drunken_targets=false,folly=false,mutable_perm=true,mutable_temp=true,wizard=false;
 int duration[512]={};map<int,bool> mutations;Props props;int spell_no=1,hp=1,hp_max=10,max_magic_points=10,magic_points=1;
 bool berserk()const{return rage;}bool confused()const{return conf;}bool is_silenced()const{return silent||duration[DUR_FLOODED];}int pos()const{return 0;}
 bool has_mutation(int m)const{auto i=mutations.find(m);return i!=mutations.end()&&i->second;}bool allies_forbidden()const{return allies;}bool stasis()const{return stasis_flag;}
 string no_tele_reason(bool)const{return stasis_flag?"You cannot teleport right now.":"";}
 ZhArg no_tele_display_reason(bool b)const{auto s=no_tele_reason(b);return {"reason",ZhArgType::Text,s,s,s.empty()};}
 bool can_drink(bool t)const{return drink_perm&&(!t||drink_temp);}bool can_potion_heal(bool t)const{return heal_perm&&(!t||heal_temp);}bool unrand_equipped(int)const{return folly;}bool can_safely_mutate(bool t)const{return mutable_perm&&(!t||mutable_temp);}
}you;
struct {int level_state=0;}env;
struct item_def {int base_type=OBJ_SCROLLS,sub_type=SCR_IDENTIFY;bool identified=true;bool is_type(int b,int s)const{return base_type==b&&sub_type==s;}string name(int)const{return "phial of floods";}bool is_identified()const{return identified;}};
bool item_type_known(const item_def&i){return i.identified;}bool player_in_branch(int b){return you.branch==b;}bool you_worship(int){return you.trog;}bool have_passive(int p){return p==passive_t::identify_items?you.identify:you.no_haste;}
bool silenced(int){return you.silent;}const char*player_silenced_reason(){return you.silent?"silenced":you.duration[DUR_FLOODED]?"unable to breathe":"";}
bool mapped=true,selectable=true,cancellable=true;
bool is_map_persistent(){return mapped;}bool any_items_of_type(int,int,bool){return selectable;}
string no_selectables_message(int type){switch(type){case OSEL_UNIDENT:return "You don't currently have any unidentified items.";case OSEL_ENCHANTABLE_ARMOUR:return "You aren't carrying any armour which can be enchanted further.";case OSEL_ENCHANTABLE_WEAPON:return "You aren't carrying any weapons that can be enchanted.";case OSEL_BRANDABLE_WEAPON:return "You aren't carrying any weapons that can be branded.";default:return "Unknown selector";}}
ZhArg no_selectables_display_reason(int type){const string value=no_selectables_message(type);return {"reason",ZhArgType::Text,value,value,false};}
bool has_drunken_brawl_targets(){return you.drunken_targets;}bool player_is_cancellable(){return cancellable;}
string make_stringf(const char*fmt,...){char b[1024];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);return b;}
struct PotionSeam {bool can_quaff(string*r,bool,ZhArg*d=nullptr)const{*r="";if(d)*d={"reason",ZhArgType::Text,"","",true};return true;}} potion;
const PotionSeam*get_potion_effect(int){return &potion;}
'''
code+=r'''
bool removed=false,known_empty=false,ally_only=false,xp_evoker=false;int charges=1;string transform_reason;
string lowercase_first(string s){if(!s.empty())s[0]=tolower(s[0]);return s;}
string cant_transform_reason(int,bool,bool){return transform_reason;}
ZhArg cant_transform_display_reason(int,bool,bool){return {"reason",ZhArgType::Text,transform_reason,transform_reason,transform_reason.empty()};}
bool item_type_removed(int,int){return removed;}bool is_known_empty_wand(const item_def&){return known_empty;}bool _evoke_ally_only(const item_def&,bool){return ally_only;}bool is_xp_evoker(const item_def&){return xp_evoker;}int evoker_charges(int){return charges;}
string sub_type_string(const item_def&i,bool){return i.name(DESC_DBNAME);}
'''
code+='namespace old {\n'+ref['evoke.cc'][0]+'\n'+'\n'.join(ref['item-name.cc'])+'\n'+ref['mutation']+'\n'
for c in classes:code+='struct '+c+' {\n'+ref['potions'][c].replace(' const override',' const')+'\n};\n'
# spell noise seams below, outside namespace
code+='}\n'
for n in ['static ZhArg _unmigrated_item_reason(','static ZhArg _no_items_reason(','static ZhArg _general_cannot_read_reason(','ZhArg cannot_read_item_display_reason(','ZhArg cannot_drink_item_display_reason(']:code+=block(files['item-name.cc'],n)+'\n'
code+=block(files['evoke.cc'],'ZhArg cannot_evoke_item_display_reason(')+'\n'
code+=block(files['potion.cc'],'static string _potion_reason(')+'\n'+block(files['potion.cc'],'static bool _can_mutate(')+'\n'
for c in classes:code+='struct '+c+' {\n'+block(files['potion.cc'],'bool can_quaff(',files['potion.cc'].index('class '+c+' ')).replace(' const override',' const')+'\n};\n'
code+=r'''
int cast_noise=0,effect_noise=0;
int spell_noise(int){return cast_noise;}int spell_effect_noise(int){return effect_noise;}
int breakpoint_rank(int v,const int*b,int n){int r=0;while(r<n&&v>=b[r])++r;return r;}
string chop_string(string s,int n){return s.substr(0,n);}
string spell_noise_string(spell_type,int=0);
'''
code+='namespace old {\n'+ref['spl-cast.cc'][0]+'\n}\n'
for n in ['static int _display_spell_noise(','static const char *_spell_noise_description(','string spell_noise_string(','ZhArg spell_noise_display_arg(']:code+=block(files['spl-cast.cc'],n)+'\n'
code+=r'''
int checks=0;void compare(const ZhArg&v,const string&en){
 if(v.canonical!=en){cerr<<"Canonical drift: "<<v.canonical<<" != "<<en<<"\n";abort();}
 if(v.supported&&!en.empty()){assert(v.localized!=en);assert(v.localized.find("You ")==string::npos);}
 ++checks;
}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.consumable");
 const int mutations[]={MUT_INNATE_CASTER,MUT_NO_GRASPING,MUT_RENOUNCE_SCROLLS,MUT_RENOUNCE_POTIONS,MUT_DRUNKEN_BRAWLING,MUT_HP_CASTING};
 const int scrolls[]={SCR_AMNESIA,SCR_ENCHANT_WEAPON,SCR_BRAND_WEAPON,SCR_ENCHANT_ARMOUR,SCR_IDENTIFY,SCR_SUMMONING,SCR_BUTTERFLIES,SCR_BLINKING,SCR_TELEPORTATION,SCR_FOG,SCR_POISON,SCR_REVELATION};
 for(int state=0;state<34;++state){
  you=Player();env.level_state=0;mapped=selectable=cancellable=true;
  switch(state){
   case 1:you.branch=BRANCH_GEHENNA;break;case 2:you.rage=true;break;case 3:you.conf=true;break;case 4:you.duration[DUR_NO_SCROLLS]=1;break;case 5:you.silent=true;break;case 6:you.duration[DUR_FLOODED]=1;break;
   case 7:you.props.values[RENOUNCE_SCROLLS_TIMER_KEY]=true;you.mutations[MUT_RENOUNCE_SCROLLS]=true;break;
   case 8:you.mutations[MUT_INNATE_CASTER]=true;break;case 9:you.mutations[MUT_NO_GRASPING]=true;break;case 10:you.trog=true;break;
   case 11:you.props.values[IDENTIFIED_ALL_KEY]=true;break;case 12:you.identify=true;break;case 13:you.allies=true;break;case 14:you.stasis_flag=true;break;case 15:you.spell_no=0;break;case 16:selectable=false;break;case 17:env.level_state=LSTATE_STILL_WINDS;break;case 18:mapped=false;break;
   case 19:you.drink_perm=false;break;case 20:you.drink_temp=false;break;case 21:you.props.values[RENOUNCE_POTIONS_TIMER_KEY]=true;you.mutations[MUT_RENOUNCE_POTIONS]=true;break;case 22:you.branch=BRANCH_COCYTUS;break;
   case 23:you.duration[DUR_DEATHS_DOOR]=1;break;case 24:you.hp=you.hp_max;you.magic_points=you.max_magic_points;break;case 25:you.heal_perm=false;break;case 26:you.heal_temp=false;break;case 27:you.no_haste=true;break;case 28:you.folly=true;break;case 29:cancellable=false;break;case 30:you.mutations[MUT_HP_CASTING]=true;break;case 31:you.mutable_perm=false;break;case 32:you.mutable_temp=false;break;case 33:you.hp=you.hp_max;you.magic_points=you.max_magic_points;you.mutations[MUT_DRUNKEN_BRAWLING]=true;you.drunken_targets=true;break;
  }
  for(bool temp:{false,true})for(bool ident:{false,true}){
   compare(cannot_read_item_display_reason(nullptr,temp,ident),old::cannot_read_item_reason(nullptr,temp,ident));
   compare(cannot_drink_item_display_reason(nullptr,temp,false,ident),old::cannot_drink_item_reason(nullptr,temp,false,ident));
   for(int subtype:scrolls)for(bool known:{false,true}){item_def i;i.sub_type=subtype;i.identified=known;compare(cannot_read_item_display_reason(&i,temp,ident),old::cannot_read_item_reason(&i,temp,ident));}
   item_def i;i.base_type=OBJ_WEAPONS;compare(cannot_read_item_display_reason(&i,temp,ident),old::cannot_read_item_reason(&i,temp,ident));compare(cannot_drink_item_display_reason(&i,temp,false,ident),old::cannot_drink_item_reason(&i,temp,false,ident));
   for(int p:{POT_INVISIBILITY,NUM_POTIONS}){i.base_type=OBJ_POTIONS;i.sub_type=p;compare(cannot_drink_item_display_reason(&i,temp,true,ident),old::cannot_drink_item_reason(&i,temp,true,ident));}
   POTION_CHECKS
  }
 }

 for(int state=0;state<13;++state){
  you=Player();removed=known_empty=ally_only=xp_evoker=false;charges=1;env.level_state=0;transform_reason="";
  switch(state){case 1:you.rage=true;break;case 2:you.conf=true;break;case 3:you.form=transformation::flux;break;case 4:transform_reason="Your body cannot transform.";break;case 5:you.mutations[MUT_NO_ARTIFICE]=true;break;case 6:removed=true;break;case 7:known_empty=true;break;case 8:ally_only=true;you.allies=true;break;case 9:env.level_state=LSTATE_STILL_WINDS;break;case 10:you.silent=true;break;case 11:xp_evoker=true;charges=0;break;case 12:you.duration[DUR_FLOODED]=1;break;}
  for(bool temp:{false,true})for(bool ident:{false,true}){
   compare(cannot_evoke_item_display_reason(nullptr,temp,ident),old::cannot_evoke_item_reason(nullptr,temp,ident));
   for(int base:{OBJ_MISCELLANY,OBJ_BAUBLES,OBJ_WANDS,OBJ_WEAPONS})for(int sub:{MISC_ZIGGURAT,BAUBLE_FLUX,MISC_CONDENSER_VANE,MISC_HORN_OF_GERYON,MISC_PHIAL_OF_FLOODS}){
    item_def i;i.base_type=base;i.sub_type=sub;auto reason=cannot_evoke_item_display_reason(&i,temp,ident);compare(reason,old::cannot_evoke_item_reason(&i,temp,ident));
   }
  }
 }
 for(int cast:{0,1,2,3,4,7,8,14,15,19,20,29,30,70})for(int effect:{0,1,6,18,32})for(bool wizard:{false,true})for(int spell:{0,int(SPELL_POLAR_VORTEX)}){
  cast_noise=cast;effect_noise=effect;you.wizard=wizard;
  assert(spell_noise_string(spell)==old::spell_noise_string(spell,0));
  assert(spell_noise_string(spell,3)==old::spell_noise_string(spell,3));
  const auto a=spell_noise_display_arg("noise",spell);compare(a,old::spell_noise_string(spell,0));assert(a.supported);
  auto displayed=zh_message("spell.stats.noise",{zh_text("indent","",""),a});assert(displayed.localized!=displayed.canonical);
 }
 for(const string s:{"2d5","3d(4+2)","0","1.5x","(2 * 3)/4","25%",""}){auto a=zh_numeric_notation("damage",s);assert(a.supported&&a.localized==s);++checks;}
 for(const string s:{"death","1d4 flaming","<red>2d5</red>","2d5\nYou die.","damage: 5"}){assert(!zh_numeric_notation("damage",s).supported);++checks;}
 auto parent=zh_message_arg("reason","item.reason.use.inert_evoker",{{"item",ZhArgType::Name,"Unknown item","Unknown item",false}});assert(!parent.supported&&parent.localized==parent.canonical);++checks;
 cout<<"PASS: "<<checks<<" production restriction/noise cases, canonical snapshots and typed arithmetic\n";
}
'''
checks=[]
for c in classes:
 checks.append('{string en,actual;ZhArg d{"reason",ZhArgType::Text,"","",true};bool before=old::'+c+'().can_quaff(&en,temp);bool after='+c+'().can_quaff(&actual,temp,&d);assert(before==after&&actual==en);compare(d,en);}')
code=code.replace('POTION_CHECKS','\n'.join(checks))
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'test.cc';p.write_text(code);exe=Path(tmp)/'test'
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,timeout=30)
