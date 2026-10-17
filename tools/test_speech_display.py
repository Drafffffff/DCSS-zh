#!/usr/bin/env python3
"""Actual old/new monster speech consumers, including visibility and channels."""
import json,subprocess,tempfile
from pathlib import Path
from compile_message_ids import SRC
from test_speech_protocol import block
ROOT=Path(__file__).resolve().parents[1]

def main():
 old='bool mons_speaks_msg('+json.loads((ROOT/'tools/fixtures/monster-speech-display-english.json').read_text())['function']
 source=(SRC/'mon-speak.cc').read_text()
 code=r'''
#include "zh-speech.h"
#include <string>
#include <vector>
#include <map>
#include <cassert>
#include <cstdarg>
#include <iostream>
using namespace std;
using msg_channel_type=int;
enum {MSGCH_TALK,MSGCH_TALK_VISUAL,MSGCH_MONSTER_SPELL,MSGCH_MONSTER_ENCHANT,MSGCH_FRIEND_SPELL,MSGCH_FRIEND_ENCHANT,MSGCH_SOUND,MSGCH_WARN,ENCH_MUTE};
struct monster {bool visible=true,muted=false,ally=false;int pos()const{return 1;}bool has_ench(int)const{return muted;}bool friendly()const{return ally;}};
struct {bool cell=true;bool see_cell(int)const{return cell;}bool can_see(const monster&m)const{return m.visible;}}you;
int acts=0,replacements=0;
struct mon_acting {mon_acting(monster*){++acts;}};
string do_mon_str_replacements(const string&s,const monster&){++replacements;return s;}
string replace_all(string s,const string&a,const string&b){size_t p=0;while((p=s.find(a,p))!=string::npos){s.replace(p,a.size(),b);p+=b.size();}return s;}
void lowercase(string&s){for(char&c:s)c=tolower(c);}
vector<string> split_string(const string&sep,const string&s){vector<string>r;size_t p=0;for(;;){auto e=s.find(sep,p);auto v=s.substr(p,e==string::npos?e:e-p);if(!v.empty())r.push_back(v);if(e==string::npos)break;p=e+sep.size();}return r;}
int str_to_channel(const string&s){static map<string,int>m={{"talk",MSGCH_TALK},{"visual",MSGCH_TALK_VISUAL},{"spell",MSGCH_MONSTER_SPELL},{"enchant",MSGCH_MONSTER_ENCHANT},{"sound",MSGCH_SOUND},{"plain",MSGCH_TALK}};return m.count(s)?m[s]:-1;}
vector<pair<int,string>>lines;vector<string>localized;
void mprf(int channel,const char*,const char*s){lines.emplace_back(channel,s);}
void mpr(const ZhMessage&m,int channel){lines.emplace_back(channel,m.canonical);localized.push_back(m.localized);}
ZhMessage zh_mon_speech_message(const ZhSpeech&s,const monster&mon,int){return {"test",do_mon_str_replacements(s.canonical,mon),s.source};}
'''
 code+=block((SRC/'message.cc').read_text(),'bool strip_channel_prefix(')+'\n'
 code+=old.replace('bool mons_speaks_msg(','bool frozen_mons_speaks_msg(',1)+'\n'
 code+=block(source,'static bool _mons_speaks_message(')+'\n'
 # Two overloads are extracted as distinct source functions.
 code+=block(source,'bool mons_speaks_msg(monster *mon, const ZhSpeech &speech,')+'\n'
 code+=block(source,'bool mons_speaks_msg(monster *mon, const string &source,')+'\n'
 code+=r'''
int main(){int cases=0;monster m;
for(int mask=0;mask<32;++mask)for(const string&a:{string(""),string("hello"),string("VISUAL:seen"),string("TALK:said"),string("SPELL:cast"),string("ENCHANT:enchanted"),string("SOUND:noise"),string("PLAIN:plain"),string("TALK:")})for(const string&b:{string(""),string("\nVISUAL:next"),string("\nTALK:after"),string("\n\nPLAIN:end")}){
 you.cell=mask&1;m.visible=mask&2;m.muted=mask&4;m.ally=mask&8;const bool silence=mask&16;const string text=a+b;
 lines.clear();acts=replacements=0;const bool old=frozen_mons_speaks_msg(&m,text,MSGCH_TALK,silence);const auto expected=lines;const int expected_acts=acts,expected_replacements=replacements;
 lines.clear();acts=replacements=0;const bool legacy=mons_speaks_msg(&m,text,MSGCH_TALK,silence);assert(legacy==old&&lines==expected&&acts==expected_acts&&replacements==expected_replacements);
 lines.clear();localized.clear();acts=replacements=0;ZhSpeech s;s.source=s.canonical=text;const bool typed=mons_speaks_msg(&m,s,MSGCH_TALK,silence);assert(typed==old&&lines==expected&&acts==expected_acts&&replacements==expected_replacements);++cases;
}
cout<<"PASS: "<<cases<<" actual canonical/typed consumer cases, multiline/channel/friendly/mute/visibility/side-effect parity\n";}
'''
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'test.cc').write_text(code)
  subprocess.run(['c++','-std=c++14','-I'+str(SRC),str(p/'test.cc'),'-o',str(p/'test')],check=True)
  subprocess.run([str(p/'test')],check=True)
if __name__=='__main__':main()
