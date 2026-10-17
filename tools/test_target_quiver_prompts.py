#!/usr/bin/env python3
"""Actual targeting/quiver producers vs frozen pre-migration functions."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog

def block(s,name):
 p=s.index(name);a=s.rfind('\n',0,p)+1;b=s.index('{',p);depth=0
 for end in range(b,len(s)):
  if s[end]=='{':depth+=1
  elif s[end]=='}':
   depth-=1
   if not depth:return s[a:end+1]
 raise AssertionError(name)

compile_catalog()
d=(SRC/'directn.cc').read_text();q=(SRC/'quiver.cc').read_text()
throw=(SRC/'throw.cc').read_text()
assert 'internal_prompt = internal_message.canonical;' in throw
assert 'get_top_prompt_message(ZhMessage &message) const override' in throw
refs=json.loads((ROOT/'tools/fixtures/target-quiver-prompts-english.json').read_text())['functions']
assert 'zh_translate(key_hint)' not in q
assert 'fire_key_hints_message()' in d
assert 'top_prompt == current.canonical' in d
assert 'top_prompt(args.top_prompt_message.id.empty() ? args.top_prompt' in d
assert q.count('_quiver_named_description(')==7
assert 'zh_item_arg("item", you.inv[s->get_item()], DESC_INVENTORY)' in q
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
enum {DIR_NONE,DIR_TARGET,DIR_ENFORCE_RANGE,DIR_UNKNOWN,CMD_TARGET_SELECT_ACTION,CMD_TARGET_CYCLE_QUIVER_BACKWARD,CMD_TARGET_CYCLE_QUIVER_FORWARD,MSGCH_PROMPT};
using command_type=int;string key="Q";string captured;bool visible=true,has_item=false,bounds=true;
string old_translate(const string&s){return s;}
string lowercase_first(string s){if(!s.empty())s[0]=tolower(s[0]);return s;}
string uppercase_first(string s){if(!s.empty())s[0]=toupper(s[0]);return s;}
void insert_commands(string&s,const vector<int>&commands){size_t p=0;for(int c:commands){p=s.find('%',p);if(p==string::npos)break;s.replace(p,1,key+to_string(c));p+=key.size()+to_string(c).size();}}
template<class...A>string make_stringf(const char*f,A...a){char b[4096];snprintf(b,sizeof b,f,a...);return b;}
template<class...A>void mprf(int,const char*f,A...a){char b[4096];snprintf(b,sizeof b,f,a...);captured=b;}
struct Player{bool see_cell(int){return visible;}}you;
struct Knowledge{bool item(){return has_item;}};
struct Environment{Knowledge map_knowledge(int){return {};}}env;
bool in_bounds(int){return bounds;}
struct Behaviour{bool t;bool targeted(){return t;}};
string old_quiver_key_hints(bool);
struct Fire{bool no_other;string fire_key_hints(){return old_quiver_key_hints(no_other);}};
struct Moves{Fire*fire_context;};
struct OldDirection{bool just_looking;Moves moves;Behaviour*behaviour;int restricts;int target()const{return 0;}void print_key_hints()const;};
struct OptionsStruct{int status_caption_colour=7;}Options;
string colour_to_str(int c){return c==2?"green":c==8?"darkgrey":"lightgrey";}
struct formatted_string{string raw;string tostring()const{return raw;}void textcolour(int){}static formatted_string parse_string_raw(const string&s){return {s};}formatted_string&operator+=(const formatted_string&o){raw+=o.raw;return *this;}};
'''
old=refs['quiver_keys'].replace('string action_cycler::fire_key_hints() const','string old_quiver_key_hints(bool no_other_items)').replace('const bool no_other_items = *get() == *next();','')
code+=old.replace('zh_translate(', 'old_translate(')+'\n'+refs['target_keys'].replace('direction_chooser::','OldDirection::')+'\n'
code+=r'''
namespace quiver {struct action {string text;bool empty=true;formatted_string quiver_description(){return {text};}bool operator==(const action&)const{return empty;}};}
struct OldFire {quiver::action action;string internal_prompt;bool need_redraw=false;bool t=true;bool targeted(){return t;}void set_prompt();};
'''
code+=refs['fire_action'].replace('fire_target_behaviour::', 'OldFire::')+'\n'
code+=block(throw,'static ZhMessage _fire_action_prompt(')+'\n'
for text,name in [(q,'static ZhMessage _quiver_key_hints('),(q,'static ZhArg _quiver_caption('),(q,'static formatted_string _quiver_named_description('),(d,'static ZhMessage _target_key_prompt('),(d,'static ZhArg _target_prefix_arg(')]:code+=block(text,name)+'\n'
code+=r'''
int checked=0;
int main(){
 setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.target-quiver");
 for(const char*binding:{"Q","<","Ctrl-F"})for(bool no_other:{false,true}){
  key=binding;auto m=_quiver_key_hints(no_other);assert(m.canonical==old_quiver_key_hints(no_other));assert(m.localized!=m.canonical);assert(m.localized.find("<w>")!=string::npos);assert(m.localized.find('%')==string::npos);++checked;
  for(bool looking:{false,true})for(bool vis:{false,true})for(bool item:{false,true})for(bool bound:{false,true})for(bool targeted:{false,true})for(int restricts:{DIR_NONE,DIR_TARGET,DIR_ENFORCE_RANGE,DIR_UNKNOWN})for(bool has_action:{false,true}){
   visible=vis;has_item=item;bounds=bound;Behaviour behaviour{targeted};Fire fire{no_other};OldDirection old{looking,{has_action?&fire:nullptr},&behaviour,restricts};old.print_key_hints();
   ZhArg action=zh_text("action","","");if(has_action){action=ZhArg("action",ZhArgType::Text,m.canonical+"\n",m.localized+"\n");}
   auto now=_target_key_prompt(looking,vis,item&&bound,action,targeted,restricts);assert(now.canonical==captured);assert(now.localized!=now.canonical);{ZhTranslationPause pause;assert(now.display()==captured);}++checked;
  }
 }
 for(const char*verb:{"fire","attack","punch","reach","cleave","hit","buffet","lash","swat","headbutt","touch","bite","snap","release spores at","claw","slap","smack","future-form"})for(bool confused:{false,true})for(const char*key:{"a","-","Z"}){
  auto caption=_quiver_caption(verb,confused,key);string en=uppercase_first(string(confused?"confused ":"")+verb)+": "+key+") ";assert(caption.canonical==en);assert(caption.supported==(string(verb)!="future-form"));
  for(int colour:{2,8,7})for(bool known:{false,true}){
   ZhArg name("name",ZhArgType::Name,"+2 weapon's name!",known?"已审校名称":"+2 weapon's name!",known);
   auto full=_quiver_named_description(caption,name,colour);string expected=en+"<"+colour_to_str(colour)+">"+name.canonical+"</"+colour_to_str(colour)+">";
   {ZhTranslationPause pause;assert(_quiver_named_description(caption,name,colour).raw==expected);}
   assert((full.raw==expected)==(!known||!caption.supported));++checked;
  }
 }
 for(const char*canonical:{"Cast: Fireball", "Throw: 7 stones", "Abil: Heroism", "No action selected"})for(bool empty:{false,true})for(bool targeted:{false,true}){
  OldFire before;before.action.text=canonical;before.action.empty=empty;before.t=targeted;before.set_prompt();
  auto now=_fire_action_prompt({"quiver.prompt.description",canonical,"已审校动作"},empty,targeted);assert(now.canonical==before.internal_prompt);assert(now.localized!=now.canonical);++checked;
 }
 for(const char*id:{"target.prompt.prefix.apport","target.prompt.prefix.smite","target.prompt.prefix.fragment"})for(bool targeted:{false,true}){
  auto message=zh_message(id);auto prefix=_target_prefix_arg(message,"control override",targeted);assert(prefix.canonical==message.canonical);assert(prefix.localized==message.localized);
  auto full=zh_message("target.prompt.describe.monster",{prefix,zh_text("description","orc, badly wounded","已审校怪物状态")});assert(full.canonical==message.canonical+": <lightgrey>orc, badly wounded</lightgrey>");assert(full.localized.find("<lightgrey>")!=string::npos);++checked;
 }
 for(bool targeted:{false,true}){
  auto prefix=_target_prefix_arg({},nullptr,targeted);assert(prefix.canonical==(targeted?"Aim":"Look"));assert(prefix.supported);auto unknown=_target_prefix_arg({},"future action",targeted);assert(!unknown.supported);
  auto full=zh_message("target.prompt.describe.item",{unknown,ZhArg("item",ZhArgType::Name,"a stone","已审校物品")});assert(full.localized==full.canonical);++checked;
 }
 cout<<"PASS: "<<checked<<" actual targeting/quiver producer cases, frozen canonical key help, remapped shortcuts, semantic action forms, colour markers and whole-parent unsupported-name fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=30)
