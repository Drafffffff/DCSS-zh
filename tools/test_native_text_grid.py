#!/usr/bin/env python3
"""Exercise production text writes: wide cells, clipping, clearing and UTF-8 chunks."""
from pathlib import Path
import subprocess,tempfile,json,re
source=Path(__file__).resolve().parents[1]/'native/crawl-ref/source/tilereg-text.cc'
s=source.read_text(); start=s.index('void TextRegion::addstr('); end=s.index('\nvoid TextRegion::putwch',start)
table=(source.parent/'describe.cc').read_text(); tstart=table.index('struct TableCell'); tend=table.index('// Converts a numeric resistance',tstart)
pad=(source.parent/'stringutil.cc').read_text(); pstart=pad.index('string padded_str('); pend=pad.index('\nint ends_with(',pstart)
wstart=pad.index('string wordwrap_line('); wend=pad.index('\nstring strip_filename_unsafe_chars',wstart)
reviewed={m['en'] for file in (source.parents[3]/'localization/migration').glob('luna-*-messages.json')
          for m in json.loads(file.read_text())['messages'] if m['id'].startswith(('form.table.','monster.table.'))}
form_data=(source.parent/'form-data.h').read_text()
dice_labels=set(re.findall(r'(?:new dicedef_calculator<[^>]+>|nullptr),\s*"([^"]+)"',form_data))
form_impl=table[table.index('static string _describe_talisman_form_impl'):table.index('static string _describe_talisman_form(transformation')]
static_labels=set(re.findall(r',\s*"([^"]+)",\s*skill',form_impl))
static_labels.update(re.findall(r'pr.AddCell\("([^"]+)"',form_impl))
static_labels.update({'Skill','Min','Max','Cur','Body Armour AC','Airstrike Dmg','Str','Dex'})
assert dice_labels|static_labels <= reviewed, ('Unreviewed form labels', sorted((dice_labels|static_labels)-reviewed))
def helper(name):
    start=table.index('static ',table.index(name)-40)
    brace=table.index('{',table.index(name));depth=0
    for end in range(brace,len(table)):
        if table[end]=='{':depth+=1
        if table[end]=='}':
            depth-=1
            if not depth:return table[start:end+1]
    raise AssertionError(name)
