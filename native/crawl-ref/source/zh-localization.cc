#ifndef ZH_STANDALONE
#include "AppHdr.h"
#include "options.h"
#endif
#include "zh-localization.h"
#include "zh-message.h"
#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <cctype>
#include <fstream>
#include <regex>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {
thread_local int pause_depth = 0;
thread_local int legacy_pause_depth = 0;
thread_local std::vector<std::string> legacy_guards;
thread_local unsigned background_depth = 0;
struct ZhEntry { const char *en; const char *zh; };
#include "zh-catalog.inc"
const std::regex printf_token("%([-+#0]*)([0-9]+|\\*)?(\\.([0-9]+|\\*))?(hh|ll|[hljztL])?([diuoxXfFeEgGaAcspn%])");
struct Pattern {
    std::string anchor;
    std::vector<std::string> pieces, source;
    std::vector<char> types;
    std::vector<bool> structural;
    size_t weight;
    bool article, reviewed;
};
bool valid_capture(const std::string &s, char kind) {
    if (kind == 's') return true;
    if (kind == 'c') return s.size() == 1;
    if (s.empty()) return false;
    const char *allowed = " +-0123456789.eEinfnaINFNA";
    if (std::string("diu").find(kind) != std::string::npos) allowed = " +-0123456789";
    else if (std::string("oxX").find(kind) != std::string::npos) allowed = " 0123456789abcdefABCDEFxX";
    return s.find_first_not_of(allowed) == std::string::npos;
}
// Bounded matching: even a deliberately ambiguous string cannot monopolise a frame.
bool match_pattern(const Pattern &p, const std::string &s, size_t index,
                   size_t at, std::vector<std::string> &captures, int &fuel,
                   size_t *consumed = nullptr) {
    if (--fuel < 0 || s.compare(at, p.source[index].size(), p.source[index]) != 0) return false;
    at += p.source[index].size();
    if (index == p.types.size()) {
        if (consumed) { *consumed = at; return true; }
        return at == s.size();
    }
    const auto &next = p.source[index+1];
    size_t end = next.empty() ? (index+1 == p.types.size() ? s.size() : at) : s.find(next, at);
    // Consecutive string captures have no recoverable boundary after printf.
    // Consume them as one phrase, translating its names/suffixes together,
    // instead of exhausting the match budget over every possible partition.
    if (next.empty() && p.types[index] == 's') {
        size_t following = index + 1;
        while (following < p.types.size() && p.source[following].empty()
               && p.types[following] == 's') ++following;
        if (following == p.types.size() || !p.source[following].empty())
            end = p.source[following].empty() ? s.size() : s.find(p.source[following], at);
    }
    while (end != std::string::npos && end <= s.size() && fuel > 0) {
        const auto capture = s.substr(at, end-at);
        if (valid_capture(capture, p.types[index])) {
            captures.push_back(capture);
            if (match_pattern(p, s, index+1, end, captures, fuel, consumed)) return true;
            captures.pop_back();
        }
        --fuel;
        end = next.empty() ? end+1 : s.find(next, end+1);
    }
    return false;
}
struct Catalog {
    std::unordered_map<std::string, std::string> exact, tagged;
    std::vector<Pattern> patterns;
    std::unordered_map<char, std::vector<const Pattern*>> fragments;
    std::unordered_map<std::string, std::string> cache;
    std::unordered_set<std::string> missing;
    std::vector<std::pair<std::string, std::string>> technical_prefixes;
    Catalog() {
        for (const auto &e : zh_entries) {
            exact.emplace(e.en, e.zh);
            // Menus concatenate complete descriptions, then wrap them by line.
            // A line no longer has the catalog entry's terminal newline.
            std::string line_en(e.en), line_zh(e.zh);
            while (!line_en.empty() && line_en.back() == '\n') line_en.pop_back();
            while (!line_zh.empty() && line_zh.back() == '\n') line_zh.pop_back();
            if (line_en != e.en && !line_en.empty()) exact.emplace(line_en, line_zh);
            std::string prefix(e.en), target(e.zh);
            if (!prefix.empty() && prefix[0] == '\n') prefix.erase(0,1);
            if (!target.empty() && target[0] == '\n') target.erase(0,1);
            if (prefix == "Stash search prefixes: " || prefix == "Menu/colouring prefixes: ") {
                technical_prefixes.emplace_back(prefix, target);
                technical_prefixes.emplace_back(target, target);
            }
            static const std::regex markup("</?[a-z][a-z0-9_: -]*>");
            const std::string untagged = std::regex_replace(std::string(e.en), markup, "");
            if (untagged != e.en) {
                tagged.emplace(untagged, e.zh);
                if (line_en != e.en)
                    tagged.emplace(std::regex_replace(line_en, markup, ""), line_zh);
            }
            std::vector<std::string> variants = {std::string(e.en)};
            if (line_en != e.en) variants.push_back(line_en);
            const size_t tagged_variants = variants.size();
            for (size_t i = 0; i < tagged_variants; ++i) {
                const auto plain = std::regex_replace(variants[i], markup, "");
                if (plain != variants[i]) variants.push_back(plain);
            }
            for (const auto &en : variants) {
                std::string zh(e.zh);
                if (!en.empty() && en.back() != '\n')
                    while (!zh.empty() && zh.back() == '\n') zh.pop_back();
                std::string anchor, source_piece;
                std::vector<std::string> source;
                std::vector<char> types;
                std::vector<bool> structural;
                size_t at = 0, weight = 0, captures = 0;
                bool safe = true;
                for (std::sregex_iterator i(en.begin(), en.end(), printf_token), end; i != end; ++i) {
                    const auto &m = *i;
                    const std::string literal = en.substr(at, m.position() - at);
                    source_piece += literal;
                    weight += literal.size();
                    if (literal.size() > anchor.size()) anchor = literal;
                    const char kind = m.str().back();
                    if (m.str().find('*') != std::string::npos || kind == 'n' || kind == 'p') safe = false;
                    if (kind == '%') source_piece += '%';
                    else {
                        ++captures;
                        source.push_back(source_piece); source_piece.clear();
                        types.push_back(kind);
                        // printf may supply a colour name inside a tag. It is
                        // parser syntax, even though "red" is also prose.
                        const auto opening = en.rfind('<', m.position());
                        const auto closing = en.rfind('>', m.position());
                        structural.push_back(opening != std::string::npos
                            && (closing == std::string::npos || opening > closing));
                    }
                    at = m.position() + m.length();
                }
                const auto tail = en.substr(at);
                source_piece += tail;
                source.push_back(source_piece);
                weight += tail.size();
                if (tail.size() > anchor.size()) anchor = tail;
                // Avoid generic wrappers ("%s %s") and pathological ambiguous matches.
                const bool article = en == "a %s" || en == "an %s" || en == "the %s"
                    || en == "A %s" || en == "An %s" || en == "The %s";
                // A generic "%s the %s" also matches spell names such as Fugue of
                // the Fallen. Titles are localized at their presentation callsite.
                if (en == "%s the %s") continue;
                const bool composition = en == " of %s";
                const bool reviewed = std::find(std::begin(zh_reviewed), std::end(zh_reviewed), std::string(e.en)) != std::end(zh_reviewed);
                const bool combat = reviewed && (en == "You %s %s%s." || en == "You %s %s!"
                    || en == "The %s %s %s%s%s%s" || en == "You %s %s%s%s%s%s%s");
                const bool property_sentence = reviewed && (en == "It is %s.\n"
                    || en == "It is %s." || en == "He is %s.\n" || en == "He is %s."
                    || en == "She is %s.\n" || en == "She is %s."
                    || en == "They are %s.\n" || en == "They are %s.");
                // Reviewed, verb-specific templates may start with a name
                // capture ("%s bites %s%s"). Keep their fixed verb as an
                // anchor while rejecting unbounded wrappers such as "%s %s".
                const bool reviewed_phrase = reviewed && weight >= 4
                    && std::count_if(anchor.begin(), anchor.end(), [](unsigned char c) {
                        return std::isalpha(c);
                    }) >= 3 && anchor != " the " && anchor != " and ";
                const bool numeric = std::find(types.begin(), types.end(), 's') == types.end()
                    && weight >= 2 && !anchor.empty();
                if (!safe || captures == 0 || captures > 12
                    || (!article && !composition && !numeric && !combat && !property_sentence && !reviewed_phrase
                        && (weight < 8 || anchor.size() < 4))) continue;
                std::vector<std::string> pieces;
                std::string piece;
                at = 0;
                for (std::sregex_iterator i(zh.begin(), zh.end(), printf_token), end; i != end; ++i) {
                    piece += zh.substr(at, i->position() - at);
                    if (i->str().back() == '%') piece += '%';
                    else { pieces.push_back(piece); piece.clear(); }
                    at = i->position() + i->length();
                }
                piece += zh.substr(at);
                pieces.push_back(piece);
                if (pieces.size() != captures + 1) continue;
                patterns.push_back({anchor, pieces, source, types, structural, weight, article, reviewed});
            }
        }
        std::stable_sort(patterns.begin(), patterns.end(), [](const Pattern &a, const Pattern &b) {
            const bool ar = a.reviewed && a.weight >= 8;
            const bool br = b.reviewed && b.weight >= 8;
            if (ar != br) return ar > br;
            return a.weight != b.weight ? a.weight > b.weight : a.reviewed > b.reviewed; });
        for (const auto &p : patterns) {
            // A fixed beginning and ending delimit a complete translated
            // phrase inside an ostream/concatenation-built description.
            if (p.weight < 8 || p.source.front().size() < 4 || p.source.back().empty()) continue;
            if (p.types.back() == 's' && p.source.back().find_first_not_of(" \t\n") == std::string::npos) continue;
            fragments[p.source.front()[0]].push_back(&p);
        }
    }
    std::string lookup_capture(const std::string &s, char kind, int depth) {
        auto localized = lookup(s, depth);
        // A greedy noun capture can include the sentence's final punctuation.
        // Retry only unresolved English articles, preserving the original marks.
        if (kind == 's' && s.find('\n') == std::string::npos) {
            for (const auto *article : {"a ", "an ", "the ", "The "}) {
                if (s.compare(0, std::strlen(article), article) != 0
                    || localized.compare(0, std::strlen(article), article) != 0)
                    continue;
                const auto end = s.find_last_not_of(".!?");
                if (end != std::string::npos && end + 1 < s.size()) {
                    const auto noun = s.substr(0, end + 1);
                    const auto translated = lookup(noun, depth);
                    if (translated != noun)
                        localized = translated + s.substr(end + 1);
                }
                break;
            }
        }
        if (kind == 's' && localized != s && localized.find('\n') == std::string::npos) {
            const auto first = localized.find_first_not_of(" \t");
            const auto last = localized.find_last_not_of(" \t");
            if (first != std::string::npos) localized = localized.substr(first, last-first+1);
        }
        return localized;
    }
    std::string lookup(const std::string &s, int depth) {
        if (s.empty() || s.size() > 16000) return s;
        auto e = exact.find(s);
        if (e != exact.end()) return e->second;
        if (s.find('<') == std::string::npos) {
            const auto visible = tagged.find(s);
            if (visible != tagged.end()) {
                static const std::regex tags("</?[a-z][a-z0-9_: -]*>");
                return std::regex_replace(visible->second, tags, "");
            }
        }
        // Deep captures must still resolve exact names. Cache only root calls:
        // a recursion-limited partial result must never poison later rendering.
        if (depth > 12) return s;
        if (depth == 0) {
            auto c = cache.find(s);
            if (c != cache.end()) return c->second;
        }
        // Layout indentation is not part of a sentence's semantics. Match the
        // reviewed full sentence before an older, indented partial template.
        const size_t indent_at = s.find_first_not_of(" \t");
        if (indent_at != std::string::npos && indent_at >= 2
            && s[indent_at] >= 'A' && s[indent_at] <= 'Z') {
            const auto body = s.substr(indent_at);
            const auto localized = lookup(body, depth + 1);
            if (localized != body)
                return s.substr(0, indent_at) + localized;
        }
        // message_line::full_text joins separate stored messages with these
        // markers. Keep their sentence boundaries before matching printf
        // captures, which otherwise swallow several combat messages at once.
        const std::string separators[] = {"<lightgrey> </lightgrey>",
                                          "<lightgrey>; </lightgrey>"};
        size_t begin = 0;
        std::string joined;
        while (begin < s.size()) {
            size_t next = std::string::npos;
            const std::string *separator = nullptr;
            for (const auto &candidate : separators) {
                const auto at = s.find(candidate, begin);
                if (at < next) { next = at; separator = &candidate; }
            }
            if (!separator) break;
            joined += lookup(s.substr(begin, next-begin), depth+1) + *separator;
            begin = next + separator->size();
        }
        if (begin)
            return joined + lookup(s.substr(begin), depth+1);
        // These values are literal input-parser tokens, not prose. Preserve
        // them after the localized heading, including on subsequent renders.
        for (const auto &prefix : technical_prefixes) {
            const size_t at = s.find(prefix.first);
            if (at == std::string::npos) continue;
            size_t end = s.find('\n', at);
            if (end == std::string::npos) end = s.size();
            return lookup(s.substr(0, at), depth+1) + prefix.second
                + s.substr(at+prefix.first.size(), end-at-prefix.first.size())
                + lookup(s.substr(end), depth+1);
        }
        std::string result = s;
        if (result == s && s.size() <= 2048) {
            for (const auto &p : patterns) {
                if (s.find(p.anchor) == std::string::npos) continue;
                if (p.weight < 8 && !p.article) {
                    if ((p.source.front() == "The " || p.source.front() == "You ")
                        && s.find('\n') != std::string::npos) continue;
                    if (p.source.front() == "The "
                        && s.find(" hits ") == std::string::npos
                        && s.find(" pierces through ") == std::string::npos) continue;
                }
                std::vector<std::string> captures;
                int fuel = 256;
                if (!match_pattern(p, s, 0, 0, captures, fuel)) continue;
                if (p.reviewed && p.source.front().empty() && !captures.empty()) {
                    // A leading actor capture must not swallow an enclosing
                    // paragraph, menu selector or bracketed description.
                    // Let the complete inner sentence/fragment match instead.
                    static const std::regex actor_markup("</?[a-z][a-z0-9_: -]*>");
                    const auto actor = std::regex_replace(captures.front(), actor_markup, "");
                    if (actor.find_first_of("\n[]{}.!?:;") != std::string::npos) continue;
                }
                if (p.article) {
                    // Articles describe names, not whole sentences/paragraphs.
                    // Otherwise "The %s" steals a composed help paragraph
                    // before its complete lines can match the catalog.
                    if (captures[0].find_first_of("\n.!?") != std::string::npos) continue;
                    const auto start = captures[0].find_first_not_of(" \t");
                    if (start == std::string::npos
                        || (captures[0][start] == '-'
                            && (start + 1 == captures[0].size()
                                || !std::isdigit(static_cast<unsigned char>(captures[0][start+1]))))
                        || captures[0][start] == ')' || captures[0][start] == ':') continue;
                    if (lookup(captures[0], depth+1) == captures[0]) continue;
                }
                result = p.pieces[0];
                for (size_t j = 0; j < captures.size(); ++j)
                    result += (p.structural[j] ? captures[j] : lookup_capture(captures[j], p.types[j], depth + 1)) + p.pieces[j+1];
                break;
            }
        }
        // Menu selectors are structural. Translate the complete description
        // after them before generic fragments can consume "You have ...".
        if (result == s) {
            static const std::regex selector("^([ ]*[A-Za-z0-9?] [+-] )(.+)$");
            std::smatch selected;
            if (std::regex_match(s, selected, selector))
                result = selected[1].str() + lookup(selected[2].str(), depth+1);
        }
        // Complete item-description lines take precedence over shorter
        // embedded templates. Keep hotkey tags intact until the full line has
        // had a chance to match its tagged printf template.
        if (result == s && s.find('\n') != std::string::npos) {
            result.clear();
            size_t at = 0;
            while (at < s.size()) {
                const size_t end = s.find('\n', at);
                if (end == std::string::npos) {
                    result += lookup(s.substr(at), depth+1); break;
                }
                result += lookup(s.substr(at, end-at), depth+1) + "\n";
                at = end+1;
            }
        }
        // Stored messages canonicalise <w> to <white> and insert base colours.
        // Match visible text, then restore the source translation's hotkey tags.
        static const std::regex markup("</?[a-z][a-z0-9_: -]*>");
        if (result == s && s.find('<') != std::string::npos) {
            const auto plain = std::regex_replace(s, markup, "");
            if (plain != s) {
                auto tagged_entry = tagged.find(plain);
                const auto localized = tagged_entry != tagged.end()
                    ? tagged_entry->second : lookup(plain, depth+1);
                if (localized != plain) {
                    size_t leading = 0;
                    while (leading < s.size() && s[leading] == '<') {
                        const size_t end = s.find('>', leading);
                        if (end == std::string::npos) break;
                        leading = end+1;
                    }
                    result = s.substr(0, leading) + localized;
                    if (tagged_entry == tagged.end()) {
                        // Preserve the final colour and balanced closing tags
                        // when a dynamic sentence spans multiple colour runs.
                        for (std::sregex_iterator i(s.begin()+leading, s.end(), markup), end;
                             i != end; ++i) result += i->str();
                    }
                }
            }
        }
        if (result == s && s.size() <= 8192) {
            std::string pending;
            bool any_fragment = false;
            result.clear();
            for (size_t at = 0; at < s.size();) {
                bool matched = false;
                const auto bucket = fragments.find(s[at]);
                if (bucket != fragments.end()) {
                    for (const Pattern *p : bucket->second) {
                        if (at > 0 && std::isalnum(static_cast<unsigned char>(s[at-1]))
                            && std::isalnum(static_cast<unsigned char>(s[at]))) continue;
                        if (s.compare(at, p->source.front().size(), p->source.front()) != 0) continue;
                        std::vector<std::string> captures;
                        int fuel = 256; size_t end = 0;
                        if (!match_pattern(*p, s, 0, at, captures, fuel, &end) || end <= at) continue;
                        result += lookup(pending, depth+1); pending.clear();
                        result += p->pieces[0];
                        for (size_t j = 0; j < captures.size(); ++j)
                            result += (p->structural[j] ? captures[j] : lookup_capture(captures[j], p->types[j], depth+1)) + p->pieces[j+1];
                        at = end; matched = true; any_fragment = true; break;
                    }
                }
                if (!matched) pending += s[at++];
            }
            if (any_fragment) result += lookup(pending, depth+1);
            else result = s;
        }
        if (result == s) {
            // Translate inside intact colour tags and on line boundaries.
            static const std::regex boundary("</?[a-z][a-z0-9_: -]*>|\n");
            size_t at = 0; result.clear(); bool split = false;
            for (std::sregex_iterator i(s.begin(), s.end(), boundary), end; i != end; ++i) {
                split = true;
                result += lookup(s.substr(at, i->position() - at), depth + 1) + i->str();
                at = i->position() + i->length();
            }
            if (split) result += lookup(s.substr(at), depth + 1);
            else {
                result = s;
                const auto first = s.find_first_not_of(" \t\r");
                const auto last = s.find_last_not_of(" \t\r");
                if (first != std::string::npos && (first > 0 || last + 1 < s.size()))
                    result = s.substr(0, first) + lookup(s.substr(first, last-first+1), depth+1) + s.substr(last+1);
            }
        }
        if (depth == 0) {
            if (cache.size() >= 8192) cache.clear();
            cache.emplace(s, result);
        }
        return result;
    }
    static std::string json(const std::string &s) {
        static const char hex[]="0123456789abcdef";
        std::string out="\"";
        for (unsigned char c : s) {
            if (c == '"' || c == '\\') { out += '\\'; out += c; }
            else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
            else out += c;
        }
        return out+'"';
    }
    void trace(const std::string &s, const std::string &result) {
        // Include partial translations and cached inputs. Names and key labels
        // remain in this evidence; the audit must classify them, not hide them.
        const char *log = std::getenv("DCSS_ZH_TRACE");
        if (log && *log && missing.insert(s).second) {
            std::ofstream f(log, std::ios::app);
            f << "{\"en\":" << json(s) << ",\"rendered\":" << json(result) << "}\n";
        }
        const char *old_log = std::getenv("DCSS_ZH_MISSING");
        if (old_log && *old_log && result == s && s.size() > 8) {
            std::ofstream f(old_log, std::ios::app); f << s << '\n';
        }
    }
};
bool enabled() {
    if (pause_depth) return false;
    const char *lang = std::getenv("DCSS_LANG");
    if (lang && *lang) return std::string(lang) == "zh" || std::string(lang) == "zh_CN";
#ifndef ZH_STANDALONE
    return Options.lang_name && std::string(Options.lang_name) == "zh";
#else
    return true;
#endif
}
}
std::string zh_lookup_exact(const std::string &text) {
    static const ZhEntry names[] = {
#include "zh-display-lexicon.inc"
    };
    for (const auto &entry : names)
        if (text == entry.en) return entry.zh;
    static Catalog catalog;
    const auto it = catalog.exact.find(text);
    return it == catalog.exact.end() ? text : it->second;
}

