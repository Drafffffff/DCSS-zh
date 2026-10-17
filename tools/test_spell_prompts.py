#!/usr/bin/env python3
"""Compile real spell prompt producers against frozen pre-migration behavior."""
import json,subprocess,tempfile,unicodedata
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
catalog=compile_catalog()
width=lambda s:sum(2 if unicodedata.east_asian_width(c) in ('W','F') else 1 for c in s)
for suffix,pairs in [('base',[('Type','类型'),('Failure','失败率'),('Level','等级')]),('extra',[('Power','威力'),('Damage','伤害'),('Range','射程'),('Noise','噪声')])]:
 entry=catalog['spell.prompt.menu.header.'+suffix]
 for en,zh in pairs:assert width(entry['en'][:entry['en'].index(en)])==width(entry['zh'][:entry['zh'].index(zh)]),(suffix,en)
 assert width(entry['en'])==width(entry['zh'])
s=(SRC/'spl-cast.cc').read_text()
refs=json.loads((ROOT/'tools/fixtures/spell-prompt-english.json').read_text())['functions']
assert '_spell_failure_rate_description' not in s
assert 'args.top_prompt_message = ZhMessage{title.message_id' in s
assert 'spell_menu.set_more_pretranslated(more_str)' in s
assert 'chop_string(\n        zh_message("spell.prompt.menu.title"' in s
assert 'parse_string(failure_rate)' not in s
assert 'me->pretranslated = true' in s
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <iostream>
using namespace std;
using spell_type=int;
enum {MSGCH_WARN,DIS_CONFIRMATIONS,MSG_OK};
int severity=0,failure=0;bool consent=true,known=true;
string captured,reason;bool was_prompt=false;
struct text_pattern {bool enabled;bool matches(const char*)const{return enabled;}};
struct {vector<text_pattern>confirm_action;int fail_severity_to_confirm=0;}Options;
struct {bool disables[1]={false};}crawl_state;
const char*spell_title(int){return known?"Magic Dart":"Unreviewed future spell";}
int fail_severity(int){return severity;}
int raw_spell_fail(int){return failure;}
int failure_rate_to_int(int x){return x;}
string failure_rate_to_string(int x){return to_string(x)+"%";}
int failure_rate_colour(int){return severity;}
string colour_to_str(int x){static const char*c[]={"lightgrey","white","yellow","lightred","red","magenta"};return c[x];}
const char*fail_severity_adjs[]={"safe","mildly dangerous","dangerous","quite dangerous","extremely dangerous","astonishingly dangerous"};
template<class...A>string make_stringf(const char*f,A...a){char b[4096];snprintf(b,sizeof b,f,a...);return b;}
string spell_failure_rate_string(int s,bool){auto c=colour_to_str(failure_rate_colour(s));return "<"+c+">"+to_string(failure)+"%</"+c+">";}
ZhArg spell_uselessness_display_reason(int,bool,bool,bool){return ZhArg("reason",ZhArgType::Text,reason,reason);}
bool yesno(const char*p,bool,char){was_prompt=true;captured=p;return consent;}
bool yesno(const ZhMessage&m,bool b,char c){return yesno(m.canonical.c_str(),b,c);}
void mpr(const ZhMessage&m,int=0){captured=m.canonical;}
template<class...A>void mprf(int,const char*f,A...a){captured=make_stringf(f,a...);}
void canned_msg(int){}
'''
code+=refs['static string _spell_failure_rate_description(spell_type spell)\n'].replace('_spell_failure_rate_description','old_risk')+'\n'
code+=refs['static bool _spellcasting_aborted(spell_type spell, bool fake_spell)'].replace('_spellcasting_aborted','old_abort')+'\n'
for name in ['static ZhArg _spell_menu_name(', 'static ZhArg _spell_menu_action(', 'static ZhArg _spell_failure_rate_arg(const string &key, spell_type spell)\n','static bool _spellcasting_aborted(']:code+=block(s,name)+'\n'
code+=r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.spell-prompts");int checked=0;
for(severity=0;severity<6;++severity)for(int f:{0,1,29,99,100,150}){failure=f;
 auto risk=_spell_failure_rate_arg("risk",0);assert(risk.canonical==old_risk(0));assert(risk.localized!=risk.canonical);
 for(bool n:{false,true})for(bool answer:{false,true})for(bool fake:{false,true})for(bool disabled:{false,true})for(int threshold:{0,1,2,3,5,7})for(bool confirm:{false,true})for(bool useless:{false,true}){
  known=n;consent=answer;Options.confirm_action={{confirm}};Options.fail_severity_to_confirm=threshold;crawl_state.disables[0]=disabled;reason=useless?"canonical reason":"";
  captured="";was_prompt=false;bool expected=old_abort(0,fake);string expected_message=captured;bool expected_prompt=was_prompt;
  captured="";was_prompt=false;bool actual=_spellcasting_aborted(0,fake);assert(actual==expected);assert(captured==expected_message);assert(was_prompt==expected_prompt);++checked;
 }
}
for(const char*action:{"cast","describe","adjust","adjust it to","forget","quiver","unknown future action"}){
 auto a=_spell_menu_action(action);auto m=zh_message("spell.prompt.menu.title",{a});assert(m.canonical==string("Your spells (")+action+")");assert(a.supported==(string(action)!="unknown future action"));if(!a.supported)assert(m.canonical==m.localized);++checked;
}
severity=0;failure=29;
for(bool n:{false,true})for(int available:{0,1,99}){
 known=n;auto title=zh_message_arg("title","spell.prompt.target.aim",{zh_colour("colour","w"),_spell_menu_name(0)});
 title=zh_message_arg("title","spell.prompt.target.risk",{title,_spell_failure_rate_arg("risk",0)});
 title=zh_message_arg("title","spell.prompt.target.charges",{title,zh_integer("available",available),zh_integer("maximum",3)});
 assert(title.supported==n);if(!n)assert(title.canonical==title.localized);++checked;
}
cout<<"PASS: "<<checked<<" actual spell prompt/risk/confirmation cases; frozen canonical Lua prompts, accept/cancel behavior, semantic menu actions and complete unknown-name fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=60)
