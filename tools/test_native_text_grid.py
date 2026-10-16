#!/usr/bin/env python3
"""Check the actual TextRegion write routine against wide-cell cursor regressions."""
from pathlib import Path
import subprocess,tempfile
source=Path(__file__).resolve().parents[1]/'native/crawl-ref/source/tilereg-text.cc'
s=source.read_text(); start=s.index('void TextRegion::addstr_aux('); end=s.index('\nvoid TextRegion::clear_to_end_of_line',start)
pad=(source.parent/'stringutil.cc').read_text(); pstart=pad.index('string padded_str('); pend=pad.index('\nint ends_with(',pstart)
code=r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
using std::max;
using std::string;
int strwidth(const string &s) { int width=0; for (unsigned char c : s) if ((c&0xc0)!=0x80) width += c>=0xe0 ? 2 : 1; return width; }
#define ASSERT assert
int wcwidth(char32_t c) { return c >= 0x3000 ? 2 : c ? 1 : 0; }
struct TextRegion {
 int print_x=0, print_y=0, cx_ofs=0, cy_ofs=0, mx=40,my=1,text_col=7;
 char32_t cbuf[40]; uint8_t abuf[40];
 TextRegion() { std::fill(cbuf,cbuf+40,U' '); }
 void addstr_aux(const char32_t*,int);
 void write(int x, const std::u32string &s) { print_x=x;addstr_aux(s.data(),s.size()); }
};
'''+s[start:end]+pad[pstart:pend]+r'''
int main() {
 assert(strwidth(padded_str("生命上限",16,false))==16);
 assert(strwidth(padded_str("护甲",8,true))==8);
 assert(padded_str("ASCII",8,false)=="ASCII   ");
 TextRegion t;
 t.write(0,U"生命： "); assert(t.print_x==7);
 t.write(7,U"20/20"); assert(t.cbuf[7]==U'2');
 t.write(18,U"########"); assert(t.cbuf[18]==U'#');
 assert(t.cbuf[0]==U'生' && t.cbuf[1]==0 && t.cbuf[2]==U'命');
 t.write(1,U"X"); assert(t.cbuf[0]==U' ' && t.cbuf[1]==U'X');
 t.write(2,U"Z"); assert(t.cbuf[2]==U'Z' && t.cbuf[3]==U' ');
 t.write(39,U"界"); assert(t.cbuf[39]==U' ' && t.print_x==41);
 t.write(38,U"界"); assert(t.cbuf[38]==U'界' && t.cbuf[39]==0);
 std::cout << "PASS: CJK terminal cells, HUD value/bar columns, partial overwrite, right-edge clipping\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11',str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
