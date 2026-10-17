#!/usr/bin/env python3
"""Actual item/delay/melee producers versus the frozen cc710081 English oracle.
Only engine/world/name services are seams. A private catalog runs the production
renderer, with legacy matching forbidden; this test never emits shared catalogs.
"""
import json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'native/crawl-ref/source'
def block(s,needle):
    start=s.index(needle);brace=s.index('{',start);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[start:end+1]
    raise AssertionError(needle)
refs=json.loads((ROOT/'tools/fixtures/sol61-item-edges-english.json').read_text())
assert refs['baseline']=='cc710081cd3f163eabf78c65b9144e040ef30aa8'
refs=refs['sources']
needles={'items.cc':['string item_message(','void item_check(','static void _identify_last_item(','void name_weapon(','string get_weapon_name(','void maybe_name_weapon(','void say_farewell_to_weapon('],
'delay.cc':['bool ImbueDelay::try_interrupt(','bool ImprintDelay::try_interrupt(','void ImbueDelay::start(','void ImbueDelay::finish(','void ImprintDelay::start(','void ImprintDelay::finish('],
'quiver.cc':['        void trigger(dist &t) override\n        {\n            // TODO: does it actually make sense']}
oldblocks='\n'.join(block(refs[f],n) for f,ns in needles.items() for n in ns)
symbols=set(re.findall(r'\b(?:OBJ|DESC|MSG|CH|HINT|CAUGHT|MONS|KILL|NON|DIR|TARG)_[A-Z_]+\b',oldblocks))
symbols.update(['OBJ_WEAPONS','OBJ_WANDS','OBJ_STAVES','OBJ_POTIONS','OBJ_SCROLLS','OBJ_JEWELLERY','DESC_YOUR','DESC_A','DESC_THE','DESC_INVENTORY_EQUIP','CAUGHT_NET','MSGCH_PLAIN','MSGCH_FLOOR_ITEMS','MSGCH_MULTITURN_ACTION','DIS_CONFIRMATIONS'])
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
#include <memory>
#include <sstream>
#include <set>
#include <string>
#include <vector>
using namespace std;
'''
code+='enum {'+','.join(sorted(symbols))+'};\n'
code+=r'''
#define ASSERT(x) assert(x)
// The semantic-name service is a seam; template rendering remains production.
#define zh_glossary_name edge_glossary_name
using cglyph_t=struct {unsigned int ch;};
const string SERVITOR_SPELL_KEY="servitor";
const string NEEDS_AUTOPICKUP_KEY="autopick",WEAPON_NAME_KEY="name",PARAGON_WEAPON_KEY="paragon";
vector<string> trace,displayed;set<string> seen_ids;vector<ZhMessage> typed;bool known=true,answer=false,net_flag=true;int rng=0,lines=8;
string fmt(const char*f,va_list a){char b[8192];vsnprintf(b,sizeof b,f,a);return b;}
void output(string en,string zh,int ch=MSGCH_PLAIN,bool nojoin=false,bool cap=true){trace.push_back("M:"+to_string(ch)+":"+to_string(nojoin)+":"+to_string(cap)+":"+en);displayed.push_back(zh);}
void mpr(const ZhMessage&m,int ch=MSGCH_PLAIN){seen_ids.insert(m.id);typed.push_back(m);output(m.canonical,m.display(),ch);}
void mpr(const string&m){output(m,m);}
void mprf(const char*f,...){va_list a;va_start(a,f);auto s=fmt(f,a);va_end(a);output(s,s);}
void mprf(int ch,const char*f,...){va_list a;va_start(a,f);auto s=fmt(f,a);va_end(a);output(s,s,ch);}
void mpr_nojoin(int ch,const string&s){output(s,s,ch,true);}
void mpr_nojoin(int ch,const ZhMessage&m){seen_ids.insert(m.id);typed.push_back(m);output(m.canonical,m.display(),ch,true);}
void mpr_nocap(const ZhMessage&m){seen_ids.insert(m.id);typed.push_back(m);output(m.canonical,m.display(),MSGCH_PLAIN,false,false);}
void mprf_nocap(const char*f,...){va_list a;va_start(a,f);auto s=fmt(f,a);va_end(a);output(s,s,MSGCH_PLAIN,false,false);}
void mprf_nojoin(int ch,const char*f,...){va_list a;va_start(a,f);auto s=fmt(f,a);va_end(a);output(s,s,ch,true);}
void canned_msg(int m){trace.push_back("canned:"+to_string(m));}
namespace msg {struct Capture:ostream {int channel=MSGCH_FLOOR_ITEMS;struct Buffer:stringbuf {Capture*owner;explicit Buffer(Capture*o):owner(o){}int sync()override{string s=str();if(!s.empty()){assert(s.back()=='\n');s.pop_back();output(s,s,owner->channel);str("");}return 0;}}buf;Capture():ostream(&buf),buf(this){}string str()const{return buf.str();}void str(string s){buf.str(s);}};Capture capture;
ostream&streams(int ch){capture.channel=ch;return capture;}}
void flush_stream(){if(!msg::capture.str().empty()){string s=msg::capture.str();assert(s.back()=='\n');s.pop_back();output(s,s,msg::capture.channel);msg::capture.str("");}}
struct coord_def {int x=0,y=0;coord_def(int X=0,int Y=0):x(X),y(Y){}bool origin()const{return x==0&&y==0;}coord_def operator+(coord_def o)const{return {x+o.x,y+o.y};}coord_def operator-(coord_def o)const{return {x-o.x,y-o.y};}};
struct item_def;
struct Value {string s;int n=0;shared_ptr<item_def>item;Value&operator=(bool v){n=v;return *this;}Value&operator=(const string&v){s=v;return *this;}Value&operator=(int v){n=v;return *this;}string get_string()const{return s;}item_def&get_item();};
struct Props:map<string,Value>{using map<string,Value>::operator[];const Value&operator[](const string&k)const{return at(k);}bool exists(string k)const{return count(k);}};
struct item_def {int base_type=OBJ_WANDS,sub_type=0,quantity=1,specialness=0;bool name_supported=true,inventory=false,autopick=false,useless=false,identified=false,artefact=false;char glyph=')';string english="wand of flame",chinese="烈焰魔杖",inscription;Props props;
 string name(int desc,bool=false,bool=false,bool with_inscription=true)const{return (desc==DESC_YOUR?"your ":desc==DESC_THE?"the ":desc==DESC_INVENTORY_EQUIP?"a - ":quantity>1?to_string(quantity)+" ":"a ")+english+(with_inscription&&!inscription.empty()?" {"+inscription+"}":"");}};
