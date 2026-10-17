#ifndef ZH_STANDALONE
#include "AppHdr.h"
#endif
#include "zh-message.h"
#include "zh-localization.h"
#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>

namespace {
struct ZhDefinition { const char *id, *en, *zh, *schema; };
#include "zh-message-catalog.inc"
const ZhDefinition &definition(const std::string &id) {
    for (const auto &entry : zh_definitions)
        if (id == entry.id) return entry;
    throw std::invalid_argument("Unknown localization message ID: " + id);
}
std::map<std::string, ZhArgType> schema(const std::string &spec) {
    static const std::map<std::string, ZhArgType> types = {
        {"text",ZhArgType::Text},{"name",ZhArgType::Name},
        {"integer",ZhArgType::Integer},{"number",ZhArgType::Number},
        {"key",ZhArgType::Key},{"colour",ZhArgType::Colour},
        {"key_markup",ZhArgType::KeyMarkup}};
    std::map<std::string, ZhArgType> result;
    std::istringstream stream(spec); std::string item;
    while (std::getline(stream,item,';')) {
        auto at=item.find(':'); result.emplace(item.substr(0,at),types.at(item.substr(at+1)));
    }
    return result;
}
std::string fill(const std::string &text, const std::map<std::string, ZhArg> &args, bool chinese) {
    std::string result;
    for (size_t at=0;at<text.size();) {
        if (at + 1 < text.size() && (text[at] == '{' || text[at] == '}')
            && text[at + 1] == text[at]) {
            result += text[at]; at += 2; continue;
        }
        if (text[at]!='{') {result+=text[at++];continue;}
        auto end=text.find('}',at); if (end==std::string::npos) throw std::invalid_argument("Unclosed localization parameter");
        const auto &arg=args.at(text.substr(at+1,end-at-1));
        result += chinese ? arg.localized : arg.canonical; at=end+1;
    }
    return result;
}
}
std::string ZhMessage::display() const { return zh_language_enabled() ? localized : canonical; }
ZhArg zh_integer(const std::string &key,long long value) {
    auto text=std::to_string(value);return {key,ZhArgType::Integer,text,text};
}
ZhArg zh_number(const std::string &key,double value,int precision) {
    std::ostringstream out;out<<std::fixed<<std::setprecision(precision)<<value;
    return {key,ZhArgType::Number,out.str(),out.str()};
}
ZhArg zh_text(const std::string &key,const std::string &canonical,const std::string &localized) {
    return {key,ZhArgType::Text,canonical,localized,
        canonical != localized || canonical.find_first_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") == std::string::npos};
}
ZhArg zh_numeric_notation(const std::string &key, const std::string &notation) {
    const bool supported = notation.empty()
        || (notation.find_first_of("0123456789") != std::string::npos
            && notation.find_first_not_of("0123456789dx+-*/(). %") == std::string::npos);
    return {key,ZhArgType::Text,notation,notation,supported};
}
ZhArg zh_key(const std::string &key,const std::string &value) {
    if (value.find_first_of("<>\n\r")!=std::string::npos) throw std::invalid_argument("Invalid localization key token");
    return {key,ZhArgType::Key,value,value};
}
ZhArg zh_key_markup(const std::string &key,const std::string &value) {
    bool highlighted = false;
    for (size_t at = 0; at < value.size();) {
        const unsigned char c = value[at];
        if (c < 32 || c == 127)
            throw std::invalid_argument("Invalid localization key markup");
        if (value.compare(at, 2, "<<") == 0) { at += 2; continue; }
        if (value.compare(at, 3, "<w>") == 0 && !highlighted) {
            highlighted = true; at += 3; continue;
        }
        if (value.compare(at, 4, "</w>") == 0 && highlighted) {
            highlighted = false; at += 4; continue;
        }
        if (c == '<')
            throw std::invalid_argument("Invalid localization key markup");
        ++at;
    }
    if (highlighted)
        throw std::invalid_argument("Unclosed localization key markup");
    return {key,ZhArgType::KeyMarkup,value,value};
}
ZhArg zh_colour(const std::string &key,const std::string &value) {
    static const std::set<std::string> colours={"black","blue","green","cyan","red","magenta","brown","lightgrey","darkgrey","lightblue","lightgreen","lightcyan","lightred","lightmagenta","yellow","white"};
    if (!colours.count(value)) throw std::invalid_argument("Invalid localization colour token");
    return {key,ZhArgType::Colour,value,value};
}
ZhMessage zh_message(const std::string &id,std::initializer_list<ZhArg> values,const std::string &canonical) {
    const auto &entry=definition(id);const auto expected=schema(entry.schema);
    std::map<std::string,ZhArg> args;
    for (const auto &value:values) {
        // Validate structure even when callers construct ZhArg directly.
        if (value.type == ZhArgType::Key) {
            zh_key(value.key, value.canonical);
            if (value.localized != value.canonical)
                throw std::invalid_argument("Translated localization key token: " + id);
        }
        if (value.type == ZhArgType::KeyMarkup) {
            zh_key_markup(value.key, value.canonical);
            if (value.localized != value.canonical)
                throw std::invalid_argument("Translated localization key markup: " + id);
        }
        if (value.type == ZhArgType::Colour) {
            zh_colour(value.key, value.canonical);
            if (value.localized != value.canonical)
                throw std::invalid_argument("Translated localization colour token: " + id);
        }
        if (value.type == ZhArgType::Integer || value.type == ZhArgType::Number) {
            const std::regex numeric(value.type == ZhArgType::Integer
                ? "[-+]?[0-9]+" : "[-+]?[0-9]+(\\.[0-9]+)?");
            const bool infinity = value.type == ZhArgType::Number
                && (value.canonical == "inf" || value.canonical == "-inf"
                    || value.canonical == "∞" || value.canonical == "-∞");
            if ((!std::regex_match(value.canonical, numeric) && !infinity)
                || value.localized != value.canonical)
                throw std::invalid_argument("Invalid localization numeric token: " + id);
        }
        if (!expected.count(value.key) || expected.at(value.key)!=value.type || !args.emplace(value.key,value).second)
            throw std::invalid_argument("Invalid localization parameter for "+id+": "+value.key);
    }
    if (args.size()!=expected.size()) throw std::invalid_argument("Missing localization parameter for "+id);
    // Select the complete templates before inserting any values. Never feed
    // the English result to a pattern matcher or translate parameter substrings.
    const std::string english = canonical.empty() ? fill(entry.en,args,false) : canonical;
    const bool complete = std::all_of(args.begin(),args.end(),[](const std::pair<const std::string,ZhArg> &value) {return value.second.supported;});
    if (!complete) {
        const char *path=std::getenv("DCSS_ZH_ID_MISSING");
        if (path && *path) {std::ofstream out(path,std::ios::app);out << id << "\tunsupported parameter\n";}
    }
    if (const char *trace=std::getenv("DCSS_ZH_ID_TRACE")) {
        if (*trace) {std::ofstream out(trace,std::ios::app);out<<id<<"\t"<<(complete?"localized":"canonical-fallback")<<"\n";}
    }
    const std::string localized = complete ? fill(entry.zh,args,true) : english;
    if (const char *trace=std::getenv("DCSS_ZH_MESSAGE_VALUES")) {
        if (*trace) {
            const auto escaped = [](const std::string &value) {
                std::string result;
                for (char ch : value) {
                    if (ch == '\\') result += "\\\\";
                    else if (ch == '\n') result += "\\n";
                    else if (ch == '\r') result += "\\r";
                    else if (ch == '\t') result += "\\t";
                    else result += ch;
                }
                return result;
            };
            std::ofstream out(trace,std::ios::app);
            out << id << '\t' << escaped(english) << '\t' << escaped(localized) << '\n';
        }
    }
    return {id,english,localized};
}

ZhArg zh_word_arg(const std::string &key,const std::string &domain,const std::string &english,ZhArgType kind) {
    if (english.empty()) return {key,kind,english,english,true};
    for (const auto &entry : zh_definitions) {
        if (std::string(entry.id).compare(0,domain.size(),domain)==0
            && english==entry.en && !*entry.schema)
            return {key,kind,english,entry.zh,true};
    }
    const char *path=std::getenv("DCSS_ZH_ID_MISSING");
    if (path && *path) {std::ofstream out(path,std::ios::app);out<<domain<<"\tmissing semantic atom\t"<<english<<"\n";}
    return {key,kind,english,english,false};
}
std::string zh_word(const std::string &domain,const std::string &english) {
    const auto arg=zh_word_arg("value",domain,english);
    return zh_language_enabled()?arg.localized:arg.canonical;
}

ZhArg zh_glossary_name(const std::string &key,const std::string &domain,const std::string &english) {
    for (const auto &entry : zh_definitions)
        if (std::string(entry.id).compare(0,domain.size()+1,domain+".")==0
            && english==entry.en && !*entry.schema)
            return {key,ZhArgType::Name,english,entry.zh,true};
    const auto localized=zh_lookup_exact(english);
    const bool supported=english.empty() || localized!=english;
    if (!supported) {
        const char *path=std::getenv("DCSS_ZH_NAME_MISSING");
        if (path && *path) {std::ofstream out(path,std::ios::app);out<<domain<<"\t"<<english<<"\n";}
    }
    return {key,ZhArgType::Name,english,localized,supported};
}

std::string zh_source(const char *context, const char *source_literal)
{
    if (!context || !source_literal)
        throw std::invalid_argument("Null localization source literal");
    // Optional database rows (quotes, symbol prefixes) may be absent. There
    // is no player-facing text to translate or report in that case.
    if (!*source_literal)
        return "";
    // Canonical/Lua readers must not depend on coverage of the display table.
    if (!zh_language_enabled())
        return source_literal;
    for (const auto &entry : zh_source_definitions)
        if (entry.context && std::string(context) == entry.context
            && std::string(source_literal) == entry.source)
            return zh_message(entry.id).display();
    if (const char *path = std::getenv("DCSS_ZH_ID_MISSING"))
        if (*path)
        {
            std::ofstream out(path, std::ios::app);
            out << context << "\tmissing source literal\t";
            for (const char *p = source_literal; *p; ++p)
                out << (*p == '\n' || *p == '\r' || *p == '\t' ? ' ' : *p);
            out << '\n';
        }
    if (std::getenv("DCSS_ZH_STRICT_SOURCE"))
        throw std::invalid_argument(std::string("Missing localization source: ") + context);
    return source_literal;
}

ZhArg zh_message_arg(const std::string &key, const std::string &id,
                     std::initializer_list<ZhArg> args) {
    const ZhMessage value = zh_message(id, args);
    const bool supported = std::all_of(args.begin(), args.end(),
        [](const ZhArg &arg) { return arg.supported; });
    return {key, ZhArgType::Text, value.canonical, value.localized, supported};
}
