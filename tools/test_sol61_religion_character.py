#!/usr/bin/env python3
"""Compile extracted production functions against frozen pre-migration functions.
No global catalog generation: a temporary catalog isolates this work package.
World mechanics are seams; production branches, formatting and state writes run.
"""
import json,re,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'native/crawl-ref/source'
CAT=ROOT/'localization/migration/luna-sol61-religion-character-messages.json'

def block(s,needle):
    start=s.index(needle); at=s.index('{',start); depth=0; quoted=False; escaped=False
    # C++ lexer ignores braces in strings/chars and comments.
    i=at; state='code'
    while i<len(s):
        c=s[i]; n=s[i:i+2]
        if state=='line':
            if c=='\n':state='code'
        elif state=='comment':
            if n=='*/':state='code';i+=1
        elif state in ('"',"'"):
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c==state:state='code'
        elif n=='//':state='line';i+=1
        elif n=='/*':state='comment';i+=1
        elif c in ('"',"'"):state=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return s[start:i+1]
        i+=1
    raise AssertionError(needle)

def validate():
    doc=json.loads(CAT.read_text()); assert doc['model']==doc['reviewer_model']=='gpt-6.1-sol'
    ids=set();slots=re.compile(r'\{([a-z][a-z0-9_]*)\}')
    for x in doc['messages']:
        assert x['id'] not in ids;ids.add(x['id'])
        assert x['source'] and x['context']
        assert set(slots.findall(x['en']))==set(slots.findall(x['zh']))==set(x['params']),x['id']
        assert sorted(re.findall(r'</?[^>]+>',x['en']))==sorted(re.findall(r'</?[^>]+>',x['zh'])),x['id']
    return doc

