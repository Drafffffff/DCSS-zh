#!/usr/bin/env python3
"""Compile extracted production naming functions against a frozen English oracle.
Only unrelated item classes/world services are seams; catalog is private.
"""
import json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'native/crawl-ref/source'
def block(s,n):
 a=s.index(n); b=s.index('{',a); d=0
 for e in range(b,len(s)):
  if s[e]=='{':d+=1
  elif s[e]=='}':
   d-=1
   if not d:return s[a:e+1]
 raise AssertionError(n)
refs=json.loads((ROOT/'tools/fixtures/sol61-semantic-details-english.json').read_text())
assert refs['baseline']=='cc710081cd3f163eabf78c65b9144e040ef30aa8'
s=(SRC/'zh-display-name.cc').read_text(); old=refs['source']['item-name.cc']
# Keep the real name_aux prefix, scroll/corpse case bodies and plural/return tail.
# Other class cases are outside this work package and deliberately unavailable.
def aux(source):
 f=block(source,'string item_def::name_aux(')
 start=f.index('    switch (base_type)'); end=f.index('    // One plural to rule them all.')
 cases=''
 for case,following in [('OBJ_SCROLLS','OBJ_JEWELLERY'),('OBJ_CORPSES','OBJ_GIZMOS')]:
  a=f.index('    case '+case+':',start); b=f.index('    case '+following+':',a)
  cases+=f[a:b]
 return f[:start]+'    switch (base_type) {\n'+cases+'    default: return "unsupported";\n    }\n'+f[end:]
