#!/usr/bin/env python3
"""Exercise actual DB template/reference/unwrap path over all real status rows."""
import json,re,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC,ROOT,compile_catalog
from test_target_notifications import block
compile_catalog()
db=(SRC/'database.cc').read_text();lib=(SRC/'libutil.cc').read_text()
old=json.loads((ROOT/'tools/fixtures/monster-status-database-english.json').read_text())
rows={}
for section in (SRC/'dat/descript/monstatus.txt').read_text().split('%%%%'):
 section='\n'.join(line for line in section.splitlines() if not line.startswith('#')).strip()
 if section:
  key,body=section.split('\n',1);rows[key]=body.strip()+'\n'
code=r'''
#include "zh-database.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
using namespace std;
struct datum {const char*dptr=nullptr;int dsize=0;};
struct TextDB {map<string,string> rows;TextDB*translation=nullptr;map<string,string>*get(){return &rows;}}DescriptionDB;
datum _database_fetch(map<string,string>*db,const string&k){auto i=db->find(k);if(i==db->end())return {};datum d;d.dptr=i->second.data();d.dsize=i->second.size();return d;}
void lowercase(string&s){transform(s.begin(),s.end(),s.begin(),[](unsigned char c){return tolower(c);});}
string& trim_string_right(string&s){while(!s.empty()&&isspace((unsigned char)s.back()))s.pop_back();return s;}
string trimmed_string(string s){trim_string_right(s);size_t p=s.find_first_not_of(" \n\r\t");return p==string::npos?"":s.substr(p);}
string trim_string_right(string&&s){trim_string_right(s);return s;}
string replace_all(string s,const string&a,const string&b){size_t p=0;while((p=s.find(a,p))!=string::npos){s.replace(p,a.size(),b);p+=b.size();}return s;}
void _execute_embedded_lua(string&s){assert(s.find("{{")==string::npos);}
enum {MSGCH_DIAGNOSTICS};void mprf(int,const char*){assert(false);}
static string _query_database(TextDB&,string,bool,bool,bool=false);
'''
code+=block(lib,'string unwrap_desc(')+'\n'
code+=old['substitute']+'\n'+old['query']+'\n'+old['get']+'\n'
code+=block(db,'static ZhArg _description_message_tree(')+'\n'+block(db,'string zh_database_description(')+'\n'
code+='int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_STRICT_SOURCE","1",1);size_t checked=0;\n'
for k,v in rows.items():code+='DescriptionDB.rows['+json.dumps(k)+']='+json.dumps(v,ensure_ascii=False)+';\n'
code+=r'''
for(const auto &row:DescriptionDB.rows){
 auto result=_description_message_tree(row.first,"detail.monster.status_text",0);assert(result.supported);assert(result.localized.find("[[")==string::npos);
 string expected;{ZhTranslationPause pause;expected=getLongDescription(row.first);assert(zh_database_description(row.first,"detail.monster.status_text")==expected);}
 assert(trimmed_string(unwrap_desc(string(result.canonical)))==trimmed_string(expected));
 auto zh=zh_database_description(row.first,"detail.monster.status_text");assert(zh==unwrap_desc(string(result.localized)));if(zh==expected && !expected.empty()){cerr<<"Untranslated DB row: "<<row.first<<" = "<<expected<<endl;assert(false);}++checked;
}
DescriptionDB.rows["test alias"]="<asleep monstatus>\n";
assert(zh_database_description("TEST ALIAS","detail.monster.status_text")==zh_database_description("asleep monstatus","detail.monster.status_text"));++checked;
unsetenv("DCSS_ZH_STRICT_SOURCE");
DescriptionDB.rows["future status"]="Future unknown status template.\n";
DescriptionDB.rows["asleep monstatus"]+="\n[[future status]]\n";
const string fallback=zh_database_description("asleep monstatus","detail.monster.status_text");{ZhTranslationPause pause;assert(fallback==getLongDescription("asleep monstatus"));}++checked;
cout<<"PASS: "<<checked<<" real database status rows/alias/recursive reference expansion cases, frozen canonical DB path, actual unwrap, complete-parent fallback, source IDs and markup\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11','-DZH_STANDALONE','-I'+str(SRC),str(p/'test.cc'),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=30)
