#!/usr/bin/env python3
"""Extract real spell/attack functions and compare frozen English + side effects.
Uses a private temporary catalog and never writes shared generated files.
World queries, RNG and entity-name APIs are seams; production control flow stays.
"""
import json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'native/crawl-ref/source'
def block(s,needle):
    start=s.index(needle);brace=s.index('{',start);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[start:end+1]
    raise AssertionError(needle)
refs=json.loads((ROOT/'tools/fixtures/sol61-combat-spells-english.json').read_text())
needles={
 'spl-selfench.cc':['spret cast_deaths_door(','void remove_ice_armour(','spret ice_armour(','void fiery_armour(','spret cast_revivification(','spret cast_swiftness(','spret cast_fugue_of_the_fallen(','void do_fugue_wail(','spret cast_silence(','spret cast_liquefaction(','bool jinxbite_targets_available(','spret cast_jinxbite(','spret cast_detonation_catalyst('],
 'spl-other.cc':['spret cast_sublimation_of_blood(','spret cast_death_channel(','static bool _dismiss_dead(','spret cast_animate_dead('],
 'spl-summoning.cc':['bool player_summon_check(const vector<monster_type>&','bool player_summon_check(monster_type type,','spret cast_summon_small_mammal(','spret cast_call_canine_familiar(','spret cast_summon_cactus(','spret cast_awaken_armour(','spret cast_summon_ice_beast(','spret cast_monstrous_menagerie(','spret cast_sphinx_sisters(','spret cast_summon_hydra(','spret cast_summon_mana_viper('],
 'spl-clouds.cc':['spret cast_putrefaction(','spret kindle_blastmotes(','spret scroll_of_poison('],
 'attack.cc':['void attack::stab_message(']}