item_name=block(old,'string item_def::name('); aux_name=aux(old)
# Canonical naming API and relevant source paths must remain byte-identical.
assert block((SRC/'item-name.cc').read_text(),'string item_def::name(')==item_name
assert aux((SRC/'item-name.cc').read_text())==aux_name
functions=['std::string exact_component(','std::string description_prefix(','std::string possessive_suffix(', 'std::string _monster_type_component(', 'ZhArg _monster_visible_species_arg(', 'std::string item_classifier(', 'std::string semantic_item_base(', 'std::string cosmetic_item_modifier(', 'std::string translated_item_name(', 'ZhArg zh_monster_type_arg(', 'ZhArg zh_monster_arg(', 'ZhArg zh_monster_info_arg(', 'ZhArg zh_item_arg(', 'ZhArg zh_item_quantity_arg(', 'ZhArg zh_item_menu_arg(']
actual='\n'.join(block(s,n) for n in functions)
syms=set(re.findall(r'\b(?:OBJ|CORPSE|DESC|ISFLAG|MI|ARM|BOOK|MISC|SPWPN|MB|MBN|SLOT|UNRAND|MONS|MILEV|ATT|MNAME)_[A-Z_]+\b',actual+item_name+aux_name))
syms.discard('CORPSE_NAME_TYPE_KEY')
syms.update(['MONS_RAT','MONS_HYDRA','MONS_UNIQUE','ATT_HOSTILE','MONS_REMNANT','MONS_DART_SLUG','MONS_ORC','MONS_UNKNOWN','MF_NAME_MASK','MF_NAME_ADJECTIVE','MF_NAME_SUFFIX','MF_NAME_REPLACE','MF_NAME_SPECIES','MF_NAME_DEFINITE','RED','BROWN','GREEN','CYAN','MAGENTA','LIGHTGREY'])
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>
#include <map>
#include <sstream>
#include <iostream>
#include <algorithm>
using namespace std;
using colour_t=int;using description_level_type=int;using monster_type=int;using equipment_slot=int;using iflags_t=int;using brand_type=int;using missile_type=int;using stave_type=int;using skill_type=int;using spell_type=int;
'''
code+='\n'.join('const int '+n+'='+str(i)+';' for i,n in enumerate(sorted(syms)))+'\n'
code+=r'''
#define TAG_MAJOR_VERSION 34
#define ASSERT(x) assert(x)
const string HELPLESS_KEY="helpless";
const string ITEM_NAME_KEY="item_name",CORPSE_NAME_KEY="corpse_name",CORPSE_NAME_TYPE_KEY="corpse_name_type";
struct Value{string s;int n=0;Value&operator=(bool b){n=b;return *this;}int get_int64()const{return n;}string get_string()const{return s;}};
struct Props:map<string,Value>{using map<string,Value>::operator[];const Value&operator[](const string&k)const{return at(k);}bool exists(const string&k)const{return count(k);}};
struct monster_flags_t{int flags=0;monster_flags_t operator&(int n)const{monster_flags_t f;f.flags=flags&n;return f;}operator int()const{return flags;}};
struct item_def {int base_type=OBJ_SCROLLS,sub_type=0,quantity=1,slot='c',plus=0,plus2=0,charges=0,mon_type=MONS_DART_SLUG;unsigned subtype_rnd=0;bool identified=false,inventory=false,artifact=false,curse=false;int special=0;string inscription;Props props;
 bool is_identified()const{return identified;}bool cursed()const{return curse;}
 string name(int,bool=false,bool=false,bool=true,bool=false)const;string name_aux(int,bool=false,bool=false,bool=true)const;
};
struct Quiver{bool item_is_quivered(const item_def&)const{return false;}};
struct {int zigs_completed=0;Quiver quiver_action;const item_def*active_talisman()const{return nullptr;}}you;
bool in_inventory(const item_def&i){return i.inventory;}bool is_artefact(const item_def&i){return i.artifact;}bool armour_is_hide(const item_def&){return false;}bool item_is_orb(const item_def&){return false;}bool item_is_horn_of_geryon(const item_def&){return false;}bool book_has_title(const item_def&){return false;}bool is_weapon(const item_def&){return false;}bool item_is_melded(const item_def&){return false;}int item_equip_slot(const item_def&){return SLOT_UNUSED;}
string number_in_words(unsigned n){const char*w[]={"zero","one","two","three","four","five","six","seven","eight","nine","ten"};return n<11?w[n]:to_string(n);}
bool is_vowel(char c){return string("aeiouAEIOU").find(c)!=string::npos;}
string make_stringf(const char*f,...){return "bad item";}void die(const char*,int){abort();}
string _item_inscription(const item_def&i){return i.inscription.empty()?"":" {"+i.inscription+"}";}
bool _use_basename(const item_def&i,int desc,bool ident){return desc==DESC_BASENAME||desc==DESC_DBNAME&&!(ident||i.is_identified());}
string make_name(unsigned n,int){return n==0?"GIOJOT FEUBA":n==1?"X Y Z":n==2?"AaBb <&> \"":to_string(n)+" QOP";}
int effect_lookups=0;string scroll_type_name(int n){++effect_lookups;return n==0?"identify":"teleportation";}
string item_base_name(int,int){return "spear";}string missile_name(int){return "dart";}string staff_type_name(int){return "fire";}string sub_type_string(const item_def&,bool){return "book of Flames";}string talisman_type_name(int){return "beast talisman";}string potion_type_name(int){return "curing";}bool jewellery_is_amulet(int){return false;}string jewellery_effect_name(int,bool){return "protection";}
int get_equip_desc(const item_def&){return 0;}int get_weapon_brand(const item_def&){return SPWPN_NORMAL;}string weapon_brand_name(const item_def&,bool){return "";}string armour_ego_name(const item_def&,bool){return "";}string missile_brand_name(const item_def&,int){return "";}
bool is_xp_evoker(const item_def&){return false;}int evoker_plus(int){return 0;}int evoker_charges(int){return 1;}int evoker_max_charges(int){return 1;}bool armour_is_enchantable(const item_def&){return false;}bool jewellery_has_pluses(const item_def&){return false;}string skill_name(int){return "Fighting";}string spell_title(int){return "Magic Dart";}
string lowercase_string(string s){transform(s.begin(),s.end(),s.begin(),[](unsigned char c){return tolower(c);});return s;}
bool is_named_corpse(const item_def&i){return i.props.exists(CORPSE_NAME_KEY);}string get_corpse_name(const item_def&i,monster_flags_t*f){f->flags=0;if(!is_named_corpse(i))return "";f->flags=i.props.at(CORPSE_NAME_TYPE_KEY).n;return i.props.at(CORPSE_NAME_KEY).s;}
bool starts_with(const string&s,const string&p){return s.compare(0,p.size(),p)==0;}
string pluralise(string s){auto n=s.find("scroll");if(n!=string::npos)s.insert(n+6,"s");else if((n=s.find("corpse"))!=string::npos)s.insert(n+6,"s");else if((n=s.find("skeleton"))!=string::npos)s.insert(n+8,"s");return s;}
struct monsterentry{const char*name;};monsterentry data_rat{"rat"},data_hydra{"hydra"};monsterentry data_slug{"dart slug"},data_orc{"orc"},data_ugly{"ugly thing"},data_very{"very ugly thing"},data_unknown{"future beast"};
const monsterentry*get_monster_data(int t){return t==MONS_RAT?&data_rat:t==MONS_HYDRA?&data_hydra:t==MONS_DART_SLUG?&data_slug:t==MONS_ORC?&data_orc:t==MONS_UGLY_THING?&data_ugly:t==MONS_VERY_UGLY_THING?&data_very:&data_unknown;}
bool mons_is_the(int){return false;}bool mons_is_unique(int t){return t==MONS_UNIQUE;}int mons_species(int t){return t;}bool mons_class_is_remnant(int t){return t==MONS_REMNANT;}
string mons_type_name(int t,int){return get_monster_data(t)->name;}
int make_low_colour(int c){return c>=1000?c-1000:c;}
#define ARRAYSZ(a) (sizeof(a)/sizeof(a[0]))
int ugly_thing_colour_offset(int);
struct monster;
struct monster_info{int type=MONS_UGLY_THING,num_heads=0,_colour=RED,attitude=ATT_HOSTILE,flag=-1;string qualifier;bool headed=false;Props props;bool is(int f)const{return f==flag||(!qualifier.empty()&&f==MB_NAME_ADJECTIVE);}
 monster_info(){}monster_info(const monster*,int);
 bool has_hydra_multi_attack()const{return headed;}bool has_proper_name()const{return false;}string proper_name(int)const{return "";}
 string common_name(int=DESC_PLAIN)const;string full_name(int d)const{if(d==DESC_NONE)return "";string n=common_name();if(d==DESC_THE||d==DESC_ITS)n=(attitude==ATT_FRIENDLY?"your ":"the ")+n;else if(d==DESC_A)n="a "+n;else if(d==DESC_YOUR)n="your "+n;return d==DESC_ITS?n+"'s":n;}
};
struct monster{monster_info info;bool visible=true;monster(monster_info mi):info(mi){}bool observable()const{return visible;}bool friendly()const{return info.attitude==ATT_FRIENDLY;}string name(int d)const{return info.full_name(d);}};
monster_info::monster_info(const monster*m,int){*this=m->info;}
vector<string>missing;void audit_name_fallback(const string&domain,const string&name){missing.push_back(domain+":"+name);}
ZhArg zh_monster_type_arg(const string&,int);
string item_prefix(const item_def&,bool){return "scroll";}int menu_test_colour=13;int menu_colour(const string&,const string&,const string&,bool){return menu_test_colour;}string colour_to_str(int c){return c==13?"magenta":"lightgrey";}
'''
for name in ('ugly_colour_names','ugly_colour_values'):
 source=refs['source']['mon-util.cc'];a=source.index('static const ',source.index('static const char *ugly_colour_names') if name=='ugly_colour_names' else source.index('static const colour_t ugly_colour_values'));b=source.index(';',a)
 code+=source[a:b+1]+'\n'
for n in ('string ugly_thing_colour_name(', 'int ugly_thing_colour_offset('):code+=block(refs['source']['mon-util.cc'],n)+'\n'
code+=r'''string monster_info::common_name(int)const{string n=qualifier;if(props.exists(HELPLESS_KEY))n="helpless "+n;if(headed)n+=(num_heads<11?number_in_words(num_heads):to_string(num_heads))+"-headed ";if(type==MONS_UGLY_THING||type==MONS_VERY_UGLY_THING)n+=ugly_thing_colour_name(_colour)+" ";return n+mons_type_name(type,0); }'''+"\n"
code+=item_name+'\n'+aux_name+'\n'
code+='std::string exact_component(const std::string&);std::string description_prefix(int,bool);std::string semantic_item_base(const item_def&);std::string cosmetic_item_modifier(const item_def&,int,bool&);std::string item_classifier(const item_def&);\n'
code+='namespace frozen {\n'+block(refs['source']['zh-display-name.cc'],'std::string translated_item_name(')+'\n}\n'
# Separate frozen original visible-name wrappers; canonical calls remain English.
for n in ['ZhArg zh_item_arg(', 'ZhArg zh_item_quantity_arg(', 'ZhArg zh_item_menu_arg(']:
 f=block(refs['source']['zh-display-name.cc'],n)
 code+='namespace frozen {\n'+f+'\n}\n'
code+=actual+'\n'
code+=r'''
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);ZhLegacyGuard guard("sol61.semantic-details");int checks=0;
for(int cls:{OBJ_SCROLLS,OBJ_CORPSES})for(int subtype:{0,1})for(bool id:{false,true})for(int q:{1,2,17})for(unsigned label:{0u,1u,2u,999u})for(int mon:{MONS_DART_SLUG,MONS_ORC,MONS_UNKNOWN})for(bool inv:{false,true})for(int desc:{DESC_A,DESC_THE,DESC_YOUR,DESC_ITS,DESC_PLAIN,DESC_INVENTORY,DESC_INVENTORY_EQUIP,DESC_BASENAME,DESC_DBNAME,DESC_QUALNAME,DESC_NONE}){
 item_def i;i.base_type=cls;i.sub_type=cls==OBJ_CORPSES?(subtype?CORPSE_SKELETON:CORPSE_BODY):subtype;i.identified=id;i.quantity=q;i.subtype_rnd=label;i.mon_type=mon;i.inventory=inv;
 missing.clear();effect_lookups=0;auto a=zh_item_arg("item",i,desc);int calls=effect_lookups;auto actual_missing=missing;
 auto b=frozen::zh_item_arg("item",i,desc);missing=actual_missing;assert(a.canonical==b.canonical&&a.canonical==i.name(desc));
 bool translated=desc!=DESC_NONE&&desc!=DESC_BASENAME&&((desc!=DESC_DBNAME&&desc!=DESC_QUALNAME)||(cls==OBJ_SCROLLS&&id))&&!(cls==OBJ_CORPSES&&mon==MONS_UNKNOWN);
 if(a.supported!=translated){cerr<<"support "<<cls<<" "<<desc<<" "<<a.canonical<<"\n";abort();}
 if(translated){assert(a.localized!=a.canonical&&missing.empty());if(cls==OBJ_SCROLLS&&!id){assert(a.localized.find(make_name(label,MNAME_SCROLL))!=string::npos);assert(calls==0);}if(cls==OBJ_CORPSES&&mon==MONS_DART_SLUG){assert(a.localized.find("飞镖蛞蝓")!=string::npos);if(q>1)assert(a.localized.find(to_string(q)+"具")!=string::npos);else if(desc==DESC_A||desc==DESC_INVENTORY||desc==DESC_INVENTORY_EQUIP)assert(a.localized.find("一具")!=string::npos);else assert(a.localized.find("一具")==string::npos);}}
 else {assert(a.localized==a.canonical);if(desc!=DESC_NONE)assert(!missing.empty());}
 for(int count:{1,3}){auto qa=zh_item_quantity_arg("item",i,count,desc);auto qb=frozen::zh_item_quantity_arg("item",i,count,desc);assert(qa.canonical==qb.canonical);item_def snap=i;snap.quantity=count;auto direct=zh_item_arg("item",snap,desc);assert(qa.localized==direct.localized&&i.quantity==q);++checks;}
 auto ma=zh_item_menu_arg("item",i,desc);auto mb=frozen::zh_item_menu_arg("item",i,desc);assert(ma.canonical==mb.canonical);assert(ma.localized=="<magenta>"+a.localized+"</magenta>");++checks;
}
for(int cls:{OBJ_SCROLLS,OBJ_CORPSES})for(int mode:{0,1,2,3}){item_def i;i.base_type=cls;i.sub_type=CORPSE_BODY;if(mode==0)i.inscription="custom";if(mode==1)i.artifact=true;if(mode==2)i.props[ITEM_NAME_KEY].s="custom";if(mode==3&&cls==OBJ_CORPSES){i.props[CORPSE_NAME_KEY].s="Trog's pet";i.props[CORPSE_NAME_TYPE_KEY].n=0;}else if(mode==3)i.curse=true;auto a=zh_item_arg("item",i,DESC_A);assert(!a.supported&&a.localized==a.canonical);auto p=zh_message("sol61.name.corpse.body",{zh_named_arg("species",a)},"Parent "+a.canonical);assert(p.localized==p.canonical);++checks;}
for(int t:{MONS_UGLY_THING,MONS_VERY_UGLY_THING})for(int c:{RED,BROWN,GREEN,CYAN,MAGENTA,LIGHTGREY,RED+1000,BROWN+1000,GREEN+1000,CYAN+1000,MAGENTA+1000,LIGHTGREY+1000,-1})for(string qual:{"","ghostly ","bound ","custom "}){monster_info mi;mi.type=t;mi._colour=c;mi.qualifier=qual;auto a=_monster_visible_species_arg(mi);bool ok=qual.empty()&&c!=-1;assert(a.supported==ok);if(ok){assert(a.canonical==mi.common_name(0));assert(a.localized.find(t==MONS_UGLY_THING?"丑陋之物":"非常丑陋之物")!=string::npos);}else assert(a.localized==a.canonical);
 for(int desc:{DESC_A,DESC_THE,DESC_YOUR,DESC_ITS,DESC_PLAIN})for(int attitude:{ATT_HOSTILE,ATT_FRIENDLY}){mi.attitude=attitude;monster live(mi);auto x=zh_monster_arg("monster",live,desc);auto y=zh_monster_info_arg("monster",mi,desc);assert(x.supported==ok&&y.supported==ok&&x.localized==y.localized);assert(x.canonical==live.name(desc)&&y.canonical==mi.full_name(desc));++checks;}
 ++checks;}
