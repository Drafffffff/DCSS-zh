#!/usr/bin/env python3
"""Exercise typed rendering and independent Luna oracles; inspect real call sites."""
import json,subprocess,tempfile
from pathlib import Path
from compile_message_ids import ROOT,SRC,LOC,SHORTCUT,compile_catalog
assert SHORTCUT.findall('<w>%?!"=()[</w> text <input>$cmd[CMD_DROP]</input>') == ['[CMD_DROP]']
assert SHORTCUT.findall('[a-z] (y/n) [Esc]') == ['[a-z]', '(y/n)', '[Esc]']
messages=compile_catalog();q=lambda s:json.dumps(s,ensure_ascii=False).replace('?', r'\?')
types={'text':'Text','name':'Name','integer':'Integer','number':'Number','key':'Key','colour':'Colour','key_markup':'KeyMarkup'}
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
code+='''
// Mirror the semantic enum lookup and typed binding used by the real
// spell-detail noise producer; this catches catalog/schema type drift.
{
 auto rating=zh_word_arg("noise","spell.noise.","Almost silent",ZhArgType::Name);
 assert(rating.supported && rating.localized=="几乎无声");
 ZhArg noise{"noise",ZhArgType::Name,"Almost silent (1)","几乎无声（1）",rating.supported};
 auto rendered=zh_message("spell.stats.noise",{
   zh_text("indent"," "," "),noise});
 assert(rendered.display()=="\\n 噪声：几乎无声（1）");++checks;
}
{
 auto rendered=zh_message("spell.stats.damage",{
   zh_text("indent","",""),
   ZhArg{"damage",ZhArgType::Text,"1d3","1d3",true},
   ZhArg{"maximum",ZhArgType::Text," (max 1d8)","（最高1d8）",true}});
 assert(rendered.display()=="\\n伤害：1d3（最高1d8）");++checks;
}
'''
for path in sorted(LOC.glob('luna-*-messages.json')):
 for case in json.loads(path.read_text()).get('test_cases',[]):
  args=[]
  for key,value in case['args'].items():
   args.append('{'+q(key)+',ZhArgType::'+types[value['type']]+','+q(str(value['canonical']))+','+q(str(value['localized']))+'}')
  template_en=messages[case['id']]['en']
  for key,value in case['args'].items():
   template_en=template_en.replace('{'+key+'}',str(value['canonical']))
  # The renderer decodes literal braces after named substitutions.
  template_en=template_en.replace('{{','{').replace('}}','}')
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
for identity,entry in messages.items():
 if entry.get('source_context') and not entry['params']:
  code+='assert(zh_source('+q(entry['source_context'])+','+q(entry['en'].replace('{{','{').replace('}}','}'))+')=='+q(entry['zh'].replace('{{','{').replace('}}','}'))+');++checks;\n'
code+='''
setenv("DCSS_ZH_STRICT_SOURCE","1",1);
assert(zh_source("test.optional_empty", "").empty());
bool missing_source=false;
try {zh_source("test.unregistered","Unregistered fixed source");}
catch(const std::invalid_argument &) {missing_source=true;}
assert(missing_source);
{ZhTranslationPause pause;assert(zh_source("test.unregistered","Canonical Lua source")=="Canonical Lua source");}
unsetenv("DCSS_ZH_STRICT_SOURCE");++checks;
// A completed producer boundary rejects old matching without disabling new
// template selection. Raw formatted parsing uses pause only for structural I/O.
setenv("DCSS_ZH_FORBID_LEGACY","1",1);
{
 ZhLegacyGuard guard("test.completed");
 assert(zh_message("shop.balance",{zh_integer("gold",5)}).display() != "You have 5 gold pieces.");
 bool old_rejected=false;
 try {zh_translate("You feel better.");}catch(const std::logic_error &){old_rejected=true;}
 assert(old_rejected);
 {ZhTranslationPause pause;assert(zh_translate("already selected")=="already selected");}
 {ZhLegacyBackground background;assert(!zh_translate("You feel better.").empty());}
 bool restored=false;
 try {zh_translate("You feel better.");}catch(const std::logic_error &){restored=true;}
 assert(restored);
 ++checks;
}
unsetenv("DCSS_ZH_FORBID_LEGACY");
// Legacy renderer bypass never changes typed-message or source selection.
{
 auto text=zh_message("hud.label.noise");
 {ZhLegacyPause raw;
  assert(zh_language_enabled()); assert(!zh_translation_paused());
  assert(text.display()==text.localized && text.display()!=text.canonical);
  assert(zh_translate("already selected")=="already selected");
  {ZhTranslationPause canonical;
   assert(!zh_language_enabled()); assert(text.display()==text.canonical);
  }
  assert(text.display()==text.localized);
 }
 assert(text.display()==text.localized); ++checks;
}
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
// Exercise the actual menu key helper output, preserving its markup exactly.
{
 auto key=zh_key_markup("key","[<w>Esc</w>]");
 auto rendered=zh_message("shopping_list.help.exit",{key});
 assert(rendered.display()=="[<w>Esc</w>]退出");++checks;
 assert(zh_key_markup("key","[<w><<</w>|<w>></w>]").supported);++checks;
 for (const auto &value:{"<red>Esc</red>","<w>Esc","</w>","<w><w>Esc</w></w>","Esc\\n"}) {
  bool rejected=false;try{zh_key_markup("key",value);}catch(const std::exception &){rejected=true;}
  assert(rejected);++checks;
 }
 bool rejected=false;
 try{zh_message("shopping_list.help.exit",{{"key",ZhArgType::KeyMarkup,"[<w>Esc</w>]","[<w>退出</w>]"}});}
 catch(const std::exception &){rejected=true;}
 assert(rejected);++checks;
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
 subprocess.run(['c++','-std=c++11','-O0','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(SRC/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=20)
