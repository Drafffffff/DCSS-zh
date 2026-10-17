#pragma once
#include <string>
// Presentation-only lookup. Never use for save IDs, input parsers, or Lua keys.
std::string zh_translate(const std::string &text);
bool zh_language_enabled();
bool zh_translation_paused();

// Rendering bypass only: suppress the legacy matcher without changing the
// selected language of typed messages, semantic names or database entries.
class ZhLegacyPause {
public:
    ZhLegacyPause();
    ~ZhLegacyPause();
    ZhLegacyPause(const ZhLegacyPause &) = delete;
    ZhLegacyPause &operator=(const ZhLegacyPause &) = delete;
};

// Preserve canonical English while serialising or inspecting message history.
class ZhTranslationPause {
public:
    ZhTranslationPause();
    ~ZhTranslationPause();
    ZhTranslationPause(const ZhTranslationPause &) = delete;
    ZhTranslationPause &operator=(const ZhTranslationPause &) = delete;
};

// Development assertion for completed migration boundaries. It does not pause
// translation or change display language. Enable DCSS_ZH_FORBID_LEGACY to reject
// a legacy matcher reached through a guarded generator or renderer.
class ZhLegacyGuard {
public:
    explicit ZhLegacyGuard(const char *context);
    ~ZhLegacyGuard();
    ZhLegacyGuard(const ZhLegacyGuard &) = delete;
    ZhLegacyGuard &operator=(const ZhLegacyGuard &) = delete;
};

// The global HUD is redrawn behind modal windows by the UI event loop. Its
// migration is tracked separately from the modal's producer/render boundary.
// This changes only the development assertion, never language or translation.
class ZhLegacyBackground {
public:
    ZhLegacyBackground();
    ~ZhLegacyBackground();
    ZhLegacyBackground(const ZhLegacyBackground &) = delete;
    ZhLegacyBackground &operator=(const ZhLegacyBackground &) = delete;
};
