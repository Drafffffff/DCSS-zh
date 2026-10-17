#!/usr/bin/env python3
"""Compare real monster hint branch generation with the frozen English API."""
import json
import subprocess
import tempfile
from pathlib import Path
from compile_message_ids import SRC, compile_catalog
from test_target_notifications import block


def main():
    compile_catalog()
    text = (SRC / 'hints.cc').read_text()
    frozen = json.loads((Path(__file__).parent/'fixtures/monster-hints-english.json').read_text())['function']
    code = r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <sstream>
#include <iostream>
using namespace std;
enum {MONS_PLAYER_GHOST=1,ATT_FRIENDLY=1,MTHRT_NASTY=3,MTHRT_TOUGH=2,MB_BERSERK=1,MB_WANDERING=2,MB_UNAWARE=4,MB_DISTRACTED=8,CHATTR_NORMAL=0,GOD_TROG=1,MSGCH_TUTORIAL=1};
struct monster_info {int type=0,attitude=0,threat=0,flags=0;bool sleeping=false;bool is(int n)const{return flags&n;}bool asleep()const{return sleeping;}};
struct {bool hints_explored=false;} Hints;
struct {int may_stab_highlight=0;} Options;
struct {bool berserk=false;bool can_go_berserk()const{return berserk;}} you;
bool trog=false;
bool you_worship(int){return trog;}
bool mons_is_unique(int type){return type==2;}
// Value 2 models a nominally friendly attitude which will resume attacking;
// test it independently of the friendly display branch.
bool mons_att_wont_attack(int att){return att==ATT_FRIENDLY||att==3;}
string colour_to_str(int){return "cyan";}
int channel_to_colour(int){return 1;}
'''
    code += frozen.replace('string hints_describe_monster(', 'string old_hints_describe_monster(', 1) + '\n'
    for query in ['static ZhArg _hints_describe_monster_message(',
                  'string hints_describe_monster(',
                  'string hints_describe_monster_display(']:
        code += block(text, query) + '\n'
    code += r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.monster.hints");int cases=0;
for(int type:{0,1,2})for(int attitude:{0,1,2,3})for(int threat:{0,2,3})for(int flags=0;flags<16;++flags)for(int mask=0;mask<64;++mask){
 monster_info mi;mi.type=type;mi.attitude=attitude;mi.threat=threat;mi.flags=flags;mi.sleeping=mask&1;Hints.hints_explored=mask&2;Options.may_stab_highlight=mask&4;trog=mask&8;you.berserk=mask&16;const bool stats=mask&32;
 const auto expected=old_hints_describe_monster(mi,stats);const auto generated=_hints_describe_monster_message(mi,stats);assert(generated.canonical==expected);assert(generated.supported);assert(hints_describe_monster(mi,stats)==expected);const auto displayed=hints_describe_monster_display(mi,stats);assert(displayed==generated.localized);if(!expected.empty())assert(displayed!=expected);{ZhTranslationPause canonical;assert(hints_describe_monster_display(mi,stats)==expected);}++cases;
}
cout<<"PASS: "<<cases<<" actual monster hint producer cases, full canonical parity, semantic branch ordering, display/canonical API separation and markup\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        (root/'test.cc').write_text(code)
        subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(root/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(root/'test')],check=True)
        subprocess.run([str(root/'test')],check=True)


if __name__ == '__main__':
    main()
