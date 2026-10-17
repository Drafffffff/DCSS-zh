#!/usr/bin/env python3
"""Compile real doll editor + skill help against baseline English and UI seams.
Private temporary catalog only; no full game build or shared catalog writes.
"""
import json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'native/crawl-ref/source'
refs=json.loads((ROOT/'tools/fixtures/sol61-ui-help-english.json').read_text())
assert refs['baseline']=='cc710081cd3f163eabf78c65b9144e040ef30aa8'
def block(s,needle):
    start=s.index(needle);brace=s.index('{',start);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[start:end+1]
    raise AssertionError(needle)
def doll_source(s):
    s=re.sub(r'#include[^\n]*\n','',s)
    s=re.sub(r'#ifdef DEBUG_TILES_REDRAW.*?#endif','',s,flags=re.S)
    return s.replace('#ifdef USE_TILE_LOCAL','').replace('#endif','')
doll=(SRC/'tilereg-doll.cc').read_text();skill=(SRC/'skill-menu.cc').read_text()
assert 'zh_translate' not in doll
assert 'formatted_string::parse_string_raw(' in doll
assert 'doll_part_message(m_cat_idx, m_part_idx).display()' in doll
assert 'doll_command_text(row, col)' in doll
assert 'm_help->set_text_pretranslated(msg)' in skill
assert 'zh_word_arg("cause"' not in skill
header=block((SRC/'tilereg-doll.h').read_text(),'class DollEditRegion')+';'
header=header.replace('protected:','public:')
code=r'''
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <functional>
#include <iostream>
#include <memory>
#include <string>
#include <vector>
using namespace std;
#define ASSERT(x) assert(x)
string make_stringf(const char*f,...){char b[8192];va_list a;va_start(a,f);vsnprintf(b,sizeof b,f,a);va_end(a);return b;}
int utf8towc(char32_t*out,const char*s){unsigned char c=*s;if(c<128){*out=c;return 1;}int n=c<224?2:c<240?3:4;char32_t v=c&(n==2?31:n==3?15:7);for(int i=1;i<n;++i)v=(v<<6)|(s[i]&63);*out=v;return n;}
int cells(string s){int n=0;for(size_t i=0;i<s.size();){char32_t c;int b=utf8towc(&c,s.c_str()+i);i+=b;n+=(c>=0x2e80?2:1);}return n;}
int strwidth(const string&s){return cells(s);}
string chop_string(const string&s,int limit){int n=0;size_t i=0;while(i<s.size()){char32_t c;int b=utf8towc(&c,s.c_str()+i);int w=c>=0x2e80?2:1;if(n+w>limit)break;n+=w;i+=b;}return s.substr(0,i);}
const int NUM_MAX_DOLLS=10,TILEP_PART_MAX=16,TILEP_PART_BASE=0,TILEP_PART_SHADOW=1,TILEP_PART_HALO=2,TILEP_PART_ENCH=3,TILEP_PART_DRCWING=15,TILEP_SHOW_EQUIP=999999,TILEP_CURSOR=1,TEX_PLAYER=0,YELLOW=14;
using tileidx_t=int;
enum tile_doll_mode{TILEP_MODE_EQUIP,TILEP_MODE_LOADING,TILEP_MODE_DEFAULT,TILEP_MODE_MAX};
int tile_player_part_start[16],tile_player_part_count[16];
struct dolls_data{int parts[16]={};};dolls_data player_doll;
struct VColour{VColour(int,int,int,int){} VColour(int=0){}static VColour white;};VColour VColour::white;
struct TextDraw{string text;float x,y;};vector<TextDraw>drawn;vector<string>trace;string popup_title;
struct FontWrapper{int cw=8,ch=16;int char_width(){return cw;}int char_height(){return ch;}int string_width(const char*s){return cells(s)*cw;}};
struct FontBuffer{FontBuffer(FontWrapper*){}void clear(){drawn.clear();}void add(string s,VColour,float x,float y){drawn.push_back({s,x,y});}void draw(){}};
struct ShapeBuffer{void clear(){}void add(int,int,int,int,VColour){}void draw(){}};
struct SubmergedTileBuffer{SubmergedTileBuffer(int*,int){}void clear(){}void add(int,int,int){}void draw(){}};
struct ImageManager{int texture=0;int&get_texture(int){return texture;}};
struct GLW_3VF{GLW_3VF(float,float,float=0){}};
struct GLManager{void set_transform(GLW_3VF,GLW_3VF){}void reset_transform(){}}manager;GLManager*glmanager=&manager;
struct wm_mouse_event{};
struct ControlRegion{int sx=0,sy=0,dx=0,dy=0,mx=0,my=0;virtual void render(){}virtual void clear(){}virtual void run(){}virtual int handle_mouse(wm_mouse_event&){return 0;}virtual void on_resize(){}void set_transform(){}};
const int GOD_ASHENZARI=1,GOD_OTHER=2,DUR_HEROISM=0,BANE_DILETTANTE=0;
enum class transformation{none,walking_scroll};enum class passive_t{bondage_skill_boost};
struct Player{int species=0,experience_level=1,char_class=0,religion=GOD_ASHENZARI;int duration[1]={};vector<int>skill_boost;transformation form=transformation::none;bool bane=false;bool has_bane(int){return bane;}}you;
struct{bool seen_hups=false;}crawl_state;
int tilep_species_to_base_tile(int,int){return tile_player_part_start[0];}int tile_player_count(int){return tile_player_part_count[0]+1;}
void fill_doll_equipment(dolls_data&){}void pack_doll_buf(SubmergedTileBuffer&,dolls_data,int,int,bool,bool){}
void tilep_race_default(int,int,dolls_data*){trace.push_back("race");}void tilep_job_default(int,dolls_data*){trace.push_back("job");}
void create_random_doll(dolls_data&d){trace.push_back("random");d.parts[0]=tile_player_part_start[0]+1;}
int loadpreset=-1;bool load_doll_data(const char*s,dolls_data*d,int n,tile_doll_mode*m,int*i){trace.push_back(s);if(loadpreset<0)return false;*m=tile_doll_mode(loadpreset);*i=8;for(int j=0;j<n;++j)for(int c=0;c<16;++c)d[j].parts[c]=tile_player_part_start[c];return true;}
void save_doll_data(tile_doll_mode m,int i,dolls_data*d){trace.push_back("save:"+to_string(m)+":"+to_string(i));for(int j=0;j<16;++j)trace.push_back(to_string(d->parts[j]));}
struct formatted_string{string text;formatted_string(string s,int=0):text(s){}static formatted_string parse_string_raw(string s,int=0){return {s};}};
enum command_type{CMD_DOLL_QUIT,CMD_DOLL_RANDOMIZE,CMD_DOLL_SELECT_NEXT_DOLL,CMD_DOLL_SELECT_PREV_DOLL,CMD_DOLL_SELECT_NEXT_PART,CMD_DOLL_SELECT_PREV_PART,CMD_DOLL_CHANGE_PART_NEXT,CMD_DOLL_CHANGE_PART_PREV,CMD_DOLL_TOGGLE_EQUIP,CMD_DOLL_CONFIRM_CHOICE,CMD_DOLL_COPY,CMD_DOLL_PASTE,CMD_DOLL_TAKE_OFF,CMD_DOLL_TAKE_OFF_ALL,CMD_DOLL_TOGGLE_EQUIP_ALL,CMD_DOLL_JOB_DEFAULT,CMD_DOLL_CHANGE_MODE,CMD_DOLL_SAVE,CMD_NONE};
const int KMC_DOLL=0;command_type key_to_command(int k,int){return k>=1000?command_type(k-1000):CMD_NONE;}
namespace ui{
using Direction=int;struct SizeReq{int a,b;};struct KeyEvent{int k;int key()const{return k;}};
struct Widget{enum{VERT,CENTER};struct{int x=0,y=0;}m_region;virtual void _render(){}virtual SizeReq _get_preferred_size(Direction,int){return {0,0};}virtual void _allocate_region(){}void _expose(){}};
struct Text:Widget{Text(formatted_string f){popup_title=f.text;}void set_margin_for_sdl(int,int,int,int){}};
struct Box:Widget{Box(int){}void set_cross_alignment(int){}template<class T>void add_child(T){}};
function<bool(const KeyEvent&)>onkey;vector<int>keys;size_t keypos=0;
struct Popup:Widget{template<class T>Popup(T){}template<class F>void on_keydown_event(F f){onkey=f;}};
void push_layout(shared_ptr<Popup>,int){trace.push_back("push");}void pop_layout(){trace.push_back("pop");onkey=nullptr;}
void pump_events(){assert(keypos<keys.size());onkey(KeyEvent{keys[keypos++]});}
}
string apostrophise(string s){return s+"'s";}string god_name(int g){return g==GOD_ASHENZARI?"Ashenzari":"Future God";}
template<class I>string comma_separated_line(I a,I b){string s;size_t n=distance(a,b),i=0;for(;a!=b;++a,++i){if(i)s+=(i+1==n?" and ":", ");s+=*a;}return s;}
bool cross=false,hermit=false,wild=false,charlatan=false,penalty=false,passive=false,penance=false;
bool _any_crosstrained(){return cross;}bool _hermit_bonus(){return hermit;}bool _wildshape_bonus(){return wild;}bool _charlatan_bonus(){return charlatan;}bool _hermit_penalty(){return penalty;}bool have_passive(passive_t){return passive;}bool player_under_penance(int){return penance;}
enum{SKM_MODE_AUTO,SKM_MODE_MANUAL,SKM_DO_PRACTISE,SKM_DO_FOCUS,SKM_LEVEL_ENHANCED,SKM_VIEW_TRAINING,SKM_VIEW_TARGETS,SKM_VIEW_PROGRESS,SKM_VIEW_COST};
enum{SKMF_SIMPLE=1,SKMF_ENHANCED=2,SKMF_REDUCED=4,SKMF_MANUAL=8};
struct{int flags=0;bool is_set(int f){return flags&f;}}skm;
struct SkillMenuSwitch{int m_state=0;string get_help();};
'''
code+='\nnamespace oracle {\n'+header+'\n'+doll_source(refs['sources']['tilereg-doll.cc'])+'\n'+block(refs['sources']['skill-menu.cc'],'static ZhArg _skill_cause_arg(')+'\nstruct SkillMenuSwitch: ::SkillMenuSwitch {string get_help();};\n'+block(refs['sources']['skill-menu.cc'],'string SkillMenuSwitch::get_help(')+'\n'
for name in ['_hud_place_line','_hud_experience_line']:
    code+=block(refs['sources']['output.cc'],'static string '+name+'(')+'\n'