item_def&Value::get_item(){if(!item)item=make_shared<item_def>();return *item;}
vector<item_def>floor_items;
struct {int item_stack_summary_minimum=5;}Options;
struct {bool disables[512]={};bool tutorial=false;bool game_is_hints_tutorial()const{return tutorial;}}crawl_state;
int msgwin_lines(){return lines;}void describe_floor(){trace.push_back("describe");}void origin_set(coord_def){trace.push_back("origin");}
cglyph_t get_item_glyph(const item_def&i){return {static_cast<unsigned int>(i.glyph)};}
int _item_name_specialness(const item_def&i){return i.specialness;}
string stringize_glyph(int ch){return string(1,char(ch));}
template<class I>string join_strings(I b,I e,string sep){string s;for(;b!=e;++b){if(!s.empty())s+=sep;s+=*b;}return s;}
string menu_colour_item_name(const item_def&i,int d){return "<cyan>"+i.name(d)+"</cyan>";}
ZhArg zh_item_arg(const string&k,const item_def&i,int d){return {k,ZhArgType::Name,i.name(d),i.chinese+(!i.inscription.empty()?" {"+i.inscription+"}":""),known&&i.name_supported};}
ZhArg zh_item_menu_arg(const string&k,const item_def&i,int d){auto a=zh_item_arg(k,i,d);a.canonical="<cyan>"+a.canonical+"</cyan>";a.localized="<cyan>"+a.localized+"</cyan>";return a;}
ZhArg zh_glossary_name(const string&k,const string&,const string&en){return {k,ZhArgType::Name,en,"审校语义名",known};}
void learned_something_new(int h){trace.push_back("hint:"+to_string(h));}
vector<const item_def*>const_item_list_on_square(int){vector<const item_def*>v;for(auto&i:floor_items)v.push_back(&i);return v;}
bool in_inventory(const item_def&i){return i.inventory;}bool item_needs_autopickup(const item_def&i){trace.push_back("autopick");return i.autopick;}
void identify_item(item_def&i){trace.push_back("identify");i.identified=true;}bool is_useless_item(const item_def&i){trace.push_back("useless");return i.useless;}
void auto_assign_item_slot(item_def&){trace.push_back("slot");}
string item_base_name(const item_def&i){return i.sub_type?"amulet":"ring";}
const char*item_class_name(int t,bool){return t==OBJ_WANDS?"wand":t==OBJ_STAVES?"magical staff":t==OBJ_POTIONS?"potion":t==OBJ_SCROLLS?"scroll":"future category";}
bool is_artefact(const item_def&i){return i.artefact;}
string getRandMonNameString(string){trace.push_back("rng-name:"+to_string(++rng));return "A \"N:5\" <glyph>";}
string do_mon_name_replacements(string s){trace.push_back("replace-name");return s;}
struct dist {coord_def target;bool valid=true,cancel=false,needs=true,me=false,isEndpoint=false;
 bool needs_targeting()const{return needs;}bool isMe()const{return me;}bool isValid=true,isCancel=false;};
