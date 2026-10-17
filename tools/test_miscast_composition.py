#!/usr/bin/env python3
"""Compare actual miscast composition to frozen English across school bitsets."""
import json, re, subprocess, tempfile
from pathlib import Path
from compile_message_ids import SRC, ROOT, compile_catalog

def extract(s, name):
    m=re.search(r'(?:static )?(?:ZhArg|ZhMessage|vector<ZhArg>|string) '+re.escape(name)+r'\([^;]*?\)\s*\{',s)
    assert m,name
    start=s.index('{',m.start());depth=0
    for end in range(start,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[m.start():end+1]
    raise AssertionError(name)

compile_catalog()
source=(SRC/'describe.cc').read_text()
assert '_miscast_damage_string(' not in source
assert 'description << _miscast_composition_message(spell).display();' in source
frozen=json.loads((ROOT/'tools/fixtures/miscast-composition-english.json').read_text())['function']
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
#include <vector>
using namespace std;
using spell_type=int;
enum class spschool {none=0,conjuration=1,hexes=2,fire=4,ice=8,necromancy=16,summoning=32,translocation=64,alchemy=128,earth=256,air=512,forgecraft=1024};
struct spschools_type {int bits;bool operator&(spschool s)const{return bits&static_cast<int>(s);}};
int damage=0,severity=0,range_value=0;
int you=0;
int spell_range(int,int*,int,bool){return range_value;}
string spell_range_string(int){return to_string(range_value);}
spschools_type get_spell_disciplines(int s){return {s};}
int max_miscast_damage(int){return damage;}
int fail_severity(int){return severity;}
template<class I>string comma_separated_line(I a,I b,const string&last=" and ",const string&sep=", "){
 string out;for(auto it=a;it!=b;++it){if(it!=a){auto next=it;++next;out+=next==b?last:sep;}out+=*it;}return out;
}
template<class...A>string make_stringf(const char*f,A...a){char b[2048];snprintf(b,sizeof b,f,a...);return b;}
'''
code+=frozen+'\n'
for name in ['_miscast_list_arg','_miscast_effect_args','_miscast_composition_message','_spell_range_display_arg']:
    code+=extract(source,name)+'\n'
code+=r'''
int main(){
 setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.miscast");int count=0;
 for(int mask=0;mask<2048;++mask)for(int d:{0,1,5,99,9999})for(int fail:{0,1,3}){
  damage=d;severity=fail;
  const string expected="Miscasting this spell causes magic contamination"+(fail?" and also "+_miscast_damage_string(mask):string())+".\n";
  auto m=_miscast_composition_message(mask);
  if(m.canonical!=expected){cerr<<mask<<" "<<d<<" ["<<m.canonical<<"] != ["<<expected<<"]\n";return 1;}
  assert(m.localized!=expected&&m.display()==m.localized);
  assert(m.localized.find_first_of("{}ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")==string::npos);
  {ZhTranslationPause pause;assert(m.display()==expected);}
  ++count;
 }
 for(int r:{-1,0,1,7,9999}){
  range_value=r;auto arg=_spell_range_display_arg(0);assert(arg.supported);
  assert(arg.canonical==(r<=0?string("N/A"):to_string(r)));
  assert(r<=0?arg.localized!=arg.canonical:arg.localized==arg.canonical);
 }
 vector<ZhArg> mixed={{"effect",ZhArgType::Text,"a Wizard's unknown effect!","a Wizard's unknown effect!",false},zh_message_arg("effect","spell.miscast.effect.slows")};
 auto list=_miscast_list_arg("effects",mixed,"spell.miscast.effect.list.more","spell.miscast.effect.list.final");
 assert(!list.supported);
 auto parent=zh_message("spell.miscast.parent.multiple",{list});
 assert(parent.localized==parent.canonical&&parent.canonical.find("either a Wizard's unknown effect! or slows you")!=string::npos);
 cout<<"PASS: "<<count<<" actual miscast compositions, all school bitsets/numbers/severity, frozen canonical and parent fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);(p/'test.cc').write_text(code)
    subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,timeout=40)