code=r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>
#include <sstream>
#include <map>
#include <regex>
#include <utility>
using std::vector;
using std::map;
using std::pair;
using std::ostringstream;
using std::min;
using colour_t=int;
const int LIGHTGREY=7;
using std::max;
using std::string;
int strwidth(const string &s) { int width=0; for (unsigned char c : s) if ((c&0xc0)!=0x80) width += c>=0xe0 ? 2 : 1; return width; }
#define ASSERT assert
#define ASSERTS 1
string padded_str(const string&,int,bool=false);
#define ARRAYSZ(a) (sizeof(a)/sizeof((a)[0]))
int wcwidth(char32_t c) { return c >= 0x3000 ? 2 : c ? 1 : 0; }
int utf8towc(char32_t *out,const char *s) {
 unsigned char c=*s; if (!c) { *out=0;return 0; }
 int n=c<128?1:(c<224?2:(c<240?3:4)); *out=c & (n==1?127:(n==2?31:(n==3?15:7)));
 for(int i=1;i<n;i++) *out=(*out<<6)|(static_cast<unsigned char>(s[i])&63);
 return n;
}
struct TextRegion {
 int print_x=0, print_y=0, cx_ofs=0, cy_ofs=0, mx=40,my=3,text_col=7;
 bool cursor_flag=false;
 char32_t cbuf[4096*3]; uint8_t abuf[4096*3];
 TextRegion() { std::fill(cbuf,cbuf+4096*3,U' ');std::fill(abuf,abuf+4096*3,0); }
 void addstr(const char*);
 void addstr_aux(const char32_t*,int);
 void clear_to_end_of_line();
 void scroll() { std::copy(cbuf+mx,cbuf+mx*my,cbuf);std::fill(cbuf+mx*(my-1),cbuf+mx*my,U' ');print_y--; }
 void cgotoxy(int,int) {}
 void write(int x, const std::u32string &s) { print_x=x;addstr_aux(s.data(),s.size()); }
 void valid() { for(int y=0;y<my;y++) for(int x=0;x<mx;x++) {
  const auto c=cbuf[y*mx+x];
  if(c==0) assert(x>0 && wcwidth(cbuf[y*mx+x-1])==2);
  if(wcwidth(c)==2) assert(x+1<mx && cbuf[y*mx+x+1]==0);
 } }
};
'''+s[start:end]+pad[pstart:pend]+r'''
string zh_translate(const string &s) {return s;}
string zh_source(const char *,const char *s) {return s;}
string colourize_str(const string &s,colour_t) {return s;}
string _get_indent(const string&) {return "";}
string wordwrap_line(string&,int,bool,bool,int=0);
'''+pad[wstart:wend]+table[tstart:tend]+r'''
// Geometry seam; production raw parsing/colours have a separate test.
struct formatted_string {
 string text;
 int width()const{return strwidth(text);}
 string to_colour_string()const{return text;}
 static formatted_string parse_string_raw(const string&s){return {std::regex_replace(s,std::regex("</?[^>]+>"),"")};}
 static void parse_string_to_multiple_raw(const string&s,vector<formatted_string>&out,int width){
  string text=parse_string_raw(s).text;
  while(!text.empty())out.push_back({wordwrap_line(text,width,false,false)});
 }
};
'''+helper('_form_table_widths')+helper('_render_form_scaling_table')+r'''
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
 int cases=0;
 for(int width : {1,2,3,7,20,40,80,160}) for(int x=0;x<=width;x++) {
  TextRegion a;a.mx=width;
  for(int i=0;i+1<width;i+=2) a.write(i,U"界");
  a.write(x,U"地");a.valid();
  a.write(x,U"A");a.valid();
  a.write(x,U"天地A界");a.valid();
  a.print_x=x;a.clear_to_end_of_line();a.valid();cases++;
 }
 TextRegion cross;cross.write(0,U"天地");cross.write(1,U"界");cross.valid();
 assert(cross.cbuf[0]==U' ' && cross.cbuf[1]==U'界' && cross.cbuf[2]==0 && cross.cbuf[3]==U' ');
 for(int count : {0,1,1023,1024,1025,2048,3072}) {
  TextRegion longtext;longtext.mx=4096;
  longtext.addstr((string(count,'A')+"中B\r\n界C").c_str());
  assert(longtext.print_y==1 && longtext.print_x==3);
  for(int i=0;i<count;i++) assert(longtext.cbuf[i]==U'A');
  assert(longtext.cbuf[count]==U'中' && longtext.cbuf[count+1]==0 && longtext.cbuf[count+2]==U'B');
  assert(longtext.cbuf[4096]==U'界' && longtext.cbuf[4097]==0 && longtext.cbuf[4098]==U'C');
  longtext.valid();cases++;
 }
 // Actual detail-table printer: long CJK labels, mixed scripts, large values
 // and empty padding cells must preserve content inside each column.
 for(int columns : {2,3,4,5}) for(int total : {40,60,80,100}) {
  TablePrinter table(columns,total); table.AddRow();
  const string value="12345678901234567890";
  for(int i=0;i<columns-1;i++) table.AddCell("负能量抗性生命上限",value);
  table.AddCell(); std::ostringstream output;table.Print(output);
  string remaining=output.str();int lines=0;
  while(!remaining.empty()) {
   auto e=remaining.find('\n');assert(e!=string::npos);
   assert(strwidth(remaining.substr(0,e))==columns*(total/columns));
   remaining.erase(0,e+1);lines++;
  }
  if(strwidth("负能量抗性生命上限: "+value)>total/columns) assert(lines>1);
  // Strip layout whitespace/newlines; every repeated label/value survives.
  string compact=output.str();compact.erase(std::remove_if(compact.begin(),compact.end(),[](char c){return c==' '||c=='\n';}),compact.end());
  // Each column can wrap at a different character, so count digits and CJK
  // codepoints independently instead of assuming row-major text order.
  for(char digit='0';digit<='9';digit++) assert(std::count(compact.begin(),compact.end(),digit)==2*(columns-1));
  assert(std::count(compact.begin(),compact.end(),':')==columns-1);
  cases++;
 }
 // The actual fixed-column form renderer cannot grow with property count.
 for(int count:{1,10,30}) {
  vector<vector<string>> items={{" ","最低","最高","当前"}};
  for(int row=0;row<count;++row)items.push_back({"极长中文属性标签用于验证表格自动换行与列宽","<red>-12345678901234567890%</red>","+12345678901234567890%","12345678901234567890"});
  const auto widths=_form_table_widths(items);assert(widths.size()==4);
  const string rendered=_render_form_scaling_table(items);
  std::istringstream lines(rendered);string line;
  while(std::getline(lines,line))assert(strwidth(line)<=76);
  for(char digit='0';digit<='9';++digit)assert(std::count(rendered.begin(),rendered.end(),digit)==6*count);
  cases++;
 }
 TextRegion scrolling;scrolling.addstr("A\nB\nC\nD");
 assert(scrolling.cbuf[0]==U'B' && scrolling.cbuf[40]==U'C' && scrolling.cbuf[80]==U'D');
 std::cout << "PASS: " << cases << " grid/chunk cases, HUD columns, wide overwrite, clearing, clipping, UTF-8 chunks, scrolling and bounded detail/form tables\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cc').write_text(code)
 subprocess.run(['c++','-std=c++11',str(p/'test.cc'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
