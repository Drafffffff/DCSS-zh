#!/usr/bin/env python3
"""Exercise actual spell target-effect producers against frozen canonical code."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
from test_target_notifications import block


def main():
    messages=compile_catalog()
    source=(SRC/'spl-cast.cc').read_text()
    fixture=json.loads((Path(__file__).parent/'fixtures/spell-target-effects-english.json').read_text())
    assert 'ZhTranslationPause' in block(source,'string target_spell_desc('), 'Lua strings must stay canonical'
    assert '"spell.prompt.effect.immune_roots"' in block(source,'typed_desc_filter targeter_addl_desc_messages(')
    assert '"spell.prompt.effect.unstickable"' in block(source,'typed_desc_filter targeter_addl_desc_messages(')
    assert 'zh_monster_info_arg("monster", info, DESC_PLAIN)' in source
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;using monster_type=int;
enum {SPELL_PLASMA_BEAM,MR_RES_POISON,MB_NO_ATTACKS=1,MB_CLARITY=2,MB_CANT_DRAIN=4,MB_RIMEBLIGHT=8,MB_SHAPESHIFTER=16,M_INSUBSTANTIAL,BEAM_POLYMORPH,MONS_UGLY_THING,MONS_VERY_UGLY_THING,MONS_SLIME_CREATURE,DUR_BLIND,DESC_PLAIN,WILL_INVULN=10000,MEPH_HD_CAP=20};
const string POLY_SET_KEY="poly_set";
struct coord {int x=1;int distance_from(coord p)const{return abs(x-p.x);}};
struct Player {int duration[32]={};coord pos()const{return coord();}}you;
struct CrawlStoreValue;using CrawlVector=vector<CrawlStoreValue>;
CrawlVector polyset;
struct CrawlStoreValue {int value;CrawlStoreValue(int n=1):value(n){}int get_int()const{return value;}const CrawlVector&get_vector()const{return polyset;}};
struct Props {bool has=false;CrawlStoreValue value;bool exists(const string&)const{return has;}const CrawlStoreValue&operator[](const string&)const{return value;}};
struct monster {int type=0;};int defines=0;void define_monster(monster&){++defines;}
const char* names[]={"orc","adder","ogre","ugly thing","unknown extension's +9 ghost"};
const char* rawname(int type){return names[abs(type)%5];}
struct monsterentry {string name;};monsterentry md;
const monsterentry*get_monster_data(int type){md.name=rawname(type);return &md;}
bool mons_is_ghost_demon(int type){return type==3;}
struct Flags {int flags=0;bool get(int n)const{return flags&n;}};
struct monster_info {int type=0,hd=1,slime_size=1,wl=0,poison=0;bool antimagic=false;coord pos;Flags mb;Props props;
 monster_info(){}monster_info(monster*m):type(m->type){}
 bool is(int n)const{return mb.get(n);}int willpower()const{return wl;}int resists()const{return poison;}bool antimagic_susceptible()const{return antimagic;}
 void to_string(int,string&desc,int&colour,bool,const char*,bool)const{desc=mons_is_ghost_demon(type)?"random coloured ugly thing":rawname(type);colour=type%2;}
};
struct bolt {int hit=0,flavour=0;};int accuracy=50;
struct targeter {bool affected=true;virtual ~targeter(){}bool affects_monster(const monster_info&)const{return affected;}};
struct targeter_beam:targeter {bolt beam;};
int spell_to_zap(int n){return n;}void zappy(int,int,bool,bolt&b){b.hit=accuracy;}
int _to_hit_pct(const monster_info&,int acc){return acc;}
int get_resist(int n,int){return n;}int _tetrahedral_number(int n){return n*(n+1)*(n+2)/6;}
int gloom_success_chance(int pow,int hd){return max(0,min(100,pow-hd));}
int airstrike_space_around(coord p,bool){return p.x;}
int get_mercury_weaken_chance(int hd){return 100-hd;}int get_warp_space_chance(int pow){return pow;}
bool blind=false,insubstantial=false,peripheral=false,stationary=false,beckon=true;
bool mons_res_blind(int){return blind;}bool mons_class_flag(int,int){return insubstantial;}bool mons_class_is_peripheral(int){return peripheral;}bool mons_class_is_stationary(int){return stationary;}bool can_beckon(const monster_info&){return beckon;}
int apply_willpower_bypass(Player&,int wl){return wl-5;}int hex_success_chance(int wl,int pow,int){return max(0,min(100,pow-wl));}
string article_a(const string&s){return (s[0]=='a'||s[0]=='o'||s[0]=='u'?"an ":"a ")+s;}
string colour_to_str(int n){return n?"red":"green";}
bool known=true;ZhArg zh_monster_info_arg(const string&key,const monster_info&mi,int){return {key,ZhArgType::Name,rawname(mi.type),known?string("甲"):rawname(mi.type),known};}
ZhArg zh_monster_type_arg(const string&key,int type){return {key,ZhArgType::Name,rawname(type),known?string("乙"):rawname(type),known};}
template<class...A>string make_stringf(const char*f,A...a){char b[2048];snprintf(b,sizeof b,f,a...);return b;}
template<class Z,class F>string comma_separated_fn(Z start,Z end,F fn,const string&last=" and ",const string&middle=", "){string out;for(auto i=start;i!=end;++i){if(i!=start)out+=i+1==end?last:middle;out+=fn(*i);}return out;}
template<class Z>string comma_separated_line(Z a,Z b){return comma_separated_fn(a,b,[](const string&s){return s;});}
void describe_hit_chance(int pct,ostringstream&out,void*,bool,int){out<<"chance to hit: "<<pct<<"%";if(you.duration[DUR_BLIND])out<<" (range 1)";}
'''
    # Match the already migrated shared hit descriptor's canonical exactly.
    en=messages['target.hit_chance']['en'];blind_en=messages['target.hit_chance.distance']['en']
    code=code.replace('out<<"chance to hit: "<<pct<<"%";if(you.duration[DUR_BLIND])out<<" (range 1)";', 'string result=you.duration[DUR_BLIND]?'+json.dumps(blind_en)+':'+json.dumps(en)+';auto p=result.find("{hit_percent}");result.replace(p,13,to_string(pct));out<<result;')
    code+=r'''
ZhArg describe_hit_chance_message(int pct,void*,bool,int){return zh_message_arg("chance",you.duration[DUR_BLIND]?"target.hit_chance.distance":"target.hit_chance",{zh_integer("hit_percent",pct)});}
'''
    mapping={q.split('(')[0].split()[-1]:'old_'+q.split('(')[0].split()[-1] for q in fixture['functions']}
    for text in fixture['functions'].values():
        for name,new in sorted(mapping.items(),key=lambda pair:-len(pair[0])):
            text=re.sub(r'\b'+re.escape(name)+r'\b',new,text)
        code+=text+'\n'
    for q in fixture['functions']:
        if '_mon_threat_string' in q:
            code+=block(source,'static ZhArg _mon_threat_arg(')+'\n'
            code+=block(source,'static ZhArg _polymorph_outcomes_arg(')+'\n'
        else:
            typed_query=q.replace('vector<string>', 'vector<ZhArg>')
            name=q.split('(')[0].split()[-1]
            typed_query=typed_query.replace(name+'(', name+'_messages(')
            code+=block(source,typed_query)+'\n'

    code+=r'''
int cases=0;
vector<string> displayed(const vector<ZhArg>& args){vector<string> result;for(const auto&arg:args)result.push_back(zh_language_enabled()?arg.localized:arg.canonical);return result;}
template<class F,class G>void compare(F old,G now){
 vector<string> canonical;defines=0;{ZhTranslationPause pause;canonical=old();}int old_defines=defines;defines=0;
 vector<string> actual;{ZhTranslationPause pause;actual=displayed(now());}assert(canonical==actual&&old_defines==defines);defines=0;
 auto translated=displayed(now());assert(translated.size()==canonical.size());for(size_t i=0;i<translated.size();++i){assert(translated[i]!=canonical[i]);}assert(old_defines==defines);++cases;
}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.spell.effects");monster_info mi;targeter hit;targeter_beam beam;
for(int mask=0;mask<128;++mask)for(int pow:{1,3,10,25,99})for(int hd:{1,3,10,25}){
 mi=monster_info();mi.hd=hd;mi.wl=(mask&1)?WILL_INVULN:10;mi.poison=(mask&2)?1:0;mi.mb.flags=mask&4?MB_NO_ATTACKS:0;if(mask&8)mi.mb.flags|=MB_CLARITY;if(mask&16)mi.mb.flags|=MB_CANT_DRAIN;if(mask&32)mi.mb.flags|=MB_RIMEBLIGHT;mi.antimagic=mask&64;hit.affected=mask&16;blind=mask&1;insubstantial=mask&2;peripheral=mask&4;stationary=mask&8;beckon=mask&32;
 compare([&]{return old__desc_intoxicate_chance(mi,&hit,pow);},[&]{return _desc_intoxicate_chance(mi,&hit,pow);});
 compare([&]{return old__desc_englaciate_chance(mi,&hit,pow);},[&]{return _desc_englaciate_chance(mi,&hit,pow);});
 compare([&]{return old__desc_gloom_chance(mi,pow);},[&]{return _desc_gloom_chance(mi,pow);});
 compare([&]{return old__desc_mercury_weak_chance(mi);},[&]{return _desc_mercury_weak_chance(mi);});
 compare([&]{return old__desc_warp_space_chance(pow);},[&]{return _desc_warp_space_chance(pow);});
 compare([&]{return old__desc_meph_chance(mi);},[&]{return _desc_meph_chance(mi);});
 compare([&]{return old__desc_vampiric_draining_valid(mi);},[&]{return _desc_vampiric_draining_valid(mi);});
 compare([&]{return old__desc_rimeblight_valid(mi);},[&]{return _desc_rimeblight_valid(mi);});
 compare([&]{return old__desc_dispersal_chance(mi,pow);},[&]{return _desc_dispersal_chance(mi,pow);});
 compare([&]{return old__desc_enfeeble_chance(mi,pow);},[&]{return _desc_enfeeble_chance(mi,pow);});
 compare([&]{return old__desc_beckoning_valid(mi);},[&]{return _desc_beckoning_valid(mi);});
}
for(int pct:{-1,0,1,25,99,100})for(bool isblind:{false,true}){accuracy=pct;you.duration[DUR_BLIND]=isblind;compare([&]{return old__desc_plasma_hit_chance(mi,42);},[&]{return _desc_plasma_hit_chance(mi,42);});}
for(int spaces=0;spaces<=8;++spaces){mi.pos.x=spaces;compare([&]{return old__desc_airstrike_bonus(mi);},[&]{return _desc_airstrike_bonus(mi);});}
for(bool state:{false,true})for(const char*kind:{"immune_roots","unstickable"}){insubstantial=state;string id="spell.prompt.effect."+string(kind);string en=string(kind)=="immune_roots"?"immune to roots":"unstickable";compare([&]{return old__desc_insubstantial(mi,en);},[&]{return _desc_insubstantial(mi,id);});}
// Polymorph branch order, empty/unavailable set, slime/ugly/shapeshifter and colours.
for(int type:{0,int(MONS_UGLY_THING),int(MONS_VERY_UGLY_THING),int(MONS_SLIME_CREATURE)})for(int mask=0;mask<32;++mask)for(int size:{0,1,2,3}){
 mi=monster_info();mi.type=type;mi.wl=(mask&1)?WILL_INVULN:10;mi.props.has=mask&2;mi.mb.flags=(mask&4)?MB_SHAPESHIFTER:0;mi.slime_size=(mask&8)?2:1;beam.affected=mask&16;beam.beam.flavour=BEAM_POLYMORPH;polyset.clear();for(int n=0;n<size;++n)polyset.emplace_back(n+1);known=true;
 compare([&]{return old_desc_wl_success_chance(mi,40,&beam);},[&]{return desc_wl_success_chance(mi,40,&beam);});
}
// Unknown semantic monster name triggers an entire polymorph sentence fallback.
mi=monster_info();mi.wl=5;mi.props.has=true;beam.affected=true;beam.beam.flavour=BEAM_POLYMORPH;polyset={1,4,2};known=false;auto visible_args=desc_wl_success_chance(mi,40,&beam);auto visible=displayed(visible_args);assert(!visible_args[0].supported&&visible_args[1].supported);vector<string> canonical;{ZhTranslationPause pause;canonical=old_desc_wl_success_chance(mi,40,&beam);}assert(visible.size()==2&&visible[0]==canonical[0]&&visible[1]!=canonical[1]);++cases;
// The public Lua entry is guarded by a translation pause; every effect helper
// above is compared inside that same pause to prove canonical English survives.
cout<<"PASS: "<<cases<<" actual spell effect producer cases, chances, effect combinations, polymorph grammar/colours, unknown-name full fallback and canonical Lua mode\n";
}
'''
    for q in fixture['functions']:
        name=q.split('(')[0].split()[-1]
        if name=='_mon_threat_string':
            continue
        code=re.sub(r'\b'+re.escape(name)+r'(?=\()',name+'_messages',code)
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp);(p/'test.cc').write_text(code)
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
        subprocess.run([str(p/'test')],check=True,timeout=180)


if __name__=='__main__':main()
