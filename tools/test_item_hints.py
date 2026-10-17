#!/usr/bin/env python3
"""Exercise the actual item-hint branches against pre-migration English producers.
Engine state and object queries are seams; the producers, command substitution,
message runtime and reviewed catalog are production code.
"""
import re,subprocess,tempfile,json,os
from pathlib import Path
from compile_message_ids import ROOT,SRC,compile_catalog
compile_catalog()
def block(s,needle):
 pos=s.index(needle);start=s.rfind('\n',0,pos)+1;begin=s.index('{',pos);depth=0
 for end in range(begin,len(s)):
  if s[end]=='{':depth+=1
  if s[end]=='}':
   depth-=1
   if not depth:return s[start:end+1]
 raise AssertionError(needle)
source=(SRC/'hints.cc').read_text()
# A checked-in reference snapshot makes this check portable outside native git.
snapshot=ROOT/'tools/fixtures/item-hints-english.cc'
if snapshot.exists():reference=snapshot.read_text()
else:
 reference=subprocess.check_output(['git','show','b0ad16b5ca8421ccc1789f4b59bcaa9d84cc07a8:crawl-ref/source/hints.cc'],cwd=ROOT/'native',text=True)
 snapshot.parent.mkdir(exist_ok=True)
 reference='\n\n'.join(block(reference,n) for n in ['static string _hints_target_mode(','static string _hints_abilities(','static string _hints_throw_stuff(','string hints_describe_item('])
 snapshot.write_text('// Pre-migration b0ad16b English producers, test reference only.\n'+reference+'\n')
base=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include "skill-type.h"
#include <algorithm>
#include <cassert>
#include <cstdlib>
#include <initializer_list>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
#define ASSERT assert
enum command_type { CMD_FIRE,CMD_CAST_SPELL,CMD_USE_ABILITY,CMD_WIELD_WEAPON,CMD_WEAR_ARMOUR,CMD_WEAR_JEWELLERY,CMD_RESISTS_SCREEN,CMD_WEAPON_SWAP,CMD_ADJUST_INVENTORY,CMD_DISPLAY_SKILLS,CMD_PRIMARY_ATTACK,CMD_DISPLAY_MUTATIONS,CMD_REMOVE_ARMOUR,CMD_EVOKE,CMD_READ,CMD_REMOVE_JEWELLERY,CMD_QUAFF,CMD_MEMORISE_SPELL,CMD_DROP };
enum { OBJ_WEAPONS,OBJ_MISSILES,OBJ_ARMOUR,OBJ_WANDS,OBJ_SCROLLS,OBJ_JEWELLERY,OBJ_POTIONS,OBJ_BOOKS,OBJ_CORPSES,OBJ_STAVES,OBJ_MISCELLANY,OBJ_OTHER };
enum { MI_DART, MI_JAVELIN, MI_STONE, MI_LARGE_ROCK, MI_THROWING_NET, MI_BOOMERANG, MI_NEEDLE, MI_SLUG, MI_ARROW, MI_BOLT, MI_SLING_BULLET };
enum { HINT_SEEN_WEAPON,HINT_SEEN_MISSILES,HINT_SEEN_ARMOUR,HINT_SEEN_WAND,HINT_SEEN_SCROLL,HINT_SEEN_JEWELLERY,HINT_SEEN_POTION,HINT_SEEN_SPBOOK,HINT_SEEN_STAFF,HINT_SEEN_MISC,HINT_MAGIC_CHAR,HINT_RANGER_CHAR,HINT_BERSERK_CHAR };
enum { MSGCH_TUTORIAL, DESC_YOUR, MUT_HORNS, ARM_BARDING=10, NUM_RINGS=20, BOOK_MANUAL=30, SLOT_BODY_ARMOUR=40, ISFLAG_NO_DESC=0, GOD_TROG=50 };
struct item_def {int base_type=OBJ_WEAPONS,sub_type=0,quantity=1;char slot='d';bool equipped=false,art=false,identified=true,resistance=false,ability=false,ranged=false,throwable=true,helmet=false,body=false,light=true,shield=false,offhand=false;int cosmetic=0;skill_type skill=SK_AXES;bool name_supported=true;
 bool is_identified()const{return identified;}string name(int)const{return quantity>1?"your javelins":"your javelin";}};
