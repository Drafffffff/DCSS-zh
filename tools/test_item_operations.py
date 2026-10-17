#!/usr/bin/env python3
"""Exercise real operation producers against frozen canonical English functions.
Only world/item effects are seams; formatting and source branches are production.
"""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog
def block(s,needle):
    start=s.index(needle);end=s.index('{',start);depth=0
    # Production blocks below contain no braces embedded in strings.
    for i in range(end,len(s)):
        if s[i]=='{':depth+=1
        elif s[i]=='}':
            depth-=1
            if not depth:return s[start:i+1]
    raise AssertionError(needle)

compile_catalog()
refs=json.loads((ROOT/'tools/fixtures/item-operation-english.json').read_text())
needles={'items.cc':['void get_gold('], 'item-use.cc':['bool enchant_weapon(','bool enchant_armour('], 'invent.cc':['bool maybe_warn_about_removing(','static string _operation_verb(','bool check_warning_inscriptions(']}
blocks=[block(refs[f],n) for f,ns in needles.items() for n in ns]
symbols=set(re.findall(r'\b(?:OBJ|DESC|OPER|GOD|MSG|HINT|ARM)_[A-Z_]+\b','\n'.join(blocks)))
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
'''
symbols.update(['DESC_YOUR','DESC_THE','DESC_A','OBJ_JEWELLERY'])
code+='enum {'+','.join(sorted(symbols))+'};\nusing operation_types=int;\n'
code+=r'''
#define ASSERT(x) assert(x)
const int MAX_WPN_ENCHANT=9;
struct item_def {
 int base_type=OBJ_WEAPONS,sub_type=0,quantity=1,plus=0;bool inventory=true,known=true,cursed_flag=false,hide=false;
 string english="long sword",chinese="长剑";
 string name(int d)const {return (d==DESC_YOUR?"your ":d==DESC_THE?"the ":d==DESC_A?"a ":"b - ")+to_string(plus)+" "+english;}
 bool defined()const{return true;}bool cursed()const{return cursed_flag;}
};
struct {int religion=-1,gold=0,attribute[512]={};bool wield_change=false;void add_gold(int n){gold+=n;}}you;
struct {bool disables[512]={};}crawl_state;
struct {bool confirmation=true;} Options;
bool penance_flag=false,warning_flag=true,tele_flag=false,despise_flag=false;int tithe=0;
bool you_worship(int g){return you.religion==g;}int zin_tithe(const item_def&,int,bool){return tithe;}
bool in_inventory(const item_def&i){return i.inventory;}bool is_weapon(const item_def&i){return i.base_type==OBJ_WEAPONS;}
bool is_enchantable_weapon(const item_def&i){return i.plus<MAX_WPN_ENCHANT;}
bool is_enchantable_armour(const item_def&i){return i.plus<5;}
bool armour_is_hide(const item_def&i){return i.hide;}
bool needs_handle_warning(const item_def&,int,bool&out){out=penance_flag;return warning_flag;}
bool needs_notele_warning(const item_def&,int){return tele_flag;}
bool god_despises_item(const item_def&,int){return despise_flag;}
void learned_something_new(int){}
string make_stringf(const char*fmt,...){char b[8192];va_list args;va_start(args,fmt);vsnprintf(b,sizeof b,fmt,args);va_end(args);return b;}
string conjugate_verb(string v,bool plural){return v+(plural?"":"s");}
vector<string> emitted,rendered;bool answer=false;int canned=0;
void mpr(const ZhMessage&m){emitted.push_back(m.canonical);rendered.push_back(m.display());}
void mprf(const char*fmt,...){char b[8192];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);emitted.push_back(b);rendered.push_back(b);}
void canned_msg(int){++canned;}
int yesno(const char*s,bool,int){emitted.push_back(s);rendered.push_back(s);return answer;}
int yesno(const ZhMessage&m,bool,int){emitted.push_back(m.canonical);rendered.push_back(m.display());return answer;}
ZhArg zh_item_arg(const string&key,const item_def&i,int desc){return {key,ZhArgType::Name,i.name(desc),i.known?("+"+to_string(i.plus)+i.chinese):i.name(desc),i.known};}
string _item_name(item_def&i){return i.name(i.inventory?DESC_YOUR:DESC_THE);}
const int ATTR_GOLD_FOUND=0;
'''
for f,ns in needles.items():
 for n in ns:
  old=block(refs[f],n)
  # Frozen canonical calls stay separate from current producers.
  if n=='bool check_warning_inscriptions(':old=old.replace('_operation_verb(','old_operation_verb(')
  old=old.replace(n,n.replace(' get_gold(',' old_get_gold(').replace(' enchant_weapon(',' old_enchant_weapon(').replace(' enchant_armour(',' old_enchant_armour(').replace(' maybe_warn_about_removing(',' old_maybe_warn_about_removing(').replace(' _operation_verb(',' old_operation_verb(').replace(' check_warning_inscriptions(',' old_check_warning_inscriptions('),1)
  code+=old+'\n'+block((SRC/f).read_text(),n)+'\n'
code+=r'''
int checks=0;
void compare(const vector<string>&old){if(old!=emitted){for(auto&s:old)cerr<<"OLD "<<s<<"\n";for(auto&s:emitted)cerr<<"NEW "<<s<<"\n";abort();}++checks;}
void reset(){emitted.clear();rendered.clear();canned=0;}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("test.item.operations");
 for(int gold:{0,1,2,99,100000})for(int amount:{1,2,9})for(int tax:{0,1})for(bool quiet:{false,true}){
  item_def i;you.gold=gold;you.religion=tax?GOD_ZIN:-1;tithe=tax;reset();old_get_gold(i,amount,quiet);auto old=emitted;int total=you.gold;
  you.gold=gold;reset();get_gold(i,amount,quiet);compare(old);assert(you.gold==total);if(!emitted.empty())assert(rendered[0]!=emitted[0]);
 }
 for(bool inventory:{false,true})for(bool quiet:{false,true})for(bool known:{false,true})for(int plus:{0,4,8,9})for(int kind:{OBJ_WEAPONS,OBJ_ARMOUR})for(bool hide:{false,true}){
  item_def i;i.inventory=inventory;i.known=known;i.plus=plus;i.base_type=kind;i.hide=hide;
  i.english="<cyan>weapon \"N:5\"</cyan>";i.chinese="<cyan>武器「N:5」</cyan>";
  item_def copy=i;reset();bool a=kind==OBJ_WEAPONS?old_enchant_weapon(copy,quiet):old_enchant_armour(copy,quiet);auto old=emitted;int oldc=canned;
  reset();bool b=kind==OBJ_WEAPONS?enchant_weapon(i,quiet):enchant_armour(i,quiet);compare(old);assert(a==b&&i.plus==copy.plus&&canned==oldc);
  for(size_t n=0;n<emitted.size();++n){assert(known?(rendered[n]!=emitted[n]):(rendered[n]==emitted[n]));assert(rendered[n].find("<cyan>")!=string::npos);}
 }
 for(int flags=0;flags<128;++flags)for(int kind:{OBJ_WEAPONS,OBJ_STAVES,OBJ_ARMOUR,OBJ_JEWELLERY})for(int op:{OPER_ANY,OPER_DROP,OPER_EQUIP,OPER_EVOKE,OPER_FIRE,OPER_MEMORISE,OPER_PUTON,OPER_QUAFF,OPER_QUIVER,OPER_READ,OPER_REMOVE,OPER_TAKEOFF,OPER_UNEQUIP,OPER_WEAR,OPER_WIELD,OPER_ZAP}){
  item_def i;i.base_type=kind;i.cursed_flag=flags&1;i.inventory=flags&2;penance_flag=flags&4;warning_flag=flags&8;tele_flag=flags&16;despise_flag=flags&32;answer=flags&64;
  reset();bool a=old_maybe_warn_about_removing(i);auto old=emitted;reset();bool b=maybe_warn_about_removing(i);compare(old);assert(a==b);
  reset();a=old_check_warning_inscriptions(i,op);old=emitted;reset();b=check_warning_inscriptions(i,op);compare(old);assert(a==b);for(size_t n=0;n<emitted.size();++n)assert(rendered[n]!=emitted[n]);
 }
 cout<<"PASS "<<checks<<" actual producer cases: gold/enchant/snapshot/warnings, canonical behavior and full fallback\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11','-O0','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=30)
