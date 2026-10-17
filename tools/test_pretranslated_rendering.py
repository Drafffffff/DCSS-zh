#!/usr/bin/env python3
"""Exercise production raw parser dispatch and bounded precision-widget wrapping."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'native/crawl-ref/source'
fmt = (SRC / 'format.cc').read_text()
start = fmt.index('formatted_string formatted_string::parse_string(const string &s,')
end = fmt.index('// Parses a formatted string', start)
parser_start=fmt.index('void formatted_string::parse_string1(')
parser_end=fmt.index('/// Return a plaintext',parser_start)
precision = (SRC / 'precision-menu.cc').read_text()
start_wrap = precision.index('void TextItem::_wrap_text()')
end_wrap = precision.index('\n\nEditableTextItem::', start_wrap)
util = (SRC / 'stringutil.cc').read_text()
start_word = util.index('string wordwrap_line(')
end_word = util.index('\nstring strip_filename_unsafe_chars', start_word)
menu = (SRC / 'menu.cc').read_text()
start_break = menu.index('int linebreak_string(')
end_break = menu.index('\nstring get_linebreak_string', start_break)
code = r'''
#include <algorithm>
#include <cassert>
#include <iostream>
#include <regex>
#include <cstdarg>
#include <cstdio>
#include <string>
#include <vector>
using std::string; using std::vector;
#define ASSERT assert
#define ASSERTS 1
constexpr int LIGHTGREY=7, BLACK=0, LIGHTRED=12;
int translations=0,paused=0;
struct ZhLegacyPause {ZhLegacyPause(){++paused;}~ZhLegacyPause(){--paused;}};
string zh_translate(const string &s) {if(paused)return s; ++translations; return s + " LEGACY"; }
bool starts_with(const string &s,const string &prefix){return s.compare(0,prefix.size(),prefix)==0;}
struct formatted_string {
 string parsed;vector<int> colours,backgrounds;
 static formatted_string parse_string(const string &, int=LIGHTGREY);
 static formatted_string parse_string_raw(const string &, int=LIGHTGREY);
 static void parse_string1(const string &,formatted_string &,vector<int> &,vector<int> &);
 static int get_colour(string s){
  if(starts_with(s,"bg:"))s=s.substr(3);
  if(s=="red")return 4;if(s=="w"||s=="white")return 15;
  if(s=="lightmagenta")return 13;if(s=="green")return 2;
  return -1;
 }
 void textcolour(int c) {colours.push_back(c);} void textbackground(int c) {backgrounds.push_back(c);}
 void cprintf(const string &s){parsed+=zh_translate(s);}
 void cprintf(const char *format,...){char buf[2048];va_list args;va_start(args,format);vsnprintf(buf,sizeof buf,format,args);va_end(args);cprintf(string(buf));}
};
int utf8towc(char32_t *out,const char *s) {
 unsigned char c=*s; if(!c){*out=0;return 0;}
 int n=c<128?1:(c<224?2:(c<240?3:4)); *out=c&(n==1?127:(n==2?31:(n==3?15:7)));
 for(int i=1;i<n;i++) *out=(*out<<6)|(static_cast<unsigned char>(s[i])&63);
 return n;
}
int wcwidth(char32_t c) {return c>=0x3000?2:c?1:0;}
string _get_indent(const string &) {return "";}
string wordwrap_line(string &,int,bool,bool,int=-1);
int linebreak_string(string &,int,bool=false,int=-1);
struct Point {int x,y;};
struct TextItem {
 bool m_pretranslated=true;
 string m_text,m_render_text;
 Point m_min_coord{0,0},m_max_coord{20,1};
 void _wrap_text();
};
''' + fmt[start:end] + fmt[parser_start:parser_end] + util[start_word:end_word] + menu[start_break:end_break] + precision[start_wrap:end_wrap] + r'''
int main() {
 // An already selected template must remain byte-for-byte intact, including
 // complete English fallback, colour tags and shortcut characters.
 assert(formatted_string::parse_string_raw("Unknown name: <red>5</red> [m]").parsed=="Unknown name: 5 [m]");
 assert(formatted_string::parse_string_raw("<w>生命</w>：5 / 10").parsed=="生命：5 / 10");
 assert(formatted_string::parse_string_raw("A\nB").parsed=="A\nB");
 const auto coloured=formatted_string::parse_string_raw("<green>[m]</green><bg:red>5</bg:red>");
 assert(coloured.parsed=="[m]5");
 assert(coloured.colours.front()==2 && coloured.backgrounds.front()==4);
 assert(formatted_string::parse_string_raw("<<5").parsed=="<5");
 assert(translations==0);
 assert(formatted_string::parse_string("unmigrated").parsed=="unmigrated LEGACY");
 assert(translations==1);
 int checks=7;
 for(int cols : {8,20,40,80,120}) for(int rows : {1,2,3,5}) {
  TextItem item;item.m_max_coord={cols,rows};
  item.m_text="<lightmagenta>"+string(250,'A')+"天地天地天地天地天地天地天地天地天地天地</lightmagenta>";
  const int before=translations;item._wrap_text();assert(translations==before);
  int lines=1;for(char c:item.m_render_text)if(c=='\n')++lines;
  assert(lines<=rows);
  size_t at=0;
  while(at<item.m_render_text.size()) {
   const size_t end=item.m_render_text.find('\n',at);
   const string line=std::regex_replace(item.m_render_text.substr(at,end-at),std::regex("<[^>]+>"),"");
   int cells=0;char32_t cp;const char *cursor=line.c_str();
   while(int n=utf8towc(&cp,cursor)){cells+=wcwidth(cp);cursor+=n;}
   assert(cells<=cols);
   if(end==string::npos)break;
   at=end+1;
  }
  checks++;
 }
 TextItem exact;exact.m_max_coord={8,1};exact.m_text="12345678\nNEXT";exact._wrap_text();
 assert(exact.m_render_text=="12345678");++checks;
 TextItem empty;empty.m_max_coord={0,0};empty.m_text="text";empty._wrap_text();assert(empty.m_render_text.empty());++checks;
 TextItem legacy;legacy.m_pretranslated=false;legacy.m_text="text";legacy._wrap_text();assert(translations==2);++checks;
 std::cout<<"PASS: "<<checks<<" raw parser and bounded widget cases\n";
}
'''
with tempfile.TemporaryDirectory() as folder:
    p=Path(folder)
    (p/'test.cc').write_text(code)
    subprocess.run(['c++','-std=c++11',str(p/'test.cc'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
