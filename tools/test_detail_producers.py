#!/usr/bin/env python3
"""Exercise production origin/terse-spell generators with the real ID runtime."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
messages=compile_catalog()
def extract(file,name):
    s=(SRC/file).read_text()
    m=re.search(r'(?:static )?(?:string|ZhArg|bool) '+re.escape(name)+r'\([^;]*?\)\s*(?:const\s*)?\{',s)
    assert m,name
    start=s.index('{',m.start());depth=0
    for end in range(start,len(s)):
        if s[end]=='{':depth+=1
        if s[end]=='}':
            depth-=1
            if depth==0:return s[m.start():end+1]
    raise AssertionError(name)
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <cctype>
#include <iostream>
#include <string>
#include <vector>
using std::string;using std::vector;
#define TAG_MAJOR_VERSION 34
using spell_type=int;using god_type=int;using monster_type=int;
enum {GOD_NO_GOD=0,NUM_GODS=10,IT_SRC_SHOP=100,IT_SRC_START=101,
AQ_SCROLL=102,AQ_INVENTED=103,AQ_CARD_GENIE=104,AQ_WIZMODE=105,
MONS_DANCING_WEAPON=20,MONS_PLAYER_GHOST=21,MONS_PANDEMONIUM_LORD=22};
struct Branch {const char* longname;const char* abbrevname;};
static Branch branches[40];static int brdepth[40];
struct level_id {int branch=0;int depth=5;string describe(bool,bool) const;};
static bool starts_with(const string&s,const string&prefix){return s.compare(0,prefix.size(),prefix)==0;}
static char tolower_safe(char c){return std::tolower(static_cast<unsigned char>(c));}
template<class... A> string make_stringf(const char*fmt,A... args){char buf[1024];std::snprintf(buf,sizeof(buf),fmt,args...);return buf;}
struct item_def {int orig_monnum=0;bool valid=true;level_id orig_place;vector<int> spells;};
static bool origin_describable(const item_def&i){return i.valid;}
static bool _origin_is_original_equip(const item_def&){return false;}
static string _article_it(const item_def&){return "it";}
string prep_branch_level_name(level_id);
static string _origin_place_desc(const item_def&i){return prep_branch_level_name(i.orig_place);}
static string _origin_monster_name(const item_def&i){return i.orig_monnum==MONS_PLAYER_GHOST?"a player ghost":"a yak";}
static string god_name(god_type){return "Xom";}

static ZhArg zh_monster_type_arg(const string&k,monster_type t){return {k,ZhArgType::Name,"yak",t==MONS_PLAYER_GHOST?"玩家幽灵":"牦牛",t!=99};}
static const char* spell_title(int s){return s==1?"Magic Dart":s==2?"Fireball":"UNKNOWN SPELL";}
static int spell_difficulty(int s){return s==1?1:5;}
static vector<int> spells_in_book(const item_def&i){return i.spells;}
struct spschools_type {static vector<int> range(){return {1,2};}};
static bool spell_typematch(int spell,int school){return school==1 || spell!=1;}
static string spelltype_long_name(int school){return school==1?"Conjuration":"Fire";}
template<class It> string comma_separated_line(It begin,It end){string out;for(auto i=begin;i!=end;++i){if(i!=begin)out+=(i+1==end?" and ":", ");out+=*i;}return out;}
'''
# The production origin reader remains canonical; add only the UI generator.
code+='\n'+extract('travel.cc','level_id::describe')+'\n'+extract('place.cc','prep_branch_level_name')+'\n'+extract('zh-display-name.cc','zh_place_arg')
code+='\n'+extract('items.cc','origin_desc')+'\n'+extract('items.cc','origin_display_desc')+'\n'+extract('describe-spells.cc','_spell_schools_arg')+'\n'+extract('describe-spells.cc','terse_spell_list')
code+=r'''
int main(){
 setenv("DCSS_LANG","zh",1);item_def i;
PLACE_CASES
 const int sources[]={0,-IT_SRC_SHOP,-AQ_SCROLL,-AQ_INVENTED,-AQ_CARD_GENIE,-AQ_WIZMODE,-1,MONS_DANCING_WEAPON,1,MONS_PLAYER_GHOST};
 const char* expected[]={"你在兽穴第5层发现了它。","你在兽穴第5层的一家商店买到了它。","你在兽穴第5层获得了它。","你在兽穴第5层亲手创造了它。","你在兽穴第5层抽到了精灵。","你在兽穴第5层凭借法师之力创造了它。","佐姆在兽穴第5层赐予了你这件物品。","你在兽穴第5层制服了它。","你在兽穴第5层从牦牛身上取下了它。","你在兽穴第5层从玩家幽灵身上取下了它。"};
 for(int n=0;n<10;++n){i.orig_monnum=sources[n];const string en="\n"+origin_desc(i)+".";
 assert(origin_display_desc(i)=="\n"+string(expected[n]));
 {ZhLegacyPause raw;assert(origin_display_desc(i)=="\n"+string(expected[n]));}
 {ZhTranslationPause canonical;assert(origin_display_desc(i)==en);}
 setenv("DCSS_LANG","en",1);assert(origin_display_desc(i)==en);setenv("DCSS_LANG","zh",1);
 }
 i.orig_monnum=-999;assert(origin_display_desc(i)=="\n"+origin_desc(i)+".");
 i.orig_monnum=99;assert(origin_display_desc(i)=="\n"+origin_desc(i)+".");
 i.valid=false;assert(origin_display_desc(i).empty());i.valid=true;
 i.spells={1,2};assert(terse_spell_list(i)=="法术：魔法飞镖（法术等级1，塑能）、火球（法术等级5，塑能/火焰）");
 setenv("DCSS_LANG","en",1);assert(terse_spell_list(i)=="Spells: Magic Dart (L1 Conjuration) and Fireball (L5 Conjuration/Fire)");setenv("DCSS_LANG","zh",1);
 i.spells={1,99};assert(terse_spell_list(i)=="Spells: Magic Dart (L1 Conjuration) and UNKNOWN SPELL (L5 Conjuration/Fire)");
 i.spells={};assert(terse_spell_list(i)=="法术：");
 std::cout<<"PASS: actual origin branches, canonical mode, raw scopes, whole-list fallback and spell levels\n";
}
'''
places=[m for k,m in messages.items() if k.startswith('place.branch.')]
branch_names={m[1] for m in re.findall(r'"([^"\n]+)",\s*"([^"\n]+)",\s*"([^"\n]+)"',(SRC/'branch-data.h').read_text())}
assert {m['en'] for m in places}==branch_names, 'Unreviewed branch name'
assert len(places)==40
checks=[]
for n,m in enumerate(places):
    q=lambda v:json.dumps(v,ensure_ascii=False)
    checks.append('branches['+str(n)+']={'+q(m['en'])+','+q(m['en'])+'};brdepth['+str(n)+']=1;')
    checks.append('{level_id p;p.branch='+str(n)+';p.depth=5;auto value=zh_place_arg("place",p);assert(value.supported && value.localized=='+q(m['zh'])+');brdepth[p.branch]=5;value=zh_place_arg("place",p);assert(value.supported && value.localized=='+q(m['zh']+'第5层')+');assert(value.canonical==prep_branch_level_name(p));}')
    if m['id']=='place.branch.lair':lair=n
checks.append('i.orig_place.branch='+str(lair)+';')
code=code.replace('PLACE_CASES','\n'.join(checks))
with tempfile.TemporaryDirectory() as tmp:
    cpp=Path(tmp)/'detail.cc';exe=Path(tmp)/'detail';cpp.write_text(code)
    subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I',str(SRC),str(cpp),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
