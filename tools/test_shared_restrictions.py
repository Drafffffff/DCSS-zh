#!/usr/bin/env python3
"""Run real shared restriction producers against frozen pre-migration functions.
Only world queries are seams; emitted, list composition and restriction branches
are production code. The fixture makes this test portable outside native Git.
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
refs=json.loads((ROOT/'tools/fixtures/shared-restrictions-english.json').read_text())
files={f:(SRC/f).read_text() for f in refs}
symbols=set(re.findall(r'\b(?:OBJ|DESC|BRANCH|DUR|UNRAND|GOD|SPARM|MUT|SP|WU_JIAN|MSG)_[A-Z_]+\b','\n'.join(sum(refs.values(),[]))))
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
#include <string>
#include <vector>
using namespace std;
'''
code+='enum {'+','.join(sorted(symbols))+'};\n'
code+=r'''
enum class transformation {none,tree,statue,slaughter,death,flux};
struct Props {bool storm=false;bool exists(int)const{return storm;}};
struct item_def {item_def(int b,string e,string c,bool k):base_type(b),english(e),chinese(c),known(k){}int base_type=OBJ_WEAPONS;string english="a weapon",chinese="";bool known=true;string name(int)const{return english;}};
vector<item_def> equipment;
struct WorldPlayer {
 bool demon_axe=false;bool stasis_flag=false,rage=false,mesmerised=false,clear=false,undead=false,no_forms=false;
 bool permanent_light=false,temporary_light=false,halo=false,eos=false,crown=false,light_armour=false;
 int halo_range=1,religion=-1,species=-1,branch=-1;bool transform_uncancellable=false;
 transformation form=transformation::none;int duration[512]={};Props props;
 bool stasis()const{return stasis_flag;}bool berserk()const{return rage;}bool beheld()const{return mesmerised;}bool clarity()const{return clear;}
 bool is_lifeless_undead(bool)const{return undead;}bool has_mutation(int)const{return no_forms;}
 bool backlit(bool,bool temp)const{return permanent_light||(temp&&temporary_light);}
 bool haloed()const{return halo;}int halo_radius()const{return halo_range;}
 bool unrand_equipped(int u)const{return u==UNRAND_EOS?eos:u==UNRAND_VAINGLORY?crown:u==UNRAND_DEMON_AXE?demon_axe:false;}
 bool wearing_ego(int,int)const{return light_armour;}
 bool has_notele_item(vector<const item_def*>*out)const{for(auto &i:equipment)out->push_back(&i);return !equipment.empty();}
};
struct player:WorldPlayer {
 ZhArg no_tele_display_reason(bool,bool)const;
 bool can_go_berserk(bool,bool,bool,string*,bool,ZhArg*)const;
};
struct OldPlayer:WorldPlayer {string no_tele_reason(bool,bool)const;bool can_go_berserk(bool,bool,bool,string*,bool)const;};
player you;struct {bool sprint=false;bool game_is_sprint()const{return sprint;}}crawl_state;
bool lifeless_block=false;
bool lifeless_prevents_form(transformation){return lifeless_block;}
bool player_in_branch(int b){return you.branch==b;}
string make_stringf(const char*fmt,...){char b[4096];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);return b;}
string number_in_words(int n){const char*words[]={"zero","one","two","three","four","five","six","seven","eight","nine"};assert(n>=0&&n<10);return words[n];}
template<typename It>string comma_separated_line(It b,It e){string s;for(It i=b;i!=e;++i){if(i!=b){auto next=i;++next;s+=(next==e?" and ":", ");}s+=*i;}return s;}
ZhArg zh_item_arg(const string&key,const item_def&i,int){return {key,ZhArgType::Name,i.english,i.known?i.chinese:i.english,i.known};}
vector<string> emitted,prompts,rendered,rendered_prompts;bool answer=false;int canned=0;
void mpr(const string&s){emitted.push_back(s);rendered.push_back(s);}void mpr(const ZhMessage&m){emitted.push_back(m.canonical);rendered.push_back(m.display());}
int yesno(const char*s,bool,int){prompts.push_back(s);rendered_prompts.push_back(s);return answer;}
int yesno(const ZhMessage&m,bool,int){prompts.push_back(m.canonical);rendered_prompts.push_back(m.display());return answer;}
void canned_msg(int){++canned;}
void reset_events(){emitted.clear();prompts.clear();rendered.clear();rendered_prompts.clear();canned=0;}
struct Events {vector<string>emitted,prompts;int canned;Events():emitted(::emitted),prompts(::prompts),canned(::canned){}bool operator==(const Events&b)const{return emitted==b.emitted&&prompts==b.prompts&&canned==b.canned;}};
'''
for f,blocks in refs.items():
    for s in blocks:
        s=s.replace('player::','OldPlayer::').replace('bool invis_allowed(','bool old_invis_allowed(').replace('string cant_transform_reason(','string old_cant_transform_reason(')
        code+=s+'\n'
for f,needle in [('player.cc','ZhArg player::no_tele_display_reason('),('player.cc','bool invis_allowed('),('player-act.cc','bool player::can_go_berserk(bool intentional'),('transform.cc','ZhArg cant_transform_display_reason(')]:
    code+=block(files[f],needle)+'\n'
code+=r'''
int checks=0;
void verify_rendering(){assert(rendered.size()==emitted.size()&&rendered_prompts.size()==prompts.size());for(size_t i=0;i<emitted.size();++i)assert(rendered[i]!=emitted[i]);for(size_t i=0;i<prompts.size();++i)assert(rendered_prompts[i]!=prompts[i]);}
void compare(const ZhArg&v,const string&old){
 if(v.canonical!=old){cerr<<"Canonical drift: ["<<v.canonical<<"] != ["<<old<<"]\n";abort();}
 if(!old.empty()&&v.supported)assert(v.localized!=old);
 if(!v.supported)assert(v.localized==v.canonical);
 ++checks;
}
OldPlayer old_player(){OldPlayer old;static_cast<WorldPlayer&>(old)=static_cast<WorldPlayer&>(you);return old;}
void fresh(){you=player();equipment.clear();crawl_state.sprint=false;lifeless_block=false;reset_events();}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.shared.restrictions");
 // Equipment thresholds differ with pre-existing problems; both known and
 // unknown name children exercise full-parent fallback propagation.
 for(int flags=0;flags<32;++flags)for(int n=0;n<7;++n)for(bool weapon:{false,true})for(bool known:{false,true})for(bool blink:{false,true})for(bool temp:{false,true}){
  fresh();you.stasis_flag=flags&1;crawl_state.sprint=flags&2;you.branch=(flags&4)?BRANCH_GAUNTLET:-1;you.duration[DUR_DIMENSION_ANCHOR]=!!(flags&8);if(flags&16)you.form=transformation::tree;
  if(weapon)equipment.push_back({OBJ_WEAPONS,"a branded weapon","测试武器",known});
  for(int k=0;k<n;++k)equipment.push_back({OBJ_ARMOUR,"an artefact "+to_string(k),"测试装备"+to_string(k),known});
  auto expected=old_player().no_tele_reason(blink,temp);auto result=you.no_tele_display_reason(blink,temp);compare(result,expected);
  // Names disappear legitimately in the summarized quantity branch.
  if(!expected.empty()&&known)assert(result.supported);
  if(!known&&(expected.find("a branded weapon")!=string::npos||expected.find("an artefact ")!=string::npos))assert(!result.supported&&result.localized==expected);
 }
 // All rage flags together establish the exact first-failure precedence.
 for(int flags=0;flags<256;++flags)for(bool intentional:{false,true})for(bool potion:{false,true})for(bool quiet:{false,true})for(bool temp:{false,true}){
  fresh();you.rage=flags&1;you.duration[DUR_BERSERK_COOLDOWN]=!!(flags&2);you.duration[DUR_DEATHS_DOOR]=!!(flags&4);you.mesmerised=flags&8;you.clear=flags&16;you.undead=flags&32;you.stasis_flag=flags&64;you.demon_axe=flags&128;
  string before="sentinel",after="sentinel";auto old=old_player();bool a=old.can_go_berserk(intentional,potion,quiet,&before,temp);Events events;reset_events();ZhArg display;
  bool b=you.can_go_berserk(intentional,potion,quiet,&after,temp,&display);assert(a==b&&before==after&&Events()==events);verify_rendering();if(!b){compare(display,before);assert(display.supported);}++checks;
 }
 // Source combinations, permanent/temporary backlight and yes/no acceptance.
 for(int flags=0;flags<512;++flags)for(bool temp:{false,true})for(bool quiet:{false,true})for(bool yes:{false,true}){
  fresh();you.permanent_light=flags&1;you.temporary_light=flags&2;you.halo=flags&4;you.eos=flags&8;you.crown=flags&16;you.light_armour=flags&32;you.props.storm=flags&64;you.religion=(flags&128)?GOD_SHINING_ONE:-1;you.halo_range=(flags&256)?-1:1;answer=yes;
  string before="sentinel",after="sentinel";bool a=old_invis_allowed(quiet,&before,temp);Events events;reset_events();ZhArg display;
  bool b=invis_allowed(quiet,&after,temp,&display);assert(a==b&&before==after&&Events()==events);verify_rendering();if(!b){compare(display,before);assert(display.supported);}++checks;
 }
 for(int flags=0;flags<32;++flags)for(auto form:{transformation::tree,transformation::statue,transformation::slaughter,transformation::death,transformation::flux})for(bool involuntary:{false,true})for(bool temp:{false,true}){
  fresh();you.no_forms=flags&1;lifeless_block=flags&2;you.species=(flags&4)?SP_GARGOYLE:-1;you.transform_uncancellable=flags&8;you.duration[DUR_DEATHS_DOOR]=!!(flags&16);
  compare(cant_transform_display_reason(form,involuntary,temp),old_cant_transform_reason(form,involuntary,temp));
 }
 cout<<"PASS: "<<checks<<" real shared-restriction cases; canonical snapshots, state priority, confirmation and log effects\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
    source=Path(tmp)/'test.cc';source.write_text(code);exe=Path(tmp)/'test'
    subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(source),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=30)