for(int flag:{MB_NAME_REPLACE,MB_NAME_ADJECTIVE,MB_NAME_SUFFIX,MB_SPECTRALISED,MB_VAMPIRE_THRALL,MB_SHAPESHIFTER,-2}){monster_info mi;if(flag>=0)mi.flag=flag;else if(flag==-1)mi.props[HELPLESS_KEY].s="helpless";else mi.headed=true;monster live(mi);missing.clear();auto a=zh_monster_arg("monster",live,DESC_THE);assert(!a.supported&&a.localized==a.canonical&&!missing.empty());auto parent=zh_message("sol61.name.corpse.body",{zh_named_arg("species",a)},"Full "+a.canonical);assert(parent.localized==parent.canonical);++checks;}
for(int type:{MONS_RAT,MONS_ORC,MONS_HYDRA,MONS_UGLY_THING,MONS_VERY_UGLY_THING,MONS_UNKNOWN})for(int heads:{1,8,11,27})for(int colour:{RED,CYAN,MAGENTA})for(bool helpless:{false,true})for(string qual:{"","ghostly ","custom "})for(int desc:{DESC_A,DESC_THE,DESC_YOUR,DESC_ITS,DESC_PLAIN,DESC_DBNAME,DESC_NONE}){monster_info mi;mi.type=type;mi.headed=type==MONS_HYDRA;mi.num_heads=heads;mi._colour=colour;mi.qualifier=qual;if(helpless)mi.props[HELPLESS_KEY]=true;monster live(mi);auto a=zh_monster_arg("target",live,desc);auto b=zh_monster_info_arg("target",mi,desc);bool ok=qual.empty()&&type!=MONS_UNKNOWN&&desc!=DESC_DBNAME&&desc!=DESC_NONE;if(!(a.supported==((desc==DESC_DBNAME||desc==DESC_NONE)?true:ok)&&b.supported==ok&&a.canonical==live.name(desc)&&b.canonical==mi.full_name(desc)&&a.localized==b.localized)){cerr<<"helpless case "<<type<<" "<<heads<<" "<<helpless<<" "<<desc<<" "<<qual<<" "<<a.supported<<" "<<b.supported<<" "<<a.localized<<" / "<<b.localized<<"\n";abort();}assert(live.info.props.exists(HELPLESS_KEY)==helpless&&mi.props.exists(HELPLESS_KEY)==helpless);if(ok){assert((a.localized.find("无助的")!=string::npos)==helpless);if(type==MONS_HYDRA)assert(a.localized.find(to_string(heads))!=string::npos);}else assert(a.localized==a.canonical);++checks;}
monster_info helpless_rat;helpless_rat.type=MONS_RAT;helpless_rat.props[HELPLESS_KEY]=true;monster rat(helpless_rat);auto stab=zh_message("sol61.combat.stab.defend",{zh_monster_arg("target",rat,DESC_THE),zh_text("self","itself","自身")});assert(stab.canonical=="the helpless rat fails to defend itself.");assert(stab.localized=="无助的老鼠未能保护自身。");
for(int subtype:{CORPSE_BODY,CORPSE_SKELETON,255})for(int mon:{MONS_UNIQUE,MONS_UNKNOWN}){item_def i;i.base_type=OBJ_CORPSES;i.sub_type=subtype;i.mon_type=mon;auto a=zh_item_arg("item",i,DESC_A);assert(!a.supported&&a.localized==a.canonical);++checks;}
for(int colour:{-1,7,13})for(char slot:{'a','Z','$'})for(int cls:{OBJ_SCROLLS,OBJ_CORPSES}){menu_test_colour=colour;item_def i;i.base_type=cls;i.sub_type=CORPSE_BODY;i.inventory=true;i.slot=slot;auto a=zh_item_menu_arg("item",i,DESC_INVENTORY);auto b=frozen::zh_item_menu_arg("item",i,DESC_INVENTORY);assert(a.canonical==b.canonical&&a.localized.find(string(1,slot)+" - ")!=string::npos);if(colour!=-1)assert(a.localized.find("<"+colour_to_str(colour)+">")==0);else assert(a.localized[0]==slot);++checks;}menu_test_colour=13;
item_def screenshot_scroll;screenshot_scroll.inventory=true;auto scroll=zh_item_arg("item",screenshot_scroll,DESC_INVENTORY);assert(scroll.canonical=="c - a scroll labelled GIOJOT FEUBA"&&scroll.localized=="c - 标签为“GIOJOT FEUBA”的卷轴");
item_def screenshot_corpse;screenshot_corpse.base_type=OBJ_CORPSES;screenshot_corpse.sub_type=CORPSE_BODY;auto corpse=zh_item_arg("item",screenshot_corpse,DESC_A);assert(corpse.canonical=="a dart slug corpse"&&corpse.localized=="一具飞镖蛞蝓尸体");
cout<<"PASS "<<checks<<" real production name/quantity/menu cases; frozen canonical, hidden-effect isolation, labels, corpse source, ugly colour, whole-parent fallback\n";
}
'''
doc=json.loads((ROOT/'localization/migration/luna-sol61-semantic-details-messages.json').read_text());assert doc['model']==doc['reviewer_model']=='gpt-6.1-sol'
entries=doc['messages']
for file,id in [('luna-monster-events-messages.json','monster.name.headed'),('luna-sol61-combat-spells-messages.json','sol61.combat.stab.defend')]:
 entries += [e for e in json.loads((ROOT/'localization/migration'/file).read_text())['messages'] if e['id']==id]
for e in entries:
 for lang in ('en','zh'):assert set(re.findall(r'\{(\w+)\}',e[lang]))==set(e['params'])
q=lambda s:json.dumps(s,ensure_ascii=False).replace('?',r'\?')
catalog='static const ZhDefinition zh_definitions[] = {\n'
ids=set()
for e in entries:
 assert e['id'] not in ids;ids.add(e['id'])
 catalog+=' {'+', '.join(q(x) for x in (e['id'],e['en'],e['zh'],';'.join(k+':'+v for k,v in e['params'].items())))+'},\n'
catalog+='};\nstruct ZhSourceDefinition {const char *context,*source,*id;};\nstatic const ZhSourceDefinition zh_source_definitions[]={{nullptr,nullptr,nullptr}};\n'
with tempfile.TemporaryDirectory(prefix='sol61-semantic-') as td:
 p=Path(td);(p/'test.cc').write_text(code);shutil.copyfile(SRC/'zh-message.cc',p/'zh-message.cc');(p/'zh-message-catalog.inc').write_text(catalog)
 subprocess.run(['c++','-std=c++17','-O0','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(p/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=60)
