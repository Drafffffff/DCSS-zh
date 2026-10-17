#pragma once
#include <initializer_list>
#include <string>

enum class ZhArgType { Text, Name, Integer, Number, Key, Colour, KeyMarkup };
struct ZhArg {
    std::string key;
    ZhArgType type;
    std::string canonical, localized;
    bool supported;
    ZhArg() : type(ZhArgType::Text), supported(false) {}
    ZhArg(const std::string &k, ZhArgType t, const std::string &en,
          const std::string &zh, bool ok = true)
        : key(k), type(t), canonical(en), localized(zh), supported(ok) {}

};
struct ZhMessage {
    std::string id, canonical, localized;
    std::string display() const;
};
ZhArg zh_integer(const std::string &key, long long value);
ZhArg zh_number(const std::string &key, double value, int precision = 1);
ZhArg zh_text(const std::string &key, const std::string &canonical,
              const std::string &localized);
ZhArg zh_key(const std::string &key, const std::string &value);
// Menu-generated key names with their fixed <w> styling and escaped '<'.
// This is immutable structure, never an ordinary translatable text argument.
ZhArg zh_key_markup(const std::string &key, const std::string &value);
ZhArg zh_colour(const std::string &key, const std::string &value);
ZhMessage zh_message(const std::string &id, std::initializer_list<ZhArg> args = {},
                     const std::string &canonical = "");
// Exact whole entries only. Intended for semantic enum labels and base names;
// never call this with an assembled sentence or an internal identifier.
std::string zh_lookup_exact(const std::string &text);

ZhArg zh_word_arg(const std::string &key, const std::string &domain,
                  const std::string &english, ZhArgType kind = ZhArgType::Text);
std::string zh_word(const std::string &domain, const std::string &english);

ZhArg zh_glossary_name(const std::string &key, const std::string &domain, const std::string &english);

// Source-generation lookup for complete, fixed source literals only. The
// context+literal binds to a stable catalog ID; assembled sentences and printf
// results must instead use zh_message with typed, named parameters.
std::string zh_source(const char *context, const char *source_literal);
