#!/usr/bin/env python3
"""Run production transform producers and tutorial markup on copied engine seams."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(text,needle):
 p=text.index(needle);start=text.rfind('\n',0,p)+1;b=text.index('{',p);depth=0
 for end in range(b,len(text)):
  if text[end]=='{':depth+=1
  elif text[end]=='}':
   depth-=1
   if depth==0:return text[start:end+1]
 raise AssertionError(needle)

def form_snapshot(source):
 out=[]
 for match in re.finditer(r'class (Form\w+) : public Form',source):
  section=source[match.start():];end=section.find('\nclass ',1)
  if end>=0:section=section[:end]
  methods=[]
  for name in ('transform_message','get_untransform_message'):
   needle='string '+name+'() const override'
   if needle in section:methods.append(block(section,needle))
  if methods:out.append('class '+match[1]+' : public Form\n{\n'+'\n'.join(methods)+'\n};')
 return '\n'.join(out)

def data_snapshot(source):
 return '\n'.join(m[0] for m in re.finditer(r'transformation::(\w+),[^\n]*\n\s*"([^"]*)",',source))

compile_catalog()
transform=(SRC/'transform.cc').read_text();hints=(SRC/'hints.cc').read_text()
fixture=ROOT/'tools/fixtures/transform-pickup-english.json'
needles=['static void _print_death_brand_changes(', 'bool maw_considers_appetising(', 'bool maw_hunger_check(', 'bool vampire_mesmerism_check(']
if not fixture.exists():
 old=subprocess.check_output(['git','show','HEAD:crawl-ref/source/transform.cc'],cwd=ROOT/'native',text=True)
 hintdb=(SRC/'dat/descript/hints.txt').read_text().split('HINT_SEEN_FIRST_OBJECT\n\n',1)[1].split('%%%%',1)[0].strip()
 fixture.write_text(json.dumps({'producers':{n:block(old,n) for n in needles},'pickup_template':hintdb,'form_source':form_snapshot(old),'form_data':data_snapshot((SRC/'form-data.h').read_text())},ensure_ascii=False,indent=2)+'\n')
old=json.loads(fixture.read_text())
if 'form_source' not in old:
 old['form_source']=form_snapshot(subprocess.check_output(['git','show','HEAD:crawl-ref/source/transform.cc'],cwd=ROOT/'native',text=True))
 old['form_data']=data_snapshot((SRC/'form-data.h').read_text());fixture.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
q=lambda s:json.dumps(s,ensure_ascii=False)
base=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include "transformation.h"
#include <algorithm>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <map>
#include <string>
#include <vector>
using namespace std;
enum {SPWPN_HOLY_WRATH=1,DESC_YOUR,DESC_THE,PRONOUN_REFLEXIVE,MH_NATURAL=16,MH_PLANT=32,MH_DEMONIC=64,MH_HOLY=128,MF_HARD_RESET=256,MUT_MISSING_EYE,MSGCH_TUTORIAL,MID_PLAYER,SP_DEEP_DWARF};
struct item_def {int brand=1;string title="your sword";string name(int)const{return title;}};
struct monster {int holy=MH_NATURAL,flags=0,will=0,speed_increment=20;bool firewood=false,summoned=false,visible=true;string title="the goblin",reflexive="itself";int dazed=0;
 int holiness()const{return holy;}bool is_firewood()const{return firewood;}bool is_summoned()const{return summoned;}template<class T>bool can_see(const T&)const{return visible;}string name(int)const{return title;}string pronoun(int)const{return reflexive;}int check_willpower(const void*,int){return will;}void daze(int n){dazed=n;}};
struct Player {bool undead=false,beheld_value=false,clarity_value=false,visible=true,missing=false;transformation form=transformation::vampire;int beholders=0;int species=0,arms_count=2;string arms="arm",feet="feet";
 int arm_count()const{return arms_count;}string arm_name(bool)const{return arms;}string foot_name(bool)const{return feet;}
 bool invisible()const{return visible;}bool undead_or_demonic(bool)const{return undead;}bool beheld()const{return beheld_value;}bool clarity()const{return clarity_value;}void add_beholder(monster&,bool,int){++beholders;}int shout_volume(){return 7;}int pos(){return 1;}bool can_see(const monster&)const{return visible;}bool has_mutation(int){return missing;}} you;
struct Form {int get_effect_chance(){return 50;}} form;Form*get_form(){return &form;}
int get_weapon_brand(const item_def&i){return i.brand;}bool chance=false;bool one_chance_in(int){return chance;}int random_range(int a,int){return a;}int noises=0;void noisy(int,int,int){++noises;}
vector<string> captured,local;void mpr(const ZhMessage&m,int=0){captured.push_back(m.canonical);local.push_back(m.localized);}void mprf(const char*fmt,...){char b[4096];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);captured.push_back(b);}
string make_stringf(const char*fmt,...){char b[4096];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);return b;}
string uppercase_first(string s){if(!s.empty())s[0]=toupper(s[0]);return s;}
ZhArg zh_item_arg(const string&k,const item_def&i,int){return {k,ZhArgType::Name,i.title,"物品名"};}
ZhArg zh_monster_arg(const string&k,const monster&m,int){return {k,ZhArgType::Name,m.title,"怪物名"};}
'''
for n in needles:
 body=old['producers'][n]
 for name in ['_print_death_brand_changes','maw_considers_appetising','maw_hunger_check','vampire_mesmerism_check']:
  body=body.replace(name,'reference_'+name)
 base+=body+'\n'
for n in needles:base+=block(transform,n)+'\n'
base+='transformation message_form=transformation::none; bool draconian=false; string description; string hand_parts;\n'
base+='namespace species{bool is_draconian(int){return draconian;}}\n'
base+='int get_equivalent_mons(){return 1;} string get_transform_description(){return description;} string hand_transform_parts(){return hand_parts;}\n'
base+='ZhArg zh_monster_type_arg(const string&k,int){return {k,ZhArgType::Name,"red dragon","红龙"};}\n'
base+=block(transform,'static ZhMessage _transform_untranslated(')+'\n'+block(transform,'static ZhMessage _transform_log(')+'\n'
base+=block(transform,'ZhMessage Form::transform_display_message(').replace('ZhMessage Form::transform_display_message() const','ZhMessage form_entry_display()')+'\n'
for cls,method,name in [('FormEelHands','transform_display_message','eel_enter'),('FormEelHands','untransform_display_message','eel_leave'),('FormSpore','transform_display_message','spore_enter')]:
 section=transform[transform.index('class '+cls):]
 base+=block(section,'ZhMessage '+method+'(').replace('ZhMessage '+method+'() const override','ZhMessage '+name+'()')+'\n'

# Compare every virtual producer to an independently frozen original body.
oldform=old['form_source'];override_calls=[]
for match in re.finditer(r'class (Form\w+) : public Form',oldform):
 cls=match[1];oldsection=oldform[match.start():];newsection=transform[transform.index('class '+cls+' : public Form'):]
 end=oldsection.find('\nclass ',1);oldsection=oldsection[:end] if end>=0 else oldsection
 for method,newmethod in [('transform_message','transform_display_message'),('get_untransform_message','untransform_display_message')]:
  needle='string '+method+'() const override'
  if needle not in oldsection:continue
  name=cls+'_'+method
  body=block(oldsection,needle).replace(needle,'string old_'+name+'()').replace('Form::transform_message()', 'form_entry_display().canonical')
  current=block(newsection,'ZhMessage '+newmethod+'() const override').replace('ZhMessage '+newmethod+'() const override','ZhMessage new_'+name+'()').replace('Form::transform_display_message()', 'form_entry_display()')
  if cls in ('FormShadow',):base+='#if TAG_MAJOR_VERSION == 34\n'
  base+=body+'\n'+current+'\n'
  if cls in ('FormShadow',):base+='#endif\n'
  override_calls.append((cls,name))
base+=block(transform,'string Form::transform_message() const').replace('string Form::transform_message() const','string canonical_entry_wrapper()').replace('transform_display_message()', 'form_entry_display()')+'\n'
# Full production control-markup conversion, including display-mode pruning.
base+=r'''
enum command_type {CMD_PICKUP,CMD_DROP,CMD_DISPLAY_INVENTORY};map<string,command_type> names={{"CMD_PICKUP",CMD_PICKUP},{"CMD_DROP",CMD_DROP},{"CMD_DISPLAY_INVENTORY",CMD_DISPLAY_INVENTORY}};
map<command_type,string> keys={{CMD_PICKUP,"g"},{CMD_DROP,"d"},{CMD_DISPLAY_INVENTORY,"i"}};
command_type name_to_command(const string&s){return names.at(s);}string command_to_string(command_type c){return keys.at(c);}
string replace_all(string s,const string&a,const string&b){size_t p=0;while((p=s.find(a,p))!=string::npos){s.replace(p,a.size(),b);p+=b.size();}return s;}
bool is_tiles(){
#ifdef USE_TILE
return true;
#else
return false;
#endif
}
'''
lib=(SRC/'libutil.cc').read_text()
base+=block(lib,'static void inline _untag(')+'\n'+block(lib,'string untag_tiles_console(')+'\n'
base+='void trim_string_right(string&s){s.erase(s.find_last_not_of(\" \\t\\r\\n\")+1); }\n'
base+=block(lib,'string unwrap_desc(')+'\n'
base+=block(hints,'void hint_replace_cmds(')+'\n'
# This template has no $item token. Keep the real command/input helper, not a mock.
base+='void _replace_static_tags(string&s){hint_replace_cmds(s);assert(s.find("$item[")==string::npos);}\n'
base+=block(hints,'static string _prepare_pickup_hint(')+'\n'+block(hints,'static ZhMessage _pickup_hint_message(')+'\n'
base+='string reference_pickup='+q(old['pickup_template'])+';\n'
entries={}
for match in re.finditer(r'transformation::(\w+),[^\n]*\n\s*"([^"]*)",',old['form_data']):
 kind,desc=match.groups()
 if 'case transformation::'+kind+':' not in block(transform,'ZhMessage Form::transform_display_message('):continue
 if kind=='none':desc='your old self.'
 if kind=='statue':desc='a living statue of rough stone.'
 entries[kind]='You turn into '+desc
base+='int checks=0; void check_forms(){\n'
for kind,en in entries.items():
 if kind in ('porcupine','shadow'):base+='#if TAG_MAJOR_VERSION == 34\n'
 base+='message_form=transformation::'+kind+';assert(form_entry_display().canonical=='+q(en)+');++checks;\n'
 if kind in ('porcupine','shadow'):base+='#endif\n'
base+='message_form=transformation::dragon;draconian=true;assert(form_entry_display().canonical=="You turn into a fearsome red dragon!");draconian=false;++checks;\n'
base+='for(string part:{"a hand","hands","front paws","main tentacles"}){hand_parts=part;you.arms_count=(part=="a hand"?1:2);auto a=eel_enter();auto b=eel_leave();assert(a.canonical=="Your "+part+(you.arms_count==1?" turns into a wriggling electric eel!":" turn into a pair of wriggling electric eels!"));assert(b.canonical=="Your "+part+(you.arms_count==1?" reverts to its normal form.":" revert to their normal form."));assert(a.localized!=a.canonical&&b.localized!=b.canonical);checks+=2;}\n'
for cls,name in override_calls:
 if cls=='FormShadow':base+='#if TAG_MAJOR_VERSION == 34\n'
 if cls=='FormStatue':base+='message_form=transformation::statue;\n'
 base+='for(bool roll:{false,true})for(bool visible:{false,true})for(int arms:{1,2}){chance=roll;you.visible=visible;you.arms_count=arms;hand_parts=(arms==1?"a hand":"hands");you.species=SP_DEEP_DWARF;assert(new_'+name+'().canonical==old_'+name+'());++checks;}\n'
 if cls=='FormShadow':base+='#endif\n'
base+='assert(canonical_entry_wrapper()==form_entry_display().canonical);++checks;\n'
base+='#if TAG_MAJOR_VERSION == 34\n'
base+='message_form=transformation::appendage;description="";setenv("DCSS_ZH_ID_MISSING","retired-form-missing.tsv",1);auto retired=form_entry_display();assert(retired.canonical=="You turn into "&&retired.localized==retired.canonical);unsetenv("DCSS_ZH_ID_MISSING");ifstream missing("retired-form-missing.tsv");string gap;getline(missing,gap);assert(gap.find("transform.enter.retired\\tunsupported retired form\\t") == 0);missing.close();remove("retired-form-missing.tsv");++checks;\n'
base+='#endif\n'
base+='you.arms="arm";you.feet="feet";assert(spore_enter().canonical=="Dense mycelia sprout from your arm and feet.");assert(spore_enter().localized!=spore_enter().canonical);++checks;}\n'

base+=r'''
void compare(){assert(!captured.empty());for(auto&s:local){assert(!s.empty());assert(s.find("goblin")==string::npos);assert(s.find("your sword")==string::npos);}++checks;}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_STRICT_SOURCE","1",1);check_forms();
 for(string item:{"your sword","your +12 sword of fire","your sword \"Hope\""})for(int brand:{0,1})for(bool undead:{false,true})for(bool entering:{false,true}){
  item_def i;i.title=item;i.brand=brand;you.undead=undead;captured.clear();local.clear();reference__print_death_brand_changes(&i,entering);auto expected=captured;captured.clear();_print_death_brand_changes(&i,entering);assert(captured==expected);++checks;
 }
 for(string name:{"the goblin","Sigmund","the seven-headed hydra"})for(bool c:{false,true})for(bool held:{false,true})for(bool coin:{false,true}){
  monster m;m.title=name;you.clarity_value=c;you.beheld_value=held;chance=coin;you.beholders=noises=0;captured.clear();local.clear();auto a=reference_maw_hunger_check(&m);auto expected=captured;int beh=you.beholders,noise=noises;you.beholders=noises=0;captured.clear();auto b=maw_hunger_check(&m);assert(a==b&&captured==expected&&beh==you.beholders&&noise==noises);if(!captured.empty())compare();++checks;
 }
 for(string name:{"the goblin","Sigmund"})for(string pronoun:{"itself","himself","herself","themselves"})for(bool missing:{false,true})for(int will:{-1,1})for(bool coin:{false,true}){
  monster m;m.title=name;m.reflexive=pronoun;m.will=will;you.missing=missing;chance=coin;captured.clear();local.clear();auto a=reference_vampire_mesmerism_check(m);auto expected=captured;int daze=m.dazed,speed=m.speed_increment;m.dazed=0;m.speed_increment=20;captured.clear();auto b=vampire_mesmerism_check(m);assert(a==b&&captured==expected&&daze==m.dazed&&speed==m.speed_increment);if(!captured.empty())compare();++checks;
 }
 for(string key:{"g","G","<","Ctrl-G"})for(string glyph:{"<lightgreen>!</lightgreen>","<<","["}){
  keys[CMD_PICKUP]=key;auto m=_pickup_hint_message(glyph);assert(m.canonical==_prepare_pickup_hint(unwrap_desc(string(reference_pickup)),glyph));
  for(auto text:{m.canonical,m.localized}){assert(text.find("ERROR")==string::npos);assert(text.find("<input>")==string::npos);assert(text.find("</input>")==string::npos);assert(text.find("$cmd[")==string::npos);assert(text.find("$1")==string::npos);assert(text.find("<console>")==string::npos);assert(text.find("<tiles>")==string::npos);}
  assert(m.localized!=m.canonical);{ZhLegacyPause p;assert(m.display()==m.localized);}++checks;
 }
 cout<<"PASS: "<<checks<<" production transform/markup cases, canonical snapshots, RNG effects, names, remapped keys and display-mode pruning\n";
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);cpp=p/'test.cc';cpp.write_text(base)
 for mode,flags in [('console',[]),('local',['-DUSE_TILE','-DUSE_TILE_LOCAL']),('web',['-DUSE_TILE','-DUSE_TILE_WEB'])]:
  exe=p/mode
  subprocess.run(['c++','-std=c++11','-DZH_STANDALONE',*flags,'-I'+str(SRC),str(cpp),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True,cwd=p)