allblocks='\n'.join(block(refs[f],n) for f,ns in needles.items() for n in ns)
symbols=set(re.findall(r'\b(?:DUR|ATTR|MSG|MONS|SPELL|DESC|ENCH|BEAM|KILLED|KILL|ISFLAG|HINT|CLOUD|LOS|PRONOUN|MUT|UA|I|GOD|MR|M)_[A-Z_]+\b',allblocks))
symbols.update(['DESC_THE','DESC_A','DESC_ITS','DESC_YOUR','DESC_PLAIN','GOD_NO_GOD','MSGCH_SOUND','MSGCH_DURATION','MSGCH_PROMPT'])
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
enum class spret {success,abort,fail};
using monster_type=int;using spell_type=int;using god_type=int;
const int BASELINE_DELAY=10,NON_ITEM=-1,NON_MONSTER=-1,WILL_INVULN=1000,BROWN=6,YELLOW=14;
#define ASSERT(x) assert(x)
#define fail_check() do {if(fail){trace.push_back("FAIL");return spret::fail;}}while(0)
const string ICY_ARMOUR_KEY="icy",FUGUE_KEY="fugue",CANINE_FAMILIAR_MID="dog",MGEN_NUM_HEADS="heads",ANIMATE_DEAD_POWER_KEY="dead",BLASTMOTE_POWER_KEY="blast",BLASTMOTE_IMMUNE_KEY="immune",HELPLESS_KEY="helpless";
string target_base="orc";int creation_mask=7,visibility_mask=7;
vector<string>trace,rendered;int rng=0;bool known=true,space=true,stop=false,create_ok=true,cansee=true,blood=true,cloud_exists=false,mut_paws=false;int count_create=0,clouds_created=0;
void record(string s){trace.push_back(s);}
string fmt(const char*f,va_list a){char b[8192];vsnprintf(b,sizeof b,f,a);return b;}
void mpr(const string&s,int ch=0){record("M:"+to_string(ch)+":"+s);rendered.push_back(s);}
void mpr(const ZhMessage&m,int ch=0){record("M:"+to_string(ch)+":"+m.canonical);rendered.push_back(m.display());}
void mprf(const char*f,...){va_list a;va_start(a,f);auto s=fmt(f,a);va_end(a);mpr(s);}
void mprf(int ch,const char*f,...){va_list a;va_start(a,f);auto s=fmt(f,a);va_end(a);mpr(s,ch);}
void canned_msg(int m){if(m==MSG_NOTHING_HAPPENS)mpr("Nothing appears to happen.");else if(m==MSG_NO_AVAILABLE_SPACE)mpr("There is no available space!");else assert(false);}
int random2(int n){record("r2:"+to_string(n));return n>0?(++rng*37)%n:0;}
int random2avg(int n,int a){record("avg:"+to_string(a));return random2(n);}
int random_range(int a,int b){record("range:"+to_string(a)+":"+to_string(b));return a+random2(b-a+1);}
int div_rand_round(int a,int b){record("div:"+to_string(a)+":"+to_string(b));return b?a/b:0;}
bool x_chance_in_y(int a,int b){return random2(max(1,b))<a;}bool one_chance_in(int n){return random2(n)==0;}bool coinflip(){return random2(2)==0;}
int binomial(int n,int a,int b){record("bin:"+to_string(n)+":"+to_string(a)+":"+to_string(b));return random2(n);}
int random_choose(int a,int b){return coinflip()?a:b;}int summ_dur(int n){return n;}int hit_points(int a,int b){record("hpgen");return a*b;}int roll_dice(int n,int s){record("dice");return n+random2(s);}
struct Value {int value=0;Value&operator=(int x){value=x;return *this;}operator int()const{return value;}int&get_int(){return value;}};
struct Props:map<string,Value>{bool exists(const string&s)const{return count(s);}};
struct coord_def {int v;coord_def(int n=0):v(n){}bool origin()const{return v==0;}};
struct item_def {int flags=0;string english="your +9 armour",chinese="你的+9护甲";string name(int)const{return english;}void clear(){flags=0;}};
struct actor {bool player=false,visible=true;Props props;bool is_player()const{return player;}virtual bool is_monster()const{return !player;}virtual string name(int d)const{return player?(d==DESC_ITS?"your":"You"):(d==DESC_ITS?"the "+target_base+"'s":d==DESC_PLAIN?target_base:d==DESC_A?"an "+target_base:"the "+target_base);}string conj_verb(string v)const{return v+(player?"":"s");}coord_def pos()const{return {1};}virtual struct monster*as_monster(){return nullptr;}string pronoun(int)const{return "itself";}};
struct mon_enchant {int duration=0;mon_enchant(int=0,const actor* = nullptr,int d=0):duration(d){}};
struct Ghost {void init_inugami_from_player(int p){record("ghost:"+to_string(p));}} ghost;
struct monster:actor {int mid=99,type=MONS_BAT,hp=20;bool hostile=true,wood=false,alive_flag=true,created=true;int resist=0,will=0;Ghost*ghost=&::ghost;map<int,int>ench;
 monster*as_monster()override{return this;}bool is_firewood()const{return wood;}bool wont_attack()const{return !hostile;}int res_negative_energy()const{return resist;}bool alive()const{return alive_flag;}int willpower()const{return will;}
 void hurt(actor*,int damage,int,int){record("hurt:"+to_string(damage));hp-=damage;}void ghost_demon_init(){record("ghostinit");}void heal(int n){record("heal:"+to_string(n));hp+=n;}void del_ench(int e){record("del:"+to_string(e));ench.erase(e);}void add_ench(mon_enchant e){record("add:"+to_string(e.duration));}mon_enchant get_ench(int e){record("get:"+to_string(e));return {0,nullptr,ench[e]};}void update_ench(mon_enchant e){record("update:"+to_string(e.duration));ench[ENCH_SUMMON_TIMER]=e.duration;}void pickup_item(item_def&i,bool,bool){record("pickup:"+to_string(i.flags));}bool was_created_by(const actor&,int)const{return created;}
};
vector<monster>world;monster*old_dog=nullptr;monster summoned[3];item_def armour;bool has_armour=true;int item_slot=0;
struct Player:actor {int duration[512]={},attribute[512]={},hp=50,hp_max=100,magic_points=0,max_magic_points=10,time_taken=10;bool redraw_armour_class=false,redraw_evasion=false;
 Player(){player=true;}bool has_blood()const{return blood;}bool has_mutation(int)const{return mut_paws;}bool can_see(const actor&a)const{return cansee&&a.visible;}bool see_cell(coord_def)const{return cansee;}const item_def*body_armour()const{return has_armour?&armour:nullptr;}
 void increase_duration(int d,int n,int cap=0,const char*msg=nullptr){if(msg)mpr(msg);if(cap&&duration[d]>cap*10)return;duration[d]+=n*10;if(cap)duration[d]=min(duration[d],cap*10);}
 void set_duration(int d,int n,int cap=0,const char*msg=nullptr){duration[d]=0;increase_duration(d,n,cap,msg);}void paralyse(actor*,int n,string reason){record("paralyse:"+to_string(n)+":"+reason);}
}you;
int player_icemail_armour_class(){return 0;}void set_hp(int n){record("sethp:"+to_string(n));you.hp=n;}void dec_max_hp(int n){record("maxhp:"+to_string(n));you.hp_max-=n;}bool enough_hp(int n,bool){record("enoughhp");return you.hp>=n;}void inc_mp(int n){you.magic_points+=n;record("mp:"+to_string(n));}void dec_hp(int n,bool){you.hp-=n;record("hp:"+to_string(n));}
void invalidate_agrid(bool){record("agrid");}void learned_something_new(int n){record("hint:"+to_string(n));}void flash_view_delay(int,int c,int n){record("flash:"+to_string(c)+":"+to_string(n));}int spell_power_cap(int){return 100;}int calc_spell_power(int){return 80;}
struct adjacent_iterator {size_t i=0;adjacent_iterator(coord_def){}operator bool()const{return i<world.size();}void operator++(){++i;}coord_def operator*()const{return {int(i)};}};
struct radius_iterator:adjacent_iterator {radius_iterator(coord_def p,int):adjacent_iterator(p){}};
struct monster_iterator {size_t i=0;operator bool()const{return i<world.size();}void operator++(){++i;}monster*operator*(){return &world[i];}monster*operator->(){return &world[i];}};
struct monster_near_iterator:monster_iterator {monster_near_iterator(actor*,int){}};
monster*monster_at(coord_def p){return p.v<int(world.size())?&world[p.v]:nullptr;}const actor*actor_at(coord_def p){return p.v==0&&world.size()?&world[0]:nullptr;}bool mons_is_threatening(const monster&m){return m.hostile;}void monster_die(monster&m,int,int){record("die:"+to_string(m.mid));m.alive_flag=false;}
struct mgen_data {int cls=0,hp=0,hd=0;Props props;mgen_data(int c=0):cls(c){}void set_range(int a,int b){record("rangegen:"+to_string(a)+":"+to_string(b));}};
mgen_data _pal_data(int type,int dur,int spell,bool=true){record("pal:"+to_string(type)+":"+to_string(dur)+":"+to_string(spell));return {type};}
mgen_data _summon_data(const actor&,int t,int d,int s){return _pal_data(t,d,s);}
monster*create_monster(mgen_data d){record("create:"+to_string(d.cls)+":"+to_string(d.hp)+":"+to_string(d.hd)+":"+to_string(d.props[MGEN_NUM_HEADS].value));int i=count_create++;if(!create_ok||!(creation_mask&(1<<(i%3))))return nullptr;summoned[i%3].type=d.cls;return &summoned[i%3];}
monster*find_canine_familiar(){return old_dog;}int get_mitm_slot(int n){record("slot:"+to_string(n));return item_slot;}
struct {int HD=7;}mondata;auto get_monster_data(int)->decltype(&mondata){return &mondata;}
string mons_type_name(int,int){return "a beast";}
bool _can_summon_any_of(const vector<int>&,int,int,coord_def,int){return space;}bool _maybe_stop_summoning_prompt(const vector<int>&){return stop;}
ZhArg zh_actor_arg(const string&k,const actor*a,int d=DESC_THE){return {k,ZhArgType::Name,a->name(d),a->player?(d==DESC_ITS?"你的":"你"):(d==DESC_ITS?"兽人的":"兽人"),a->player||known};}
ZhArg zh_monster_arg(const string&k,const monster&m,int d=DESC_THE){return zh_actor_arg(k,&m,d);}ZhArg zh_monster_type_arg(const string&k,int){return {k,ZhArgType::Name,"beast","野兽",known};}ZhArg zh_item_arg(const string&k,const item_def&i,int){return {k,ZhArgType::Name,i.english,i.chinese,known};}
struct map_cloud_spreader_marker {int speed_increment=0;map_cloud_spreader_marker(coord_def,int,int,int,int,int,actor*){record("marker");}};
struct Markers {void add(map_cloud_spreader_marker*m){record("markeradd:"+to_string(m->speed_increment));delete m;}void clear_need_activate(){record("markeractivate");}};
struct {item_def item[2];Markers markers;}env;
bool place_cloud(int c,coord_def,int d,actor*){record("cloud:"+to_string(c)+":"+to_string(d));++clouds_created;return create_ok;}bool cloud_at(coord_def){return cloud_exists;}void drain_player(int n,bool,bool){record("drain:"+to_string(n));}
struct attack {actor*defender=nullptr;int stab_bonus=0;void stab_message();};
'''
# Defaults live at declarations, as in real headers.
decls='''bool player_summon_check(const vector<monster_type>&,int=2,int=0,coord_def={},spell_type=0);\nbool player_summon_check(monster_type,int=2,int=0,coord_def={},spell_type=0);\n'''
code+='namespace old {\n'+decls
for f,ns in needles.items():
 for n in ns:
  if f!='attack.cc':code+=block(refs[f],n)+'\n'
# Frozen stab method lives in its own class, same actor effects.
code+='struct attack {actor*defender=nullptr;int stab_bonus=0;void stab_message();};\n'+block(refs['attack.cc'],'void attack::stab_message(')+'\n}\n'
code+=decls
for f,ns in needles.items():
 for n in ns:code+=block((SRC/f).read_text(),n)+'\n'
code+=r'''
int checks=0;string ename="the orc";
void reset(int flags,int dur,int hp,int mp){trace.clear();rendered.clear();rng=0;count_create=0;clouds_created=0;you=Player();you.hp=hp;you.magic_points=mp;
 for(auto&d:you.duration)d=dur;world.assign(3,monster());for(size_t i=0;i<world.size();++i)world[i].mid=10+i;for(int n=0;n<3;++n){summoned[n]=monster();summoned[n].visible=visibility_mask&(1<<n);}for(auto&m:summoned)m.ench[ENCH_SUMMON_TIMER]=flags&128?150:50;
 known=flags&1;space=flags&2;stop=flags&4;create_ok=flags&8;cansee=flags&16;blood=flags&32;cloud_exists=flags&64;mut_paws=flags&128;old_dog=flags&256?&summoned[0]:nullptr;has_armour=flags&512;item_slot=flags&1024?NON_ITEM:0;armour.flags=4;env.item[0]=item_def();
 for(auto&m:world){m.wood=flags&64;m.hostile=!(flags&128);m.resist=flags&256?3:0;m.created=flags&512;m.will=flags&1024?WILL_INVULN:0;}
}
string state(){string s=to_string(rng)+":"+to_string(you.hp)+":"+to_string(you.hp_max)+":"+to_string(you.magic_points)+":"+to_string(you.redraw_armour_class)+":"+to_string(you.redraw_evasion)+":"+to_string(env.item[0].flags)+":"+to_string(clouds_created);
 for(int d:you.duration)s+=","+to_string(d);for(int a:you.attribute)s+=","+to_string(a);for(auto&p:you.props)s+=p.first+to_string(p.second.value);for(auto&m:world)s+=to_string(m.hp)+to_string(m.alive_flag)+to_string(m.props.count(HELPLESS_KEY));for(auto&m:summoned)s+=to_string(m.hp)+to_string(m.ench[ENCH_SUMMON_TIMER]);return s;}
