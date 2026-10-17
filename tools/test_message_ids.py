#!/usr/bin/env python3
"""Exercise typed rendering and independent Luna oracles; inspect real call sites."""
import json,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,LOC,compile_catalog
messages=compile_catalog();q=lambda s:json.dumps(s,ensure_ascii=False)
types={'text':'Text','name':'Name','integer':'Integer','number':'Number','key':'Key','colour':'Colour'}
code='''#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <stdexcept>
#include <iostream>
int main() {
setenv("DCSS_LANG","zh",1);
int checks=0;
'''
for path in sorted(LOC.glob('luna-*-messages.json')):
 for case in json.loads(path.read_text()).get('test_cases',[]):
  args=[]
  for key,value in case['args'].items():
   args.append('{'+q(key)+',ZhArgType::'+types[value['type']]+','+q(str(value['canonical']))+','+q(str(value['localized']))+'}')
  template_en=messages[case['id']]['en']
  for key,value in case['args'].items():
   template_en=template_en.replace('{'+key+'}',str(value['canonical']))
  override=''
  if template_en != case['canonical']:
   # The English caller retains its original singular/plural morphology.
   assert case['id'] in ('shop.balance','shop_gold_shortfall','shop_gold_after_purchase')
   assert any(str(v['canonical']) == '1' for v in case['args'].values())
   override=','+q(case['canonical'])
  call='zh_message('+q(case['id'])+', {'+','.join(args)+'}'+override+')'
  if case.get('wrapper_colour'):
   assert case['wrapper_colour'] in ('white','red')
  code+='''{ auto message='''+call+''';
if(message.canonical!='''+q(case['canonical'])+''' || message.display()!='''+q(case['zh'])+''') {std::cerr<<message.id<<": "<<message.display()<<"\\n";return 1;}
{ZhTranslationPause pause;assert(message.display()==message.canonical);}
setenv("DCSS_LANG","en",1);assert(message.display()==message.canonical);setenv("DCSS_LANG","zh",1);++checks;}
'''
code+='''
// Required, duplicate, unexpected, wrong-type, and missing-ID failures.
for(int variant=0;variant<5;variant++) {
 bool rejected=false;
 try {
  if(variant==0) zh_message("shop.balance",{});
  if(variant==1) zh_message("shop.balance",{zh_integer("gold",1),zh_integer("gold",2)});
  if(variant==2) zh_message("shop.balance",{zh_integer("gold",1),zh_integer("unknown",2)});
  if(variant==3) zh_message("shop.balance",{zh_number("gold",1)});
  if(variant==4) zh_message("not.a.registered.id");
 } catch(const std::exception &) {rejected=true;}
 assert(rejected);++checks;
}
for(const auto &value:{"red><white","红色","red\\n","notacolour"}) {
 bool rejected=false;try{zh_colour("colour",value);}catch(const std::exception &){rejected=true;}assert(rejected);++checks;
}
for(const auto &value:{"<w>f</w>","f\\n","<red>"}) {
 bool rejected=false;try{zh_key("key",value);}catch(const std::exception &){rejected=true;}assert(rejected);++checks;
}
for (const auto &value:{"5级","five","5.0","1\\n"}) {
 bool rejected=false;try{zh_message("shop.balance",{{"gold",ZhArgType::Integer,value,value}});}catch(const std::exception &){rejected=true;}assert(rejected);++checks;
}
// Unsupported ordinary names must preserve the entire English sentence.
auto fallback=zh_message("shop.welcome",{{"shop",ZhArgType::Name,"Unknown Shop","Unknown Shop",false}});
assert(fallback.display()==fallback.canonical);++checks;
// No general word fallback may produce mixed language from unknown prose.
assert(zh_translate("what would XQZ like to perform in an unknown situation") == "what would XQZ like to perform in an unknown situation");++checks;
std::cout<<"PASS: "<<checks<<" named-message oracle and validation checks\\n";
}
'''
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11','-O1','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=20)
