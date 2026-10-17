#!/usr/bin/env python3
"""Exercise extracted HUD layout producers and guard their rendered cell bounds."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native/crawl-ref/source/output.cc"
source = SOURCE.read_text()


def extract_function(name):
    match = re.search(r"static\s+(?:int|string|void)\s+" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", source)
    if not match:
        raise AssertionError(f"production helper not found: {name}")
    start = match.start()
    brace = source.index("{", match.start())
    depth = 0
    for end in range(brace, len(source)):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                return source[start:end + 1]
    raise AssertionError(f"unclosed helper: {name}")


experience = extract_function("_hud_experience_line")
noise = extract_function("_print_stats_noise")
place = extract_function("_hud_place_line")
weapon = extract_function("_print_weapon_name")

# The weapon formatter depends on game state/item naming. Keep its production
# boundary explicit: the caller must chop by display-cell width.
assert "chop_string(_level_description_string_hud()," in source
assert "std::max(0, crawl_view.hudsz.x - place_x + 1)" in source
assert "chop_string(name, max_name_width)" in source
assert "const int max_name_width = width - slot_name.size();" in weapon

prefix = r'''#include <algorithm>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>
using std::string; using std::max; using std::min;
struct ZhArg { string canonical; string localized; };
static ZhArg zh_integer(const char*, int n) { return {std::to_string(n),std::to_string(n)}; }
static ZhArg zh_text(const char*, const string&, const string& s) { return {s,s}; }
static int pause_depth=0;
static bool zh_language_enabled(){return pause_depth==0;}
struct ZhMessage { string canonical,localized; string display() const { return zh_language_enabled()?localized:canonical; } };
static ZhMessage zh_message(const char* id, std::initializer_list<ZhArg> a, const string&) {
    auto i=a.begin();
    if (string(id)=="hud.experience.max") return {"XL: "+i->canonical,"等级 "+i->canonical};
    if (string(id)=="hud.experience.progress") return {"XL: "+i->canonical+" Next: "+(i+1)->canonical+"%","等级 "+i->canonical+" 升级 "+(i+1)->canonical+"%"};
    if (string(id)=="hud.label.noise") return {"Noise","噪声"};
    if (string(id)=="hud.noise.silenced") return {"Silenced","静音"};
    if (string(id)=="hud.place.branch") return {i->canonical,i->localized};
    return {i->canonical+":"+(i+1)->canonical,i->localized+"："+(i+1)->canonical};
}
static ZhMessage zh_message(const char* id) { return string(id)=="hud.label.noise"?ZhMessage{"Noise","噪声"}:ZhMessage{"Silenced","静音"}; }
static string make_stringf(const char* fmt, ...) {
    char b[128]; va_list ap; va_start(ap,fmt); std::vsnprintf(b,sizeof(b),fmt,ap); va_end(ap); return b;
}
static int strwidth(const string& s) {
    int w=0; for (unsigned char c : s) if ((c&0xc0)!=0x80) w += c < 0x80 ? 1 : 2; return w;
}
static string chop_string(const string& s, int width) {
    if (width<=0) return ""; int w=0; size_t i=0;
    while(i<s.size()) { unsigned char c=s[i]; int n=c<0x80?1:((c&0xe0)==0xc0?2:((c&0xf0)==0xe0?3:4)); int cells=c<0x80?1:2; if(w+cells>width) break; w+=cells; i+=n; }
    return s.substr(0,i);
}
struct ZhLegacyGuard { ZhLegacyGuard(const char*){} };
struct ZhLegacyPause { ZhLegacyPause(){} ~ZhLegacyPause(){} };
static bool small_layout=false;
static bool _is_using_small_layout(){return small_layout;}
struct Pos { int x=0; };
struct Player { int running=0; int wizard=false; int noise=0; Pos pos() const{return{};} int get_noise_perception(bool) const{return noise;} int corrosion_amount()const{return 0;} };
static Player you;
struct Opt { int travel_delay=0; }; static Opt Options;
enum { MOUSE_MODE_NORMAL=0 }; namespace mouse_control { static int current_mode(){return 1;} }
static bool silenced_value=false; static bool silenced(Pos){return silenced_value;}
using colour_t=int; enum { LIGHTGREY,YELLOW,RED,LIGHTMAGENTA,HUD_CAPTION_COLOUR,LIGHTGREY_UNUSED };
static void textcolour(int){}
static int cursor_x=0, max_written=0; static std::vector<string> printed;
static void gotoxy(int x,int,int){cursor_x=x;}
#define CGOTOXY(x,y,z) gotoxy((x),(y),(z))
#define GOTO_STAT 0
static void cprintf(const char* fmt, ...) { char b[256]; va_list ap; va_start(ap,fmt); std::vsnprintf(b,sizeof(b),fmt,ap); va_end(ap); printed.emplace_back(b); max_written=std::max(max_written,cursor_x+strwidth(b)-1); cursor_x += strwidth(b); }
#define CPRINTF(...) cprintf(__VA_ARGS__)
struct Bar { int horiz_bar_width=0; int m_change_neg=0,m_default=0,m_change_pos=0; void reset(){} void draw(int x,int,int,int w){max_written=std::max(max_written,x+w-1);} };
static Bar Noise_Bar;
static int div_round_up(int a,int b){return (a+b-1)/b;}
'''

main = r'''
int main() {
  // Actual production experience formatter with independent boundary cases.
  for (int level : {1,2,27}) for (int progress : {0,29,100}) {
    const string line=_hud_experience_line(level,progress,false,false);
    assert(strwidth(line)<=17);
    assert(line.find("等级 ")==0);
  }
  assert(strwidth(_hud_experience_line(27,0,true,false))<=17);
  const string deep_place=_hud_place_line("Abyss","深渊",27,true);
  assert(deep_place=="深渊：27");
  assert(strwidth(chop_string(deep_place,6))<=6);

  // Actual noise producer: the left pane occupies columns 1..18. Exercise
  // ordinary, wizard, silence, loud, and compact layouts from x=1.
  struct Case { bool wizard,silence,small; int level; };
  for (Case c : {Case{false,false,false,29}, Case{true,false,false,29},
                 Case{false,true,false,0}, Case{false,false,false,1000},
                 Case{false,false,true,29}, Case{true,false,true,1000}}) {
    you.wizard=c.wizard; you.noise=c.level; silenced_value=c.silence;
    small_layout=c.small; max_written=0; printed.clear();
    _print_stats_noise(1,1);
    assert(max_written<=18);
    bool has_noise=false, has_silence=!c.silence;
    for (const string& s : printed) { if (s=="噪声") has_noise=true; if (s.find("静音")==0) has_silence=true; }
    assert(has_noise && has_silence);
    if (!c.silence) assert(Noise_Bar.horiz_bar_width <= (c.wizard ? 6 : 9) + (c.small ? -1 : 0) + (c.level==1000 ? 1 : 0));
  }
  // Long-to-short weapon name chopping must use display cells (CJK = 2).
  for (const string& name : {string("长长长长长长"), string("短剑"), string("A"), string("")})
    assert(strwidth(chop_string(name, 5))<=5);
  item_def w; max_written=0; cursor_x=1; _print_weapon_name(w,8);
  assert(max_written<=8);
  // Place values share the same bounded chop path even when a branch is long.
  assert(strwidth(chop_string("深渊：27", 6))<=6);
  std::cout << "PASS: HUD experience/noise extracted producers and display-cell bounds\n";
}
'''

# Provide a minimal item/name shell so the extracted production function parses;
# this test deliberately exercises the exact chop_string call above separately.
weapon_stub = "struct item_def { int slot='a'; int base_type=0; int plus=0; }; enum { OBJ_WEAPONS=0, DESC_PLAIN=0 }; static ZhArg zh_item_arg(const char*, const item_def&, int){return {\"长长长长长长\",\"长长长长长长\"};} static int _wpn_name_colour(const item_def&){return 0;}"
with tempfile.TemporaryDirectory() as tmp:
    cpp = Path(tmp) / "test.cc"
    exe = Path(tmp) / "test"
    cpp.write_text(prefix + "\n" + place + "\n" + experience + "\n" + noise + "\n" + weapon_stub + "\n" + weapon + "\n" + main)
    subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", str(cpp), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