struct Player {int skills[NUM_SKILLS]={};int horns=0;bool trog=false;int get_innate_mutation_level(int)const{return horns;}} you;
struct HintsState {bool hints_events[20]={};int hints_type=HINT_BERSERK_CHAR;} Hints;
struct Tiles {bool fullscreen=false;bool is_fullscreen()const{return fullscreen;}} tiles;
bool item_is_equipped(const item_def&i){return i.equipped;}bool is_artefact(const item_def&i){return i.art;}
bool gives_ability(const item_def&i){return i.ability;}bool gives_resistance(const item_def&i){return i.resistance;}
bool is_range_weapon(const item_def&i){return i.ranged;}bool is_throwable(Player*,const item_def&i){return i.throwable;}
bool is_hard_helmet(const item_def&i){return i.helmet;}int get_armour_slot(const item_def&i){return i.body?SLOT_BODY_ARMOUR:0;}
bool is_effectively_light_armour(const item_def*i){return i->light;}bool is_shield(const item_def&i){return i.shield;}
bool is_offhand(const item_def&i){return i.offhand;}int get_equip_desc(const item_def&i){return i.cosmetic;}
skill_type item_attack_skill(const item_def&i){return i.skill;}skill_type best_skill(skill_type,skill_type){return SK_LONG_BLADES;}
string item_base_name(const item_def&){return "javelin";}string god_name(int,bool){return "Trog";}bool you_worship(int){return you.trog;}
string colour_to_str(int){return "cyan";}int channel_to_colour(int){return 0;}
map<command_type,string> keys={{CMD_FIRE,"f"},{CMD_CAST_SPELL,"z"},{CMD_USE_ABILITY,"a"},{CMD_WIELD_WEAPON,"w"},{CMD_WEAR_ARMOUR,"W"},{CMD_WEAR_JEWELLERY,"P"},{CMD_RESISTS_SCREEN,"%"},{CMD_WEAPON_SWAP,"'"},{CMD_ADJUST_INVENTORY,"="},{CMD_DISPLAY_SKILLS,"m"},{CMD_PRIMARY_ATTACK,"p"},{CMD_DISPLAY_MUTATIONS,"A"},{CMD_REMOVE_ARMOUR,"T"},{CMD_EVOKE,"V"},{CMD_READ,"r"},{CMD_REMOVE_JEWELLERY,"R"},{CMD_QUAFF,"q"},{CMD_MEMORISE_SPELL,"M"},{CMD_DROP,"d"}};
string command_to_string(command_type c){return keys.at(c);}string untag_tiles_console(string s){return s;}
string replace_all(string s,const string&a,const string&b){size_t p=0;while((p=s.find(a,p))!=string::npos){s.replace(p,a.size(),b);p+=b.size();}return s;}
ZhArg zh_item_base_arg(const string&k,const item_def&){return zh_glossary_name(k,"item.base","javelin");}
ZhArg zh_item_arg(const string&k,const item_def&i,int){return {k,ZhArgType::Name,i.name(DESC_YOUR),i.name_supported?"已审校名称":i.name(DESC_YOUR),i.name_supported};}
'''
base+=block((SRC/'zh-display-name.cc').read_text(),'std::string item_classifier(')+'\n'
base+=block((SRC/'macro.cc').read_text(),'void insert_commands(').replace('bool formatted)','bool formatted = true)')+'\n'
base+=block((SRC/'skills.cc').read_text(),'static const char *skill_titles')+';\n'
base+=block((SRC/'skills.cc').read_text(),'const char *skill_name(')+'\n'
reference=reference.replace('_hints_target_mode','_reference_target').replace('_hints_abilities','_reference_abilities').replace('_hints_throw_stuff','_reference_throw').replace('hints_describe_item','reference_item')
base+=reference+'\n'
start=source.index('static ZhArg _item_hint_key(');end=source.index('// num_old_talents',start)
base+=source[start:end]+'\n'+block(source,'string hints_describe_item(')+'\n'
# Compile the real potion/scroll rarity bindings: a previous Name/Text mismatch
# crashed actual detail scenes even though catalog self-validation passed.
rarity_source=(SRC/'describe.cc').read_text()
rarity_calls=re.findall(r'description << zh_message\("item\.consumable\.rarity", \{.*?\}\)\.display\(\);',rarity_source,re.S)
assert len(rarity_calls)==2
base+='\nvoid check_rarity_bindings(){\n'
base+='string rarity="common",article="a",localized_rarity=zh_lookup_exact(rarity),localized_article=zh_lookup_exact(article);\n'
for statement in rarity_calls:
 base+='{ostringstream description; '+statement+' assert(!description.str().empty());}\n'
base+='}\n'
base+=r'''
string normalized(string s){s=replace_all(s," forthis "," for this ");return replace_all(s," forthese "," for these ");}
int checks=0;
void check(item_def item){
 fill(begin(Hints.hints_events),end(Hints.hints_events),true);
 string expected=normalized(reference_item(item));vector<bool> events(begin(Hints.hints_events),end(Hints.hints_events));
 fill(begin(Hints.hints_events),end(Hints.hints_events),true);
 string canonical;{ZhTranslationPause english;canonical=hints_describe_item(item);}
 if(canonical!=expected){cerr<<"Canonical mismatch type "<<item.base_type<<" sub "<<item.sub_type<<"\nOLD "<<expected<<"\nNEW "<<canonical<<"\n";abort();}
 assert(vector<bool>(begin(Hints.hints_events),end(Hints.hints_events))==events);
 const string chinese=hints_describe_item(item);{ZhLegacyPause raw;assert(chinese==hints_describe_item(item));}
 assert(chinese.empty() || (chinese.find("<cyan>")==0 && chinese.substr(chinese.size()-7)=="</cyan>"));
 ++checks;
}
int main(){setenv("DCSS_LANG","zh",1);setenv("DCSS_ZH_FORBID_LEGACY","1",1);
 {item_def name;name.base_type=OBJ_MISSILES;
 const char* classifiers[]={"枚","支","块","块","张","枚"};
 for(int subtype=MI_DART;subtype<=MI_BOOMERANG;++subtype){name.sub_type=subtype;assert(item_classifier(name)==classifiers[subtype]);}
 name.sub_type=999;assert(item_classifier(name).empty());name.base_type=OBJ_STAVES;assert(item_classifier(name)=="根");}
 check_rarity_bindings();
 for(int type=OBJ_WEAPONS;type<=OBJ_OTHER;++type){
  for(int variant=0;variant<16;++variant){
   item_def i;i.base_type=type;i.equipped=variant&1;i.art=variant&2;i.resistance=variant&4;i.ability=variant&8;
   check(i);i.identified=false;i.cosmetic=1;check(i);
  }
 }
 item_def weapon;weapon.ranged=true;weapon.equipped=true;check(weapon);
 weapon.equipped=false;you.skills[SK_LONG_BLADES]=10;check(weapon);you.skills[SK_UNARMED_COMBAT]=15;check(weapon);
 item_def missile;missile.base_type=OBJ_MISSILES;
 for(int quantity:{1,2,99})for(char slot:{'d','\0'}){missile.quantity=quantity;missile.slot=slot;check(missile);}
 missile.throwable=false;check(missile);
 item_def armour;armour.base_type=OBJ_ARMOUR;you.horns=2;armour.helmet=true;check(armour);you.horns=0;armour.helmet=false;armour.sub_type=ARM_BARDING;check(armour);
 armour.sub_type=0;Hints.hints_type=HINT_MAGIC_CHAR;armour.body=true;armour.light=false;check(armour);armour.body=false;armour.shield=true;check(armour);
 Hints.hints_type=HINT_RANGER_CHAR;armour.offhand=true;check(armour);
 item_def jewellery;jewellery.base_type=OBJ_JEWELLERY;jewellery.resistance=true;jewellery.sub_type=NUM_RINGS;check(jewellery);
 item_def book;book.base_type=OBJ_BOOKS;book.sub_type=BOOK_MANUAL;check(book);
 item_def staff;staff.base_type=OBJ_STAVES;you.trog=true;check(staff);
 item_def other;other.base_type=OBJ_OTHER;assert(_item_hint_abilities(other).supported);
 item_def wand;wand.base_type=OBJ_WANDS;tiles.fullscreen=true;check(wand);
 // Remapping is a structural input, including escaped '<' and percent keys.
 keys[CMD_FIRE]="<";keys[CMD_WIELD_WEAPON]="?";keys[CMD_WEAPON_SWAP]="=";keys[CMD_ADJUST_INVENTORY]="@";check(weapon);missile.throwable=true;check(missile);
 assert(_item_hint_target().canonical.find("<w><<f</w>")!=string::npos);
 assert(_item_hint_target(true).canonical.find("<w>zap</w>")!=string::npos);
 missile.name_supported=false;
 auto nested=_item_hint_throw(missile); // Independent nested semantic names.
 auto unknown=zh_item_arg("item_name",missile,DESC_YOUR);
 auto message=zh_message("item.hints.missile.throwable",{unknown,_item_hint_key("fire_key",CMD_FIRE),nested});
 assert(message.localized==message.canonical);
 cout<<"PASS: "<<checks<<" actual item-hint branch/state combinations, canonical reference, event side effects and remapped keys\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 cpp=Path(tmp)/'hints.cc';cpp.write_text(base)
 visited=set()
 for mode,flags in [('console',[]),('tiles',['-DUSE_TILE','-DUSE_TILE_LOCAL','-DUNIX']),('web',['-DUSE_TILE','-DUSE_TILE_WEB'])]:
  exe=Path(tmp)/mode
  subprocess.run(['c++','-std=c++11','-DZH_STANDALONE',*flags,'-I',str(SRC),str(cpp),str(SRC/'zh-message.cc'),str(SRC/'zh-localization.cc'),'-o',str(exe)],check=True)
  trace=Path(tmp)/(mode+'.tsv')
  subprocess.run([str(exe)],check=True,env={**os.environ,'DCSS_ZH_ID_TRACE':str(trace)})
  visited.update(line.split('\t')[0] for line in trace.read_text().splitlines())
 expected={m['id'] for m in json.loads((ROOT/'localization/migration/luna-item-hints-messages.json').read_text())['messages']}
 assert expected<=visited, ('Unreached reviewed hint branches',sorted(expected-visited))
 print('PASS: all',len(expected),'reviewed hint IDs reached through production branches across console/local/web modes')