bool zh_language_enabled() { return enabled(); }
bool zh_translation_paused() { return pause_depth != 0; }
std::string zh_translate(const std::string &text) {
    if (!enabled() || legacy_pause_depth
        || text.find_first_not_of(" \t\n\r") == std::string::npos) return text;
    if (!background_depth && !legacy_guards.empty() && std::getenv("DCSS_ZH_FORBID_LEGACY"))
    {
        if (const char *path = std::getenv("DCSS_ZH_ID_MISSING"))
            if (*path)
            {
                std::ofstream out(path, std::ios::app);
                out << legacy_guards.back() << "\tlegacy renderer reached\t";
                for (char c : text)
                    out << (c == '\n' || c == '\r' || c == '\t' ? ' ' : c);
                out << '\n';
            }
        throw std::logic_error("Legacy translation reached migrated boundary: "
                               + legacy_guards.back() + ": " + text);
    }
    static Catalog catalog;
    const auto result = catalog.lookup(text, 0);
    catalog.trace(text, result);
    return result;
}

ZhTranslationPause::ZhTranslationPause() { ++pause_depth; }
ZhTranslationPause::~ZhTranslationPause() { --pause_depth; }
ZhLegacyPause::ZhLegacyPause() { ++legacy_pause_depth; }
ZhLegacyPause::~ZhLegacyPause() { --legacy_pause_depth; }

ZhLegacyGuard::ZhLegacyGuard(const char *context)
{
    legacy_guards.emplace_back(context ? context : "unspecified");
    if (const char *path = std::getenv("DCSS_ZH_BOUNDARY_TRACE"))
        if (*path)
        {
            std::ofstream out(path, std::ios::app);
            out << legacy_guards.back() << "\tenter\n";
        }
}
ZhLegacyGuard::~ZhLegacyGuard()
{
    legacy_guards.pop_back();
}
ZhLegacyBackground::ZhLegacyBackground() { ++background_depth; }
ZhLegacyBackground::~ZhLegacyBackground() { --background_depth; }
