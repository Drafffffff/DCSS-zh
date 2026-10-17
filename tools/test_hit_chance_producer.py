#!/usr/bin/env python3
"""Run actual hit-chance producers, including the tutorial auxiliary attack crash."""
import subprocess
import tempfile
from pathlib import Path
from compile_message_ids import SRC
from test_target_notifications import block


def main():
    source = (SRC / 'describe.cc').read_text()
    code = r'''
#include "zh-message.h"
#include <algorithm>
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <sstream>
using namespace std;
enum { DESC_YOUR, DUR_BLIND=0 };
struct coord { int distance_from(const coord&)const{return 7;} };
struct player {int duration[1]={0};coord pos()const{return {};}int reach_range()const{return 2;}string hand_name(bool)const{return "hands";}} you;
struct monster_info {coord pos;};
struct item_def {bool valid=true,ranged=false,throwable=false;string name(int,bool,bool,bool)const{return "your sword";}};
struct attack {};
struct melee_attack:attack {melee_attack(player*,void*){}};
struct ranged_attack:attack {ranged_attack(player*,void*,const item_def*,bool){}};
bool is_weapon(const item_def&i){return i.valid;}
bool is_throwable(player*,const item_def&i){return i.throwable;}
bool is_range_weapon(const item_def&i){return i.ranged;}
bool is_penetrating_attack(const item_def&){return false;}
int last_distance;
int to_hit_pct(const monster_info&,const attack&,bool,bool,int d){last_distance=d;return 73;}
int to_hit_pct_aux(const monster_info&,const melee_attack&){return 42;}
vector<string> aux;
vector<string> get_player_aux_names(){return aux;}
ZhArg zh_item_arg(const string&key,const item_def&,int){return {key,ZhArgType::Name,"your sword","你的剑"};}
ZhArg describe_hit_chance_message(int,const item_def*,bool,int);
'''
    for name in ['static void _describe_aux_hit_chance(',
                 'ZhArg describe_to_hit_message(',
                 'ZhArg describe_hit_chance_message(']:
        code += block(source, name) + '\n'
    code += r'''
int main(){
 setenv("DCSS_LANG","zh",1);
 monster_info mi;item_def sword;int cases=0;
 for(bool verbose:{false,true})for(bool blind:{false,true})
 for(int count:{0,1,2,3})for(bool armed:{false,true}){
  you.duration[DUR_BLIND]=blind;
  aux={"kick","headbutt","peck"};aux.resize(count);
  const item_def*w=armed?&sword:nullptr;
  auto result=describe_to_hit_message(mi,w,verbose,nullptr,0);
  string expected=(verbose?"about ":"")+string("73% to hit");
  if(verbose)expected+=armed?" with your sword":" with your hands";
  if(blind)expected+=verbose?" (while you are blinded and from distance 2)":" at this distance";
  ostringstream suffix;if(count)_describe_aux_hit_chance(suffix,aux,42);
  expected+=suffix.str();
  assert(result.canonical==expected);
  assert(last_distance==2);
  if(!verbose||armed)assert(result.supported&&result.localized!=expected);
  ++cases;
 }
 aux={"unknown auxiliary attack"};
 auto unknown=describe_to_hit_message(mi,&sword,true,nullptr,0);
 assert(!unknown.supported&&unknown.localized==unknown.canonical);++cases;
 aux.clear();sword.ranged=true;
 auto ranged=describe_to_hit_message(mi,&sword,false,nullptr,9);
 assert(last_distance==9&&ranged.canonical=="73% to hit at this distance");++cases;
 sword.valid=false;sword.ranged=false;
 assert(describe_to_hit_message(mi,&sword,false,nullptr,0).canonical.empty());++cases;
 cout<<"PASS: "<<cases<<" hit-chance producer cases, auxiliary lists, blindness, canonical grammar and fallback\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'test.cc'
        path.write_text(code)
        exe = Path(tmp) / 'test'
        subprocess.run(['c++', '-std=c++11', '-DZH_STANDALONE', '-I'+str(SRC),
                        str(path), str(SRC/'zh-localization.cc'),
                        str(SRC/'zh-message.cc'), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True, timeout=30)

if __name__ == '__main__':
    main()
