#pragma once
#include <map>
#include <string>
#include <vector>
#include "zh-message.h"

// UI-only selection tree. Never serialized, passed to Lua or used as DB keys.
struct ZhSpeech {
    std::string canonical, source, key;
    std::vector<ZhSpeech> children;
    std::vector<std::string> child_markers;
    std::vector<size_t> child_positions;
    bool supported = true;
};
struct ZhSpeechFacts {
    std::map<std::string, std::string> values;
    std::map<std::string, ZhSpeech> nested;
    std::vector<int> choices;
    std::vector<std::string> generated_names;
};
class monster;
ZhMessage zh_mon_speech_message(const ZhSpeech &speech, const monster &mon,
                               int shout_type = -1);
// Full-template renderer consumes the already selected tree and semantic facts.
ZhMessage zh_render_speech(const ZhSpeech &speech, const monster &mon,
                          const ZhSpeechFacts &facts, const std::string &canonical);
ZhArg zh_speech_actor_arg(const std::string &key, const std::string &tag,
                         const monster &mon, const ZhSpeechFacts &facts);

inline bool zh_speech_has_tag(const ZhSpeech &speech, const std::string &marker)
{
    if (speech.source.find(marker) != std::string::npos) return true;
    for (const auto &child : speech.children)
        if (zh_speech_has_tag(child, marker)) return true;
    return false;
}

inline ZhSpeech zh_speech_source(const std::string &key, const std::string &source)
{
    ZhSpeech result;
    result.key = key; result.source = result.canonical = source;
    return result;
}
