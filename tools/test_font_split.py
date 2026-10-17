#!/usr/bin/env python3
"""Compile the real FT split routine with deterministic glyph metrics.
The styled-string seam rejects legacy string appends; wrapping must preserve
UTF-8 bytes and use raw punctuation when clipping.
"""
import subprocess,tempfile
from pathlib import Path
def block(s,needle):
 pos=s.index(needle);start=s.rfind('\n',0,pos)+1;begin=s.index('{',pos);depth=0
 for end in range(begin,len(s)):
  if s[end]=='{':depth+=1
  if s[end]=='}':
   depth-=1
   if not depth:return s[start:end+1]
 raise AssertionError(needle)
from compile_message_ids import SRC
source=block((SRC/'fontwrapper-ft.cc').read_text(),'formatted_string FTFontWrapper::split(')
code=r'''
#include <algorithm>
#include <cassert>
#include <climits>
#include <cstring>
#include <iostream>
#include <string>
using namespace std;
struct Density{int logical_to_device(int x){return x;}}display_density;
struct formatted_string{
 string s; formatted_string(){} explicit formatted_string(string t):s(t){}
 string tostring()const{return s;}
 formatted_string substr_bytes(int p,int n)const{return formatted_string(s.substr(p,n));}
 formatted_string chop_bytes(int n)const{return substr_bytes(0,n);}
 formatted_string& operator+=(const formatted_string&o){s+=o.s;return *this;}
 formatted_string& operator+=(const string&){assert(false && "legacy append");return *this;}
 char& operator[](size_t p){return s[p];}
 static formatted_string parse_string_raw(string s){return formatted_string(s);}
};
int glyph_bytes(const char*p){unsigned char c=*p;return c<128?1:c<224?2:c<240?3:4;}
char*prev_glyph(char*p,char*first){if(p==first)return nullptr;--p;while(p>first && (static_cast<unsigned char>(*p)&192)==128)--p;return p;}
int _find_newline(const char*p){const char*n=strchr(p,'\n');return n?n-p:INT_MAX;}
struct FTFontWrapper{
 int char_height(bool){return 1;}
 int find_index_before_width(char*p,unsigned width){unsigned used=0;int pos=0;while(p[pos] && p[pos]!='\n'){int n=glyph_bytes(p+pos);unsigned w=n==1?1:2;if(used+w>width)return pos;used+=w;pos+=n;}return INT_MAX;}
 formatted_string split(const formatted_string&,unsigned,unsigned);
};
'''+source+r'''
int main(){FTFontWrapper font;
 for(const string text:{"连续中文没有空格但必须完整换行且不得缺字","中文与LongEnglishWordWithoutSpaces混排","第一行\n第二行仍然很长需要换行"}){
  auto wrapped=font.split(formatted_string(text),8,100).tostring();
  string original=text;original.erase(remove(original.begin(),original.end(),'\n'),original.end());
  string plain=wrapped;plain.erase(remove(plain.begin(),plain.end(),'\n'),plain.end());assert(original==plain);
  int width=0;for(size_t p=0;p<wrapped.size();){if(wrapped[p]=='\n'){assert(width<=8);width=0;++p;}else{int n=glyph_bytes(wrapped.data()+p);width+=n==1?1:2;p+=n;}}assert(width<=8);
 }
 auto clipped=font.split(formatted_string("连续中文超过高度限制"),8,1).tostring();assert(clipped.substr(clipped.size()-2)=="..");
 assert(font.split(formatted_string("text"),8,0).tostring().empty());
 cout<<"PASS: actual FT wrapping preserves unspaced UTF-8 and clips with raw ellipsis\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'split.cc';p.write_text(code);exe=Path(tmp)/'split'
 subprocess.run(['c++','-std=c++17',str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