code+='}\n'
code+='\nnamespace actual {\n'+header+'\n'+doll_source(doll)+'\n'+block(skill,'static ZhArg _skill_cause_arg(')+'\n'+block(skill,'static ZhArg _skill_power_cause_arg(')+'\nstruct SkillMenuSwitch: ::SkillMenuSwitch {string get_help();};\n'+block(skill,'string SkillMenuSwitch::get_help(')+'\n'
for name in ['_skill_cells','_skill_wrap','_skill_line_count','_skill_help_rows','_skill_help_columns','_skill_help_rows_available','_skill_text_width']:
    code+=block(skill,('static string ' if name=='_skill_wrap' else 'static int ')+name+'(')+'\n'
for name in ['_hud_place_line','_hud_experience_line']:
    code+=block((SRC/'output.cc').read_text(),'static string '+name+'(')+'\n'
code+='}\n'

code+=r'''
vector<string>texts(){vector<string>s;for(auto&t:drawn)s.push_back(t.text);return s;}
void setlang(bool zh){setenv("DCSS_LANG",zh?"zh":"en",1);}
template<class T>void init(T&r,int mode,int category,int variant){r.m_doll_idx=9;r.m_mode=tile_doll_mode(mode);r.m_cat_idx=category;for(auto&d:r.m_dolls)for(int c=0;c<16;++c)d.parts[c]=variant==0?0:variant==1?TILEP_SHOW_EQUIP:tile_player_part_start[c]+tile_player_part_count[c]-1;r.m_part_idx=variant==1?0:r.m_dolls[9].parts[category];}
int main(int argc,char**argv){
 assert(argc==2);setenv("DCSS_ZH_ID_MISSING",argv[1],1);
 for(int c=0;c<16;++c){tile_player_part_start[c]=100+c*200;tile_player_part_count[c]=c==0?28:3+c*17;}
 ImageManager im;FontWrapper f;int rendercases=0;
 for(auto metric:vector<pair<int,int>>{{8,16},{12,24},{24,40},{32,56}}){f.cw=metric.first;f.ch=metric.second;
 for(int mode=0;mode<3;++mode)for(int cat=0;cat<16;++cat)for(int variant=0;variant<3;++variant){
 oracle::DollEditRegion old(&im,&f);actual::DollEditRegion now(&im,&f);init(old,mode,cat,variant);init(now,mode,cat,variant);
 setlang(false);old.render();auto expected=texts();now.render();if(expected!=texts()){auto got=texts();for(size_t z=0;z<expected.size();++z)if(expected[z]!=got[z])cerr<<"DIFF "<<z<<":"<<expected[z]<<" / "<<got[z]<<"\n";assert(false);}
 assert(now.dx==now.dy&&now.dx%32==0);const auto layout=actual::doll_layout(&f);
 for(auto&t:drawn){assert(t.x>=0&&t.y>=0);assert(t.x+f.string_width(t.text.c_str())<=layout.width);assert(t.y+f.char_height()<=layout.height);}
 setlang(true);now.render();assert(now.dx==now.dy&&now.dx%32==0);auto localized=texts();assert(localized!=expected);
 const auto zh_layout=actual::doll_layout(&f);
 for(auto&t:drawn){assert(t.x>=0&&t.y>=0);assert(t.x+f.string_width(t.text.c_str())<=zh_layout.width);assert(t.y+f.char_height()<=zh_layout.height);}
 // Command columns occupy disjoint intervals with the same producer/metric.
 for(int row=0;row<6;++row)for(int col=0;col<3;++col)assert(zh_layout.command_x[col]+f.string_width(actual::doll_command_text(row,col).c_str())<zh_layout.command_x[col+1]);
 setlang(false);now.render();assert(texts()==expected);++rendercases;
 }}
 // The production keyboard/save loop runs unchanged in both namespaces.
 for(loadpreset=-1;loadpreset<3;++loadpreset)for(auto script:vector<vector<int>>{
 {1000+CMD_DOLL_SAVE},{1000+CMD_DOLL_RANDOMIZE,1000+CMD_DOLL_COPY,1000+CMD_DOLL_SELECT_NEXT_DOLL,1000+CMD_DOLL_PASTE,1000+CMD_DOLL_SAVE},
 {1000+CMD_DOLL_TOGGLE_EQUIP,1000+CMD_DOLL_CHANGE_PART_NEXT,1000+CMD_DOLL_SELECT_NEXT_PART,1000+CMD_DOLL_CHANGE_PART_PREV,1000+CMD_DOLL_CHANGE_MODE,1000+CMD_DOLL_CONFIRM_CHOICE,'5',1000+CMD_DOLL_SAVE},
 {1000+CMD_DOLL_TAKE_OFF,1000+CMD_DOLL_TAKE_OFF_ALL,1000+CMD_DOLL_TOGGLE_EQUIP_ALL,1000+CMD_DOLL_JOB_DEFAULT,1000+CMD_DOLL_QUIT}}){
  oracle::DollEditRegion old(&im,&f);actual::DollEditRegion now(&im,&f);
  setlang(false);trace.clear();ui::keys=script;ui::keypos=0;old.run();auto en_trace=trace;auto en_doll=player_doll;
  for(bool zh:{false,true}){actual::DollEditRegion now(&im,&f);trace.clear();ui::keys=script;ui::keypos=0;setlang(zh);now.run();assert(trace==en_trace);for(int c=0;c<16;++c)assert(player_doll.parts[c]==en_doll.parts[c]);assert(popup_title==(zh?"角色外观编辑器":"Doll Editor"));}
 }

 // Existing HUD typed fields use the real message renderer too. Their parent
 // consumers already bound these display strings before cprintf with a local
 // legacy pause; no global suppression is added by this work package.
 int hudcases=0;
 for(bool zh:{false,true}){setlang(zh);for(int level:{1,9,27,99})for(int progress:{0,9,99,100,999})for(bool maxlevel:{false,true})for(bool small:{false,true}){
   const string line=actual::_hud_experience_line(level,progress,maxlevel,small);assert(cells(line)==17);if(!zh)assert(line==oracle::_hud_experience_line(level,progress,maxlevel,small));assert(line.find(zh?"等级 ":"XL: ")==0);++hudcases;
 }
 assert(actual::_hud_place_line("Abyss","深渊",27,true)==(zh?"深渊：27":"Abyss:27"));
 assert(actual::_hud_place_line("Abyss","深渊",27,false)==(zh?"深渊":"Abyss"));
 assert(actual::_hud_place_line("Future Branch","Future Branch",27,true)=="Future Branch:27");
 }
 int skillcases=0;
 for(int mask=0;mask<1024;++mask){
  you.duration[0]=mask&1;you.skill_boost=mask&2?vector<int>{1}:vector<int>{};passive=true;you.religion=GOD_ASHENZARI;cross=mask&4;hermit=mask&8;wild=mask&16;charlatan=mask&32;you.form=mask&64?transformation::walking_scroll:transformation::none;penance=mask&128;penalty=mask&256;you.bane=mask&512;
  for(int flags=0;flags<16;++flags)for(int state=0;state<=SKM_VIEW_COST;++state){
   skm.flags=flags;oracle::SkillMenuSwitch old;actual::SkillMenuSwitch now;old.m_state=now.m_state=state;setlang(false);assert(old.get_help()==now.get_help());
   setlang(true);string help=now.get_help();
   for(int width:{20,78,100,158}){auto wrapped=actual::_skill_wrap(help,width);size_t a=0;while(a<=wrapped.size()){auto b=wrapped.find('\n',a);assert(actual::_skill_text_width(wrapped.substr(a,b==string::npos?b:b-a))<=width);if(b==string::npos)break;a=b+1;}}
   ++skillcases;
  }
 }
 // Unsupported future passive provider falls back as a complete parent sentence.
 skm.flags=SKMF_ENHANCED;you.duration[0]=0;you.skill_boost={1};passive=true;you.religion=GOD_OTHER;cross=hermit=wild=charlatan=false;you.form=transformation::none;
 actual::SkillMenuSwitch unknown;unknown.m_state=SKM_LEVEL_ENHANCED;setlang(true);
 assert(unknown.get_help()=="Skills enhanced by Future God's power are in <green>green</green>.");
 assert(actual::_skill_help_columns(48,1944,24)==78);assert(actual::_skill_help_rows_available(2160,3,420,40)==46);assert(actual::_skill_help_rows(3,100,46)==46);
 cout<<"PASS: "<<rendercases<<" production doll rendering scenarios; English oracle, all modes/categories/value kinds, 4 font scales, language switching, bounds and key columns; 16 production save scenarios; "<<skillcases<<" skill-help branches and 4K wrap checks; "<<hudcases<<" HUD field boundaries\n";
}
'''
# The private catalog contains the changed view and the existing reviewed skill
# templates it reuses. First-source wins, matching the source catalog workflow.
doc=json.loads((ROOT/'localization/migration/luna-sol61-ui-help-messages.json').read_text())
assert doc['model']==doc['reviewer_model']=='gpt-6.1-sol'
entries={e['id']:e for e in doc['messages']}
for path in sorted((ROOT/'localization/migration').glob('*.json')):
    data=json.loads(path.read_text())
    for e in data.get('messages',[]):
        if e['id'].startswith(('skill.menu.','skill.cause.','hud.')):entries.setdefault(e['id'],e)
