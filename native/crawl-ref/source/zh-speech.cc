#include "AppHdr.h"
#include "zh-speech.h"
#include "zh-localization.h"
#include "stringutil.h"
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <map>
#include <regex>

namespace {
struct SpeechDefinition { const char *key, *source, *id; };
#include "zh-speech-catalog.inc"
struct RenderState {
    const monster &mon;
    const ZhSpeechFacts &facts;
    RenderState(const monster &m, const ZhSpeechFacts &f) : mon(m), facts(f) {}
    size_t choice = 0, generated_name = 0;
    bool supported = true;
};

string _parameter_label(string tag)
{
    for (auto &ch : tag)
        ch = isalnum(static_cast<unsigned char>(ch)) || ch == '_'
            ? tolower(static_cast<unsigned char>(ch)) : '_';
    const auto first = tag.find_first_not_of('_');
    tag = first == string::npos ? "" : tag.substr(first, tag.find_last_not_of('_')-first+1);
    tag = std::regex_replace(tag, std::regex("_+"), "_");
    if (tag.empty() || !isalpha(static_cast<unsigned char>(tag[0]))) tag = "tag_"+tag;
    return tag;
}
void _report_missing(const string &identity, const string &reason)
{
    const char *path = std::getenv("DCSS_ZH_ID_MISSING");
    if (path && *path)
    {
        std::ofstream out(path, std::ios::app);
        out << identity << "\t" << reason << "\n";
    }
}
ZhArg _render_node(const ZhSpeech &, RenderState &);

ZhArg _render_pattern(const ZhSpeech &node, const string &identity,
                      const string &source, RenderState &state, size_t offset = 0)
{
    // Match the compiler's structural token lexer. An English sentence after
    // formatting is never used as a lookup key.
    static const std::regex token("(^|\\n)([A-Z_]+(?: [A-Z_]+)*:)|\\[([^\\[\\]]*)\\]|@([^@\\n]+)@");
    std::map<string,int> counts;
    vector<ZhArg> args;
    for (std::sregex_iterator i(source.begin(),source.end(),token), end; i!=end; ++i)
    {
        const auto &match = *i;
        const bool channel = match[2].matched;
        const bool choice = match[3].matched;
        const string tag = match[4].str();
        const string label = channel ? "channel" : choice ? "choice" : _parameter_label(tag);
        const string key = label + "_" + std::to_string(++counts[label]);
        ZhArg value;
        if (channel)
            value = zh_key(key, match[2].str());
        else if (choice)
        {
            const auto alternatives = split_string("|", match[3].str(), false, true);
            if (state.choice >= state.facts.choices.size())
            { state.supported = false; continue; }
            const int selected = state.facts.choices[state.choice++];
            if (selected < 0 || selected >= static_cast<int>(alternatives.size()))
            { state.supported = false; continue; }
            size_t branch_offset = offset + match.position(3);
            for (int n=0; n<selected; ++n) branch_offset += alternatives[n].size()+1;
            value = _render_pattern(node, identity+"."+key+".alt_"+std::to_string(selected),
                                    alternatives[selected], state, branch_offset);
        }
        else
        {
            const string marker = "@"+tag+"@";
            const ZhSpeech *child = nullptr;
            for (size_t n=0; n<node.child_markers.size(); ++n)
                if (node.child_markers[n] == marker
                    && node.child_positions[n] == offset + size_t(match.position()))
                { child = &node.children[n]; break; }
            if (child)
                value = _render_node(*child, state);
            else if (tag == "RANDGEN")
            {
                if (state.generated_name >= state.facts.generated_names.size())
                { state.supported = false; continue; }
                const string name = state.facts.generated_names[state.generated_name++];
                value = {key, ZhArgType::Text, name, name};
            }
            else if (state.facts.nested.count(marker))
                value = _render_node(state.facts.nested.at(marker), state);
            else
                value = zh_speech_actor_arg(key, tag, state.mon, state.facts);
        }
        value.key = key;
        // DB children are prose, even when their protocol marker resembles a
        // name. Keep the catalog's explicit schema for every named argument.
        string lower = tag;
        lowercase(lower);
        const bool name = !channel && !choice && (lower.find("monster")!=string::npos
            || lower.find("something")!=string::npos || lower.find("_name")!=string::npos
            || lower.find("genus")!=string::npos || lower.find("species")!=string::npos
            || lower.find("_god")!=string::npos)
            && lower != "species_insult_adj1" && lower != "species_insult_adj2"
            && lower != "species_insult_noun";
        if (!channel) value.type = name ? ZhArgType::Name : ZhArgType::Text;
        if (!value.supported) _report_missing(identity, "unsupported speech parameter: " + key);
        state.supported = state.supported && value.supported;
        args.push_back(value);
    }
    if (!state.supported)
        return {"body", ZhArgType::Text, source, source, false};
    const auto message = zh_message_values(identity, args);
    return {"body", ZhArgType::Text, message.canonical, message.localized, true};
}

ZhArg _render_node(const ZhSpeech &node, RenderState &state)
{
    if (!node.supported)
    {
        state.supported = false;
        _report_missing("speech.db." + node.key, "embedded Lua or unsupported DB structure");
    }
    // A DB alias has no authored prose, only a structural reference.
    if (node.children.size() == 1 && node.source == node.child_markers.front())
        return _render_node(node.children.front(), state);
    for (const auto &definition : speech_definitions)
        if (node.key == definition.key && node.source == definition.source)
            return _render_pattern(node, definition.id, node.source, state);
    state.supported = false;
    _report_missing("speech.db." + node.key, "missing selected source template: " + replace_all(node.source, "\n", "\\n"));
    return {"body", ZhArgType::Text, node.canonical, node.canonical, false};
}
}

ZhMessage zh_render_speech(const ZhSpeech &speech, const monster &mon,
                          const ZhSpeechFacts &facts, const string &canonical)
{
    RenderState state{mon, facts};
    const auto result = _render_node(speech, state);
    if (!state.supported || state.choice != facts.choices.size()
        || state.generated_name != facts.generated_names.size())
        return zh_message("shout.monster.unsupported", {
            ZhArg("message", ZhArgType::Text, canonical, canonical, false)}, canonical);
    return {"speech.generated", canonical, result.localized};
}