struct monster {int type=0;bool friendly=false,visible=true,wood=false,dead=false;string english="the orc",chinese="兽人";
 string name(int)const{trace.push_back("mon-name:"+english);return english;}bool wont_attack()const{return friendly;}bool observable()const{trace.push_back("observable");return visible;}bool is_firewood()const{return wood;}};
ZhArg zh_monster_arg(const string&k,const monster&m,int d){return {k,ZhArgType::Name,m.name(d),m.chinese,known};}
struct Roll {int roll(){trace.push_back("attack-delay");return 13;}};
struct Player {bool confused_flag=false,cannot=false,caught_flag=false,turn_is_over=false;int time_taken=0,reach=2;Props props;
 bool confused()const{return confused_flag;}bool cannot_move()const{return cannot;}bool caught()const{return caught_flag;}
 void struggle_against_net(){trace.push_back("struggle");}int reach_range()const{return reach;}Roll attack_delay(){return {};}
 coord_def pos()const{return {};}int visible_igrd(coord_def)const{return 0;}bool fumbles_attack(){trace.push_back("fumble");return false;}}you;
struct Grid{int operator()(coord_def p)const{return p.x==7?1:0;}};
struct {Grid grid;}env;
bool cleave=false,override_confirm=false,dir_cancel=false,temper=false,solid=false,reachable=true,mid_present=false,enemy_present=false,fight_ok=true;
monster blocker,enemy;
int random2(int n){trace.push_back("rng:"+to_string(n));return (++rng)%n;}
bool one_chance_in(int n){return random2(n)==0;}bool coinflip(){return random2(2)==0;}
coord_def random_choose(coord_def a,coord_def b){return coinflip()?a:b;}
bool cancel_confused_move(bool){trace.push_back("confused-confirm");return override_confirm;}
const char*held_status(){return net_flag?"held in a net":"caught in a web";}
bool wielded_weapon_check(){trace.push_back("weapon-check");return !override_confirm;}
bool attack_cleaves(const Player&){return cleave;}
struct targeter {virtual ~targeter()=default;};struct targeter_cleave:targeter{targeter_cleave(Player*,coord_def,int){}};struct targeter_reach:targeter{targeter_reach(Player*,int){}};
enum class confirm_prompt_type {cancel};
struct direction_chooser_args {int restricts=0,mode=0,range=0;ZhMessage top_prompt_message;confirm_prompt_type self;targeter*hitfunc;function<int(int)> get_desc_messages_func;};
int _desc_hit_chance(int){return 0;}

