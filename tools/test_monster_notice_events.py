#!/usr/bin/env python3
"""Exercise actual alert producer with a frozen pre-migration canonical body."""
import json, subprocess, tempfile
from pathlib import Path
from compile_message_ids import SRC, compile_catalog
from test_target_notifications import block

def main():
    compile_catalog()
    source=(SRC/'player-notices.cc').read_text()
    old=json.loads((Path(__file__).parent/'fixtures/monster-notice-events-english.json').read_text())['static bool _check_monster_alert(']
    code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdio>
#include <iostream>
#include <vector>
using namespace std;
enum {DESC_A,DESC_THE,MSGCH_MONSTER_WARNING,GOD_GOZAG,MSGCH_GOD,MTHRT_UNDEF=9};
vector<string> effects;string canonical,localized;int channel=-1;bool supported=true;
struct monster {bool living=true,firewood=false,summoned=true,unusual=false;int attitude=0,type=1,threat=2;string label="orc";bool alive()const{return living;}bool is_firewood()const{return firewood;}bool is_summoned()const{return summoned;}string name(int d)const{return (d==DESC_A?"an ":"the ")+label;}};
struct monster_info{const monster* m;monster_info(const monster* p):m(p){}bool has_unusual_items()const{return m->unusual;}};
struct {bool monster_alert[4]={},monster_alert_uniques=false,monster_alert_unusual=false;int monster_alert_min_threat=MTHRT_UNDEF;}Options;
bool mons_is_unique(int t){return t==2;}int mons_threat_level(const monster&m){return m.threat;}bool mons_att_wont_attack(int a){return a!=0;}
void update_screen(){effects.push_back("update");}void viewwindow(){effects.push_back("view");}void more(bool f){assert(f);effects.push_back("more");}
void mpr(const ZhMessage& m,int ch){effects.push_back("message");canonical=m.canonical;localized=m.localized;channel=ch;}
void mprf(int ch,const char*fmt,const char*name){char b[256];snprintf(b,sizeof b,fmt,name);effects.push_back("message");canonical=b;channel=ch;}
ZhArg zh_monster_arg(const string&key,const monster&m,int d){return {key,ZhArgType::Name,m.name(d),"测试怪物",supported};}
void reset(){effects.clear();canonical=localized="";channel=-1;}
'''
    code+=old.replace('_check_monster_alert(', '_old_alert(',1)+'\n'
    for q in ('static ZhMessage _summoned_alert_message(', 'static ZhMessage _wyrmbane_alert_message(', 'static ZhMessage _gozag_incite_message(', 'static bool _check_monster_alert('):code+=block(source,q)+'\n'
    code+=r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.monster.notice_events");int count=0;
for(int mask=0;mask<1024;++mask){monster m;m.living=mask&1;m.firewood=mask&2;m.summoned=mask&4;m.attitude=mask&8;m.unusual=mask&16;m.type=mask&32?2:1;Options.monster_alert[m.type]=mask&64;Options.monster_alert_uniques=mask&128;Options.monster_alert_unusual=mask&256;Options.monster_alert_min_threat=mask&512?1:MTHRT_UNDEF;reset();auto old=_old_alert(m);auto oldeffects=effects;auto oldtext=canonical;auto oldch=channel;reset();assert(_check_monster_alert(m)==old);assert(effects==oldeffects&&canonical==oldtext&&channel==oldch);++count;}
for(const string&name:{string("orc"),string("ogre's brother"),string("Unique, the Bold")})for(bool known:{false,true}){monster m;m.label=name;supported=known;auto a=_summoned_alert_message(m);assert(a.canonical==m.name(DESC_A)+" comes into view.");auto g=_gozag_incite_message(m);assert(g.canonical=="Gozag incites "+m.name(DESC_THE)+" against you.");for(auto msg:{a,g}){assert(known?msg.localized!=msg.canonical:msg.localized==msg.canonical);}{ZhTranslationPause pause;assert(_summoned_alert_message(m).display()==a.canonical);}++count;}
auto w=_wyrmbane_alert_message();assert(w.canonical=="<green>Wyrmbane glows as a worthy foe approaches.</green>");assert(w.localized.find("<green>")==0&&w.localized.find("</green>")!=string::npos);cout<<"PASS: "<<count+1<<" canonical parity, side effects, warning channel, punctuation/name, fallback and colour cases\n";
}
'''
    assert 'mpr(_gozag_incite_message(*mons), MSGCH_GOD, GOD_GOZAG);' in source
    assert 'mpr(_wyrmbane_alert_message());' in source
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'test.cc').write_text(code)
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
        subprocess.run([str(p/'test')],check=True)
if __name__=='__main__':main()
