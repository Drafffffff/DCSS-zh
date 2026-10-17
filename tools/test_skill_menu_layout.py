#!/usr/bin/env python3
"""Compile and exercise the exact static layout helpers from skill-menu.cc."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native/crawl-ref/source/skill-menu.cc"
source = SOURCE.read_text()

# Switch allocation and footer reservation must use the same production
# display-cell geometry as the layout tests below.
assert "return _skill_text_width(m_text);" in source
assert "if (coord.x + size > m_max_coord.x)" in source
assert "item->get_max_coord().y" in source


def extract_function(name):
    match = re.search(r"static\s+(?:int|string)\s+" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", source)
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


helpers = "\n".join(extract_function(name) for name in (
    "_skill_cells", "_skill_wrap", "_skill_line_count",
    "_skill_help_rows", "_skill_help_columns", "_skill_help_rows_available", "_skill_text_width"))

harness = r'''#include <algorithm>
#include <cassert>
#include <cstddef>
#include <iostream>
#include <string>
using std::string;
using std::max;
using std::min;
static int utf8towc(char32_t *out, const char *s) {
    const unsigned char c = static_cast<unsigned char>(*s);
    if (!c) { *out = 0; return 0; }
    if (c < 0x80) { *out = c; return 1; }
    int n = (c & 0xe0) == 0xc0 ? 2 : (c & 0xf0) == 0xe0 ? 3 : 4;
    char32_t value = c & (n == 2 ? 0x1f : n == 3 ? 0x0f : 0x07);
    for (int i = 1; i < n; ++i)
        value = (value << 6) | (static_cast<unsigned char>(s[i]) & 0x3f);
    *out = value; return n;
}
'''
checks = r'''
int main() {
    // Style tags are zero-width, while their CJK content occupies two cells.
    assert(_skill_text_width("<white>中文</white>") == 4);
    // Escaped << is a literal '<', never a tag extending to a later '>'.
    assert(_skill_text_width("<<not a tag>") == 11);
    assert(_skill_wrap("<<not a tag>", 80) == "<<not a tag>");
    // Punctuation and arrows remain one cell; combining marks remain zero.
    assert(_skill_cells(0x2192) == 1); // →
    assert(_skill_cells(0x2026) == 1); // …
    assert(_skill_cells(0x0301) == 0);
    assert(_skill_text_width("→…") == 2);
    assert(_skill_text_width("e\xcc\x81") == 1);

    const string mixed = "<cyan>技能</cyan> → next";
    for (int width : {8, 12, 20, 80, 120}) {
        const string wrapped = _skill_wrap(mixed, width);
        size_t begin = 0;
        while (begin <= wrapped.size()) {
            const size_t end = wrapped.find('\n', begin);
            const string line = wrapped.substr(begin, end == string::npos ? end : end - begin);
            assert(_skill_text_width(line) <= width);
            if (end == string::npos) break;
            begin = end + 1;
        }
    }

    // Long 4K-style help wraps into multiple rows and the help box grows only
    // as far as its available vertical space permits.
    string help;
    for (int i = 0; i < 500; ++i) help += "训练目标与经验比例 → ";
    const string wrapped = _skill_wrap(help, 100);
    const int lines = _skill_line_count(wrapped);
    assert(lines > 3);
    assert(_skill_help_rows(3, lines, 200) == lines);
    assert(_skill_help_rows(3, lines, 12) == 12);
    assert(_skill_help_rows(3, 2, 12) == 3);
    assert(_skill_help_columns(2, 81, 1) == 78);
    assert(_skill_help_columns(48, 1944, 24) == 78);
    assert(_skill_help_columns(100, 105, 24) == 1);
    assert(_skill_help_columns(0, 0, 0) == 1);
    // Reserve the complete footer span: two wrapped switch rows need one
    // additional row, and tile coordinates scale by the font height.
    assert(_skill_help_rows_available(36, 3, 14, 1) == 25);
    assert(_skill_help_rows_available(36, 3, 15, 1) == 24);
    assert(_skill_help_rows_available(720, 3, 300, 20) == 24);
    std::cout << "PASS: extracted production skill-menu layout helpers; " << lines
              << " rows at 100 cells\n";
}
'''
with tempfile.TemporaryDirectory() as tmp:
    cpp = Path(tmp) / "test.cc"
    exe = Path(tmp) / "test"
    cpp.write_text(harness + "\n" + helpers + "\n" + checks)
    subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", str(cpp), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
