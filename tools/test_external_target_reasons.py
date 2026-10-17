#!/usr/bin/env python3
"""Real external reason predicates versus frozen pre-migration implementations."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
from test_target_notifications import block

def main():
    compile_catalog()
    fixture=json.loads((Path(__file__).parent/'fixtures/external-target-reasons-english.json').read_text())
    files={name:(SRC/file).read_text() for name,file in [('wall','god-abil.cc'),('pass','spl-other.cc'),('flame','spl-damage.cc'),('summon','spl-summoning.cc')]}
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>
using namespace std;
enum { DESC_THE, WILL_INVULN=100, ENCH_INNER_FLAME=1, MONS_CROCODILE=2};
int names=0;bool visible=true,known=true,wall=true,passive=true,movable=true,habitable=true,bounds=true,solid=false,aligned=false,expiry=false,croc=true;
struct coord_def {int x=0;coord_def(){}coord_def(int n):x(n){}int distance_from(coord_def p)const{return abs(x-p.x);}coord_def sgn()const{return coord_def((x>0)-(x<0));}bool zero()const{return x==0;}coord_def operator+(coord_def p)const{return x+p.x;}coord_def operator-(coord_def p)const{return x-p.x;}coord_def operator-()const{return -x;}};
struct actor {string en="the orc",zh="甲";bool seen=true,player_state=false,stationary=false;coord_def pos()const{return 0;}bool can_see(const actor&)const{return visible;}bool observable()const{return seen;}string name(int,bool=false)const{++names;return en;}bool is_habitable(coord_def)const{return habitable;}bool is_stationary()const{return stationary;}bool is_player()const{return player_state;}};
struct monster:actor {bool flame=false,spectral=true,friendly_state=false,neutral_state=false;int will=0;bool has_ench(int)const{return flame;}int willpower()const{return will;}bool friendly()const{return friendly_state;}bool neutral()const{return neutral_state;}};
monster live,beholder,fearmonger;bool has=true,has_beholder=false,has_fearmonger=false;
struct player:actor {monster*get_beholder(coord_def)const{return has_beholder?&beholder:nullptr;}monster*get_fearmonger(coord_def)const{return has_fearmonger?&fearmonger:nullptr;}}you;
struct world {int grid(coord_def)const{return 1;}}env;
bool feat_can_wall_jump_against(int){return wall;}
bool wu_jian_can_wall_jump_in_principle(coord_def){return wall&&passive&&movable;}
bool feat_is_solid(int){return solid;}bool in_bounds(coord_def){return bounds;}bool cell_is_solid(coord_def){return solid;}
actor*actor_at(coord_def){return has?&live:nullptr;}monster*monster_at(coord_def){return has?&live:nullptr;}
bool mons_can_be_spectralised(const monster&m){return m.spectral;}bool mons_aligned(const actor*,const actor*){return aligned;}
bool monster_habitable_grid(int,coord_def){return croc;}bool need_expiration_warning(coord_def){return expiry;}
string terrain_name="rock wall";const char*feat_type_name(int){return terrain_name.c_str();}string feature_description_at(coord_def,bool,int){return "the "+terrain_name;}
ZhArg zh_monster_arg(const string&key,const monster&m){return {key,ZhArgType::Name,m.name(DESC_THE),known?m.zh:m.en,known};}
ZhArg zh_actor_arg(const string&key,const actor*m){return {key,ZhArgType::Name,m->name(DESC_THE),known?m->zh:m->en,known};}
template<class...T>string make_stringf(const char*fmt,T...v){char b[2048];snprintf(b,sizeof(b),fmt,v...);return b;}
struct passwall_path {coord_def delta,actual_dest;bool dest_found=true;int walls=1;int actual_walls()const{return walls;}bool is_valid(string*)const;bool is_valid_display(ZhArg*)const;bool old_is_valid(string*)const;};
'''
    queries=[('wall','bool wu_jian_can_wall_jump_display('),('wall','bool wu_jian_can_wall_jump('),('pass','bool passwall_path::is_valid_display('),('pass','bool passwall_path::is_valid('),('flame','ZhArg mons_inner_flame_immune_reason_display('),('flame','string mons_inner_flame_immune_reason('),('summon','ZhArg mons_simulacrum_immune_reason_display('),('summon','string mons_simulacrum_immune_reason('),('summon','ZhArg surprising_crocodile_unusable_reason_display('),('summon','string surprising_crocodile_unusable_reason(')]
    for f,q in queries:code+=block(files[f],q)+'\n'
    for q,old in fixture['functions'].items():
        if 'passwall_path' in q:old=old.replace('passwall_path::is_valid','passwall_path::old_is_valid')
        else:
            name=q.split('(')[0].split()[-1];old=old.replace(name+'(','old_'+name+'(',1)
        code+=old+'\n'
    # Structural assertions bind actual display consumers, preserving their state/cost order.
    target=(SRC/'target.cc').read_text()
    for family,name in [('walljump','wu_jian_can_wall_jump_display'),('passwall','is_valid_display'),('inner_flame','mons_inner_flame_immune_reason_display'),('simulacrum','mons_simulacrum_immune_reason_display'),('surprising_crocodile','surprising_crocodile_unusable_reason_display')]:
        consumer=block(target,'bool targeter_'+family+'::valid_aim(')
        assert consumer.count(name+'(')==1,(family,'duplicate or missing query')
        assert 'notify_fail(' in consumer
    cast=block(files['flame'],'spret cast_inner_flame(')
    assert cast.count('mons_inner_flame_immune_reason_display(')==1 and 'mpr(ZhMessage{' in cast
    cast=block(files['pass'],'spret cast_passwall(')
    assert cast.count('is_valid_display(')==1 and cast.count('mpr(ZhMessage{')==2
    cast=block(files['summon'],'spret cast_surprising_crocodile(')
    assert cast.index('fail_check()')<cast.index('unusable_reason_display(')<cast.index('target.external.crocodile.hidden_blocker')
    cast=block(files['summon'],'spret cast_simulacrum(')
    assert cast.index('!you.can_see')<cast.index('fail_check()')<cast.index('!mons_can_be_spectralised')
    assert 'target.external.simulacrum.cast_immune' in cast and 'target.external.simulacrum.essence' in cast
    code+=r'''
int cases=0;
void compare(const ZhArg&r,const string&old){assert(r.canonical==old);if(!old.empty()&&r.supported){assert(r.localized!=old);assert(r.localized.find("the orc")==string::npos);}else if(!r.supported)assert(r.localized==old);++cases;}
void reset(){visible=known=wall=passive=movable=habitable=bounds=croc=true;solid=aligned=expiry=false;has=true;has_beholder=has_fearmonger=false;live=monster();you.player_state=true;}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.external.reasons");
for(string name:{"the orc","Sigmund","the Wizard's ghost","the two-headed ogre","the +7 spectral blade"})
for(int mask=0;mask<512;++mask){reset();live.en=name;visible=mask&1;known=mask&2;has=mask&4;live.flame=mask&8;live.will=(mask&16)?WILL_INVULN:0;live.spectral=mask&32;live.friendly_state=mask&64;live.neutral_state=mask&128;aligned=mask&256;
 auto m=has?&live:nullptr;names=0;auto a=mons_inner_flame_immune_reason_display(m);if(!has||!visible)assert(names==0);compare(a,old_mons_inner_flame_immune_reason(m));assert(mons_inner_flame_immune_reason(m)==a.canonical);
 compare(mons_simulacrum_immune_reason_display(m),old_mons_simulacrum_immune_reason(m));assert(mons_simulacrum_immune_reason(m)==old_mons_simulacrum_immune_reason(m));
 for(bool actual:{false,true})for(int terrain=0;terrain<8;++terrain){croc=terrain&1;solid=terrain&2;habitable=terrain&4;expiry=!habitable;
 names=0;auto r=surprising_crocodile_unusable_reason_display(you,1,actual);assert(names==0);compare(r,old_surprising_crocodile_unusable_reason(you,1,actual));assert(surprising_crocodile_unusable_reason(you,1,actual)==r.canonical);}
}
for(int mask=0;mask<1024;++mask){reset();wall=mask&1;passive=mask&2;movable=mask&4;has_beholder=mask&8;has_fearmonger=mask&16;solid=mask&32;bounds=mask&64;habitable=mask&128;has=mask&256;live.seen=mask&512;
 for(int distance:{0,1,2}){ZhArg r;string old;bool ok=wu_jian_can_wall_jump_display(distance,r);bool was=old_wu_jian_can_wall_jump(distance,old);assert(ok==was);compare(r,old);string canonical;assert(wu_jian_can_wall_jump(distance,canonical)==was&&canonical==old);if(has&&!live.seen&&r.message_id=="target.external.wall_jump.blocked")assert(r.canonical.find("the orc")==string::npos);}
}
for(int mask=0;mask<128;++mask){reset();passwall_path p;p.delta=(mask&1)?1:0;p.walls=(mask&2)?1:0;p.dest_found=mask&4;bounds=mask&8;solid=mask&16;has=mask&32;live.stationary=mask&64;ZhArg r;string old="preserve on success";bool ok=p.is_valid_display(&r);bool was=p.old_is_valid(&old);assert(ok==was);if(!ok)compare(r,old);string canonical="preserve on success";assert(p.is_valid(&canonical)==was&&canonical==old);assert(p.is_valid(nullptr)==was);}
// Reuse the typed output across a failure and a successful validation.
reset();passwall_path reused;ZhArg reused_reason;reused.delta=0;
assert(!reused.is_valid_display(&reused_reason));assert(!reused_reason.canonical.empty()&&!reused_reason.message_id.empty());
reused.delta=1;live.stationary=false;assert(reused.is_valid_display(&reused_reason));
assert(reused_reason.canonical.empty()&&reused_reason.localized.empty()&&reused_reason.message_id.empty()&&reused_reason.supported);++cases;
assert(reused.is_valid_display(nullptr));++cases;
cout<<"PASS: "<<cases<<" actual external target predicate comparisons; canonical wrappers, priority, visibility, hidden blockers and consumer binding\n";
}
'''
    # Derive names from the real classifier, so future terrain kinds cannot
    # silently pass through a stub which only ever returns rock wall.
    terrain_names=sorted(set(re.findall(r'return "([^"\n]+)";',
        block((SRC/'terrain.cc').read_text(),'const char* feat_type_name('))))
    assert len(terrain_names)>=17,terrain_names
    check='for(const char* kind:{'+','.join(json.dumps(n) for n in terrain_names)+'}){reset();terrain_name=kind;wall=false;ZhArg reason;string old;assert(!wu_jian_can_wall_jump_display(1,reason));assert(!old_wu_jian_can_wall_jump(1,old));assert(reason.supported);assert(reason.message_id=="target.external.wall_jump.terrain");compare(reason,old);}'
    code=code.replace('cout<<"PASS: "',check+'\ncout<<"PASS: "')
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'test.cc';path.write_text(code);exe=Path(tmp)/'test'
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(path),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True,timeout=30)
if __name__=='__main__':main()