template<class A,class B>void compare(string name,int flags,int dur,int hp,int mp,A a,B b){reset(flags,dur,hp,mp);auto ar=a();auto oldtrace=trace;auto oldstate=state();reset(flags,dur,hp,mp);auto br=b();
 if(ar!=br||oldtrace!=trace||oldstate!=state()){cerr<<"DRIFT "<<name<<" flags="<<flags<<" dur="<<dur<<" hp="<<hp<<" mp="<<mp<<"\n";for(auto&s:oldtrace)cerr<<"OLD "<<s<<"\n";for(auto&s:trace)cerr<<"NEW "<<s<<"\n";abort();}
 size_t i=0;for(auto&s:trace)if(s.rfind("M:",0)==0){auto en=s.substr(s.find(':',2)+1);bool fallback=!known&&((en.find("the "+target_base)!=string::npos||en.find("an "+target_base)!=string::npos||en.find("unaware "+target_base)!=string::npos)||en.find("beast")!=string::npos||en.find(armour.english)!=string::npos);if(!(fallback?(rendered[i]==en):(rendered[i]!=en))){cerr<<"TRANSLATION "<<name<<" flags="<<flags<<" en="<<en<<" zh="<<rendered[i]<<" fallback="<<fallback<<"\n";abort();}assert(rendered[i].find('{')==string::npos);++i;}++checks;
}
#define PAIR(fn,...) compare(#fn,flags,dur,hp,mp,[&](){return old::fn(__VA_ARGS__);},[&](){return fn(__VA_ARGS__);})
#define VOIDPAIR(fn,...) compare(#fn,flags,dur,hp,mp,[&](){old::fn(__VA_ARGS__);return 0;},[&](){fn(__VA_ARGS__);return 0;})
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("sol61.combat");
 for(int flags=0;flags<2048;++flags)for(int dur:{0,280,16000}){int hp=flags&1?1:50,mp=flags&1?10:0;int pow=flags%4==0?0:flags%4==1?1:flags%4==2?50:200;bool fail=flags&4;
 PAIR(cast_deaths_door,pow,fail);VOIDPAIR(remove_ice_armour);PAIR(ice_armour,pow,fail);VOIDPAIR(fiery_armour);PAIR(cast_revivification,pow,fail);PAIR(cast_swiftness,pow,fail);PAIR(cast_fugue_of_the_fallen,pow,fail);VOIDPAIR(do_fugue_wail,coord_def{});PAIR(cast_silence,pow,fail);PAIR(cast_liquefaction,pow,fail);PAIR(jinxbite_targets_available);PAIR(cast_jinxbite,pow,fail);PAIR(cast_detonation_catalyst,fail);
 PAIR(cast_sublimation_of_blood,pow,fail);PAIR(cast_death_channel,pow,flags&8?GOD_NO_GOD:3,fail);PAIR(cast_animate_dead,pow,fail);
 PAIR(cast_summon_small_mammal,pow,fail);PAIR(cast_call_canine_familiar,pow,fail);PAIR(cast_summon_cactus,pow,fail);PAIR(cast_awaken_armour,pow,fail);PAIR(cast_summon_ice_beast,pow,fail);PAIR(cast_monstrous_menagerie,&world[0],pow);PAIR(cast_sphinx_sisters,flags&8?static_cast<actor&>(you):static_cast<actor&>(world[0]),pow,fail);PAIR(cast_summon_hydra,flags&8?static_cast<actor*>(&you):static_cast<actor*>(&world[0]),pow,fail);PAIR(cast_summon_mana_viper,pow,fail);
 PAIR(cast_putrefaction,&world[0],pow,fail);PAIR(kindle_blastmotes,pow,fail);PAIR(scroll_of_poison,bool(flags&4));
 }
 for(int flags=0;flags<256;++flags)for(int bonus:{1,2,4})for(int seed:{0,1,2}){int dur=0,hp=50,mp=0;
 compare("stab",flags,dur,hp,mp,[&](){rng=seed;old::attack a;a.defender=&world[0];a.stab_bonus=bonus;a.stab_message();return 0;},[&](){rng=seed;attack a;a.defender=&world[0];a.stab_bonus=bonus;a.stab_message();return 0;});}
 for(string base:{"Sigmund","Wizard's ghost","two-headed ogre","<cyan>beast N:5</cyan>"})for(int flags:{26,27,1050,1051}){target_base=base;int dur=0,hp=50,mp=0;int pow=100;bool fail=false;
 PAIR(cast_summon_small_mammal,pow,fail);PAIR(cast_awaken_armour,pow,fail);PAIR(cast_monstrous_menagerie,&world[0],pow);PAIR(cast_summon_hydra,&world[0],pow,fail);PAIR(cast_putrefaction,&world[0],pow,fail);
 for(int cm=0;cm<4;++cm)for(int vm=0;vm<4;++vm){creation_mask=cm;visibility_mask=vm;PAIR(cast_sphinx_sisters,world[0],pow,fail);}creation_mask=7;visibility_mask=7;
 for(int bonus:{1,4})for(int seed:{0,1,2})compare("stab names",flags,dur,hp,mp,[&](){rng=seed;old::attack a;a.defender=&world[0];a.stab_bonus=bonus;a.stab_message();return 0;},[&](){rng=seed;attack a;a.defender=&world[0];a.stab_bonus=bonus;a.stab_message();return 0;});
 }
 cout<<"PASS "<<checks<<" real producer cases: canonical, channels, RNG, HP/MP, durations, props, creation, inventory, visibility and whole-parent fallback\n";
}
'''
# Pure private catalog, using exactly reviewed entries. Includes production renderer.
doc=json.loads((ROOT/'localization/migration/luna-sol61-combat-spells-messages.json').read_text())
assert doc['model']=='gpt-6.1-sol'
entries=doc['messages'];ids=set()
for e in entries:
 assert e['id'] not in ids;ids.add(e['id'])
 for lang in ('en','zh'):assert set(re.findall(r'\{(\w+)\}',e[lang]))==set(e['params'])
 assert e['en']!=e['zh']
q=lambda s:json.dumps(s,ensure_ascii=False).replace('?',r'\?')
catalog='static const ZhDefinition zh_definitions[] = {\n'
for e in entries:catalog+=' {'+', '.join(q(s) for s in (e['id'],e['en'],e['zh'],';'.join(k+':'+v for k,v in e['params'].items())))+'},\n'
catalog+='};\nstruct ZhSourceDefinition { const char *context, *source, *id; };\nstatic const ZhSourceDefinition zh_source_definitions[] = {{nullptr,nullptr,nullptr}};\n'
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.cc').write_text(code)
 # Include-relative resolution uses this temporary copy; no shared files mutate.
 shutil.copyfile(SRC/'zh-message.cc',p/'zh-message.cc');(p/'zh-message-catalog.inc').write_text(catalog)
 subprocess.run(['c++','-std=c++11','-O0','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(p/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=60)