q=lambda s:json.dumps(s,ensure_ascii=False).replace('?',r'\?')
catalog='static const ZhDefinition zh_definitions[] = {\n'
for e in entries.values():
    for lang in ('en','zh'):assert set(re.findall(r'\{(\w+)\}',e[lang]))==set(e['params'])
    catalog+=' {'+', '.join(q(s) for s in (e['id'],e['en'],e['zh'],';'.join(k+':'+v for k,v in e['params'].items())))+'},\n'
catalog+='};\nstruct ZhSourceDefinition { const char *context, *source, *id; };\nstatic const ZhSourceDefinition zh_source_definitions[] = {{nullptr,nullptr,nullptr}};\n'
with tempfile.TemporaryDirectory() as td:
    p=Path(td);(p/'test.cc').write_text(code)
    shutil.copyfile(SRC/'zh-message.cc',p/'zh-message.cc');(p/'zh-message-catalog.inc').write_text(catalog)
    subprocess.run(['c++','-std=c++11','-O0','-DZH_STANDALONE','-I'+str(SRC),str(SRC/'zh-localization.cc'),str(p/'zh-message.cc'),str(p/'test.cc'),'-o',str(p/'test')],check=True)
    env={k:v for k,v in os.environ.items() if not k.startswith('DCSS_ZH_')}
    subprocess.run([str(p/'test'),str(p/'missing.log')],check=True,timeout=60,env=env)
    assert (p/'missing.log').read_text()==('hud.place.depth\tunsupported parameter\n'*2+'skill.menu.enhanced\tunsupported parameter\n')