void direction(dist&t,direction_chooser_args&){trace.push_back("direction");t.isValid=!dir_cancel;t.isCancel=dir_cancel;}
bool feat_is_solid(int v){return solid||v==1;}bool feat_is_reachable_past(int){trace.push_back("reachable");return reachable;}
string feature_description_at(coord_def,bool,int){trace.push_back("feature-name");return "the granite wall";}
monster*monster_at(coord_def p){if(mid_present&&p.x==1)return &blocker;return enemy_present&&p.x>=2?&enemy:nullptr;}
bool could_harm(Player*,monster*){return true;}void player_attempted_attack(bool,bool dangerous){trace.push_back("attempt:"+to_string(dangerous));}
bool force_player_cleave(coord_def){trace.push_back("cleave");return false;}
bool is_valid_tempering_target(const monster&,const Player&,bool){trace.push_back("temper");return temper;}
void monster_die(monster&m,int,int){trace.push_back("die");m.dead=true;}
bool fight_melee(Player*,monster*){trace.push_back("fight");if(!fight_ok)you.turn_is_over=false;return fight_ok;}
struct ImbueDelay {int spell=0;bool was_prompted=false;bool try_interrupt(bool);void start();void finish();};struct ImprintDelay {item_def wpn;bool try_interrupt(bool);void start();void finish();};
const char*spell_title(int){return "Magic Dart";}
int yesno(const char*s,bool,int,bool){trace.push_back("Q:"+string(s));return answer;}
int yesno(const ZhMessage&m,bool,int,bool){seen_ids.insert(m.id);typed.push_back(m);trace.push_back("Q:"+m.canonical);displayed.push_back(m.display());return answer;}
'''
# Only requested production entry points are extracted. The original melee class
# method is re-homed in a minimal class that keeps its real trigger body intact.
def source_chunks(source,current=False):
    out=''
    if current:
        for n in ['ZhArg item_message_display_arg(','static ZhArg _weapon_display_name_arg(']:out+=block(source['items.cc'],n)+'\n'
    for f,ns in needles.items():
        for n in ns:
            b=block(source[f],n)
            if f=='quiver.cc':
                b=b[b.index('void trigger'):].replace(' override','',1)
                out+='struct melee_action {dist target;void set_target(dist&t){trace.push_back("set-target");target=t;}ZhMessage quiver_description_message(){return {"","caption","caption"};}\n'+b+'\n};\n'
            else:out+=b+'\n'
    return out
# Current helpers need item_message declaration; old/current functions isolate
# names and generated-name side effects without a second rendering model.
code+='namespace old {\nstruct ImbueDelay {int spell=0;bool was_prompted=false;bool try_interrupt(bool);void start();void finish();};struct ImprintDelay {item_def wpn;bool try_interrupt(bool);void start();void finish();};\n'+source_chunks(refs)+'}\n'
code+='string item_message(vector<const item_def*>const&);\n'+source_chunks({f:(SRC/f).read_text() for f in refs},True)
code+=r'''
int checks=0;
void reset(){trace.clear();displayed.clear();typed.clear();rng=0;you=Player();msg::capture.str("");blocker=monster();enemy=monster();}
string state(){return to_string(rng)+":"+to_string(you.turn_is_over)+":"+to_string(you.time_taken)+":"+to_string(enemy.dead)+":"+to_string(blocker.dead)+":"+to_string(you.props[PARAGON_WEAPON_KEY].item?1:0);}
template<class A,class B>void compare(string name,A a,B b){reset();a();flush_stream();auto prev=trace;auto prevstate=state();reset();b();flush_stream();if(prev!=trace||prevstate!=state()){cerr<<"DRIFT "<<name<<"\n";for(auto&s:prev)cerr<<"OLD "<<s<<"\n";for(auto&s:trace)cerr<<"NEW "<<s<<"\n";abort();}++checks;}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.edges");
 for(int n:{0,1,2,3,4,5,8,50,51,65})for(int threshold:{2,5,100})for(int height:{2,8})for(bool tutorial:{false,true})for(bool support:{false,true}){
  floor_items.assign(n,item_def());for(int i=0;i<n;++i){floor_items[i].quantity=i+1;floor_items[i].glyph=i%2?')':'?';floor_items[i].specialness=i%4;floor_items[i].base_type=i%3?OBJ_SCROLLS:OBJ_CORPSES;floor_items[i].english="scroll \"N:5\"";floor_items[i].chinese="标记为“N:5”的卷轴";}
  Options.item_stack_summary_minimum=threshold;lines=height;crawl_state.tutorial=tutorial;known=support;
  compare("floor",[]{old::item_check();},[]{item_check();});
  for(auto&m:typed){if(m.id=="sol61.item.floor.single"||m.id=="sol61.item.floor.list")assert(support?(m.localized!=m.canonical):(m.localized==m.canonical));else assert(m.localized!=m.canonical);}
  auto names=const_item_list_on_square(0);assert(old::item_message(names)==item_message(names));auto arg=item_message_display_arg("items",names);assert(arg.canonical==old::item_message(names));if(!support&&n<threshold)assert(arg.localized==arg.canonical);
 }
 floor_items.assign(2,item_def());floor_items[1].name_supported=false;Options.item_stack_summary_minimum=5;lines=8;known=true;compare("mixed-list",[]{old::item_check();},[]{item_check();});for(auto&m:typed)if(m.id=="sol61.item.floor.list")assert(m.localized==m.canonical);
 for(int type:vector<int>{OBJ_WANDS,OBJ_STAVES,OBJ_POTIONS,OBJ_SCROLLS,OBJ_JEWELLERY,int(999)})for(int bits=0;bits<64;++bits){
  item_def input;input.base_type=type;input.sub_type=bits&1;input.inventory=bits&2;input.autopick=bits&4;input.useless=bits&8;if(bits&16)input.props[NEEDS_AUTOPICKUP_KEY]=true;known=bits&32;
  item_def a=input,b=input;compare("identify",[&]{old::_identify_last_item(a);},[&]{_identify_last_item(b);});for(auto&m:typed)if(m.id=="sol61.item.identify.last")assert(type==999?(m.localized==m.canonical):(m.localized!=m.canonical));assert(a.identified==b.identified&&a.props.count(NEEDS_AUTOPICKUP_KEY)==b.props.count(NEEDS_AUTOPICKUP_KEY));
 }
 for(int bits=0;bits<32;++bits)for(string nickname:{"Steel","A \"N:5\" <glyph>","中文名字"}){
  item_def input;input.base_type=OBJ_WEAPONS;input.english="+9 long sword";input.chinese="+9长剑";input.artefact=bits&1;input.inscription=bits&2?"!w, old":"";known=bits&4;if(bits&8)input.props[WEAPON_NAME_KEY]=nickname;bool silent=bits&16;
  item_def a=input,b=input;compare("welcome",[&]{old::maybe_name_weapon(a,silent);},[&]{maybe_name_weapon(b,silent);});for(auto&m:typed)assert(known?(m.localized!=m.canonical):(m.localized==m.canonical));assert(a.inscription==b.inscription&&a.props[WEAPON_NAME_KEY].s==b.props[WEAPON_NAME_KEY].s);
  if(a.artefact||a.props.exists(WEAPON_NAME_KEY)){compare("farewell",[&]{old::say_farewell_to_weapon(a);},[&]{say_farewell_to_weapon(b);});for(auto&m:typed)assert((known||!a.artefact)?(m.localized!=m.canonical):(m.localized==m.canonical));}
 }
 for(bool support:{false,true}){known=support;compare("imbue",[]{old::ImbueDelay d;d.start();},[]{ImbueDelay d;d.start();});compare("imprint-start",[]{old::ImprintDelay d;d.start();},[]{ImprintDelay d;d.start();});compare("imprint-finish",[]{old::ImprintDelay d;d.finish();},[]{ImprintDelay d;d.finish();});assert(you.props[PARAGON_WEAPON_KEY].get_item().english=="wand of flame");}
 for(int bits=0;bits<16;++bits){known=true;answer=bits&1;crawl_state.disables[DIS_CONFIRMATIONS]=bits&2;bool force=bits&4;old::ImbueDelay a;ImbueDelay b;a.was_prompted=b.was_prompted=bits&8;bool ar=false,br=false;compare("imbue-interrupt",[&]{ar=a.try_interrupt(force);},[&]{br=b.try_interrupt(force);});assert(ar==br&&a.was_prompted==b.was_prompted);compare("imprint-interrupt",[&]{old::ImprintDelay d;ar=d.try_interrupt(force);},[&]{ImprintDelay d;br=d.try_interrupt(force);});assert(ar==br);}
 compare("imbue-finish",[]{old::ImbueDelay d;d.spell=17;d.finish();assert(you.props[SERVITOR_SPELL_KEY].n==17);},[]{ImbueDelay d;d.spell=17;d.finish();assert(you.props[SERVITOR_SPELL_KEY].n==17);});
 for(int flags=0;flags<4096;++flags)for(int range:{1,2,3})for(int distance:{0,1,2,4,7})for(int seed:{0,1}){
  known=flags&1;cleave=flags&2;override_confirm=flags&4;dir_cancel=flags&8;temper=flags&16;solid=flags&32;reachable=flags&64;mid_present=flags&128;enemy_present=flags&256;fight_ok=flags&512;
  auto configure=[&]{you.confused_flag=flags&1024;you.cannot=flags&512;you.caught_flag=flags&2048;net_flag=flags&2;you.reach=range;rng=seed;blocker.friendly=flags&32;blocker.visible=flags&16;blocker.type=flags&8?MONS_SPECTRAL_WEAPON:0;};
  dist t;t.target={distance,0};t.needs=!(flags&128);t.me=distance==0;
  dist a=t,b=t;
  compare("melee",[&]{configure();old::melee_action m;m.trigger(a);},[&]{configure();melee_action m;m.trigger(b);});assert(a.target.x==b.target.x&&a.isValid==b.isValid&&a.isCancel==b.isCancel);for(auto&m:typed){bool named=m.id=="quiver.log.attack_feature"||m.id=="quiver.log.fail_reach_past"||m.id=="quiver.log.deconstruct"||(m.id=="quiver.log.in_the_way"&&blocker.visible);assert((!known&&named)?(m.localized==m.canonical):(m.localized!=m.canonical));}
 }
 // Exercise parameter punctuation and unknown semantic names through the real
 // melee producer, including a hidden blocker whose name must never be read.
 for(string name:{"Sigmund","two-headed ogres","<cyan>beast N:5</cyan>","Wizard's ghost"})for(bool visible:{false,true})for(bool support:{false,true}){
 known=support;cleave=false;override_confirm=false;dir_cancel=false;temper=false;solid=false;reachable=true;mid_present=true;enemy_present=true;fight_ok=true;
 auto setup=[&]{you.reach=2;rng=1;blocker.visible=visible;blocker.english=name;};dist a,b;a.target=b.target={2,0};a.needs=b.needs=false;
 compare("melee-name",[&]{setup();old::melee_action m;m.trigger(a);},[&]{setup();melee_action m;m.trigger(b);});if(!visible)for(auto&v:trace)assert(v!="mon-name:"+name);
 }
 setenv("DCSS_LANG","en",1);known=true;floor_items.assign(1,item_def());compare("english-floor",[]{old::item_check();},[]{item_check();});for(auto&m:typed)assert(m.display()==m.canonical);setenv("DCSS_LANG","zh",1);
 for(string id:{"quiver.log.cannot_attack_held","quiver.log.attack_feature","quiver.log.fail_reach_past","quiver.log.in_the_way","quiver.log.deconstruct"})assert(seen_ids.count(id));
 cout<<"PASS "<<checks<<" real producer cases: floor/identify/naming/delay/melee canonical, channels, nojoin, cap, RNG, state and hidden-name boundaries\n";
}
'''
# Helpers precede their callees in source_chunks: forward declarations preserve
# the real implementations rather than replacing them with test equivalents.
code=code.replace('string item_message(vector<const item_def*>const&);','string item_message(vector<const item_def*>const&);')
entries={}
for p in sorted((ROOT/'localization/migration').glob('luna-*-messages.json')):
    doc=json.loads(p.read_text())
    if p.name=='luna-sol61-item-edges-messages.json':assert doc['model']==doc['reviewer_model']=='gpt-6.1-sol'
    for e in doc['messages']:assert e['id'] not in entries;entries[e['id']]=e
ids=set(re.findall(r'"((?:sol61\.item|quiver\.log|log\.(?:quiver|delay)|operation\.pickup)\.[a-z0-9_.]+)"',code))
ids={k for k in ids if not k.endswith('.')}
ids.update(k for k in entries if k.startswith('sol61.item.'))
q=lambda s:json.dumps(s,ensure_ascii=False).replace('?',r'\?')
catalog='static const ZhDefinition zh_definitions[] = {\n'
for identity in sorted(ids):
    e=entries[identity]
    for lang in ['en','zh']:assert set(re.findall(r'\{(\w+)\}',e[lang]))==set(e['params'])
    catalog+=' {'+', '.join(q(x) for x in (identity,e['en'],e['zh'],';'.join(k+':'+v for k,v in e['params'].items())))+'},\n'
catalog+='};\nstruct ZhSourceDefinition { const char *context,*source,*id; };\nstatic const ZhSourceDefinition zh_source_definitions[]={{nullptr,nullptr,nullptr}};\n'
with tempfile.TemporaryDirectory() as td:
    p=Path(td);(p/'test.cc').write_text(code);shutil.copyfile(SRC/'zh-message.cc',p/'zh-message.cc');(p/'zh-message-catalog.inc').write_text(catalog)
    subprocess.run(['c++','-std=c++14','-O0','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(p/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,timeout=60)