def main():
    doc=validate();menu=block((SRC/'ability.cc').read_text(),'int choose_ability_menu(')
    assert menu.count('_talent_menu_message(talents[i]).display()')==4
    assert menu.count('me->pretranslated = true;')==3 and 'title->pretranslated = true;' in menu
    assert menu.count('set_more_pretranslated(')==2 and 'hints_abilities_info()' not in menu
    refs=json.loads((ROOT/'tools/fixtures/sol61-religion-character-english.json').read_text())
    assert block((SRC/'god-conduct.cc').read_text(),'struct dislike_response')==block(refs['god-conduct.cc'],'struct dislike_response'), 'unowned response semantics changed'
    needles={
      'player-stats.cc':['const char* stat_desc(','static void _handle_stat_change(stat_type stat)\n{','void modify_stat(','void notify_stat_change(stat_type which_stat,','bool attribute_increase('],
      'god-prayer.cc':['static bool _prompt_ecu_worship(','void try_god_conversion(','int zin_tithe('],
      'religion.cc':['void dock_piety(','void ostracise_player(','void player_change_ostracism(','void print_god_rejection('],
      'god-abil.cc':['static int _gold_to_donation(','bool zin_donate_gold(','void tso_divine_shield(','void tso_expend_divine_shield_charge(','void elyvilon_purification(','void elyvilon_remove_divine_vigour('],
      'god-passive.cc':['void qazlal_element_adapt('],
      'mutation.cc':['static const char* _stat_mut_desc(','bool temp_mutation_wanes('],
      'ability.cc':['const string make_cost_description(','string describe_talent('],
      'god-conduct.cc':['struct like_response','static int _piety_bonus_for_holiness(','static like_response _on_kill(']}
    allblocks='\n'.join(block(refs[f],n) for f,ns in needles.items() for n in ns)
    symbols=set(re.findall(r'\b(?:ABIL|MH|MSGCH|MSG|GOD|MUT|STAT|SD|ATTR|DUR|TS|NOTE|HINT|BRANCH|BEAM|CK|SK|MOUSE)_[A-Z_]+\b',allblocks))
    symbols.update(['NUM_STATS','NUM_STAT_DESCS','STAT_RANDOM','SD_NAME','SD_INCREASE','SD_DECREASE','STAT_STR','STAT_INT','STAT_DEX','ATTR_STAT_ZERO','ATTR_TEMP_MUT_KILLS','MSGCH_PLAIN','GOD_ELYVILON','GOD_OKAWARU','MUT_NO_LOVE','GOD_TROG','ABIL_NON_ABILITY','ABIL_RENOUNCE_RELIGION','ABIL_EVOKE_TURN_INVISIBLE','ABIL_GOZAG_POTION_PETITION','ABIL_CACOPHONY','ABIL_HEAL_WOUNDS'])
    # Stats are array indexes, descriptor rows mirror the frozen production data.
    special=['STAT_STR','STAT_INT','STAT_DEX','NUM_STATS','SD_NAME','SD_LOSS','SD_DECREASE','SD_INCREASE','NUM_STAT_DESCS']
    symbols-=set(special)
    code='''#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cwchar>
#include <clocale>
#include <iomanip>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
using stat_type=int;using stat_desc_type=int;using mutation_type=int;using god_type=int;using beam_type=int;using duration_type=int;
enum {STAT_STR,STAT_INT,STAT_DEX,NUM_STATS};
enum {SD_NAME,SD_LOSS,SD_DECREASE,SD_INCREASE,NUM_STAT_DESCS};
'''
    code+='\n'.join('const int '+symbol+'='+str(i+10)+';' for i,symbol in enumerate(sorted(symbols)))+'\nconst int NUM_DURATIONS=900;\n'
    code+=r'''
#define ASSERT(x) assert(x)
#define ASSERT_RANGE(x,a,b) assert((x)>=(a)&&(x)<(b))
#define CASE_ESCAPE case CK_ESCAPE:
const int MAX_OSTRACISM=300,MAX_PIETY=200,MAX_PENANCE=200;
enum class easy_confirm_type {all,none};
struct {easy_confirm_type easy_confirm=easy_confirm_type::all;} Options;
vector<string> events;
struct AbilityProps {vector<int>v;AbilityProps&operator[](const char*){return *this;}vector<int>&get_vector(){return v;}};
struct PietyInfo {void record_conduct_like(int c,int g,int d){events.push_back("conduct:"+to_string(c)+":"+to_string(g)+":"+to_string(d));}};
struct Player {AbilityProps props;PietyInfo piety_info;int get_experience_level()const{return 10;}

 int religion=GOD_ZIN,gold=100,raw_piety=50,num_turns=0,attribute[1024]={},duration[1024]={},penance[1024]={},base_stats[3]={10,10,10};
 int bonus=0;bool forlorn=false,divine=false,silent=false,turn_is_over=false,redraw_title=false,redraw_armour_class=false,redraw_evasion=false,redraw_stats[3]={};
 int strength()const{return base_stats[0]+bonus;}int intel()const{return base_stats[1]+bonus;}int dex()const{return base_stats[2]+bonus;}
 int stat(int i)const{return base_stats[i]+bonus;}int piety()const{return max(0,raw_piety-attribute[ATTR_OSTRACISM]);}
 bool has_mutation(int m)const{return m==MUT_FORLORN?forlorn:m==MUT_DIVINE_ATTRS?divine:false;}
 bool cannot_speak()const{return silent;}int get_mutation_level(int)const{return forlorn?1:0;}
 int skill_rdiv(int,int n=1,int d=1)const{return 12*n/d;}
 void del_gold(int n){gold-=n;}void increase_duration(int d,int v,int maxv=9999){duration[d]=min(maxv,duration[d]+v);}
}you;
struct {bool seen_hups=false,stat_gain_prompt=false;bool game_is_arena()const{return false;}}crawl_state;
struct {int absdepth0=3;}env;
vector<string> canon,displayed;int rng=0,seed=0;bool answer=true,passive=true,chance=true,under_penance=false,orc=false;vector<int> keys;size_t keyat=0;
string make_stringf(const char*fmt,...){char b[8192];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);return b;}
void mpr(const string&s,int ch=MSGCH_PLAIN,int p=0){canon.push_back(s);displayed.push_back(s);events.push_back("channel:"+to_string(ch)+":"+to_string(p));}
void mpr(const ZhMessage&m,int ch=MSGCH_PLAIN,int p=0){canon.push_back(m.canonical);displayed.push_back(m.display());events.push_back("channel:"+to_string(ch)+":"+to_string(p));}
void mprf(const char*fmt,...){char b[8192];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);mpr(string(b));}
void mprf(int ch,const char*fmt,...){char b[8192];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);mpr(string(b),ch);}
void mprf(int ch,int p,const char*fmt,...){char b[8192];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);mpr(string(b),ch,p);}
void dprf(const char*,...){}
[[noreturn]] void die(const char*,int=0){abort();}
string god_name(int g){return g==GOD_ZIN?"Zin":g==GOD_ECUMENICAL?"an unknown god":g==GOD_XOM?"Xom":g==GOD_GOZAG?"Gozag":g==GOD_ELYVILON?"Elyvilon":g==GOD_OKAWARU?"Okawaru":g==GOD_TROG?"Trog":"Future Unknown God";}
bool you_worship(int g){return you.religion==g;}
void god_pitch(int g){events.push_back("pitch:"+to_string(g));}
bool _pray_ecumenical_altar(){events.push_back("ecumenical");return true;}
void describe_god(int g){events.push_back("describe:"+to_string(g));}
void flush_prev_message(){events.push_back("flush");}int getch_ck(){assert(keyat<keys.size());return keys[keyat++];}int getchm(){return getch_ck();}
void canned_msg(int m){events.push_back("canned:"+to_string(m));}
int yesno(const char*s,bool b,int d){mpr(s,MSGCH_PROMPT);events.push_back(to_string(b)+":"+to_string(d));return answer;}
int yesno(const ZhMessage&m,bool b,int d){mpr(m,MSGCH_PROMPT);events.push_back(to_string(b)+":"+to_string(d));return answer;}
template<class I>string comma_separated_line(I start,I end,const string&last){vector<string>v(start,end);string out;for(size_t i=0;i<v.size();++i){if(i)out+=i+1==v.size()?last:", ";out+=v[i];}return out;}
int piety_scale(int n){events.push_back("scale:"+to_string(n));return n;}
void lose_piety(int n){you.raw_piety-=n;events.push_back("lose:"+to_string(n));}
void excommunication(){you.religion=GOD_NO_GOD;events.push_back("excommunication");}
void _inc_penance(int n){you.penance[you.religion]+=n;events.push_back("penance:"+to_string(n));}
void god_speaks(int g,const char*s){mpr(string(s),MSGCH_GOD,g);}
string god_speaker(int g=you.religion){return god_name(g);}
void simple_god_message(const char*s,bool=false,int g=you.religion){mpr(god_speaker(g)+s,MSGCH_GOD,g);}
bool loveless_reject=true,transformed_can_join=true;bool _god_rejects_loveless(int){return loveless_reject;}bool _transformed_player_can_join_god(int){return transformed_can_join;}int gozag_service_fee(){return 87;}
void _handle_piety_gain(int n){events.push_back("gain-handler:"+to_string(n));}void _handle_piety_loss(int n){events.push_back("loss-handler:"+to_string(n));}
int random2(int n){events.push_back("random2:"+to_string(n));return (seed+rng++)%n;}
int random_range(int a,int b){return a+random2(b-a+1);}
void delete_temp_mutation(){events.push_back("delete-temp");--you.attribute[ATTR_TEMP_MUTATIONS];}
void learned_something_new(int n){events.push_back("hint:"+to_string(n));}
int innate_stat(int i){return you.base_stats[i];}
struct mouse_control{mouse_control(int){events.push_back("mouse");}};
struct {bool callfn(const char*s,int,int){events.push_back(s);return false;}void fnreturns(const char*,string*){}}clua;
int toupper_safe(int c){return toupper(c);}void redraw_screen(){events.push_back("redraw");}void update_screen(){events.push_back("update");}
int piety_breakpoint(int i){return (i+1)*30;}
bool player_under_penance(){return under_penance;}bool player_in_branch(int){return orc;}
struct Note{int n,a,b;string text;Note(int n_,int a_=0,int b_=0,string s=""):n(n_),a(a_),b(b_),text(s){}};
void take_note(Note n){events.push_back("note:"+to_string(n.n)+":"+to_string(n.a)+":"+to_string(n.b)+":"+n.text);}
int stepdown_value(int n,int,int,int,int){events.push_back("stepdown");return n/2;}
const char*ACQUIRE_KEY="acquire";
struct Props{bool acquired=false;bool exists(const char*)const{return acquired;}};
struct item_def{int tithe_state=TS_NO_TITHE;Props props;};
void gain_piety(int n,int d){events.push_back("piety:"+to_string(n)+":"+to_string(d));}
void undrain_hp(int n){events.push_back("undrain:"+to_string(n));}void calc_hp(){events.push_back("calc-hp");}void calc_mp(){events.push_back("calc-mp");}
namespace passive_t {const int elemental_adaptation=0;}
bool have_passive(int){events.push_back("passive");return passive;}int piety_rank(){return 3;}
bool x_chance_in_y(int a,int b){events.push_back("chance:"+to_string(a)+":"+to_string(b));return chance;}
int get_beam_resist_type(int b){return b;}
'''
    code+=r"""
using ability_type=int;using conduct_type=int;using mon_holy_type=int;
namespace abflag {enum {variable_mp=1,breath=2,drac_charges=4,delay=8,torment=16,injury=32,exhaustion=64,instant=128,max_hp_drain=256,curse=512,gold=1024,sacrifice=2048,card=4096,torchlight=8192};}
const char* CURSE_KNOWLEDGE_KEY="curse";const int MAX_DRACONIAN_BREATH=3;
struct ability_def{int mp=0,hp=0,piety_cost=0,flags=0;int get_mp_cost()const{return mp;}int get_hp_cost()const{return hp;}string piety_pips()const{return "***";}}definition;
const ability_def&get_ability_def(int){return definition;}
struct talent{int which=ABIL_RENOUNCE_RELIGION,fail=0;};
bool invis_drain=false;int gold_cost=0;
bool _invis_causes_drain(){return invis_drain;}int get_gold_cost(int){return gold_cost;}int get_real_mp(bool){return 7;}int draconian_breath_uses_available(){return 2;}
string ability_name(int a){return a==ABIL_RENOUNCE_RELIGION?"Renounce Religion":a==-111?"Unreviewed Future Ability":"Sacrifice Unknown";}
string ru_sac_text(int){return " (value)";}string nemelex_card_text(int){return "(3 in deck)";}string _ashenzari_curse_text(){return "(Boost: Fighting)";}
// SOL61_UNICODE_PRODUCTION
string trimmed_string(string s){while(!s.empty()&&s.back()==' ')s.pop_back();return s;}
string failure_rate_to_string(int f){return to_string(f)+"%";}
struct monster{};using special_piety_t=void(*)(int&,int&,const monster*);
struct god_acting{god_acting(){events.push_back("god-start");}~god_acting(){events.push_back("god-end");}};
bool likes_kill=true;bool _god_likes_killing(const monster&){return likes_kill;}
void _handle_piety_penance(int g,int d,int p,int c){events.push_back("piety-penance:"+to_string(g)+":"+to_string(d)+":"+to_string(p)+":"+to_string(c));}
"""
    # Forward declarations keep the production mutually calling order intact.
    for name,source in [('frozen',refs),('production',{f:(SRC/f).read_text() for f in needles})]:
        code+='namespace '+name+' {\nvoid player_change_ostracism(int);void modify_stat(int,int,bool);\n'
        code+='static const char* descs[NUM_STATS][NUM_STAT_DESCS]={{"strength","weakened","weaker","stronger"},{"intelligence","dopey","stupid","clever"},{"dexterity","clumsy","clumsy","agile"}};\n'
        if name=='production':
            code+=block(source['religion.cc'],'static void _religion_god_log(')+'\n'+block(source['religion.cc'],'static void _god_welcome_message(')+'\n'
            for needle in ['static ZhMessage _stat_change_message(','static ZhArg _stat_name_arg(']:
                # stat_desc must be declared before helper.
                code+='const char* stat_desc(stat_type,stat_desc_type);\n'+block(source['player-stats.cc'],needle)+'\n'
        for f,ns in needles.items():
            if f=='god-conduct.cc' and name=='production':code+=block(source[f],'static void _conduct_god_log(')+'\n'
            for n in ns:code+=block(source[f],n)+(';' if n=='struct like_response' else '')+'\n'
        if name=='production':
            for n in ['static ZhArg _ability_menu_cost_arg(','static ZhMessage _talent_menu_message(','static ZhMessage _ability_menu_hints_message(']:code+=block(source['ability.cc'],n)+'\n'
        if name=='production':code+=block(source['mutation.cc'],'static ZhMessage _stat_mutation_message(')+'\n'
        code+='}\n'
    code+=r'''
string snapshot(){ostringstream s;s<<you.religion<<","<<you.gold<<","<<you.raw_piety<<","<<you.turn_is_over<<","<<you.redraw_title<<","<<you.redraw_armour_class<<","<<you.redraw_evasion<<","<<crawl_state.stat_gain_prompt<<","<<rng<<","<<keyat;for(int i=0;i<1024;++i)s<<","<<you.attribute[i]<<","<<you.duration[i]<<","<<you.penance[i];for(int i=0;i<3;++i)s<<","<<you.base_stats[i]<<","<<you.redraw_stats[i];return s.str();}
void clear(){events.clear();canon.clear();displayed.clear();rng=0;keyat=0;crawl_state.stat_gain_prompt=false;}
int checks=0;
template<class A,class B>void compare(A a,B b){Player initial=you;clear();int x=a();auto old=canon;auto effects=events;string oldstate=snapshot();you=initial;clear();int y=b();if(old!=canon||effects!=events||oldstate!=snapshot()||x!=y){cerr<<"case "<<checks<<"\n";for(auto&s:old)cerr<<"OLD: "<<s<<"\n";for(auto&s:canon)cerr<<"NEW: "<<s<<"\n";cerr<<"results "<<x<<":"<<y<<" events "<<(effects==events)<<" state "<<(oldstate==snapshot())<<"\n";abort();}++checks;}
#define COMPARE(call) compare([&](){return frozen::call;},[&](){return production::call;})
#define COMPARE_VOID(call) compare([&](){frozen::call;return 0;},[&](){production::call;return 0;})
int main(){assert(setlocale(LC_CTYPE,""));setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.sol61.religion.character");
 for(int m:{MUT_STRONG,MUT_WEAK,MUT_CLEVER,MUT_DOPEY,MUT_AGILE,MUT_CLUMSY})for(bool g:{false,true}){auto now=production::_stat_mutation_message(m,g);assert(now.canonical==make_stringf("You feel %s.",frozen::_stat_mut_desc(m,g)));assert(now.display()!=now.canonical);++checks;}
 for(int r:{GOD_NO_GOD,GOD_ZIN,GOD_XOM,GOD_GOZAG})for(int n:{0,1,39,40,299,300})for(int a:{-500,-1,0,1,500}){you=Player();you.religion=r;you.attribute[ATTR_OSTRACISM]=n;COMPARE_VOID(ostracise_player(a));you.attribute[ATTR_OSTRACISM]=n;COMPARE_VOID(player_change_ostracism(a));}
 for(int n=1;n<120;++n)for(int p:{0,1,3})for(bool lecture:{false,true}){you=Player();you.num_turns=n;you.raw_piety=50;COMPARE_VOID(dock_piety(n%18,p,lecture));}
 for(int g:{GOD_GOZAG,GOD_OKAWARU,GOD_ZIN})for(int money:{0,1,1000})for(int flags=0;flags<8;++flags){you=Player();you.gold=money;you.forlorn=flags&1;loveless_reject=flags&2;transformed_can_join=flags&4;COMPARE_VOID(print_god_rejection(g));for(size_t i=0;i<canon.size();++i)assert(canon[i]!=displayed[i]);}
 for(int g:{GOD_ZIN,GOD_XOM,GOD_ELYVILON})for(bool returning:{false,true}){you=Player();clear();production::_god_welcome_message(g,returning);assert(canon[0]==god_speaker(g)+(returning?" welcomes you back!":" welcomes you!"));assert(displayed[0]!=canon[0]);++checks;}
 for(int r:{GOD_NO_GOD,GOD_ZIN,GOD_XOM})for(int g:{GOD_ZIN,GOD_ECUMENICAL,GOD_XOM})for(bool f:{false,true})for(bool quiet:{false,true}){you=Player();you.religion=r;you.forlorn=f;you.silent=quiet;COMPARE_VOID(try_god_conversion(g));if(r==g&&!f&&g!=GOD_ECUMENICAL)assert(canon[0]!=displayed[0]);}
 for(vector<int> gods:vector<vector<int>>{{GOD_ZIN},{GOD_ZIN,GOD_XOM},{GOD_ZIN,GOD_XOM,GOD_ELYVILON},{GOD_ZIN,GOD_NO_GOD}})for(int k:vector<int>{CK_ENTER,CK_ESCAPE,'y','n'}){keys={'a',k};you=Player();COMPARE(_prompt_ecu_worship(gods));bool known=find(gods.begin(),gods.end(),GOD_NO_GOD)==gods.end();assert(known?(displayed[0]!=canon[0]):(displayed[0]==canon[0]));assert(canon[0].find("(a) Zin")!=string::npos);}
 for(int due:{0,1,9,10,99})for(int q:{1,10,500})for(int p:{0,199,200})for(int state:{TS_NO_TITHE,TS_NO_PIETY,-1})for(bool acquired:{false,true})for(bool convert:{false,true}){you=Player();you.attribute[ATTR_TITHE_BASE]=due;you.raw_piety=p;item_def item;item.tithe_state=state;item.props.acquired=acquired;COMPARE(zin_tithe(item,q,convert));}
 for(int gold:{0,1,2,10,100,1000,20000,1000000})for(int p:{0,29,30,59,60,89,90,119,120,149,150,179,180,200})for(bool ans:{false,true})for(bool pen:{false,true}){you=Player();you.gold=gold;you.raw_piety=p;you.penance[GOD_ZIN]=500;answer=ans;under_penance=pen;COMPARE(zin_donate_gold());}
 for(int d:{0,1,2,20}){you=Player();you.duration[DUR_DIVINE_SHIELD]=d;COMPARE_VOID(tso_divine_shield());you.duration[DUR_DIVINE_SHIELD]=d;COMPARE_VOID(tso_expend_divine_shield_charge());}
 for(int n=0;n<9;++n){you=Player();fill(begin(you.duration),end(you.duration),n);COMPARE_VOID(elyvilon_purification());COMPARE_VOID(elyvilon_remove_divine_vigour());}
 for(int f:{BEAM_FIRE,BEAM_STICKY_FLAME,BEAM_STEAM,BEAM_COLD,BEAM_ELECTRICITY,BEAM_MISSILE,-1})for(int flags=0;flags<64;++flags)for(int strength:{0,2}){you=Player();you.duration[DUR_QAZLAL_FIRE_RES]=flags&1;you.duration[DUR_QAZLAL_COLD_RES]=flags&2;you.duration[DUR_QAZLAL_ELEC_RES]=flags&4;you.duration[DUR_QAZLAL_AC]=flags&8;passive=flags&16;chance=flags&32;COMPARE_VOID(qazlal_element_adapt(f,strength));if(!canon.empty())assert(canon.back()!=displayed.back());}
 for(int n=0;n<10;++n)for(int s:{0,1}){you=Player();you.attribute[ATTR_TEMP_MUTATIONS]=n;seed=s;COMPARE(temp_mutation_wanes());if(n)assert(canon[0]!=displayed[0]);}
 for(int stat:vector<int>{STAT_STR,STAT_INT,STAT_DEX,STAT_RANDOM})for(int base:{-2,0,1,10})for(int a:{-5,-1,0,1,5})for(bool quiet:{false,true})for(int mask=0;mask<8;++mask){you=Player();fill(begin(you.base_stats),end(you.base_stats),base);you.attribute[ATTR_STAT_ZERO]=mask;COMPARE_VOID(modify_stat(stat,a,quiet));you=Player();you.attribute[ATTR_STAT_ZERO]=mask;you.bonus=base;COMPARE_VOID(notify_stat_change(stat,a,quiet));}
 for(bool caps:{false,true})for(bool divine:{false,true})for(int bonus:{0,2})for(char key:{'S','I','D'}){you=Player();you.divine=divine;you.bonus=bonus;Options.easy_confirm=caps?easy_confirm_type::none:easy_confirm_type::all;keys={CK_REDRAW,'s',key};COMPARE(attribute_increase());for(size_t i=0;i<canon.size();++i)assert(canon[i]!=displayed[i]);}
 for(int flags=0;flags<16384;flags+=13)for(int mp:{0,5})for(int hp:{0,8})for(int gold:{0,123}){definition=ability_def();definition.flags=flags;definition.mp=mp;definition.hp=hp;definition.piety_cost=flags&2;gold_cost=gold;talent t;t.fail=flags%101;auto expected=frozen::describe_talent(t);auto now=production::_talent_menu_message(t);assert(now.canonical==expected);bool supported=!(flags&(abflag::sacrifice|abflag::card));assert(supported?(now.localized!=now.canonical):(now.localized==now.canonical));if(supported)assert(now.localized.find(to_string(t.fail)+"%")!=string::npos);++checks;}
 definition=ability_def();talent renounce;auto ren=production::_talent_menu_message(renounce);assert(ren.localized.find("放弃信仰")!=string::npos&&ren.localized.find("无")!=string::npos);renounce.which=-111;ren=production::_talent_menu_message(renounce);assert(ren.localized==ren.canonical);
 for(string color:{"lightgrey","yellow"}){auto help=production::_ability_menu_hints_message(color);assert(help.canonical.find("This screen shows your character's set of talents.")!=string::npos);assert(help.localized.find("此界面显示你拥有的能力。")!=string::npos);assert(help.localized.find("<w>!</w>")!=string::npos&&help.localized.find("<w>?</w>")!=string::npos);assert(help.localized.find("<"+color+">")==0);++checks;}
 for(int god:{GOD_TROG,GOD_ZIN,GOD_XOM,GOD_ELYVILON,GOD_NO_GOD})for(int holy:{MH_NATURAL,MH_PLANT,MH_NONLIVING,MH_DEMONIC,MH_UNDEAD})for(int level:{0,1,30,100})for(bool good:{false,true})for(bool liked:{false,true}){you=Player();you.religion=god;likes_kill=liked;monster victim;compare([&](){auto response=frozen::_on_kill("kill",holy,good);response(5,level,true,&victim);return 0;},[&](){auto response=production::_on_kill("kill",holy,good);response(5,level,true,&victim);return 0;});if(liked)assert(god==GOD_NO_GOD?(canon[0]==displayed[0]):(canon[0]!=displayed[0]));}
 // Header and talent columns include the different title/hotkey prefixes.
 for(string id:{"character.ability.menu.title_use","character.ability.menu.title_describe"}){
  auto header=zh_message(id);assert(header.localized.find("—")==string::npos);
  assert(strwidth(title_indent)+strwidth(header.localized.substr(0,header.localized.find("代价")))==strwidth(row_preface)+32);
  assert(strwidth(title_indent)+strwidth(header.localized.substr(0,header.localized.find("失败率")))==strwidth(row_preface)+64);
  assert(strwidth(header.canonical.substr(0,header.canonical.find("Cost")))==36);
  assert(strwidth(header.canonical.substr(0,header.canonical.find("Failure")))==68);++checks;
 }
 assert(strwidth("放弃信仰")==8&&strwidth("能力：要做什么？")==16);
 assert(strwidth(chop_string("放弃信仰",32))==32);
 // Semantic unknown names must fall back as a complete parent, including key lists.
 auto unknown=zh_glossary_name("god","character.god.name","Unreviewed Future God");assert(!unknown.supported);auto m=zh_message("character.prayer.offer",{unknown});assert(m.localized==m.canonical);
 auto tagged=ZhArg("god",ZhArgType::Name,"<cyan>G\"5</cyan>","<cyan>神「5」</cyan>",true);m=zh_message("character.prayer.offer",{tagged});assert(m.localized.find("<cyan>神「5」</cyan>")!=string::npos);
 bool threw=false;try{zh_message("character.prayer.offer",{zh_integer("god",1)});}catch(const invalid_argument&){threw=true;}assert(threw);
 cout<<"PASS "<<checks<<" extracted production cases; canonical English, side effects, channels, RNG, ranks, flags, keys and complete fallback\n";
}
'''
    unicode=(SRC/'unicode.cc').read_text()
    real_unicode='string chop_string(const char*,int,bool=true);\nstring chop_string(const string&,int,bool=true);\n'
    for needle in ['int utf8towc(','int strwidth(const char *s)','int strwidth(const string &s)','string chop_string(const char *s,','string chop_string(const string &s,']:
        real_unicode+=block(unicode,needle)+'\n'
    menu_source=(SRC/'menu.cc').read_text()
    preface=block(menu_source,'string MenuEntry::_get_text_preface() const')
    assert 'return make_stringf(" %s - ", keycode_to_name(hotkeys[0]).c_str());' in preface
    assert 'formatted_string indented(" ");' in menu_source
    real_unicode+='const string title_indent=" ",row_preface=" a - ";\n'
    code=code.replace('// SOL61_UNICODE_PRODUCTION',real_unicode)
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp);(p/'test.cc').write_text(code)
        # This temporary generated catalog never mutates the shared source catalog.
        entries={}
        for q in sorted((ROOT/'localization/migration').glob('luna-*-messages.json')):
            for x in json.loads(q.read_text())['messages']:entries[x['id']]=x
        quote=lambda s:json.dumps(s,ensure_ascii=False).replace('?',r'\?')
        inc=['static const ZhDefinition zh_definitions[] = {']
        for id,x in sorted(entries.items()):inc.append('{'+','.join(quote(v) for v in [id,x['en'],x['zh'],';'.join(k+':'+v for k,v in x['params'].items())])+'},')
        inc+=['};','struct ZhSourceDefinition { const char *context,*source,*id; };','static const ZhSourceDefinition zh_source_definitions[]={{nullptr,nullptr,nullptr}};']
        (p/'zh-message-catalog.inc').write_text('\n'.join(inc));(p/'zh-message.cc').write_text((SRC/'zh-message.cc').read_text())
        subprocess.run(['c++','-std=c++11','-O0','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(p/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
        result=subprocess.run([str(p/'test')],check=False,text=True,capture_output=True,timeout=60);print(result.stdout,end='');print(result.stderr,end='');result.check_returncode()
    return len(doc['messages'])
if __name__=='__main__':main()
