#pragma once
#include <string>
// Presentation-only lookup. Never use for save IDs, input parsers, or Lua keys.
std::string zh_translate(const std::string &text);

// Preserve canonical English while serialising or inspecting message history.
class ZhTranslationPause {
public:
    ZhTranslationPause();
    ~ZhTranslationPause();
    ZhTranslationPause(const ZhTranslationPause &) = delete;
    ZhTranslationPause &operator=(const ZhTranslationPause &) = delete;
};
