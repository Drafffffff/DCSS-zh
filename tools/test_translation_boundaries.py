#!/usr/bin/env python3
"""Compile actual DB/skill producers against the real typed translation layer."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog
messages=compile_catalog();q=lambda v:json.dumps(v,ensure_ascii=False)
def extract(filename,name):
 text=(SRC/filename).read_text();match=re.search(r'static\s+(?:string|MenuEntry\*)\s*'+re.escape(name)+r'\([^;]*?\)\s*\{',text)
 assert match,name
 depth=0
 for end in range(text.index('{',match.start()),len(text)):
  if text[end]=='{':depth+=1
  elif text[end]=='}':
   depth-=1
   if not depth:return text[match.start():end+1]
 raise AssertionError(name)
lore=next(m for m in messages.values() if m.get('source_context')=='detail.monster.lore' and m['en']!=m['zh'])
quote=next(m for m in messages.values() if m.get('source_context')=='detail.monster.quote' and m['en']!=m['zh'])
names=[m for key,m in messages.items() if key.startswith('skill.name.')]
code=r'''#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using std::string;
static string lore,quote;
static string getLongDescription(const string& key) {
 if(key.empty())return "";
 return zh_language_enabled()?"AUTO-LOCALIZED DB SENTINEL":lore;
}
static string getQuoteString(const string& key) {
 if(key.empty())return "";
 return zh_language_enabled()?"AUTO-LOCALIZED QUOTE SENTINEL":quote;
}
static string trimmed_string(string s) {
 auto begin=s.find_first_not_of(" \r\n\t");
 return begin==string::npos?"":s.substr(begin,s.find_last_not_of(" \r\n\t")-begin+1);
}
// Database-tree expansion is covered by test_monster_status_database.py;
// this seam supplies one canonical fixed DB leaf to the actual display caller.
static string zh_database_description(const string& key,const char* context) {
 string source;{ZhTranslationPause canonical;source=getLongDescription(key);}
 return zh_source(context,source.c_str());
}
using skill_type=int;
static string current_skill;
static skill_type str_to_skill_safe(const string&) {return 1;}
static string skill_name(skill_type) {return current_skill;}
static const int MEL_ITEM=0,TRAINING_ENABLED=0;
struct tile_def {tile_def(int){}};
static int tileidx_skill(skill_type,int){return 0;}
struct MenuEntry {
 string text;void* data=nullptr;bool pretranslated=false;
 MenuEntry(const string& t,int,int,char):text(t){}
 void add_tile(tile_def){}
};
static MenuEntry* _simple_menu_gen(char letter,const string& str,string& key) {
 auto *me=new MenuEntry(str,MEL_ITEM,1,letter);me->data=&key;return me;
}
'''
code+='\n'+extract('describe.cc','_monster_db_source')+'\n'+extract('describe.cc','_monster_quote_source')+'\n'+extract('lookup-help.cc','_skill_menu_gen')+'\n'
code+='int main(){\nsetenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_STRICT_SOURCE","1",1);\n'
code+='lore='+q(lore['en'])+';quote='+q(quote['en'])+';\n'
code+='assert(_monster_db_source("detail.monster.lore","key")=='+q(lore['zh'])+');\n'
code+='assert(_monster_quote_source("key")=='+q(quote['zh'])+');\n'
code+='''assert(_monster_db_source("detail.monster.lore","").empty());
assert(_monster_quote_source("").empty());
{ZhLegacyPause raw;
 assert(_monster_db_source("detail.monster.lore","key")!=lore);
 assert(_monster_quote_source("key")!=quote);
}
{ZhTranslationPause canonical;
 assert(_monster_db_source("detail.monster.lore","key")==lore);
 assert(_monster_quote_source("key")==quote);
}
setenv("DCSS_LANG","en",1);
assert(_monster_db_source("detail.monster.lore","key")==lore);
setenv("DCSS_LANG","zh",1);
'''
for m in names:
 code+='{current_skill='+q(m['en'])+';string key='+q(m['en'].lower())+'; const string before=key;auto*entry=_skill_menu_gen(\'a\',current_skill,key);assert(entry->text=='+q(m['zh'])+');assert(entry->data==&key && key==before && entry->pretranslated);delete entry;\n'
 code+='setenv("DCSS_LANG","en",1);entry=_skill_menu_gen(\'a\',current_skill,key);assert(entry->text==current_skill && key==before);delete entry;setenv("DCSS_LANG","zh",1);}\n'
code+='std::cout<<"PASS: actual canonical DB readers, raw language scopes and '+str(len(names))+' skill chooser labels/keys\\n";}\n'
with tempfile.TemporaryDirectory() as folder:
 cpp=Path(folder)/'boundaries.cc';exe=Path(folder)/'boundaries';cpp.write_text(code)
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I',str(SRC),str(cpp),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
