#!/usr/bin/env python3
"""Run the real curse source map, skill reader and detail producers."""
import re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,compile_catalog
compile_catalog()
def block(file,needle):
 s=(SRC/file).read_text();pos=s.index(needle);start=s.rfind('\n',0,pos)+1
 begin=s.index('{',pos);depth=0
 for end in range(begin,len(s)):
  if s[end]=='{':depth+=1
  if s[end]=='}':
   depth-=1
   if not depth:return s[start:end+1]
 raise AssertionError(needle)
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include "skill-type.h"
#include "curse-type.h"
#include <cassert>
#include <cstdlib>
#include <map>
#include <string>
#include <vector>
#include <iostream>
using std::string;using std::vector;using std::map;
#define ASSERT assert
struct CrawlStoreValue {int value;int get_int() const{return value;}};
using CrawlVector=vector<CrawlStoreValue>;
struct Props {CrawlVector values;bool present=true;bool exists(const char*)const{return present;}
 const Props& operator[](const char*)const{return *this;}const CrawlVector& get_vector()const{return values;}};
struct item_def {Props props;};
static const char* CURSE_KNOWLEDGE_KEY="current_curse_offer";
struct Player {bool can_currently_train[NUM_SKILLS]={};} you;
template<class It,class Fn> string comma_separated_fn(It b,It e,Fn fn){string out;for(auto i=b;i!=e;++i){if(i!=b)out+=(i+1==e?" and ":", ");out+=fn(*i);}return out;}
template<class It> string comma_separated_line(It b,It e){return comma_separated_fn(b,e,[](const string&s){return s;});}
'''
code+=block('skills.cc','static const char *skill_titles')+';\n'
code+=block('skills.cc','const char *skill_name(')+'\n'
code+=block('god-abil.cc','struct curse_data')+';\n'
code+=block('god-abil.cc','static map<curse_type, curse_data> _ashenzari_curses')+';\n'
for file,name in [('god-abil.cc','string desc_curse_skills('),('god-abil.cc','ZhArg zh_curse_skills_arg('),('describe.cc','static string _describe_item_curse(')]:code+=block(file,name)+'\n'
code+=r'''
int main(){setenv("DCSS_LANG","zh",1);
 for(auto& group:_ashenzari_curses){
  for(int sk=0;sk<NUM_SKILLS;++sk)you.can_currently_train[sk]=true;
  CrawlStoreValue c{group.first};auto entry=zh_curse_skills_arg("skills",c);
  assert(entry.supported && entry.localized!=entry.canonical);
  assert(entry.canonical==desc_curse_skills(c));
  for(auto sk:group.second.boosted){you.can_currently_train[sk]=false;auto filtered=zh_curse_skills_arg("skills",c);assert(filtered.supported);assert(filtered.canonical==desc_curse_skills(c));}
 }
 for(int sk=0;sk<NUM_SKILLS;++sk)you.can_currently_train[sk]=false;
 you.can_currently_train[SK_AXES]=true;
 item_def item;item.props.values={{CURSE_MELEE},{CURSE_ELEMENTS}};
 assert(zh_curse_skills_arg("skills",{CURSE_MELEE}).localized=="近战：斧术");
 const string expected="\n它受到的诅咒会增强以下技能：\n近战：斧术。\n元素：当前没有可训练的技能。";
 assert(_describe_item_curse(item)==expected);
 {ZhLegacyPause raw;assert(_describe_item_curse(item)==expected);}
 const string en="\nIt has a curse which improves the following skills:\nMelee Combat: Axes.\nElements: .";
 {ZhTranslationPause canonical;assert(_describe_item_curse(item)==en);}
 setenv("DCSS_LANG","en",1);assert(_describe_item_curse(item)==en);setenv("DCSS_LANG","zh",1);
 item.props.present=false;assert(_describe_item_curse(item).find("诅咒")!=string::npos);
 item.props.present=true;item.props.values.clear();assert(_describe_item_curse(item).find("诅咒")!=string::npos);
 std::cout<<"PASS: 10 real curse groups, trainability filters, canonical skills and whole detail composition\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 cpp=Path(tmp)/'curse.cc';exe=Path(tmp)/'curse';cpp.write_text(code)
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I',str(SRC),str(cpp),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
