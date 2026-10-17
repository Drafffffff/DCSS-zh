/**
 * @file
 * @brief Functions used to print information about various game objects.
**/

#include "AppHdr.h"
#include "zh-database.h"
#include "zh-localization.h"
#include "zh-display-name.h"
#include "zh-message.h"

#include "describe.h"

#include <algorithm>
#include <cstdio>
#include <cmath>
#include <iomanip>
#include <numeric>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>

#include "ability.h"
#include "abyss.h"
#include "adjust.h"
#include "areas.h"
#include "art-enum.h"
#include "artefact.h"
#include "branch.h"
#include "cloud.h" // cloud_type_name
#include "clua.h"
#include "colour.h"
#include "command.h"
#include "database.h"
#include "dbg-util.h"
#include "decks.h"
#include "delay.h"
#include "describe-spells.h"
#include "directn.h"
#include "english.h"
#include "env.h"
#include "evoke.h"
#include "tile-env.h"
#include "evoke.h"
#include "fight.h"
#include "ghost.h"
#include "god-abil.h"
#include "god-item.h"
#include "hints.h"
#include "invent.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "items.h"
#include "item-use.h"
#include "jobs.h"
#include "lang-fake.h"
#include "libutil.h"
#include "macro.h"
#include "melee-attack.h" // describe_to_hit
#include "message.h"
#include "mon-behv.h"
#include "mon-cast.h" // mons_spell_range
#include "mon-death.h"
#include "mon-explode.h" // mon_explode_dam/on_death
#include "mon-tentacle.h"
#include "movement.h"
#include "mutation.h" // mutation_name, get_mutation_desc
#include "output.h"
#include "potion.h"
#include "prompt.h"
#include "player.h"
#include "ranged-attack.h" // describe_to_hit
#include "religion.h"
#include "rltiles/tiledef-feat.h"
#include "shout.h"
#include "skills.h"
#include "species.h"
#include "spl-cast.h"
#include "spl-damage.h"
#include "spl-book.h"
#include "spl-goditem.h"
#include "spl-miscast.h"
#include "spl-summoning.h"
#include "spl-util.h"
#include "spl-zap.h"
#include "stash.h"
#include "state.h"
#include "stringutil.h" // to_string on Cygwin
#include "tag-version.h"
#include "terrain.h"
#include "throw.h"
#include "tile-flags.h"
#include "tilepick.h"
#ifdef USE_TILE_LOCAL
 #include "tilereg-crt.h"
 #include "rltiles/tiledef-dngn.h"
#endif
#ifdef USE_TILE
 #include "tileview.h"
#endif
#include "transform.h"
#include "travel.h"
#include "unicode.h"
#include "viewchar.h"
#include "viewmap.h"

using namespace ui;

static command_type _get_action(int key, vector<command_type> actions);
static void _print_bar(int value, int scale, const string &name,
                       ostringstream &result, int base_value = INT_MAX);

static void _describe_mons_to_hit(const monster_info& mi, ostringstream &result);
static string _describe_weapon_brand(const item_def &item);

struct property_descriptor;
static const property_descriptor & _get_artp_desc_data(artefact_prop_type p);

static string _describe_talisman(const item_def &item, bool verbose);
static string _describe_talisman_form(transformation form_type);

int show_description(const string &body, const tile_def *tile)
{
    describe_info inf;
    inf.body << body;
    return show_description(inf, tile);
}

int show_description(const describe_info &inf, const tile_def *tile,
                     bool pretranslated)
{
    auto vbox = make_shared<Box>(Widget::VERT);

    if (!inf.title.empty())
    {
        auto title_hbox = make_shared<Box>(Widget::HORZ);

#ifdef USE_TILE
        if (tile)
        {
            auto icon = make_shared<Image>();
            icon->set_tile(*tile);
            icon->set_margin_for_sdl(0, 10, 0, 0);
            title_hbox->add_child(std::move(icon));
        }
#else
        UNUSED(tile);
#endif

        auto title = make_shared<Text>(pretranslated
            ? formatted_string::parse_string_raw(inf.title)
            : formatted_string::parse_string(inf.title));
        title_hbox->add_child(std::move(title));

        title_hbox->set_cross_alignment(Widget::CENTER);
        title_hbox->set_margin_for_sdl(0, 0, 20, 0);
        title_hbox->set_margin_for_crt(0, 0, 1, 0);
        vbox->add_child(std::move(title_hbox));
    }

    auto desc_sw = make_shared<Switcher>();
    auto more_sw = make_shared<Switcher>();
    desc_sw->current() = 0;
    more_sw->current() = 0;

    string body;
    if (pretranslated)
    {
        // All fields have already selected their display language at source.
        // Joining paragraphs is layout only, with no English reverse matching.
        for (const string &field : {inf.prefix, inf.body.str(), inf.suffix, inf.footer})
            if (!field.empty())
                body += "\n\n" + trimmed_string(field);
    }
    else
        body = process_description(inf, false);
    const string descs[2] =  {
        trimmed_string(body),
        trimmed_string(inf.quote),
    };

    // TODO: maybe use CMD_MENU_CYCLE_MODE
    const char* mores[2] = {
        "[<w>!</w>]: <w>Description</w>|Quote",
        "[<w>!</w>]: Description|<w>Quote</w>",
    };

    for (int i = 0; i < (inf.quote.empty() ? 1 : 2); i++)
    {
        const auto &desc = descs[static_cast<int>(i)];
        auto scroller = make_shared<Scroller>();
        auto fs = pretranslated
            ? formatted_string::parse_string_raw(trimmed_string(desc))
            : formatted_string::parse_string(trimmed_string(desc));
        auto text = make_shared<Text>(fs);
        text->set_wrap_text(true);
        scroller->set_child(text);
        desc_sw->add_child(std::move(scroller));
        more_sw->add_child(make_shared<Text>(pretranslated
            ? formatted_string::parse_string_raw(zh_message(i == 0
                ? "detail.tabs.description" : "detail.tabs.quote").display())
            : formatted_string::parse_string(mores[i])));
    }

    more_sw->set_margin_for_sdl(20, 0, 0, 0);
    more_sw->set_margin_for_crt(1, 0, 0, 0);
    desc_sw->expand_h = false;
    desc_sw->align_x = Widget::STRETCH;
    vbox->add_child(desc_sw);
    if (!inf.quote.empty())
        vbox->add_child(more_sw);

#ifdef USE_TILE_LOCAL
    vbox->max_size().width = tiles.get_crt_font()->char_width()*80;
#endif

    auto popup = make_shared<ui::Popup>(vbox);

    bool done = false;
    int lastch;
    popup->on_keydown_event([&](const KeyEvent& ev) {
        lastch = ev.key();
        if (!inf.quote.empty() && (lastch == '!' || lastch == '^'))
            desc_sw->current() = more_sw->current() = 1 - desc_sw->current();
        else
            done = ui::key_exits_popup(lastch, true);
        return true;
    });

#ifdef USE_TILE_WEB
    tiles.json_open_object();
    if (tile)
    {
        tiles.json_open_object("tile");
        tiles.json_write_int("t", tile->tile);
        tiles.json_write_int("tex", get_tile_texture(tile->tile));
        if (tile->ymax != TILE_Y)
            tiles.json_write_int("ymax", tile->ymax);
        tiles.json_close_object();
    }
    tiles.json_write_string("title", inf.title);
    tiles.json_write_string("prefix", inf.prefix);
    tiles.json_write_string("suffix", inf.suffix);
    tiles.json_write_string("footer", inf.footer);
    tiles.json_write_string("quote", inf.quote);
    tiles.json_write_string("body", inf.body.str());
    tiles.push_ui_layout("describe-generic", 0);
    popup->on_layout_pop([](){ tiles.pop_ui_layout(); });
#endif

    ui::run_layout(std::move(popup), done);

    return lastch;
}

string process_description(const describe_info &inf, bool include_title)
{
    string desc;
    if (!inf.prefix.empty())
        desc += "\n\n" + trimmed_string(filtered_lang(inf.prefix));
    if (!inf.title.empty() && include_title)
        desc += "\n\n" + trimmed_string(filtered_lang(inf.title));
    desc += "\n\n" + trimmed_string(filtered_lang(inf.body.str()));
    if (!inf.suffix.empty())
        desc += "\n\n" + trimmed_string(filtered_lang(inf.suffix));
    if (!inf.footer.empty())
        desc += "\n\n" + trimmed_string(filtered_lang(inf.footer));
    trim_string(desc);
    return desc;
}

// Format an ego or artprop description, wrapping the description within a
// column defined by the length of the name (usually pre-padded with whitespace).
//
// XXX: Assumes the output has at least 80 characters of width. This is true by
//      default in most versions, but it is possible to shrink a webtiles window
//      small enough to make this false. However, that is generally past the
//      point where other parts of the UI also start being unreadable, so this
//      seems acceptable.
static string _format_prop_desc(string prop_name, string prop_desc)
{
    // Inputs are already localized at their source. This is layout only: a
    // generated property sentence must never be reverse-matched as a whole.
    // XXX: It is possible some Android layouts are too small to wrap properly
    //      to 80 characters (and I am currently not certain how to check on my
    //      own), so let's just not do any justification.
#ifdef USE_TILE_LOCAL
    if (tiles.is_using_small_layout())
        return prop_name + prop_desc;
#endif

    const int name_len = strwidth(prop_name);
    linebreak_string(prop_desc, 80 - name_len);
    string padding = string(name_len, ' ');
    string justified_desc = replace_all(prop_desc, "\n", "\n" + padding);

    return prop_name + justified_desc;
}

const char* jewellery_base_ability_string(int subtype)
{
    switch (subtype)
    {
#if TAG_MAJOR_VERSION == 34
    case RING_SUSTAIN_ATTRIBUTES:
    case RING_TELEPORTATION:
    case RING_TELEPORT_CONTROL:
    case AMU_THE_GOURMAND:
    case AMU_HARM:
    case AMU_CONSERVATION:
    case AMU_CONTROLLED_FLIGHT:
    case AMU_INACCURACY:
#endif
    case AMU_GUARDIAN_SPIRIT:
    case AMU_FAITH:
    case AMU_REFLECTION:
    case AMU_WILDSHAPE:
    case AMU_CHEMISTRY:
    case AMU_DISSIPATION:
        return jewellery_effect_name(subtype, true);
    }
    return "";
}

/// How to display props of a given type?
enum class prop_note
{
    /// The raw numeral; e.g "Slay+3", "Int-1"
    numeral,
    /// Plusses and minuses; "rF-", "rC++"
    symbolic,
    /// Don't note the number; e.g. "rMut"
    plain,
};

struct property_descriptor
{
    artefact_prop_type property;
    const char* desc;           // If it contains %d, will be replaced by value.
    prop_note display_type;
};

// TODO: the prop_note values seem at least partly redundant with value_types
// on the regular artefact prop data? Could this be refactored into that
// structure?
static const vector<property_descriptor> & _get_all_artp_desc_data()
{
    static vector<property_descriptor> data =
    {
        { ARTP_AC,
            "It affects your AC (%d).",
            prop_note::numeral },
        { ARTP_EVASION,
            "It affects your evasion (%d).",
            prop_note::numeral },
        { ARTP_STRENGTH,
            "It affects your strength (%d).",
            prop_note::numeral },
        { ARTP_INTELLIGENCE,
            "It affects your intelligence (%d).",
            prop_note::numeral },
        { ARTP_DEXTERITY,
            "It affects your dexterity (%d).",
            prop_note::numeral },
        { ARTP_SLAYING,
            "It affects your accuracy & damage with ranged weapons and melee (%d).",
            prop_note::numeral },
        { ARTP_FIRE,
            "fire",
            prop_note::symbolic },
        { ARTP_COLD,
            "cold",
            prop_note::symbolic },
        { ARTP_ELECTRICITY,
            "It insulates you from electricity.",
            prop_note::plain },
        { ARTP_POISON,
            "It protects you from poison.",
            prop_note::plain },
        { ARTP_NEGATIVE_ENERGY,
            "negative energy",
            prop_note::symbolic },
        { ARTP_WILLPOWER,
            "buggy willpower",
            prop_note::symbolic },
        { ARTP_HP,
            "It affects your health (%d).",
            prop_note::numeral },
        { ARTP_MAGICAL_POWER,
            "It affects your magic capacity (%d).",
            prop_note::numeral },
        { ARTP_SEE_INVISIBLE,
            "It lets you see invisible.",
            prop_note::plain },
        { ARTP_INVISIBLE,
            "It lets you turn invisible.",
            prop_note::plain },
        { ARTP_FLY,
            "It grants you flight.",
            prop_note::plain },
        { ARTP_BLINK,
            "It lets you blink.",
            prop_note::plain },
        { ARTP_NOISE,
            "It may make a loud noise when swung.",
            prop_note::plain },
        { ARTP_PREVENT_SPELLCASTING,
            "It prevents spellcasting.",
            prop_note::plain },
        { ARTP_PREVENT_TELEPORTATION,
            "It prevents most forms of teleportation.",
            prop_note::plain },
        { ARTP_ANGRY,
            "It berserks you when you make melee attacks (%d% chance).",
            prop_note::plain },
        { ARTP_CLARITY,
            "It protects you from confusion, rage, mesmerisation and fear.",
            prop_note::plain },
        { ARTP_CONTAM,
            "It causes magical contamination when unequipped.",
            prop_note::plain },
        { ARTP_RMSL,
            "It protects you from missiles.",
            prop_note::plain },
        { ARTP_REGENERATION,
            "It increases your rate of health regeneration.",
            prop_note::symbolic },
        { ARTP_RCORR,
            "It protects you from acid and corrosion.",
            prop_note::plain },
        { ARTP_RMUT,
            "It protects you from mutation.",
            prop_note::plain },
        { ARTP_CORRODE,
            "It may corrode you when you take damage.",
            prop_note::plain },
        { ARTP_DRAIN,
            "It drains your maximum health when unequipped.",
            prop_note::plain },
        { ARTP_SLOW,
            "It may slow you when you take damage.",
            prop_note::plain },
        { ARTP_FRAGILE,
            "It will be destroyed if unequipped.",
            prop_note::plain },
        { ARTP_SHIELDING,
            "It affects your SH (%d).",
            prop_note::numeral },
        { ARTP_HARM,
            "It increases damage dealt and taken.",
            prop_note::plain },
        { ARTP_RAMPAGING,
            "It causes one to take an extra step when moving towards enemies, "
            "briefly stunning them if this results in an attack.",
            prop_note::plain },
        { ARTP_STEALTH,
            "buggy stealth",
            prop_note::symbolic },
        { ARTP_ARCHMAGI,
            "It increases the power of your magical spells.",
            prop_note::plain },
        { ARTP_ENHANCE_CONJ,
            "It increases the power of your Conjurations spells.",
            prop_note::plain },
        { ARTP_ENHANCE_HEXES,
            "It increases the power of your Hexes spells.",
            prop_note::plain },
        { ARTP_ENHANCE_SUMM,
            "It increases the power of your Summonings spells.",
            prop_note::plain },
        { ARTP_ENHANCE_NECRO,
            "It increases the power of your Necromancy spells.",
            prop_note::plain },
        { ARTP_ENHANCE_TLOC,
            "It increases the power of your Translocations spells.",
            prop_note::plain },
        { ARTP_ENHANCE_FIRE,
            "It increases the power of your Fire spells.",
            prop_note::plain },
        { ARTP_ENHANCE_ICE,
            "It increases the power of your Ice spells.",
            prop_note::plain },
        { ARTP_ENHANCE_AIR,
            "It increases the power of your Air spells.",
            prop_note::plain },
        { ARTP_ENHANCE_EARTH,
            "It increases the power of your Earth spells.",
            prop_note::plain },
        { ARTP_ENHANCE_ALCHEMY,
            "It increases the power of your Alchemy spells.",
            prop_note::plain },
        { ARTP_ENHANCE_FORGECRAFT,
            "It increases the power of your Forgecraft spells.",
            prop_note::plain },
        { ARTP_ACROBAT,
            "It increases your evasion after moving or waiting.",
            prop_note::plain },
        { ARTP_MANA_REGENERATION,
            "It increases your rate of magic regeneration.",
            prop_note::symbolic },
        { ARTP_WIZARDRY,
            "It increases the success rate of your magical spells.",
            prop_note::plain },
        { ARTP_SILENCE,
            "It may silence you when you take damage.",
            prop_note::plain },
        { ARTP_BANE,
            "It inflicts you with a random bane when you equip it.",
            prop_note::plain },
    };
    return data;
}

static string _randart_prop_abbrev(artefact_prop_type prop, int val)
{
    const property_descriptor &ann = _get_artp_desc_data(prop);
    switch (ann.display_type)
    {
    case prop_note::numeral: // e.g. AC+4
        return make_stringf("%s%+d", artp_name(prop), val);
    case prop_note::symbolic: // e.g. F++
    {
        const char symbol = val > 0 ? '+' : '-';
        if (val > 4)
            return make_stringf("%s%c%d", artp_name(prop), symbol, abs(val));
        else
            return make_stringf("%s%s", artp_name(prop), string(abs(val), symbol).c_str());
    }
    case prop_note::plain: // e.g. rPois or SInv
        return artp_name(prop);
    }
    return "buggy";
}

static const vector<artefact_prop_type> artprop_annotation_order =
{
    // (Generally) negative attributes
    // These come first, so they don't get chopped off!
    ARTP_PREVENT_SPELLCASTING,
    ARTP_PREVENT_TELEPORTATION,
    ARTP_BANE,
    ARTP_CONTAM,
    ARTP_ANGRY,
    ARTP_NOISE,
    ARTP_HARM,
    ARTP_RAMPAGING,
    ARTP_ACROBAT,
    ARTP_CORRODE,
    ARTP_DRAIN,
    ARTP_SLOW,
    ARTP_SILENCE,
    ARTP_FRAGILE,

    // Evokable abilities come second
    ARTP_BLINK,
    ARTP_INVISIBLE,
    ARTP_FLY,

    // Resists, also really important
    ARTP_ELECTRICITY,
    ARTP_POISON,
    ARTP_FIRE,
    ARTP_COLD,
    ARTP_NEGATIVE_ENERGY,
    ARTP_WILLPOWER,
    ARTP_REGENERATION,
    ARTP_MANA_REGENERATION,
    ARTP_RMUT,
    ARTP_RCORR,

    // Quantitative attributes
    ARTP_HP,
    ARTP_MAGICAL_POWER,
    ARTP_WIZARDRY,
    ARTP_AC,
    ARTP_EVASION,
    ARTP_STRENGTH,
    ARTP_INTELLIGENCE,
    ARTP_DEXTERITY,
    ARTP_SLAYING,
    ARTP_SHIELDING,

    // Qualitative attributes (and Stealth)
    ARTP_SEE_INVISIBLE,
    ARTP_STEALTH,
    ARTP_CLARITY,
    ARTP_RMSL,

    // spell enhancers
    ARTP_ARCHMAGI,
    ARTP_ENHANCE_CONJ,
    ARTP_ENHANCE_HEXES,
    ARTP_ENHANCE_SUMM,
    ARTP_ENHANCE_NECRO,
    ARTP_ENHANCE_FORGECRAFT,
    ARTP_ENHANCE_TLOC,
    ARTP_ENHANCE_FIRE,
    ARTP_ENHANCE_ICE,
    ARTP_ENHANCE_AIR,
    ARTP_ENHANCE_EARTH,
    ARTP_ENHANCE_ALCHEMY,
};

static vector<string> _randart_propnames(const item_def& item,
                                         bool no_comma = false)
{
    vector<string> propnames;

    if (!item.is_identified())
        return propnames;

    artefact_properties_t  proprt;
    artefact_desc_properties(item, proprt);

    const unrandart_entry *entry = nullptr;
    if (is_unrandom_artefact(item))
    {
        entry = get_unrand_entry(item.unrand_idx);
        if (testbits(item.flags, ISFLAG_CHAOTIC))
            propnames.push_back("chaos,");
    }
    const bool skip_ego = is_unrandom_artefact(item)
                          && entry && entry->flags & UNRAND_FLAG_SKIP_EGO;

    // For randart jewellery, note the base jewellery type if it's not
    // covered by artefact_desc_properties()
    if (item.base_type == OBJ_JEWELLERY && item.is_identified() && !skip_ego)
    {
        const char* type = jewellery_base_ability_string(item.sub_type);
        if (*type)
            propnames.push_back(type);
    }
    else if (!skip_ego)
    {
        string ego;
        if (item.base_type == OBJ_WEAPONS)
            ego = weapon_brand_name(item, true);
        else if (item.base_type == OBJ_ARMOUR)
            ego = armour_ego_name(item, true);
        else if (item.base_type == OBJ_GIZMOS)
            ego = gizmo_effect_name(item.brand);
        if (!ego.empty())
        {
            // XXX: Ugly hack for adding a comma if needed.
            bool extra_props = false;
            for (const artefact_prop_type &other_prop : artprop_annotation_order)
                if (other_prop != ARTP_BRAND)
                {
                    extra_props = true;
                    break;
                }

            if (!no_comma && extra_props
                || is_unrandom_artefact(item)
                   && entry && entry->inscrip != nullptr)
            {
                ego += ",";
            }

            propnames.push_back(ego);
        }
    }

    if (is_unrandom_artefact(item) && entry && entry->inscrip != nullptr)
        propnames.push_back(entry->inscrip);

    for (const artefact_prop_type &prop : artprop_annotation_order)
    {
        const int val = proprt[prop];
        if (val == 0)
            continue;

        propnames.push_back(_randart_prop_abbrev(prop, val));
    }

    return propnames;
}

string artefact_inscription(const item_def& item)
{
    if (item.base_type == OBJ_BOOKS)
        return "";

    const vector<string> propnames = _randart_propnames(item);

    string insc = comma_separated_line(propnames.begin(), propnames.end(),
                                       " ", " ");
    if (!insc.empty() && insc[insc.length() - 1] == ',')
        insc.erase(insc.length() - 1);
    return insc;
}

void add_inscription(item_def &item, string inscrip)
{
    if (!item.inscription.empty())
    {
        if (ends_with(item.inscription, ","))
            item.inscription += " ";
        else
            item.inscription += ", ";
    }

    item.inscription += inscrip;
}

static const char* _jewellery_base_ability_description(int subtype)
{
    switch (subtype)
    {
#if TAG_MAJOR_VERSION == 34
    case RING_SUSTAIN_ATTRIBUTES:
        return "It sustains your strength, intelligence and dexterity.";
    case RING_TELEPORTATION:
        return "It may teleport you next to monsters.";
    case RING_TELEPORT_CONTROL:
        return "It can be evoked for teleport control.";
    case AMU_THE_GOURMAND:
        return "It allows you to eat raw meat even when not hungry.";
    case AMU_HARM:
        return "It increases damage dealt and taken.";
    case AMU_CONSERVATION:
        return "It protects your inventory from destruction.";
    case AMU_CONTROLLED_FLIGHT:
        return "It allows you to control your flight when levitating.";
    case AMU_INACCURACY:
        return "It reduces the accuracy of all your attacks.";
#endif
    case AMU_GUARDIAN_SPIRIT:
        return "It causes incoming damage to be divided between your reserves "
               "of health and magic.";
    case AMU_FAITH:
        return "It allows you to gain divine favour quickly.";
    case AMU_REFLECTION:
        return "It reflects blocked missile attacks.";
    case AMU_WILDSHAPE:
        return "It improves your skill with shapeshifting (+5).";
    case AMU_CHEMISTRY:
        return "It restores some MP whenever you drink a potion and also enhances "
               "your alchemy spells.";
    case AMU_DISSIPATION:
        return "It reduces the duration of hostile enchantments and decays "
               "magical contamination more quickly.";
    }
    return "";
}

static const unordered_map<artefact_prop_type, property_descriptor, std::hash<int>> & _get_artp_desc_data_map()
{
    static bool init = false;
    static unordered_map<artefact_prop_type, property_descriptor, std::hash<int>> data_map;
    if (!init)
    {
        for (const auto &d : _get_all_artp_desc_data())
            data_map[d.property] = d;
        init = true;
    }
    return data_map;
}

static const property_descriptor & _get_artp_desc_data(artefact_prop_type p)
{
    const auto &data_map = _get_artp_desc_data_map();
    ASSERT(data_map.count(p));
    return data_map.at(p);
}

static const int MAX_ARTP_NAME_LEN = 10;

static string _padded_artp_name(artefact_prop_type prop, int val)
{
    // XX it would be nice to use a dynamic pad, but annoyingly, the constant
    // is used separately for egos.
    return make_stringf("%-*s", MAX_ARTP_NAME_LEN + 1,
        (_randart_prop_abbrev(prop, val) + ":").c_str());
}

void desc_randart_props(const item_def &item, vector<string> &lines)
{
    artefact_properties_t  proprt;
    artefact_desc_properties(item, proprt);

    if (!item.is_identified())
        return;

    for (artefact_prop_type prop : artprop_annotation_order)
    {
        const int stval = proprt[prop];
        if (stval == 0)
            continue;

        // these two have some custom string replacement
        if (prop == ARTP_WILLPOWER)
        {
            const bool strong = stval < -1 || stval > 1;
            const string verb = stval < 0 ? "decreases" : "increases";
            const auto message = zh_message("artifact.property.willpower",
                {zh_text("degree", strong ? "greatly " : "",
                                  strong ? "大幅" : ""),
                 zh_text("verb", verb, stval < 0 ? "降低" : "提升")},
                make_stringf("It %s%s your willpower.",
                    strong ? "greatly " : "", verb.c_str()));
            lines.push_back(_format_prop_desc(
                _padded_artp_name(ARTP_WILLPOWER, stval), message.display()));
            continue;
        }
        else if (prop == ARTP_STEALTH)
        {
            const bool strong = stval < -1 || stval > 1;
            const string degree = strong ? "much " : "";
            const string direction = stval < 0 ? "less" : "more";
            const string effect = degree + direction;
            const auto message = zh_message("artifact.property.stealth",
                {zh_text("effect", effect,
                         stval < 0 ? (strong ? "大幅降低" : "降低")
                                   : (strong ? "大幅提升" : "提升"))},
                make_stringf("It makes you %s%s stealthy.", degree.c_str(),
                             direction.c_str()));
            lines.push_back(_format_prop_desc(
                _padded_artp_name(ARTP_STEALTH, stval), message.display()));
            continue;
        }
        else if (prop == ARTP_ANGRY)
        {
            const auto message = zh_message("artifact.property.angry",
                {zh_integer("chance", stval)},
                make_stringf("It berserks you when you make melee attacks (%d%% chance).",
                             stval));
            lines.push_back(_format_prop_desc(
                _padded_artp_name(ARTP_ANGRY, stval), message.display()));
            continue;
        }

        // otherwise, we use desc.desc in some form
        const property_descriptor& desc = _get_artp_desc_data(prop);
        string sdesc = desc.desc;

        if (sdesc.find("%d") != string::npos)
        {
            const string sign = stval < 0 ? "-" : "+";
            const string value = make_stringf("%d", abs(stval));
            const char *stat = prop == ARTP_AC ? "AC" :
                prop == ARTP_EVASION ? "evasion" :
                prop == ARTP_STRENGTH ? "strength" :
                prop == ARTP_INTELLIGENCE ? "intelligence" :
                prop == ARTP_DEXTERITY ? "dexterity" :
                prop == ARTP_SLAYING ? "accuracy & damage with ranged weapons and melee" :
                prop == ARTP_HP ? "health" :
                prop == ARTP_MAGICAL_POWER ? "magic capacity" : "SH";
            const string canonical = replace_all(sdesc, "%d", sign + value);
            sdesc = zh_message("artifact.property.numeric",
                {zh_text("stat", stat,
                    prop == ARTP_AC ? "护甲" :
                    prop == ARTP_EVASION ? "闪避" :
                    prop == ARTP_STRENGTH ? "力量" :
                    prop == ARTP_INTELLIGENCE ? "智力" :
                    prop == ARTP_DEXTERITY ? "敏捷" :
                    prop == ARTP_SLAYING ? "远程武器与近战武器的命中和伤害" :
                    prop == ARTP_HP ? "生命值" :
                    prop == ARTP_MAGICAL_POWER ? "魔法容量" : "格挡"),
                 zh_text("sign", sign, sign),
                 zh_integer("value", abs(stval))}, canonical).display();
        }

        if (desc.display_type == prop_note::symbolic
            && desc.property != ARTP_REGENERATION // symbolic, but no text modification
            && desc.property != ARTP_MANA_REGENERATION)
        {
            // for symbolic props, desc.desc is just the resist name, need
            // to fill in to get a complete sentence
            const int idx = max(min(stval + 3, 6), 0);

            const char* prefixes[] =
            {
                "It makes you extremely vulnerable to ", // XX these two are worded badly? are they even used?
                "It makes you very vulnerable to ",
                "It makes you vulnerable to ",
                "Buggy descriptor!",
                "It protects you from ",
                "It greatly protects you from ",
                "It renders you almost immune to "
            };
            const string resistance = sdesc;
            const string localized_resistance = prop == ARTP_FIRE ? "火焰伤害" :
                prop == ARTP_COLD ? "寒冷伤害" : "负能量伤害";
            const string canonical = string(prefixes[idx]) + resistance + '.';
            const string localized_effect = idx == 0 ? "使你极易受到" :
                idx == 1 ? "使你很容易受到" : idx == 2 ? "使你容易受到" :
                idx == 3 ? "会影响你对" : idx == 4 ? "保护你免受" :
                idx == 5 ? "大幅保护你免受" : "使你几乎免疫";
            sdesc = zh_message("artifact.property.resistance",
                {zh_text("effect", prefixes[idx], localized_effect),
                 zh_text("resistance", resistance, localized_resistance)},
                canonical).display();
        }
        else if (desc.display_type == prop_note::plain
                 || desc.property == ARTP_REGENERATION
                 || desc.property == ARTP_MANA_REGENERATION)
            sdesc = zh_source("detail.artifact.property", desc.desc);

        lines.push_back(_format_prop_desc(_padded_artp_name(desc.property, stval), sdesc.c_str()));
    }
}

static string _desc_randart_jewel(const item_def &item)
{
    // why are these specially hardcoded?
    const char* type = jewellery_base_ability_string(item.sub_type);
    const char* desc = _jewellery_base_ability_description(item.sub_type);
    if (!*desc)
        return "";
    const string localized_desc = zh_source("detail.artifact.jewel", desc);
    if (!*type)
    {
        // if this case happens, the formatting can get mixed with
        // DBRANDS in weird ways
        return localized_desc;
    }
    return _format_prop_desc(make_stringf("%-*s", MAX_ARTP_NAME_LEN + 1,
                              (string(type) + ":").c_str()), localized_desc);
}

static string _randart_descrip(const item_def &item)
{
    vector<string> lines;

    // Give a short description of the base type, for base types with no
    // corresponding ARTP.
    if (item.base_type == OBJ_JEWELLERY && item.is_identified())
    {
        const string jewel_desc = _desc_randart_jewel(item);
        if (!jewel_desc.empty())
            lines.push_back(jewel_desc);
    }

    desc_randart_props(item, lines);
    return join_strings(lines.begin(), lines.end(), "\n");
}

static string _format_dbrand(string dbrand)
{
    vector<string> out;

    dbrand = zh_source("detail.artifact.unrand", dbrand.c_str());
    vector<string> lines = split_string("\n", dbrand);
    for (const auto &l : lines)
    {
        vector<string> brand = split_string(":", l, true, false, 1);
        if (brand.size() == 0)
            continue;
        if (brand.size() == 1)
            out.push_back(brand[0]);
        else
        {
            ASSERT(brand.size() == 2);
            const string &desc = brand[1];
            const int prefix_len = max(MAX_ARTP_NAME_LEN + 1, (int)brand[0].size() + 2);
            const string pre = padded_str(brand[0] + ":", prefix_len);
            out.push_back(_format_prop_desc(pre, desc));
        }
    }
    return join_strings(out.begin(), out.end(), "\n");
}

// If item is an unrandart with a DESCRIP field, return its contents.
// Otherwise, return "".
static string _artefact_descrip(const item_def &item)
{
    if (!is_artefact(item))
        return "";

    ostringstream out;
    if (is_unrandom_artefact(item))
    {
        bool need_newline = false;
        auto entry = get_unrand_entry(item.unrand_idx);
        // Weapons have brands added earlier.
        if (entry->dbrand
            && item.base_type != OBJ_WEAPONS
            && item.base_type != OBJ_STAVES)
        {
            out << _format_dbrand(entry->dbrand);
            need_newline = true;
        }
        if (entry->descrip)
        {
            out << (need_newline ? "\n" : "") << _format_dbrand(entry->descrip);
            need_newline = true;
        }
        if (!_randart_descrip(item).empty())
            out << (need_newline ? "\n" : "") << _randart_descrip(item);
    }
    else
        out << _randart_descrip(item);

    return out.str();
}

static const char *trap_names[] =
{
#if TAG_MAJOR_VERSION == 34
    "harlequin's", "archmage's", "spear",
#endif
#if TAG_MAJOR_VERSION > 34
    "tyrant's",
    "archmage's",
    "harlequin's",
    "devourer's",
    "dispersal",
    "teleport",
#endif
    "permanent teleport",
    "alarm",
#if TAG_MAJOR_VERSION == 34
    "tyrant's", "bolt",
#endif
    "net",
    "Zot",
#if TAG_MAJOR_VERSION == 34
    "devourer's",
#endif
    "shaft",
    "passage",
    "pressure plate",
    "web",
#if TAG_MAJOR_VERSION == 34
    "gas", "teleport", "shadow", "dormant shadow", "dispersal"
#endif
};

string trap_name(trap_type trap)
{
    COMPILE_CHECK(ARRAYSZ(trap_names) == NUM_TRAPS);

    if (trap >= 0 && trap < NUM_TRAPS)
        return trap_names[trap];
    return "";
}

string full_trap_name(trap_type trap)
{
    string basename = trap_name(trap);
    switch (trap)
    {
    case TRAP_GOLUBRIA:
        return basename + " of Golubria";
    case TRAP_PLATE:
    case TRAP_WEB:
    case TRAP_SHAFT:
        return basename;
    default:
        return basename + " trap";
    }
}

int str_to_trap(const string &s)
{
    // "Zot trap" is capitalised in trap_names[], but the other trap
    // names aren't.
    const string tspec = lowercase_string(s);

    // allow a couple of synonyms
    if (tspec == "random" || tspec == "any")
        return TRAP_RANDOM;

    for (int i = 0; i < NUM_TRAPS; ++i)
        if (tspec == lowercase_string(trap_names[i]))
            return i;

    return -1;
}

/**
 * How should this panlord be described?
 *
 * @param name   The panlord's name; used as a seed for its appearance.
 * @param flying Whether the panlord can fly.
 * @returns a string including a description of its head, its body, its flight
 *          mode (if any), and how it smells or looks.
 */
static string _describe_demon(const string& name, bool flying, colour_t colour)
{
    const uint32_t seed = hash32(&name[0], name.size());
    #define HRANDOM_ELEMENT(arr, id) arr[hash_with_seed(ARRAYSZ(arr), seed, id)]

    static const char* body_types[] =
    {
        "armoured",
        "vast, spindly",
        "fat",
        "obese",
        "muscular",
        "spiked",
        "splotchy",
        "slender",
        "tentacled",
        "emaciated",
        "bug-like",
        "skeletal",
        "mantis",
        "slithering",
    };

    static const char* wing_names[] =
    {
        "with small, bat-like wings",
        "with bony wings",
        "with sharp, metallic wings",
        "with the wings of a moth",
        "with thin, membranous wings",
        "with dragonfly wings",
        "with large, powerful wings",
        "with fluttering wings",
        "with great, sinister wings",
        "with hideous, tattered wings",
        "with sparrow-like wings",
        "with hooked wings",
        "with strange knobs attached",
        "which hovers in mid-air",
        "with sacs of gas hanging from its back",
    };

    const char* head_names[] =
    {
        "a cubic structure in place of a head",
        "a brain for a head",
        "a hideous tangle of tentacles for a mouth",
        "the head of an elephant",
        "an eyeball for a head",
        "wears a helmet over its head",
        "a horn in place of a head",
        "a thick, horned head",
        "the head of a horse",
        "a vicious glare",
        "snakes for hair",
        "the face of a baboon",
        "the head of a mouse",
        "a ram's head",
        "the head of a rhino",
        "eerily human features",
        "a gigantic mouth",
        "a mass of tentacles growing from its neck",
        "a thin, worm-like head",
        "huge, compound eyes",
        "the head of a frog",
        "an insectoid head",
        "a great mass of hair",
        "a skull for a head",
        "a cow's skull for a head",
        "the head of a bird",
        "a large fungus growing from its neck",
        "an ominous eye at the end of a thin stalk",
        "a face from nightmares",
    };

    static const char* misc_descs[] =
    {
        " It seethes with hatred of the living.",
        " Tiny orange flames dance around it.",
        " Tiny purple flames dance around it.",
        " It is surrounded by a weird haze.",
        " It glows with a malevolent light.",
        " It looks incredibly angry.",
        " It oozes with slime.",
        " It dribbles constantly.",
        " Mould grows all over it.",
        " Its body is covered in fungus.",
        " It is covered with lank hair.",
        " It looks diseased.",
        " It looks as frightened of you as you are of it.",
        " It moves in a series of hideous convulsions.",
        " It moves with an unearthly grace.",
        " It leaves a glistening oily trail.",
        " It shimmers before your eyes.",
        " It is surrounded by a brilliant glow.",
        " It radiates an aura of extreme power.",
        " It seems utterly heartbroken.",
        " It seems filled with irrepressible glee.",
        " It constantly shivers and twitches.",
        " Blue sparks crawl across its body.",
        " It seems uncertain.",
        " A cloud of flies swarms around it.",
        " The air around it ripples with heat.",
        " Crystalline structures grow on everything near it.",
        " It appears supremely confident.",
        " Its skin is covered in a network of cracks.",
        " Its skin has a disgusting oily sheen.",
        " It seems somehow familiar.",
        " It is somehow always in shadow.",
        " It is difficult to look away.",
        " It is constantly speaking in tongues.",
        " It babbles unendingly.",
        " Its body is scourged by damnation.",
        " Its body is extensively scarred.",
        " You find it difficult to look away.",
        " Oddly mechanical noises accompany its jarring movements.",
        " Its skin looks unnervingly wrinkled.",
    };

    static const char* smell_descs[] =
    {
        " It smells of brimstone.",
        " It is surrounded by a sickening stench.",
        " It smells of rotting flesh.",
        " It stinks of death.",
        " It stinks of decay.",
        " It smells delicious!",
    };

    ostringstream description;
    description << "One of the many lords of Pandemonium, " << name << " has ";

    description << article_a(HRANDOM_ELEMENT(body_types, 2));
    // ETC_RANDOM is also possible, handled later
    if (colour >= 0 && colour < NUM_TERM_COLOURS)
        description << " " << colour_to_str(colour, true);
    description << " body ";

    if (flying)
    {
        description << HRANDOM_ELEMENT(wing_names, 3);
        description << " ";
    }

    description << "and ";
    description << HRANDOM_ELEMENT(head_names, 1) << ".";

    if (!hash_with_seed(5, seed, 4) && you.can_smell()) // 20%
        description << HRANDOM_ELEMENT(smell_descs, 5);

    if (hash_with_seed(2, seed, 6)) // 50%
        description << HRANDOM_ELEMENT(misc_descs, 6);

    if (colour == ETC_RANDOM)
        description << " It changes colour whenever you look at it.";

    return description.str();
}

/**
 * Describe a given mutant beast's tier.
 *
 * @param tier      The mutant_beast_tier of the beast in question.
 * @return          A string describing the tier; e.g.
 *              "It is a juvenile, out of the larval stage but still below its
 *              mature strength."
 */
static string _describe_mutant_beast_tier(int tier)
{
    static const string tier_descs[] = {
        "It is of an unusually buggy age.",
        "It is larval and weak, freshly emerged from its mother's pouch.",
        "It is a juvenile, no longer larval but below its mature strength.",
        "It is mature, stronger than a juvenile but weaker than its elders.",
        "It is an elder, stronger than mature beasts.",
        "It is a primal beast, the most powerful of its kind.",
    };
    COMPILE_CHECK(ARRAYSZ(tier_descs) == NUM_BEAST_TIERS);

    ASSERT_RANGE(tier, 0, NUM_BEAST_TIERS);
    return zh_message(make_stringf("monster.mutant.tier.%d", tier)).display();
}


/**
 * Describe a given mutant beast's facets.
 *
 * @param facets    A vector of the mutant_beast_facets in question.
 * @return          A string describing the facets; e.g.
 *              "It flies and flits around unpredictably, and its breath
 *               smoulders ominously."
 */
static string _describe_mutant_beast_facets(const CrawlVector &facets)
{
    static const string facet_descs[] = {
        " seems unusually buggy.",
        " sports a set of venomous tails",
        " flies swiftly and unpredictably",
        "s breath smoulders ominously",
        " is covered with eyes and tentacles",
        " flickers and crackles with electricity",
        " is covered in dense fur and muscle",
    };
    COMPILE_CHECK(ARRAYSZ(facet_descs) == NUM_BEAST_FACETS);

    if (facets.size() == 0)
        return "";

    if (zh_language_enabled())
    {
        static const char* facet_localization[] = {
            " seems unusually buggy.",
            " sports a set of venomous tails",
            " flies swiftly and unpredictably",
            "s breath smoulders ominously",
            " is covered with eyes and tentacles",
            " flickers and crackles with electricity",
            " is covered in dense fur and muscle",
        };
        vector<string> localized;
        for (const auto &sv : facets)
        {
            const int facet = sv.get_int();
            ASSERT_RANGE(facet, 0, NUM_BEAST_FACETS);
            localized.emplace_back(zh_word("monster.mutant.facet.",
                                           facet_localization[facet]));
        }
        string result = "它";
        for (size_t i = 0; i < localized.size(); ++i)
        {
            if (i)
                result += "，";
            result += localized[i];
        }
        return result + "。";
    }

    return "It" + comma_separated_fn(begin(facets), end(facets),
                      [] (const CrawlStoreValue &sv) -> string {
                          const int facet = sv.get_int();
                          ASSERT_RANGE(facet, 0, NUM_BEAST_FACETS);
                          return facet_descs[facet];
                      }, ", and it", ", it")
           + ".";

}

/**
 * Describe a given mutant beast's special characteristics: its tier & facets.
 *
 * @param mi    The player-visible information about the monster in question.
 * @return      A string describing the monster; e.g.
 *              "It is a juvenile, out of the larval stage but still below its
 *              mature strength. It flies and flits around unpredictably, and
 *              its breath has a tendency to ignite when angered."
 */
static string _describe_mutant_beast(const monster_info &mi)
{
    const int xl = mi.props[MUTANT_BEAST_TIER].get_short();
    const int tier = mutant_beast_tier(xl);
    const CrawlVector facets = mi.props[MUTANT_BEAST_FACETS].get_vector();
    return _describe_mutant_beast_facets(facets)
           + " " + _describe_mutant_beast_tier(tier);
}

/**
 * Is the item associated with some specific training goal?  (E.g. mindelay)
 *
 * @return the goal, or 0 if there is none, scaled by 10.
 */
static int _item_training_target(const item_def &item)
{
    const int throw_dam = property(item, PWPN_DAMAGE);
    if (item.base_type == OBJ_WEAPONS || item.base_type == OBJ_STAVES)
        return weapon_min_delay_skill(item) * 10;
    if (item.base_type == OBJ_MISSILES && is_throwable(&you, item))
        return (((10 + throw_dam / 2) - FASTEST_PLAYER_THROWING_SPEED) * 2) * 10;
    if (item.base_type == OBJ_TALISMANS)
    {
        // Train to minimum level if below it, else maximum level.
        int current_skill = get_form(form_for_talisman(item))->get_level(10);
        int min_skill = get_form(form_for_talisman(item))->min_skill * 10;
        int max_skill = get_form(form_for_talisman(item))->max_skill * 10;
        return current_skill < min_skill ? min_skill : max_skill;
    }
    if (item.base_type == OBJ_BAUBLES)
        return get_form(transformation::flux)->min_skill * 10;
    return 0;
}

// Description and quote databases have their own source-keyed translation
// tables. Read the canonical source under ZhTranslationPause, then use the
// selected database text directly. An untranslated row is an explicit whole
// English fallback so it never re-enters the legacy sentence matcher.
static string _detail_english_fallback(const string &text)
{
    return zh_message("detail.english_fallback", {
        ZhArg{"text", ZhArgType::Text, text, text, false}}).display();
}

static string _detail_database_text(const string &key, bool quote = false)
{
    string canonical;
    {
        ZhTranslationPause pause;
        canonical = quote ? getQuoteString(key) : getLongDescription(key);
    }
    const string selected = quote ? getQuoteString(key) : getLongDescription(key);
    if (canonical.empty() || !zh_language_enabled() || selected != canonical)
        return selected;

    return _detail_english_fallback(canonical);
}

/**
 * Does an item improve with training some skill?
 *
 * @return the skill, or SK_NONE if there is none. Note: SK_NONE is *not* 0.
 */
static skill_type _item_training_skill(const item_def &item)
{
    if (item.base_type == OBJ_WEAPONS || item.base_type == OBJ_STAVES)
        return item_attack_skill(item);
    if (is_shield(item))
        return SK_SHIELDS; // shields are armour, so do shields before armour
    if (item.base_type == OBJ_ARMOUR)
        return SK_ARMOUR;
    if (item.base_type == OBJ_MISSILES && is_throwable(&you, item))
        return SK_THROWING;
    if (item.base_type == OBJ_TALISMANS || item.base_type == OBJ_BAUBLES)
        return SK_SHAPESHIFTING;
    if (item_ever_evokable(item)) // not very accurate
        return SK_EVOCATIONS;
    return SK_NONE;
}

/**
 * Return whether the character is below a plausible training target for an
 * item.
 *
 * @param item the item to check.
 * @param ignore_current if false, return false if there already is a higher
 *        target set for this skill.
 */
static bool _is_below_training_target(const item_def &item, bool ignore_current)
{
    if (!crawl_state.need_save || is_useless_item(item))
        return false;

    const skill_type skill = _item_training_skill(item);
    if (skill == SK_NONE)
        return false;

    const int target = min(_item_training_target(item), 270);

    return target && !is_useless_skill(skill)
       && you.skill(skill, 10, false, false) < target
       && (ignore_current || you.get_training_target(skill) < target);
}


/**
 * Produce the "Your skill:" line for item descriptions where specific skill targets
 * are relevant (weapons, missiles)
 *
 * @param skill the skill to look at.
 * @param show_target_button whether to show the button for setting a skill target.
 * @param scaled_target a target, scaled by 10, to use when describing the button.
 */
static string _your_skill_desc(skill_type skill, bool show_target_button,
                               int scaled_target, string padding = "")
{
    if (!crawl_state.need_save || skill == SK_NONE)
        return "";
    const int you_skill_temp = you.skill(skill, 10);
    const int you_skill = you.skill(skill, 10, false, false);
    const string skill_prefix = you_skill_temp != you_skill ? "(base) " : "";
    const string localized_prefix = you_skill_temp != you_skill ? "（基础）" : "";
    const auto level = zh_number("skill_level", you_skill / 10.0, 1);
    const auto prefix = zh_text("skill_prefix", skill_prefix, localized_prefix);
    const auto pad = zh_text("padding", padding, padding);
    if (show_target_button
        && you.get_training_target(skill) < min(scaled_target, 270))
    {
        const string skill_name_en = skill_name(skill);
        const string skill_name_zh = zh_lookup_exact(skill_name_en);
        return zh_message("item.skill.current_with_target", {
            prefix, pad, level,
            zh_number("target_level", min(scaled_target, 270) / 10.0, 1),
            ZhArg{"skill", ZhArgType::Name, skill_name_en, skill_name_zh,
                  skill_name_zh != skill_name_en}}).display();
    }
    return zh_message("item.skill.current", {prefix, pad, level}).display();
}

/**
 * Produce a description of a skill target for items where specific targets are
 * relevant.
 *
 * @param skill the skill to look at.
 * @param scaled_target a skill level target, scaled by 10.
 * @param training a training value, from 0 to 100. Need not be the actual training
 * value.
 */
static string _skill_target_desc(skill_type skill, int scaled_target,
                                        unsigned int training)
{
    string description = "";
    scaled_target = min(scaled_target, 270);

    const bool max_training = (training == 100);
    const bool hypothetical = !crawl_state.need_save ||
                                    (training != you.training[skill]);

    const skill_diff diffs = skill_level_to_diffs(skill,
                                (double) scaled_target / 10, training, false);
    const int level_diff = xp_to_level_diff(diffs.experience / 10, 10);

    const string verb = hypothetical ? "would " : "";
    const string xp_comparison =
        (you.experience_level + (level_diff + 9) / 10) > 27
            ? "the equivalent of" : "about";
    ZhArg xp_comparison_arg = zh_word_arg(
        "xp_comparison", "skill.xp_comparison.", xp_comparison);
    const auto target_level = zh_number("skill_level", scaled_target / 10.0, 1);
    const auto experience_level = zh_number("experience_level",
                                             level_diff / 10.0, 1);

    if (max_training)
        description += zh_message("skill.target.training_max", {
            zh_text("verb", verb, hypothetical ? "将" : ""),
            target_level,
            xp_comparison_arg,
            experience_level}).display();
    else if (!hypothetical)
        description += zh_message("skill.target.training_current", {
            zh_integer("training_percent", you.training[skill]),
            zh_text("verb", verb, hypothetical ? "将" : ""),
            target_level,
            xp_comparison_arg,
            experience_level}).display();
    else
        description += zh_message("skill.target.training_complete", {
            zh_integer("training_percent", training),
            zh_text("verb", verb, hypothetical ? "将" : ""),
            target_level,
            xp_comparison_arg,
            experience_level}).display();
    if (you.wizard)
    {
        description += make_stringf("\n    (%d xp, %d skp)",
                                    diffs.experience, diffs.skill_points);
    }
    return description;
}

/**
 * Append two skill target descriptions: one for 100%, and one for the
 * current training rate.
 */
static void _append_skill_target_desc(string &description, skill_type skill,
                                        int scaled_target)
{
    if (!you.has_mutation(MUT_DISTRIBUTED_TRAINING))
        description += "\n    " + _skill_target_desc(skill, scaled_target, 100);
    if (you.training[skill] > 0 && you.training[skill] < 100)
    {
        description += "\n    " + _skill_target_desc(skill, scaled_target,
                                                    you.training[skill]);
    }
}

static string _desc_attack_delay(const item_def &item)
{
    // Hide speed/heavy brand from unidentified weapons.
    item_def dummy = item;
    if (!item.is_identified())
    {
        dummy.brand = SPWPN_NORMAL;
        if (is_artefact(dummy))
            artefact_set_property(dummy, ARTP_BRAND, SPWPN_NORMAL);
    }

    const int cur_delay = you.attack_delay_with(&dummy).expected();

    return zh_message("item.weapon.current_attack_delay", {
        zh_number("delay", (float)cur_delay / 10, 1)}).display();
}

static string _describe_missile_dmg_brand(const item_def &item)
{
    switch (item.brand)
    {
    case SPMSL_POISONED:
    case SPMSL_CURARE:
    case SPMSL_SILVER:
    case SPMSL_CHAOS:
        break;
    default: // Other brands don't deal extra damage.
        return "";
    }
     const string brand_name = missile_brand_name(item, MBN_BRAND);

     if (brand_name.empty())
         return brand_name;

     return " + " + uppercase_first(brand_name);
}

string damage_rating(const item_def *item, int *rating_value)
{
    if (item && is_unrandom_artefact(*item, UNRAND_WOE))
    {
        if (rating_value)
            *rating_value = 666;

        return zh_source("detail.item.fixed",
                         "your enemies will bleed and die for Makhleb.");
    }

    const bool thrown = item && item->base_type == OBJ_MISSILES;
    if (item && !thrown && !is_weapon(*item))
        return zh_source("detail.item.fixed", "0.");

    brand_type brand = SPWPN_NORMAL;
    if (!item)
        brand = get_form()->get_uc_brand();
    else if (item->is_identified() && !thrown)
        brand = get_weapon_brand(*item);

    // Would be great to have a breakdown of UC damage by skill, form, claws etc.
    const int base_dam = item ? property(*item, PWPN_DAMAGE)
                              : unarmed_base_damage(false);
    // This is just SPWPN_HEAVY.
    const int post_brand_dam = brand_adjust_weapon_damage(base_dam, brand, false);
    const int heavy_dam = post_brand_dam - base_dam;
    const int extra_base_dam = thrown ? throwing_base_damage_bonus(*item, false) :
                               !item ? unarmed_base_damage_bonus(false) :
                                    heavy_dam; // 0 for non-heavy weapons
    const skill_type skill = item ? _item_training_skill(*item) : SK_UNARMED_COMBAT;
    const int stat_mult = stat_modify_damage(100, skill);
    const bool use_str = weapon_uses_strength(skill);
    // Throwing weapons and UC only get a damage mult from Fighting skill,
    // not from Throwing/UC skill.
    const bool use_weapon_skill = item && !thrown;
    const int weapon_skill_mult = use_weapon_skill ? apply_weapon_skill(100, skill, false) : 100;
    const int skill_mult = apply_fighting_skill(weapon_skill_mult, false, false);

    const int slaying = you.slaying(thrown, false);
    const int ench = item && item->is_identified() ? item->plus : 0;
    const int plusses = slaying + ench;

    const int DAM_RATE_SCALE = 100;
    int rating = (base_dam + extra_base_dam) * DAM_RATE_SCALE;
    rating = stat_modify_damage(rating, skill);
    if (use_weapon_skill)
        rating = apply_weapon_skill(rating, skill, false);
    rating = apply_fighting_skill(rating, false, false);
    rating /= DAM_RATE_SCALE;
    rating += plusses;

    if (rating_value)
        *rating_value = rating;

    const string base_dam_desc = thrown ? make_stringf("[%d + %d (Thrw)]",
                                                       base_dam, extra_base_dam) :
                                  !item ? make_stringf("[%d + %d (UC)]",
                                                       base_dam, extra_base_dam) :
                   brand == SPWPN_HEAVY ? make_stringf("[%d + %d (Hvy)]",
                                                       base_dam, extra_base_dam) :
                                          make_stringf("%d", base_dam);
    const string localized_base_dam_desc = thrown
        ? make_stringf("[%d + %d（投掷）]", base_dam, extra_base_dam)
        : !item ? make_stringf("[%d + %d（徒手）]", base_dam, extra_base_dam)
        : brand == SPWPN_HEAVY
            ? make_stringf("[%d + %d（重型）]", base_dam, extra_base_dam)
            : to_string(base_dam);

    string plusses_desc;
    string localized_plusses_desc;
    if (plusses)
    {
        const string sign = plusses < 0 ? "-" : "+";
        const string plusses_kind = slaying && ench ? "Ench + Slay" :
                                    ench ? "Ench" : "Slay";
        const string localized_kind = slaying && ench ? "附魔 + 杀戮" :
                                      ench ? "附魔" : "杀戮";
        plusses_desc = make_stringf(" %s %d (%s)",
                                    sign.c_str(), abs(plusses), plusses_kind.c_str());
        localized_plusses_desc = make_stringf(" %s %d（%s）",
                                    sign.c_str(), abs(plusses), localized_kind.c_str());
    }

    const string dmg_brand_desc = thrown ? _describe_missile_dmg_brand(*item) : "";
    string localized_brand_desc;
    if (thrown && !dmg_brand_desc.empty())
    {
        const string brand_name = missile_brand_name(*item, MBN_BRAND);
        string localized_brand;
        switch (item->brand)
        {
        case SPMSL_POISONED: localized_brand = "毒性"; break;
        case SPMSL_CURARE: localized_brand = "克制毒药"; break;
        case SPMSL_SILVER: localized_brand = "银质"; break;
        case SPMSL_CHAOS: localized_brand = "混沌"; break;
        default: localized_brand = brand_name; break;
        }
        localized_brand_desc = " + " + uppercase_first(localized_brand);
    }
    return zh_message("item.weapon.damage_rating", {
        zh_integer("rating", rating),
        zh_text("base", base_dam_desc, localized_base_dam_desc),
        zh_integer("stat_mult", stat_mult),
        zh_text("stat", use_str ? "Str" : "Dex", use_str ? "力量" : "敏捷"),
        zh_integer("skill_mult", skill_mult),
        zh_text("skill", use_weapon_skill ? "Skill" : "Fight",
                use_weapon_skill ? "武器技能" : "战斗技能"),
        zh_text("plusses", plusses_desc, localized_plusses_desc),
        zh_text("brand", dmg_brand_desc, localized_brand_desc)}).display();
}

static string _damage_rating_description(const item_def &item)
{
    string canonical;
    {
        ZhTranslationPause pause;
        canonical = damage_rating(&item);
    }
    const string localized = damage_rating(&item);
    return zh_message("item.weapon.dmg_rating", {
        ZhArg{"rating", ZhArgType::Text, canonical, localized,
              canonical != localized}}).display();
}

static string _weapon_ego_key(brand_type ego)
{
    string verbose_ego_name = lowercase_first(brand_type_name(ego, false));
    string terse_ego_name = lowercase_first(brand_type_name(ego, true));
    string ego_key = verbose_ego_name + " (" + terse_ego_name + ") weapon ego";

    return ego_key;
}

static void _append_skill_needed(string &description, const item_def &item,
                                 bool indent = true, string skill_padding = "")
{
    const skill_type skill = _item_training_skill(item);
    const int target_skill = _item_training_target(item);
    const bool below_target = _is_below_training_target(item, true);
    const bool can_set_target = below_target && in_inventory(item)
                                && !you.has_mutation(MUT_DISTRIBUTED_TRAINING);
    const bool useful = !is_useless_item(item) && crawl_state.need_save;
    if (useful)
    {
        description += "\n";
        if (indent)
            description += "    ";
        description += _your_skill_desc(skill, can_set_target, target_skill,
                                        std::move(skill_padding));
    }

    if (below_target)
        _append_skill_target_desc(description, skill, target_skill);
}

static void _append_weapon_stats(string &description, const item_def &item)
{
    const int base_dam = property(item, PWPN_DAMAGE);
    const int mindelay_skill = _item_training_target(item);

    if (item.base_type == OBJ_STAVES
        && item.is_identified()
        && staff_skill(static_cast<stave_type>(item.sub_type)) != SK_NONE
        && is_useless_skill(staff_skill(static_cast<stave_type>(item.sub_type))))
    {
        const string skill = skill_name(staff_skill(
            static_cast<stave_type>(item.sub_type)));
        const string localized_skill = zh_lookup_exact(skill);
        description += zh_message("item.weapon.study_staff", {
            ZhArg{"skill", ZhArgType::Name, skill, localized_skill,
                  localized_skill != skill}}).display();
    }

    const string hit_bonus = is_unrandom_artefact(item, UNRAND_WOE)
        ? (Options.char_set == CSET_ASCII ? "inf" : "\u221e")
        : make_stringf("%+d", property(item, PWPN_HIT));
    const string damage = is_unrandom_artefact(item, UNRAND_WOE)
        ? hit_bonus : to_string(base_dam);
    description += zh_message("item.weapon.base_stats", {
        ZhArg{"hit_bonus", ZhArgType::Number, hit_bonus, hit_bonus},
        ZhArg{"damage", ZhArgType::Number, damage, damage}}).display();

    description += zh_message("item.weapon.attack_delay_and_minimum", {
        zh_number("base_delay", (float) property(item, PWPN_SPEED) / 10, 1),
        zh_number("minimum_delay",
                  (float) weapon_min_delay(item, item.is_identified()) / 10, 1),
        zh_integer("skill_level", mindelay_skill / 10)}).display();

    _append_skill_needed(description, item);

    if (is_slowed_by_armour(&item))
    {
        const int penalty_scale = 100;
        const int armour_penalty = you.adjusted_body_armour_penalty(penalty_scale, true);
        description += "\n";
        if (armour_penalty)
        {
            const item_def *body_armour = you.body_armour();
            const bool significant = armour_penalty >= penalty_scale;
            if (significant)
            {
                const string actor_en = body_armour
                    ? uppercase_first(body_armour->name(DESC_YOUR))
                    : "Your heavy armour";
                ZhArg actor_arg = body_armour
                    ? zh_item_arg("actor", *body_armour, DESC_YOUR)
                    : ZhArg{"actor", ZhArgType::Name, actor_en, "你的重型护甲"};
                actor_arg.canonical = actor_en;
                description += zh_message("item.weapon.armour_slow.full", {
                    actor_arg,
                    zh_number("delay", armour_penalty /
                              (10.0f * penalty_scale), 1)}).display();
            }
            else
            {
                const string actor_en = body_armour
                    ? uppercase_first(body_armour->name(DESC_YOUR))
                    : "Your heavy armour";
                ZhArg actor_arg = body_armour
                    ? zh_item_arg("actor", *body_armour, DESC_YOUR)
                    : ZhArg{"actor", ZhArgType::Name, actor_en, "你的重型护甲"};
                actor_arg.canonical = actor_en;
                description += zh_message("item.weapon.armour_slow_slightly", {
                    actor_arg}).display();
            }
        }
        else
        {
            description += zh_source("detail.item.fixed",
                "Wearing heavy armour would reduce your attack speed with this weapon.");
        }
    }

    const bool want_player_stats = !is_useless_item(item) && crawl_state.need_save;
    if (want_player_stats)
    {
        description += _desc_attack_delay(item);
        description += _damage_rating_description(item);
    }

    const string brand_desc = _describe_weapon_brand(item);
    if (!brand_desc.empty())
    {
        const brand_type brand = get_weapon_brand(item);
        const string brand_name_en = brand_type_name(brand, true);
        string brand_name = uppercase_first(
            zh_word("item.weapon.brand.", brand_name_en));
        // Hack to match artefact prop formatting.

        string fmt_name = make_stringf("\n\n%-*s",
                                        MAX_ARTP_NAME_LEN + 1,
                                        (brand_name + ":").c_str());

        description += _format_prop_desc(fmt_name, brand_desc);
    }
    if (is_unrandom_artefact(item))
    {
        auto entry = get_unrand_entry(item.unrand_idx);
        if (entry->dbrand)
        {
            description += make_stringf("\n%s%s",
                (brand_desc.empty() ? "\n" : ""),
                _format_dbrand(entry->dbrand).c_str());
        }
        // XXX: Would be nice if this wasn't duplicated
        if (testbits(item.flags, ISFLAG_CHAOTIC))
        {
            string ego_key = _weapon_ego_key(SPWPN_CHAOS);
            string ego_desc = getEgoString(ego_key);
            description += _format_prop_desc(zh_source("detail.item.fixed",
                "\nChaotic:   "), ego_desc);
        }

        // XX spacing following brand and dbrand for randarts/unrands is a bit
        // inconsistent with other object types
    }
}

static string _handedness_string(const item_def &item)
{
    if (you.has_mutation(MUT_NO_GRASPING))
        return zh_message("item.weapon.hands_missing").display();

    if (crawl_state.need_save
        && is_weapon_too_large(item, you.body_size(PSIZE_TORSO))
        && !you.has_mutation(MUT_QUADRUMANOUS))
    {
        return zh_message("item.weapon.too_large").display();
    }

    const bool quad = you.has_mutation(MUT_QUADRUMANOUS);
    string handname = species::hand_name(you.species);
    if (quad)
        handname += "-pair";

    string n;
    switch (you.hands_reqd(item))
    {
    case HANDS_ONE:
        n = "one";
        break;
    case HANDS_TWO:
        if (quad)
            handname = pluralise(handname);
        n = "two";
        break;
    }

    const string hand_zh = zh_lookup_exact(handname);
    const ZhArg hand_arg{"handname", ZhArgType::Name, handname, hand_zh,
                         hand_zh != handname};
    if (quad)
        return zh_message("item.weapon.quadrumanous_hand_use", {
            zh_text("hands", n, n == "one" ? "一对" : "两对"), hand_arg}).display();
    const string suffix = ends_with(handname, "e") ? "d" : "ed";
    return zh_message("item.weapon.hand_use", {
        zh_text("hands", n, n == "one" ? "单" : "双"), hand_arg,
        zh_text("suffix", suffix, "")}).display();

}

static string _category_string(const item_def &item, bool monster)
{
    if (is_unrandom_artefact(item, UNRAND_LOCHABER_AXE))
        return ""; // handled in art-data DBRAND

    string description = "";
    const string weapon = is_unrandom_artefact(item)
        ? get_artefact_base_name(item) : "weapon";
    const string skill = item_attack_skill(item) == SK_FIGHTING
        ? "buggy" : skill_name(item_attack_skill(item));
    const string localized_weapon = zh_lookup_exact(weapon);
    const string localized_skill = zh_lookup_exact(skill);
    description += zh_message("item.weapon.category", {
        ZhArg{"weapon", ZhArgType::Name, weapon, localized_weapon,
              localized_weapon != weapon},
        ZhArg{"skill", ZhArgType::Name, skill, localized_skill,
              localized_skill != skill}}).display();

    const skill_type skill_type_value = item_attack_skill(item);

    switch (skill_type_value)
    {
    case SK_POLEARMS:
        // TODO(PF): maybe remove this whole section for util/monster summaries..?
        {
            const string hint = monster ? "" : " (target with [<white>v</white>])";
            const string localized_hint = monster ? "" : "（按[<white>v</white>]瞄准）";
            description += zh_message("item.weapon.reach", {
                zh_text("target_hint", hint, localized_hint)}).display();
        }
        break;
    case SK_AXES:
        {
            const string qualifier = is_unrandom_artefact(item, UNRAND_WOE)
                ? "" : ", dealing less damage to those not targeted";
            const string localized_qualifier = is_unrandom_artefact(item, UNRAND_WOE)
                ? "" : "（未指定目标的敌人受到的伤害较低）";
            description += zh_message("item.weapon.axes", {
                zh_text("damage_qualifier", qualifier, localized_qualifier)}).display();
        }
        break;
    case SK_SHORT_BLADES:
        {
            const string intensifier = (item.sub_type == WPN_DAGGER)
                ? " extremely" : "";
            const string localized_intensifier = (item.sub_type == WPN_DAGGER)
                ? "特别" : "";
            description += zh_message("item.weapon.stabbing", {
                zh_text("intensifier", intensifier, localized_intensifier)}).display();

        }
        break;
    default:
        break;
    }

    return description;
}

static string _describe_weapon_brand(const item_def &item)
{
    if (is_unrandom_artefact(item))
    {
        const unrandart_entry *entry = get_unrand_entry(item.unrand_idx);
        if (entry && entry->flags & UNRAND_FLAG_SKIP_EGO)
            return ""; // XXX FIXME
    }

    if (!item.is_identified())
        return "";

    const bool ranged = is_range_weapon(item);
    const int damtype = get_vorpal_type(item);
    const bool blade = !ranged && damtype == DVORP_SLICING || damtype == DVORP_CHOPPING;

    const brand_type ego = get_weapon_brand(item);
    string ego_key = _weapon_ego_key(ego);
    string ego_desc = getEgoString(ego_key);

    // Overrides for ranged weapons and blade weapons, if they exist.
    if (ranged)
    {
        string ranged_ego_desc = getEgoString(ego_key + " ranged");
        if (!ranged_ego_desc.empty())
            ego_desc = ranged_ego_desc;
    }
    if (blade)
    {
        string blade_ego_desc = getEgoString(ego_key + " blade");
        if (!blade_ego_desc.empty())
            ego_desc = blade_ego_desc;
    }

    if (ego == SPWPN_VALOUR)
    {
        dice_def dmg = zap_damage(ZAP_VALOUR_BEAM, property(item, PWPN_DAMAGE), false, false);
        ego_desc += zh_message("item.weapon.valour_beam", {
            zh_integer("dice_count", dmg.num),
            zh_integer("dice_size", dmg.size)}).display();
    }

    return ego_desc;
}

static ZhArg _describe_point_diff_arg(const string &key, int original,
                                     int changed, int scale = 100)
{
    if (original == changed)
        return zh_word_arg(key, "item.stat.", "remain unchanged");

    // Truncate to 1 decimal place, rather than round (so that it matches what
    // will be displayed as the player's AC/EV if they actually put this on.)
    original = original / (scale / 10) * 10;
    changed = changed / (scale / 10) * 10;

    float difference = ((float)(changed - original)) / scale;

    const string direction = difference > 0 ? "increase" : "decrease";
    const string localized_direction = difference > 0 ? "增加" : "降低";
    const ZhMessage change = zh_message("item.stat.change", {
        zh_text("direction", direction, localized_direction),
        zh_number("amount", abs(difference), 1),
        zh_number("before", (float)original / scale, 1),
        zh_number("after", (float)changed / scale, 1)});
    return {key, ZhArgType::Text, change.canonical, change.localized};
}

static string _equip_type_name(const item_def &item)
{
    if (item.base_type == OBJ_JEWELLERY)
    {
        if (jewellery_is_amulet(item))
            return "amulet";
        else
            return "ring";
    }

    return base_type_string(item.base_type);
}

static string _equipment_switchto_string(const item_def &item)
{
    if (item.base_type == OBJ_WEAPONS || item.base_type == OBJ_STAVES)
        return "wielding";
    // Not always the same verb used elsewhere, but "switch putting on" sounds weird
    else
        return "wearing";
}

/**
 * Describe how (un)equipping a piece of equipment might change the player's
 * AC/EV/SH and spell failure. We don't include temporary buffs in this
 * calculation.
 *
 * @param item    The item whose description we are writing.
 * @param remove  Whether the item is already equipped, and thus whether to
                  show the change solely from unequipping the item.
 * @return        The description.
 */
static string _equipment_property_change_description(const item_def &item,
                                                     bool remove = false)
{
    // First, test if there is any AC/EV/SH change at all.
    const int cur_ac = you.base_ac(100);
    const int cur_ev = you.evasion_scaled(100, true);
    const int cur_sh = player_displayed_shield_class(100, true);
    int new_ac, new_ev, new_sh;
    FixedVector<int, MAX_KNOWN_SPELLS> cur_fail, new_fail;
    for (int i = 0; i < MAX_KNOWN_SPELLS; ++i)
        cur_fail[i] = raw_spell_fail(you.spells[i]);

    if (remove)
        you.preview_stats_without_specific_item(100, item, &new_ac, &new_ev, &new_sh, &new_fail);
    else if (item.base_type == OBJ_TALISMANS)
        you.preview_stats_in_specific_form(100, item, &new_ac, &new_ev, &new_sh, &new_fail);
    else
        you.preview_stats_with_specific_item(100, item, &new_ac, &new_ev, &new_sh, &new_fail);

    // Check if any spell failures changed, and save the greatest magnitude that
    // any of them changed.
    int fail_change = 0;
    int visible_fail_change = 0;
    for (int i = 0; i < MAX_KNOWN_SPELLS; ++i)
    {
        if (cur_fail[i] != new_fail[i])
        {
            int new_fail_change = new_fail[i] - cur_fail[i];
            int new_visible_fail_change = failure_rate_to_int(new_fail[i])
                                            - failure_rate_to_int(cur_fail[i]);
            if (abs(new_fail_change) > abs(fail_change))
                fail_change = new_fail_change;
            if (abs(new_visible_fail_change) > abs(visible_fail_change))
                visible_fail_change = new_visible_fail_change;
        }
    }

    // If we're previewing non-armour and there is no AC/EV/SH change, print no
    // extra description at all (since almost all items of these types will
    // change nothing)
    if (cur_ac == new_ac && cur_ev == new_ev && cur_sh == new_sh
        && fail_change == 0
        && (item.base_type != OBJ_ARMOUR || item.sub_type == ARM_ORB))
    {
        return "";
    }

    string description;
    description.reserve(100);
    description = "\n\n";

    auto equipment_type = [&]() {
        const string type = _equip_type_name(item);
        string localized;
        if (type == "amulet") localized = "这枚护身符";
        else if (type == "ring") localized = "这枚戒指";
        else if (type == "armour") localized = "这件护甲";
        else if (type == "weapon") localized = "这件武器";
        else if (type == "staff") localized = "这根法杖";
        else if (type == "talisman") localized = "这枚护符";
        else localized = zh_lookup_exact(type);
        return ZhArg{"type", ZhArgType::Name, type, localized,
                      type.empty() || type != localized};
    };

    if (remove)
    {
        const string verb = item_unequip_verb(item);
        const string localized_verb = verb == "unwield" ? "收起" :
                                      verb == "take off" ? "脱下" :
                                      verb == "remove" ? "取下" : "卸下";
        description += zh_message("item.equipment.preview.remove", {
            zh_text("verb", verb, localized_verb),
            equipment_type()}).display();
    }
    else if (item.base_type == OBJ_TALISMANS)
        description += zh_source("detail.item.fixed",
            "If you transformed using this talisman:");
    else if (item.base_type == OBJ_JEWELLERY && !jewellery_is_amulet(item))
        description += zh_source("detail.item.fixed",
            "If you were wearing this ring:");
    else if (item.base_type == OBJ_WEAPONS && you.has_mutation(MUT_WIELD_OFFHAND))
        description += zh_source("detail.item.fixed",
            "If you switch to wielding this weapon in your main hand:");
    else
    {
        const string verb = _equipment_switchto_string(item);
        description += zh_message("item.equipment.preview.switch", {
            zh_text("verb", verb, verb == "wielding" ? "挥舞" : "穿戴"),
            equipment_type()}).display();
    }

    // Always display AC line on proper armour, even if there is no change
    if (item.base_type == OBJ_ARMOUR && get_armour_slot(item) != SLOT_OFFHAND
        || cur_ac != new_ac)
    {
        description += zh_message("item.equipment.preview_stat", {
            zh_text("stat", "AC", "护甲"),
            _describe_point_diff_arg("change", cur_ac, new_ac)}).display();
    }

    // Always display EV line on non-orb armour, even if there is no change
    // XXX perhaps this shouldn't display on basic aux armour?
    if (item.base_type == OBJ_ARMOUR && item.sub_type != ARM_ORB
        || cur_ev != new_ev)
    {
        description += zh_message("item.equipment.preview_stat", {
            zh_text("stat", "EV", "闪避"),
            _describe_point_diff_arg("change", cur_ev, new_ev)}).display();
    }

    // Always display SH line on shields, even if there is no change
    if (is_shield(item) || cur_sh != new_sh)
    {
        description += zh_message("item.equipment.preview_stat", {
            zh_text("stat", "SH", "格挡"),
            _describe_point_diff_arg("change", cur_sh, new_sh)}).display();
    }

    if (fail_change != 0)
    {
        const string direction = fail_change > 0 ? "worsen" : "improve";
        const string localized_direction = fail_change > 0 ? "恶化" : "改善";
        if (visible_fail_change == 0)
            description += zh_message("item.equipment.spell_fail_trivial", {
                zh_text("direction", direction, localized_direction)}).display();
        else
        {
            description += zh_message("item.equipment.spell_fail_change", {
                zh_text("direction", direction, localized_direction),
                zh_integer("amount", abs(visible_fail_change))}).display();
        }
    }

    return description;
}

static string _spell_fail_change_description(const item_def &item,
                                             bool remove = false)
{
    int dummy1, dummy2, dummy3;
    FixedVector<int, MAX_KNOWN_SPELLS> cur_fail, new_fail;
    for (int i = 0; i < MAX_KNOWN_SPELLS; ++i)
        cur_fail[i] = raw_spell_fail(you.spells[i]);

    if (remove)
        you.preview_stats_without_specific_item(100, item, &dummy1, &dummy2, &dummy3, &new_fail);
    else if (item.base_type == OBJ_TALISMANS)
        you.preview_stats_in_specific_form(100, item, &dummy1, &dummy2, &dummy3, &new_fail);
    else
        you.preview_stats_with_specific_item(100, item, &dummy1, &dummy2, &dummy3, &new_fail);

    // Check if any spell failures changed.
    int fail_change = 0;
    for (int i = 0; i < MAX_KNOWN_SPELLS; ++i)
    {
        if (cur_fail[i] != new_fail[i])
        {
            fail_change = new_fail[i] - cur_fail[i];
            break;
        }
    }

    // If nothing changed, generate no text
    if (fail_change == 0)
        return "";

    // If they did, convert all failures into percentages to see whether any
    // change was non-trivial
    fail_change = 0;
    for (int i = 0; i < MAX_KNOWN_SPELLS; ++i)
    {
        if (cur_fail[i] == new_fail[i])
            continue;

        cur_fail[i] = failure_rate_to_int(cur_fail[i]);
        new_fail[i] = failure_rate_to_int(new_fail[i]);

        if (cur_fail[i] != new_fail[i])
            fail_change = cur_fail[i] - new_fail[i];
    }

    // If nothing changed *meaningfully*, generate no text
    if (fail_change == 0)
        return "";

    // Otherwise, generate a complete list of all non-trivial changes
    string desc;
    desc = make_stringf("If you %s this item, your spell failure would %s:\n",
                        remove ? "removed" : "equipped",
                        fail_change < 0 ? "worsen" : "improve");

    // Sort spells by degree of change in their fail rates (and then by
    // absolute fail rate after that)
    vector<pair<int, int>> spell_sort;
    for (int i = 0; i < MAX_KNOWN_SPELLS; ++i)
    {
        if (cur_fail[i] == new_fail[i])
            continue;

        spell_sort.push_back({i, abs(cur_fail[i] - new_fail[i])});
    }
    sort(spell_sort.begin( ), spell_sort.end( ),
            [cur_fail](const pair<int, int>& a, const pair<int, int>& b)
                { return cur_fail[a.first] > cur_fail[b.first];});
    sort(spell_sort.begin( ), spell_sort.end( ),
            [](const pair<int, int>& a, const pair<int, int>& b)
                { return a.second > b.second;});


    // vector<string> entries;
    for (size_t i = 0; i < spell_sort.size(); ++i)
    {
        int index = spell_sort[i].first;

        int diff = new_fail[index] - cur_fail[index];
        string colour;
        if (diff > 20)
            colour = "magenta";
        else if (diff > 11)
            colour = "lightred";
        else if (diff > 5)
            colour = "yellow";
        else if (diff < -11)
            colour = "lightblue";
        else if (diff < -5)
            colour = "white";
        else
            colour = "lightgrey";

        string entry = make_stringf("<%s>%s%3d%%-> %3d%%</%s>\n",
                colour.c_str(),
                chop_string(spell_title(you.spells[index]), 32).c_str(),
                cur_fail[index], new_fail[index], colour.c_str());

        desc += entry;
    }

    return desc;
}

static string _equipment_property_change(const item_def &item)
{
    string description;

    if (!item_is_equipped(item))
        description = _equipment_property_change_description(item);
    else
        description = _equipment_property_change_description(item, true);

    return description;
}

static string _describe_weapon(const item_def &item, bool verbose, bool monster)
{
    string description;

    description.reserve(200);

    description = "";

    if (verbose)
    {
        if (!monster)
            description += "\n\n";
        _append_weapon_stats(description, item);
    }

    string art_desc = _artefact_descrip(item);
    if (!art_desc.empty())
        description += "\n\n" + art_desc;

    if (verbose && crawl_state.need_save && can_equip_item(item)
        && item.is_identified())
    {
        description += _equipment_property_change(item);
    }

    if (verbose)
    {
        description += "\n\n" + _category_string(item, monster);
        description += _handedness_string(item);
    }

    if (!monster)
    {
        if (is_enchantable_weapon(item))
        {
            description += zh_message("item.weapon.max_enchantment", {
                zh_integer("maximum", MAX_WPN_ENCHANT)}).display();
        }
        else
            description += zh_source("detail.item.fixed",
                                     "\n\nIt cannot be enchanted further.");
    }

    return description;
}

static string _missile_ego_key(const item_def &item)
{
    string verbose_ego_name = lowercase_first(missile_brand_name(item, MBN_NAME));
    string terse_ego_name = lowercase_first(missile_brand_name(item, MBN_TERSE));
    string ego_key = verbose_ego_name + " (" + terse_ego_name + ") missile ego";

    return ego_key;
}

static string _describe_ammo(const item_def &item)
{
    string description;

    description.reserve(64);

    if (item.brand && item.is_identified())
    {
        description += "\n\n";

        string ego_key = _missile_ego_key(item);
        string ego_desc = getEgoString(ego_key);

        description += ego_desc;
    }

    const int dam = property(item, PWPN_DAMAGE);
    const bool player_throwable = is_throwable(&you, item);
    if (player_throwable)
    {
        const int throw_delay = (10 + dam / 2);
        const int target_skill = _item_training_target(item);

        description += zh_message("item.projectile.stats_and_minimum_delay", {
            zh_integer("damage", dam),
            zh_number("base_delay", (float) throw_delay / 10, 1),
            zh_number("minimum_delay",
                      (float) FASTEST_PLAYER_THROWING_SPEED / 10, 1),
            zh_integer("skill_level", target_skill / 10)}).display();

        _append_skill_needed(description, item);

        if (!is_useless_item(item) && crawl_state.need_save){
            description += _desc_attack_delay(item);

            if (property(item, PWPN_DAMAGE))
                description += _damage_rating_description(item);
        }
    }

    if (ammo_always_destroyed(item))
        description += zh_source("detail.item.fixed",
                                 "\n\nIt is always destroyed on impact.");
    else if (!ammo_never_destroyed(item))
    {
        description += zh_message("item.projectile.destroy_chance", {
            zh_integer("chance", ammo_destroy_chance(item))}).display();
    }

    return description;
}

static string _warlock_mirror_reflect_desc()
{
    const int scaled_SH = crawl_state.need_save ? player_shield_class(100, false) : 0;
    const int SH = scaled_SH / 100;
    // We use random-rounded SH, so take a weighted average of the
    // chances with SH and SH+1.
    const int reflect_chance_numer = (100 - (scaled_SH % 100)) * SH * omnireflect_chance_denom(SH+1) + (scaled_SH % 100) * (SH+1) * omnireflect_chance_denom(SH);
    const int reflect_chance_denom = omnireflect_chance_denom(SH) * omnireflect_chance_denom(SH+1);
    const int reflect_chance = reflect_chance_numer / reflect_chance_denom;
    return zh_message("item.armour.warlock_mirror_reflect", {
        zh_integer("chance", reflect_chance)}).display();
}

static string _armour_ego_key(special_armour_type ego)
{
    string verbose_ego_name = lowercase_first(special_armour_type_name(ego, false));
    string terse_ego_name = lowercase_first(special_armour_type_name(ego, true));
    string ego_key = verbose_ego_name + " (" + terse_ego_name + ") armour ego";

    return ego_key;
}

static string _orb_ego_details(special_armour_type ego)
{
    switch (ego)
    {
        case SPARM_ENERGY:
            return make_stringf("\n\nSpell refund chance: %d%% (max %d%%)",
                                player_channelling_chance(), player_channelling_chance(true));

        case SPARM_GUILE:
            return make_stringf("\n\nEnemy Willpower: -%d (max -%d)",
                                guile_will_reduction(), guile_will_reduction(true));

        case SPARM_GLASS:
            return make_stringf("\n\nVitrify chance: %d%% (max %d%%)",
                        (20 + you.skill(SK_EVOCATIONS, 5)) * 100 / 500,
                        (20 + 135) * 100 / 500);

        case SPARM_PYROMANIA:
            return make_stringf("\n\nExplosion chance: %d%% (max %d%%)\nExplosion damage: %dd%d (max %dd%d)\n",
                                pyromania_trigger_chance(), pyromania_trigger_chance(true),
                                pyromania_damage(false, false).num, pyromania_damage(false, false).size,
                                pyromania_damage(false, true).num, pyromania_damage(false, true).size);

        case SPARM_STARDUST:
        {
            dice_def base_dam = zap_damage(ZAP_SHOOTING_STAR, stardust_orb_power(0), false, false);
            dice_def max_dam = zap_damage(ZAP_SHOOTING_STAR, stardust_orb_power(0, true), false, false);
            return make_stringf("\n\nBase shooting star damage: %dd%d (max %dd%d) + 25%% per MP spent"
                                "\nShooting stars conjured: 1 + 1 per visible enemy, up to %d (%d at max skill)",
                                    base_dam.num, base_dam.size,
                                    max_dam.num, max_dam.size,
                                    stardust_orb_max(), stardust_orb_max(true));
        }

        case SPARM_MESMERISM:
            return make_stringf("\n\nMesmerism radius: %d (max %d)", mesmerism_orb_radius(), mesmerism_orb_radius(true));

        default:
            return "";
    }
}

static string _describe_armour(const item_def &item, bool verbose, bool monster)
{
    string description;

    // orbs skip this entirely
    if (verbose && !(item.base_type == OBJ_ARMOUR && item.sub_type == ARM_ORB))
    {
        if (!monster && is_shield(item))
        {
            const int evp = -property(item, PARM_EVASION);
            const string cumber_desc = evp < 100 ? "slightly " :
                                       evp > 100 ? "greatly " : "";
            const string localized_degree = evp < 100 ? "轻微地"
                                            : evp > 100 ? "大幅" : "";
            description += zh_message("item.armour.shield_cumbersome", {
                zh_text("degree", cumber_desc, localized_degree)}).display();
        }
        if (!monster)
            description += "\n\n";
        if (is_shield(item))
        {
            description += zh_message("item.armour.shield_ratings", {
                zh_integer("base", property(item, PARM_AC)),
                zh_integer("encumbrance", -property(item, PARM_EVASION) / 10),
                zh_integer("blocks", shield_block_limit(item))}).display();
            if (is_unrandom_artefact(item, UNRAND_WARLOCK_MIRROR))
                description += _warlock_mirror_reflect_desc();
        }
        else
        {
            const int evp = property(item, PARM_EVASION);
            string suffix;
            string localized_suffix;
            if (get_armour_slot(item) == SLOT_BODY_ARMOUR)
            {
                suffix = "       Encumbrance rating: " + to_string(-evp / 10);
                localized_suffix = "       负重等级：" + to_string(-evp / 10);
            }
            // Bardings reduce evasion by a fixed amount, and don't have any of
            // the other effects of encumbrance.
            else if (evp)
            {
                suffix = "       Evasion: " + to_string(evp / 30);
                localized_suffix = "       闪避惩罚：" + to_string(evp / 30);
            }
            description += zh_message("item.armour.base_rating", {
                zh_integer("base", property(item, PARM_AC)),
                zh_text("suffix", suffix, localized_suffix)}).display();
        }
    }

    const special_armour_type ego = get_armour_ego_type(item);

    const unrandart_entry *entry = nullptr;
    if (is_unrandom_artefact(item))
        entry = get_unrand_entry(item.unrand_idx);
    const bool skip_ego = is_unrandom_artefact(item)
                          && entry && (entry->flags & UNRAND_FLAG_SKIP_EGO);

    // Only give a description for armour with a known ego.
    if (ego != SPARM_NORMAL && item.is_identified() && verbose && !skip_ego)
    {
        description += "\n\n";

        string ego_prefix;
        const string ego_name_en = armour_ego_name(item, !is_artefact(item));
        const string ego_name_zh = zh_word("item.armour.ego.", ego_name_en);
        if (is_artefact(item))
        {
            // Make this match the formatting in _randart_descrip,
            // since instead of the item being named something like
            // 'cloak of invisiblity', it's 'the cloak of the Snail (+Inv, ...)'
            string name = ego_name_zh + ": ";
            ego_prefix = make_stringf("%-*s", MAX_ARTP_NAME_LEN + 1, name.c_str());
        }
        else if (zh_language_enabled())
            ego_prefix = "“" + ego_name_zh + "”效果：";
        else
            ego_prefix = "'Of " + ego_name_en + "': ";

        string ego_key = _armour_ego_key(ego);
        string ego_desc = getEgoString(ego_key);
        if (is_artefact(item))
            ego_desc = uppercase_first(ego_desc);

        description += _format_prop_desc(ego_prefix, ego_desc);
    }

    string art_desc = _artefact_descrip(item);
    if (!art_desc.empty())
    {
        // Only add a section break if we didn't already add one before
        // printing an ego-based property.
        if (ego == SPARM_NORMAL || !verbose || skip_ego)
            description += "\n";
        description += "\n" + art_desc;
    }

    if (!monster)
    {
        if (is_enchantable_armour(item))
        {
            description += zh_message("item.armour.max_enchantment", {
                zh_integer("maximum", armour_max_enchant(item))}).display();
        }
        else if (armour_is_enchantable(item))
            description += zh_source("detail.item.fixed",
                "\n\nIt cannot be enchanted further.");
    }

    if (verbose
        && item.is_type(OBJ_ARMOUR, ARM_ORB)
        && item.is_identified())
    {
        description += _orb_ego_details(get_armour_ego_type(item));
    }

    // Only displayed if the player exists (not for item lookup from the menu
    // or for morgues).
    if (verbose
        && crawl_state.need_save
        && can_equip_item(item)
        && item.is_identified())
    {
        description += _equipment_property_change(item);
    }

    const int DELAY_SCALE = 100;
    const int aevp = you.adjusted_body_armour_penalty(DELAY_SCALE, true);
    if (crawl_state.need_save
        && verbose
        && aevp
        && !is_shield(item)
        && item_is_equipped(item)
        && is_slowed_by_armour(you.weapon()))
    {
        // TODO: why doesn't this show shield effect? Reconcile with
        // _display_attack_delay
        const string weapon = you.weapon()->name(DESC_YOUR);
        const string weapon_zh = zh_item_arg("weapon", *you.weapon(), DESC_YOUR).localized;
        const string delay_text = aevp >= DELAY_SCALE
            ? make_stringf("by %.1f.", aevp / (10.0f * DELAY_SCALE))
            : "only slightly.";
        const string localized_delay = aevp >= DELAY_SCALE
            ? "减慢" + make_stringf("%.1f", aevp / (10.0f * DELAY_SCALE))
            : "略微减慢。";
        description += zh_message("item.armour.current_missile_slow", {
            ZhArg{"weapon", ZhArgType::Name, weapon, weapon_zh,
                  weapon_zh != weapon},
            zh_text("delay_text", delay_text, localized_delay)}).display();
    }

    return description;
}

static string _describe_lignify_ac()
{
    const Form* tree_form = get_form(transformation::tree);

    // Turn into a tree, check our resulting AC, and then turn back without
    // anyone being the wiser.
    unwind_var<player_equip_set> unwind_eq(you.equipment);
    unwind_var<int8_t> unwind_talisman(you.cur_talisman, -1);
    unwind_var<transformation> unwind_form(you.form, transformation::tree);

    you.equipment.unmeld_all_equipment(true);
    you.equipment.meld_equipment(tree_form->blocked_slots, true);

    return zh_message("item.potion.lignify_ac", {
        zh_integer("ac", you.armour_class_scaled(1))}).display();
}

string describe_item_rarity(const item_def &item)
{
    item_rarity_type rarity = consumable_rarity(item);

    switch (rarity)
    {
    case RARITY_VERY_RARE:
        return "very rare";
    case RARITY_RARE:
        return "rare";
    case RARITY_UNCOMMON:
        return "uncommon";
    case RARITY_COMMON:
        return "common";
    case RARITY_VERY_COMMON:
        return "very common";
    case RARITY_NONE:
    default:
        return "buggy";
    }
}

// Select complete sentences from semantic enums. article_a() includes the
// noun it receives, so it must never be inserted alongside that noun again.
static string _consumable_rarity_display(const item_def &item)
{
    const bool potion = item.base_type == OBJ_POTIONS;
    const char *id;
    switch (consumable_rarity(item))
    {
    case RARITY_VERY_RARE:
        id = potion ? "item.consumable.rarity.potion.very_rare"
                    : "item.consumable.rarity.scroll.very_rare";
        break;
    case RARITY_RARE:
        id = potion ? "item.consumable.rarity.potion.rare"
                    : "item.consumable.rarity.scroll.rare";
        break;
    case RARITY_UNCOMMON:
        id = potion ? "item.consumable.rarity.potion.uncommon"
                    : "item.consumable.rarity.scroll.uncommon";
        break;
    case RARITY_COMMON:
        id = potion ? "item.consumable.rarity.potion.common"
                    : "item.consumable.rarity.scroll.common";
        break;
    case RARITY_VERY_COMMON:
        id = potion ? "item.consumable.rarity.potion.very_common"
                    : "item.consumable.rarity.scroll.very_common";
        break;
    default:
        id = potion ? "item.consumable.rarity.potion.buggy"
                    : "item.consumable.rarity.scroll.buggy";
        break;
    }
    return zh_message(id).display();
}

static string _describe_jewellery(const item_def &item, bool verbose)
{
    string description;

    description.reserve(200);

    if (verbose && !is_artefact(item) && item.is_identified())
    {
        // Explicit description of ring or amulet power.
        if (item.sub_type == AMU_REFLECTION)
        {
            const string amount = make_stringf("%+d", AMU_REFLECT_SH / 2);
            description += zh_message("item.jewellery.reflection_effect", {
                zh_text("amount", amount, amount)}).display();
        }
        else if (item.plus != 0)
        {
            const string amount = make_stringf("%+d", item.plus);
            auto stat_effect = [&](const string &stat, const string &localized) {
                description += zh_message("item.jewellery.stat_effect", {
                    zh_text("stat", stat, localized),
                    zh_text("amount", amount, amount)}).display();
            };
            switch (item.sub_type)
            {
            case RING_PROTECTION:
                stat_effect("AC", "护甲");
                break;

            case RING_EVASION:
                stat_effect("evasion", "闪避");
                break;

            case RING_STRENGTH:
                stat_effect("strength", "力量");
                break;

            case RING_INTELLIGENCE:
                stat_effect("intelligence", "智力");
                break;

            case RING_DEXTERITY:
                stat_effect("dexterity", "敏捷");
                break;

            case RING_SLAYING:
                description += zh_message("item.jewellery.slaying_effect", {
                    zh_text("amount", amount, amount)}).display();
                break;

            default:
                break;
            }
        }
    }

    // Artefact properties.
    string art_desc = _artefact_descrip(item);
    if (!art_desc.empty())
        description += "\n\n" + art_desc;

    if (verbose
        && crawl_state.need_save
        && item.is_identified()
        && !you.has_mutation(MUT_NO_JEWELLERY)
        && (is_artefact(item)
            || item.sub_type != RING_PROTECTION
               && item.sub_type != RING_EVASION
               && item.sub_type != AMU_REFLECTION))
    {
        description += _equipment_property_change(item);
    }

    return description;
}

static string _describe_item_curse(const item_def &item)
{
    if (!item.props.exists(CURSE_KNOWLEDGE_KEY))
        return "\n" + zh_source("detail.item.fixed", "It has a curse placed upon it.");

    const CrawlVector& curses = item.props[CURSE_KNOWLEDGE_KEY].get_vector();

    if (curses.empty())
        return "\n" + zh_source("detail.item.fixed", "It has a curse placed upon it.");

    string skills;
    string localized;
    bool supported = true;
    for (const auto &curse : curses)
    {
        const ZhArg entry = zh_curse_skills_arg("skills", curse);
        if (!skills.empty())
        {
            skills += ".\n";
            localized += "。\n";
        }
        skills += entry.canonical;
        localized += entry.localized;
        supported = supported && entry.supported;
    }
    const string description = string("\nIt has a curse which improves the following skills:\n")
        + skills + ".";
    if (supported)
        return "\n" + zh_message("item.curse.skills.fixed").display() + "\n"
            + zh_message("item.curse.skills_list", {
                ZhArg{"skills", ZhArgType::Text, skills, localized, true}}).display();
    return zh_message("item.curse.skills_english_fallback", {
        ZhArg{"description", ZhArgType::Text, description, description,
              false}}).display();
}

static string _describe_gizmo(const item_def &item)
{
    string ret = "\n\n";

    if (item.brand)
    {
        const string name = zh_word("item.gizmo.name.",
            gizmo_effect_name(item.brand)) + ":";
        const string fname = make_stringf("%-*s", MAX_ARTP_NAME_LEN + 1, name.c_str());
        string desc;
        switch (item.brand)
        {
            case SPGIZMO_SPELLMOTOR:
                desc = zh_source("detail.item.gizmo.fixed",
                    "Your spells cost less MP as you Rev up. Whenever you cast a spell, you make a melee attack against a random enemy in range.");
                break;

            case SPGIZMO_GADGETEER:
                desc = zh_source("detail.item.gizmo.fixed",
                    "Your evocable items recharge 30% faster and wands have a 30% chance to not spend a charge.");
                break;

            case SPGIZMO_REVGUARD:
                desc = zh_source("detail.item.gizmo.fixed",
                    "Your AC increases as you Rev (up to +5) and while fully Revved, your attacks may disarm enemies.");
                break;

            case SPGIZMO_AUTODAZZLE:
                desc = zh_source("detail.item.gizmo.fixed",
                    "It sometimes fires a blinding ray at enemies whose attacks you dodge.");
                break;

            default:
                break;
        }

        ret += _format_prop_desc(fname, desc) + "\n";
    }

    ret += _artefact_descrip(item);

    return ret;
}

bool is_dumpable_artefact(const item_def &item)
{
    return is_artefact(item) && item.is_identified();
}

static string &_trogsafe_lowercase(string &s)
{
    // hardcoding because of amnesia and brilliance msgs
    if (!starts_with(s, "Trog"))
        s = lowercase_first(s);
    return s;
}

static ZhArg _cannot_use_reason(const item_def &item, bool temp=true)
{
    // right now, description uselessness reasons only work for these four
    // item types..
    switch (item.base_type)
    {
    case OBJ_SCROLLS: return cannot_read_item_display_reason(&item, temp);
    case OBJ_POTIONS: return cannot_drink_item_display_reason(&item, temp);
    case OBJ_BAUBLES:
    case OBJ_MISCELLANY:
    case OBJ_WANDS:   return cannot_evoke_item_display_reason(&item, temp);
    default: return {"reason", ZhArgType::Text, "", "", true};
    }
}

static void _uselessness_desc(ostringstream &description, const item_def &item)
{
    if (!item.is_identified())
        return;
    if (is_useless_item(item, true))
    {
        ZhArg r;
        string id;
        string item_type;
        if (is_useless_item(item, false))
        {
            id = "item.useless.permanent";
            item_type = base_type_string(item.base_type);
            r = _cannot_use_reason(item, false);
        }
        else
        {
            switch (item.base_type)
            {
            case OBJ_SCROLLS:
                // this is somewhat heuristic:
                id = cannot_read_item_reason().size()
                    ? "item.useless.reading_impossible"
                    : "item.useless.reading_no_effect";
                break;
            case OBJ_POTIONS:
                // XX code dup
                id = cannot_drink_item_reason().size()
                    ? "item.useless.drinking_impossible"
                    : "item.useless.drinking_no_effect";
                break;
            case OBJ_MISCELLANY:
            case OBJ_WANDS:
                id = "item.useless.evoke";
                break;
            default:
                id = "item.useless.current_default";
                item_type = base_type_string(item.base_type);
                break;
            }
            r = _cannot_use_reason(item, true);
        }
        const bool empty = r.canonical.empty();
        const string reason = empty ? "." : string(": ") + _trogsafe_lowercase(r.canonical);
        const string localized_reason = empty ? "。" : "：" + r.localized;
        ZhArg reason_arg{"reason", ZhArgType::Text, reason, localized_reason,
                         empty || r.supported};
        if (item_type.empty())
            description << "\n\n" << zh_message(id, {reason_arg}).display();
        else
            description << "\n\n" << zh_message(id, {
                ZhArg{"item_type", ZhArgType::Name, item_type, "物品", true},
                reason_arg}).display();
    }
}

/**
 * Describe a specified item.
 *
 * @param item    The specified item.
 * @param mode    Controls various switches for the length of the description.
 * @return a string with the name, db desc, and some other data.
 */
string get_item_description(const item_def &item,
                            item_description_mode mode)
{
    ostringstream description;
    const bool verbose = mode == IDM_DEFAULT || mode == IDM_MONSTER;

#ifdef DEBUG_DIAGNOSTICS
    if (mode != IDM_MONSTER && mode != IDM_DUMP && !you.suppress_wizard)
    {
        description << setfill('0');
        description << "\n\n"
                    << "base: " << static_cast<int>(item.base_type)
                    << " sub: " << static_cast<int>(item.sub_type)
                    << " plus: " << item.plus << " plus2: " << item.plus2
                    << " special: " << item.special
                    << "\n"
                    << "quant: " << item.quantity
                    << " rnd?: " << static_cast<int>(item.rnd)
                    << " flags: " << hex << setw(8) << item.flags
                    << dec << "\n"
                    << "x: " << item.pos.x << " y: " << item.pos.y
                    << " link: " << item.link
                    << " slot: " << item.slot
                    << " ident_type: "
                    << type_is_identified(item)
                    << " value: " << item_value(item, true)
                    << "\nannotate: "
                    << stash_annotate_item(STASH_LUA_SEARCH_ANNOTATE, &item);
    }
#endif

    if (verbose || (item.base_type != OBJ_WEAPONS
                    && item.base_type != OBJ_ARMOUR
                    && item.base_type != OBJ_BOOKS))
    {
        if (mode != IDM_MONSTER)
            description << "\n\n";

        // Would be great to support DB descriptions in monster, but maybe tricky.
        bool need_base_desc = mode != IDM_MONSTER;
        if (mode == IDM_DUMP)
        {
            description << "["
                        << item.name(DESC_DBNAME, true, false, false)
                        << "]";
            need_base_desc = false;
        }
        else if (is_unrandom_artefact(item) && item.is_identified())
        {
            const string desc = _detail_database_text(get_artefact_name(item));
            if (!desc.empty())
            {
                description << desc;
                need_base_desc = false;
                description.seekp((streamoff)-1, ios_base::cur);
                description << " ";
            }
        }
        // Randart jewellery properties will be listed later,
        // just describe artefact status here.
        else if (is_artefact(item) && item.is_identified()
                 && item.base_type == OBJ_JEWELLERY)
        {
            description << zh_source("detail.item.fixed", "It is an ancient artefact.");
            need_base_desc = false;
        }
        else if (item.base_type == OBJ_GIZMOS)
        {
            description << zh_source("detail.item.fixed",
                "It is a fabulous contraption, custom-made by your own hands.");
            need_base_desc = false;
        }

        if (need_base_desc)
        {
            string db_name = item.name(DESC_DBNAME, true, false, false);
            string db_desc = _detail_database_text(db_name);

            if (db_desc.empty())
            {
                if (item_type_removed(item.base_type, item.sub_type))
                    description << zh_source("detail.item.fixed", "This item has been removed.") << "\n";
                else if (item.is_identified())
                {
                    description << "[ERROR: no desc for item name '" << db_name
                                << "']. Perhaps this item has been removed?\n";
                }
                else
                {
                    description << uppercase_first(zh_item_display(item, DESC_A));
                    description << ".\n";
                }
            }
            else
                description << db_desc;

            // Get rid of newline at end of description; in most cases we
            // will be adding "\n\n" immediately, and we want only one,
            // not two, blank lines. This allow allows the "unpleasant"
            // message for chunks to appear on the same line.
            description.seekp((streamoff)-1, ios_base::cur);
            description << " ";
        }
    }

    bool need_extra_line = true;
    string desc;
    switch (item.base_type)
    {
    // Weapons, armour, jewellery, books might be artefacts.
    case OBJ_WEAPONS:
        desc = _describe_weapon(item, verbose, mode == IDM_MONSTER);
        if (desc.empty())
            need_extra_line = false;
        else
            description << desc;
        break;

    case OBJ_ARMOUR:
        desc = _describe_armour(item, verbose, mode == IDM_MONSTER);
        if (desc.empty())
            need_extra_line = false;
        else
            description << desc;
        break;

    case OBJ_JEWELLERY:
        desc = _describe_jewellery(item, verbose);
        if (!desc.empty())
            description << desc;
        break;

    case OBJ_BOOKS:
        if (mode == IDM_MONSTER)
        {
            description << desc << terse_spell_list(item);
            need_extra_line = false;
        }
        else if (!verbose && is_random_artefact(item))
        {
            desc += describe_item_spells(item);
            if (desc.empty())
                need_extra_line = false;
            else
                description << desc;
        }
        break;

    case OBJ_MISSILES:
        description << _describe_ammo(item);
        break;

    case OBJ_CORPSES:
        break;

    case OBJ_STAVES:
        {
            if (verbose)
            {
                string stats = mode == IDM_MONSTER ? "" : "\n\n";
                _append_weapon_stats(stats, item);
                description << stats;
            }

            string art_desc = _artefact_descrip(item);
            if (!art_desc.empty())
                description << "\n\n" + art_desc;

            if (verbose && crawl_state.need_save && can_equip_item(item))
                description << _equipment_property_change(item);
        }
        if (verbose)
        {
            description << "\n\n" << zh_source("detail.item.fixed",
                                            "It falls into the 'Staves' category. ");
            description << _handedness_string(item);
        }
        break;

    case OBJ_MISCELLANY:
        if (item.sub_type == MISC_ZIGGURAT && you.zigs_completed)
        {
            const int zigs = you.zigs_completed;
            const string glow = zigs >= 27 ? "blinding" : // just plain silly
                                zigs >=  9 ? "dazzling" :
                                zigs >=  3 ? "bright" : "gentle";
            const string localized_glow = zigs >= 27 ? "刺眼" :
                                          zigs >=  9 ? "耀眼" :
                                          zigs >=  3 ? "明亮" : "柔和";
            description << zh_message("item.ziggurat.glow", {
                zh_text("glow", glow, localized_glow)}).display();
        }

        if (verbose)
        {
            _uselessness_desc(description, item);

            if (is_xp_evoker(item))
            {
                description << "\n\n";
                // slightly redundant with uselessness desc..
                const int charges = evoker_charges(item.sub_type);
                if (charges > 1)
                    description << zh_message("item.evoker.charges", {
                        zh_integer("charges", charges)}).display();
                else
                    description << zh_source("detail.item.fixed", "Once activated");
                description << zh_source("detail.item.fixed",
                    ", this device is rendered temporarily inert. However, it recharges as you gain experience.");

                if (evoker_plus(item.sub_type) < MAX_EVOKER_ENCHANT)
                {
                    description << zh_source("detail.item.fixed",
                        "\n\nAdditional devices of the same type can be combined with it to improve the rate at which it recharges.");
                }
                if (!is_useless_skill(SK_EVOCATIONS)
                       && you.skill(SK_EVOCATIONS) < MAX_SKILL_LEVEL)
                {
                    description << zh_source("detail.item.fixed",
                        "\n\nIncreasing your evocations skill will improve the rate at which it recharges.");
                }

                const string damage_str = evoke_damage_string(item);
                if (damage_str != "")
                    description << zh_message("item.evoker.damage", {
                        zh_numeric_notation("damage", damage_str)}).display();

                const string noise_str = evoke_noise_string(item);
                if (noise_str != "")
                    description << zh_message("item.evoker.noise", {
                        evoke_noise_display_arg("noise", item)}).display();
            }
        }

        break;

    case OBJ_POTIONS:
        if (item.is_identified())
        {
            if (verbose)
            {
                if (is_useless_item(item, true))
                    _uselessness_desc(description, item);
                // anything past here is useful
                // TODO: more effect messages.
                // heal: print heal chance
                // curing: print heal chance and/or what would be cured
                else if (item.sub_type == POT_LIGNIFY)
                    description << "\n\n" + _describe_lignify_ac();
                else if (item.sub_type == POT_CANCELLATION)
                {
                    const string state = describe_player_cancellation();
                    description << zh_message("item.potion.cancellation", {
                        ZhArg{"state", ZhArgType::Text, state, state, false}}).display();
                }
            }
            description << _consumable_rarity_display(item);
            need_extra_line = false;
        }
        break;

    case OBJ_WANDS:
        if (item.is_identified())
        {
            description << "\n";

            const string damage_str = evoke_damage_string(item);
            if (damage_str != "")
                description << zh_message("item.wand.damage", {
                    zh_numeric_notation("damage", damage_str)}).display();

            const string noise_str = evoke_noise_string(item);
            if (noise_str != "")
                description << zh_message("item.wand.noise", {
                    evoke_noise_display_arg("noise", item)}).display();

            if (verbose)
                _uselessness_desc(description, item);
        }
        break;

    case OBJ_SCROLLS:
        if (item.is_identified())
        {
            if (verbose)
                _uselessness_desc(description, item);

            description << _consumable_rarity_display(item);
            need_extra_line = false;
        }
        break;

    case OBJ_TALISMANS:
        if (mode != IDM_MONSTER)
            desc = _describe_talisman(item, verbose);
        if (desc.empty())
            need_extra_line = false;
        else
            description << desc;
        break;

    case OBJ_GIZMOS:
        description << _describe_gizmo(item);
        break;

    case OBJ_BAUBLES:
        if (!is_useless_item(item, false))
        {
            description << "\n" << _describe_talisman_form(transformation::flux);
            _append_skill_needed(desc, item, false, "   ");
            description << desc;
        }
        if (verbose)
            _uselessness_desc(description, item);
        break;

    case OBJ_ORBS:
    case OBJ_GOLD:
    case OBJ_RUNES:
    case OBJ_GEMS:

#if TAG_MAJOR_VERSION == 34
    case OBJ_FOOD:
    case OBJ_RODS:
#endif
        // No extra processing needed for these item types.
        break;

    default:
        die("Bad item class");
    }

    if (!verbose && item.cursed())
        description << _describe_item_curse(item);
    else if (verbose && mode != IDM_MONSTER)
    {
        if (need_extra_line)
            description << "\n";
        if (item.cursed())
            description << _describe_item_curse(item);

        if (is_artefact(item))
        {
            if (item.base_type == OBJ_ARMOUR
                || item.base_type == OBJ_WEAPONS)
            {
                if (you.has_mutation(MUT_ARTEFACT_ENCHANTING))
                {
                    if (!item.is_identified())
                        description << "\n" << zh_source("detail.item.fixed", "It is an ancient artefact.");
                    else if (is_unrandom_artefact(item)
                             || (item.base_type == OBJ_ARMOUR
                                 && item.plus >= armour_max_enchant(item))
                             || (item.base_type == OBJ_WEAPONS
                                 && item.plus >= MAX_WPN_ENCHANT))
                    {
                        description << "\n" << zh_source("detail.item.fixed",
                            "Enchanting this artefact any further is beyond even your skills.");
                    }
                }
                else
                {
                    description << "\n" << zh_source("detail.item.fixed",
                        "This ancient artefact cannot be changed by magic or mundane means.");
                }
            }
            // Randart jewellery has already displayed this line.
            // And gizmos really shouldn't (you just made them!)
            else if (item.base_type != OBJ_JEWELLERY && item.base_type != OBJ_GIZMOS
                     || (item.is_identified() && is_unrandom_artefact(item)))
            {
                description << "\n" << zh_source("detail.item.fixed", "It is an ancient artefact.");
            }
        }
    }

    if (god_hates_item(item))
    {
        const string god = uppercase_first(god_name(you.religion));
        const string localized_god = zh_lookup_exact(god);
        description << zh_message("item.god.disapproval", {
            ZhArg{"god", ZhArgType::Name, god, localized_god,
                  localized_god != god}}).display();
    }

    if (verbose && origin_describable(item))
        description << origin_display_desc(item);

    // This information is obscure and differs per-item, so looking it up in
    // a docs file you don't know to exist is tedious.
    if (verbose && mode != IDM_MONSTER)
    {
        description << "\n\n" << zh_message("item.detail.stash_search_prefixes").display() << " "
                    << userdef_annotate_item(STASH_LUA_SEARCH_ANNOTATE, &item);
        string menu_prefix = item_prefix(item, false);
        if (!menu_prefix.empty())
            description << "\n" << zh_message("item.detail.menu_colouring_prefixes").display()
                        << " " << menu_prefix;
    }

    return description.str();
}

string get_cloud_desc(cloud_type cloud, bool include_title)
{
    if (cloud == CLOUD_NONE)
        return "";
    const string cl_name = cloud_type_name(cloud);
    const string cl_desc = getLongDescription(cl_name + " cloud");

    string ret;
    if (include_title)
        ret = "A cloud of " + cl_name + (cl_desc.empty() ? "." : ".\n\n");
    ret += cl_desc + extra_cloud_info(cloud);
    return ret;
}

typedef struct {
    string title;
    string description;
    tile_def tile;
} extra_feature_desc;

static vector<extra_feature_desc> _get_feature_extra_descs(const coord_def &pos)
{
    vector<extra_feature_desc> ret;
    const dungeon_feature_type feat = env.map_knowledge(pos).feat();

    if (feat_is_tree(feat) && env.forest_awoken_until)
    {
        ret.push_back({
            "Awoken.",
            getLongDescription("awoken"),
            tile_def(TILE_AWOKEN_OVERLAY)
        });
    }
    if (feat_is_wall(feat) && env.map_knowledge(pos).flags & MAP_ICY)
    {
        ret.push_back({
            "A covering of ice.",
            getLongDescription("ice covered"),
            tile_def(TILE_FLOOR_ICY)
        });
    }
    else if (!feat_is_solid(feat))
    {
        if (haloed(pos) && !umbraed(pos))
        {
            ret.push_back({
                "A halo.",
                getLongDescription("haloed"),
                tile_def(TILE_HALO_RANGE)
            });
        }
        if (umbraed(pos) && !haloed(pos))
        {
            ret.push_back({
                "An umbra.",
                getLongDescription("umbraed"),
                tile_def(TILE_UMBRA)
            });
        }
        if (liquefied(pos, true))
        {
            ret.push_back({
                "Liquefied ground.",
                getLongDescription("liquefied"),
                tile_def(TILE_LIQUEFACTION)
            });
        }
        if (disjunction_haloed(pos))
        {
            ret.push_back({
                "Translocational energy.",
                getLongDescription("disjunction haloed"),
                tile_def(TILE_DISJUNCT)
            });
        }
    }
    if (const auto cloud = env.map_knowledge(pos).cloudinfo())
    {
        ret.push_back({
            "A cloud of " + cloud_type_name(cloud->type) + ".",
            get_cloud_desc(cloud->type, false),
            tile_def(tileidx_cloud(*cloud)),
        });
    }
    return ret;
}

static string _feat_action_desc(const vector<command_type>& actions,
                                                dungeon_feature_type feat)
{
    static const map<command_type, string> act_str =
    {
        { CMD_GO_UPSTAIRS,      "(<)go up" },
        { CMD_GO_DOWNSTAIRS,    "(>)go down" },
        { CMD_MAP_PREV_LEVEL,   "([)view destination" },
        { CMD_MAP_NEXT_LEVEL,   "(])view destination" },
        { CMD_OPEN_DOOR,        "(O)pen" },
        { CMD_CLOSE_DOOR,       "(C)lose" },

    };
    return comma_separated_fn(begin(actions), end(actions),
        [feat] (command_type cmd)
        {
            if (cmd == CMD_GO_DOWNSTAIRS && feat_is_altar(feat))
                return string("(>)pray");
            else if (cmd == CMD_GO_DOWNSTAIRS &&
                (feat == DNGN_ENTER_SHOP
                    || feat_is_portal(feat)
                    || feat_is_gate(feat)
                    || feat == DNGN_TRANSPORTER))
            {
                // XX disable for portals without item? The command still works.
                return string("(>)enter");
            }
            else if (cmd == CMD_GO_UPSTAIRS && feat_is_gate(feat))
                return string("(<)exit");
            else
                return act_str.at(cmd);
        },
        ", or ") + ".";
}

static vector<command_type> _allowed_feat_actions(const coord_def &pos)
{
    vector<command_type> actions;

    // Don't allow interacting with features while viewing other floors.
    if (!you.on_current_level)
        return actions;

    // ugh code duplication, some refactoring could be useful in all of this
    dungeon_feature_type feat = env.map_knowledge(pos).feat();
    // TODO: CMD_MAP_GOTO_TARGET
    const command_type dir = feat_stair_direction(feat);

    if (dir != CMD_NO_CMD && you.pos() == pos)
        actions.push_back(dir);

    if ((feat_is_staircase(feat) || feat_is_escape_hatch(feat))
        && !is_unknown_stair(pos)
        && feat != DNGN_EXIT_DUNGEON)
    {
        actions.push_back(dir == CMD_GO_UPSTAIRS
                            ? CMD_MAP_PREV_LEVEL : CMD_MAP_NEXT_LEVEL);
    }

    if (feat_is_door(feat) && feat != DNGN_BROKEN_DOOR && feat != DNGN_BROKEN_CLEAR_DOOR
        && (you.pos() - pos).rdist() == 1 // XX better handling of big gates
        && !feat_is_sealed(feat))
    {
        // XX maybe also a (G)o and traverse command?
        actions.push_back(feat_is_closed_door(feat)
            ? CMD_OPEN_DOOR : CMD_CLOSE_DOOR); // munge these later
    }
    return actions;
}

static string _esc_cmd_to_str(command_type cmd)
{
    string s = command_to_string(cmd);
    if (s == "<")
        return "<<";
    else
        return s;
}

void get_feature_desc(const coord_def &pos, describe_info &inf, bool include_extra)
{
    dungeon_feature_type feat = env.map_knowledge(pos).feat();

    string desc      = feature_description_at(pos, false, DESC_A);
    string desc_the  = feature_description_at(pos, false, DESC_THE);
    // remove " leading down", " leading back out of this place", etc.
    // XX maybe just dataify a short form, rather than do this awkward fixup?
    const vector<string> to_trim = {
        " leading ",
        " in the ",
        " through the ",
        " back to the ",
        " to a ",
        " to the "};
    for (const string &trim: to_trim)
        desc_the = desc_the.substr(0, desc_the.find(trim));

    string db_name   = feat == DNGN_ENTER_SHOP ? "a shop" : desc;
    strip_suffix(db_name, " (summoned)");
    string long_desc = getLongDescription(db_name);

    inf.title = uppercase_first(desc);
    if (!ends_with(desc, ".") && !ends_with(desc, "!")
        && !ends_with(desc, "?") && !desc.empty())
    {
        inf.title += ".";
    }
    // don't show "The floor." twice (maybe other things).
    if (trimmed_string(long_desc) == inf.title)
        long_desc = "";

    const string marker_desc =
        env.markers.property_at(pos, MAT_ANY, "feature_description_long");

    // suppress this if the feature changed out of view
    if (!marker_desc.empty() && env.grid(pos) == feat)
        long_desc += marker_desc;

    // Display branch descriptions on the entries to those branches.
    if (feat_is_stair(feat))
    {
        for (branch_iterator it; it; ++it)
        {
            if (it->entry_stairs == feat)
            {
                long_desc += "\n";
                long_desc += getLongDescription(it->shortname);
                break;
            }
        }
        const auto stair_dir = feat_stair_direction(feat);

        // it seems like there must be some way to refactor all this stuff so
        // it's cleaner...
        if (feat == DNGN_EXIT_DUNGEON)
        {
            // XX custom messages for other branch entrances/exits?
            long_desc += make_stringf(
                    "\nWhile standing here, you can exit the dungeon "
                    "with the <w>%s</w> key.",
                    _esc_cmd_to_str(stair_dir).c_str());
        }
        else if (feat_is_staircase(feat) || feat_is_escape_hatch(feat))
        {
            long_desc += make_stringf(
                    "\nWhile standing here, you can traverse %s "
                    "with the <w>%s</w> key.",
                    desc_the.c_str(),
                    _esc_cmd_to_str(stair_dir).c_str());

            if (is_unknown_stair(pos))
            {
                long_desc += " You have not yet explored it and cannot tell "
                             "where it leads.";
            }
            else
            {
                const command_type look_dir =
                    feat_stair_direction(feat) == CMD_GO_UPSTAIRS
                                         ? CMD_MAP_PREV_LEVEL
                                         : CMD_MAP_NEXT_LEVEL;
                long_desc +=
                    make_stringf(" You can view the location it leads to by "
                                 "examining it with <w>%s</w> and pressing "
                                 "<w>%s</w>.",
                                 command_to_string(CMD_DISPLAY_MAP).c_str(),
                                 command_to_string(look_dir).c_str());
            }
        }
        else if (feat == DNGN_ENTER_ABYSS || feat == DNGN_EXIT_THROUGH_ABYSS)
        {
            long_desc += make_stringf("\n(If you entered the Abyss now, you could be "
                                          "pulled as deep as Abyss:%d.)",
                                      abyss_default_depth(true));
        }
        else if (feat_is_portal(feat)
            || feat == DNGN_ENTER_ZIGGURAT) // augh this is technically a gate
        {
            long_desc += make_stringf(
                    "\nWhile standing here, you can %senter %s "
                    "with the <w>%s</w> key; it will vanish after you do so.",
                    feat == DNGN_ENTER_TROVE ? "try to " : "",
                    desc_the.c_str(),
                    _esc_cmd_to_str(stair_dir).c_str());
        }
        else if (feat_is_gate(feat))
        {
            // it's just special case after special case with these descs
            const string how = feat == DNGN_ENTER_HELL
                ? (stair_dir == CMD_GO_UPSTAIRS ? "to Hell" : "Hell")
                : make_stringf("through %s", desc_the.c_str());
            long_desc += make_stringf(
                    "\nWhile standing here, you can %s %s "
                    "with the <w>%s</w> key%s.",
                    stair_dir == CMD_GO_DOWNSTAIRS ? "enter" : "exit",
                    how.c_str(),
                    _esc_cmd_to_str(stair_dir).c_str(),
                    (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
                        ? " if you have enough runes" : "");
        }
    }
    else if (feat_is_altar(feat))
    {
        long_desc +=
            make_stringf("\nPray here with <w>%s</w> to learn more.\n",
                         command_to_string(CMD_GO_DOWNSTAIRS).c_str());
    }
    else if (feat == DNGN_ENTER_SHOP)
    {
        long_desc += make_stringf(
                "\nWhile standing here, you can enter <w>%s</w> with "
                "the <w>%s</w> key.",
                desc.c_str(),
                command_to_string(CMD_GO_DOWNSTAIRS).c_str());
    }
    else if (feat == DNGN_TRANSPORTER)
    {
        long_desc += make_stringf(
                "\nWhile standing here, you can enter %s with "
                "with the <w>%s</w> key.",
                desc_the.c_str(),
                command_to_string(CMD_GO_DOWNSTAIRS).c_str());
    }

    // mention that permanent trees are usually flammable
    // (except for autumnal trees in Wucad Mu's Monastery)
    if (feat_is_flammable(feat) && !is_temp_terrain(pos) && in_bounds(pos)
        && env.markers.property_at(pos, MAT_ANY, "veto_destroy") != "veto")
    {
        if (feat == DNGN_TREE)
            long_desc += "\n" + getLongDescription("tree burning");
        else if (feat == DNGN_MANGROVE)
            long_desc += "\n" + getLongDescription("mangrove burning");
        else if (feat == DNGN_DEMONIC_TREE)
            long_desc += "\n" + getLongDescription("demonic tree burning");
    }

    if (feat_is_door(feat) && feat != DNGN_BROKEN_DOOR && feat != DNGN_BROKEN_CLEAR_DOOR)
    {
        const bool openable = feat_is_closed_door(feat);
        const bool sealed = feat_is_sealed(feat);

        long_desc += make_stringf(
            "\nWhile adjacent to it, you can %s%s it by pressing the "
            "<w>%s</w> key.",
            sealed ? "normally " : "",
            openable ? "open" : "close",
            command_to_string(openable ? CMD_OPEN_DOOR : CMD_CLOSE_DOOR).c_str());
        if (sealed)
            long_desc += " However, this will not work until the sealing runes wear off.";
    }

    // mention that diggable walls are
    if (feat_is_diggable(feat) && in_bounds(pos)
        && env.markers.property_at(pos, MAT_ANY, "veto_destroy") != "veto")
    {
        long_desc += "\nIt can be dug through.";
    }

    // Mention things which don't stop LOS_NO_TRANS or reaching weapons,
    // but block movement.
    if (feat_is_solid(feat) && !feat_is_opaque(feat) && !feat_is_wall(feat)
        && !feat_is_closed_door(feat) && !feat_is_endless(feat))
    {
        if (feat_is_reachable_past(feat))
            long_desc += "\n" + zh_source("detail.feature.fixed",
                                             "A suitable weapon or spell can reach past it.");
        else
            long_desc += "\nSome spells can be cast through it.";
    }

    if (pos == you.pos() && you.on_current_level)
        long_desc += "\nYou are here.";

    inf.body << long_desc;

    if (include_extra)
    {
        const auto extra_descs = _get_feature_extra_descs(pos);
        for (const auto &d : extra_descs)
            inf.body << (d.title == extra_descs.back().title ? "" : "\n") << d.description;
    }

    inf.quote = zh_source("detail.monster.quote",
                          getQuoteString(db_name).c_str());
}

static bool _do_feat_action(const coord_def &pos, const command_type action)
{
    if (action == CMD_NO_CMD)
        return true;

    switch (action)
    {
    case CMD_GO_UPSTAIRS:
    case CMD_GO_DOWNSTAIRS:
        ASSERT(pos == you.pos());
        process_command(action, crawl_state.prev_cmd);
        return false;
    case CMD_MAP_PREV_LEVEL:
    case CMD_MAP_NEXT_LEVEL:
    {
        level_pos dest = map_follow_stairs(action == CMD_MAP_PREV_LEVEL, pos);
        // XX this leaves view mode on the ui stack, any issues?
        if (dest.is_valid())
        {
            show_map(dest, true, true);
            return true;
        }
        break;
    }
    case CMD_OPEN_DOOR:
        open_door_action(pos - you.pos());
        return false;
    case CMD_CLOSE_DOOR:
        close_door_action(pos - you.pos());
        return false;
    default:
        break;
    }
    return true;
}

/*
 * @return: true if the game should stay in any outer mode (e.g. `xv`).
 */
bool describe_feature_wide(const coord_def& pos, bool do_actions)
{
    typedef struct {
        string title, body, quote;
        tile_def tile;
    } feat_info;

    vector<feat_info> feats;

    {
        describe_info inf;
        get_feature_desc(pos, inf, false);
        feat_info f = { "", "", "", tile_def(TILEG_TODO)};
        f.title = inf.title;
        f.body = trimmed_string(inf.body.str());
#ifdef USE_TILE
        tileidx_t tile = tileidx_feature(pos);
        f.tile = tile_def(tile);
#endif
        f.quote = trimmed_string(inf.quote);
        if (f.title.size() || f.body.size() || f.quote.size())
            feats.emplace_back(f);
    }
    auto extra_descs = _get_feature_extra_descs(pos);
    for (const auto &desc : extra_descs)
    {
        feat_info f = { "", "", "", tile_def(TILEG_TODO)};
        f.title = desc.title;
        f.body = trimmed_string(desc.description);
        f.tile = desc.tile;
        if (f.title.size() || f.body.size() || f.quote.size())
            feats.emplace_back(f);
    }
    if (crawl_state.game_is_hints())
    {
        string hint_text = trimmed_string(hints_describe_pos(pos.x, pos.y));
        if (!hint_text.empty())
        {
            feat_info f = { "", "", "", tile_def(TILEG_TODO)};
            f.body = hint_text;
            f.tile = tile_def(TILEG_STARTUP_HINTS);
            feats.emplace_back(f);
        }
    }
    if (feats.empty())
        return true;

    auto scroller = make_shared<Scroller>();
    auto vbox = make_shared<Box>(Widget::VERT);

    for (const auto &feat : feats)
    {
        auto title_hbox = make_shared<Box>(Widget::HORZ);
#ifdef USE_TILE
        auto icon = make_shared<Image>();
        icon->set_tile(feat.tile);
        title_hbox->add_child(std::move(icon));
#endif
        auto title = make_shared<Text>(feat.title);
        title->set_margin_for_sdl(0, 0, 0, 10);
        title_hbox->add_child(std::move(title));
        title_hbox->set_cross_alignment(Widget::CENTER);

        const bool has_desc = feat.body != feat.title && feat.body != "";

        if (has_desc || &feat != &feats.back())
        {
            title_hbox->set_margin_for_crt(0, 0, 1, 0);
            title_hbox->set_margin_for_sdl(0, 0, 20, 0);
        }
        vbox->add_child(std::move(title_hbox));

        if (has_desc)
        {
            formatted_string desc_text = formatted_string::parse_string(feat.body);
            if (!feat.quote.empty())
            {
                desc_text.cprintf("\n_________________\n\n");
                desc_text += formatted_string::parse_string("<darkgrey>" + feat.quote + "</darkgrey>");
            }
            auto text = make_shared<Text>(desc_text);
            if (&feat != &feats.back())
            {
                text->set_margin_for_sdl(0, 0, 20, 0);
                text->set_margin_for_crt(0, 0, 1, 0);
            }
            text->set_wrap_text(true);
            vbox->add_child(text);
        }
    }

    vector<command_type> actions;
    if (do_actions)
        actions = _allowed_feat_actions(pos);
    formatted_string footer_text("", CYAN);
    if (!actions.empty())
    {
        const dungeon_feature_type feat = env.map_knowledge(pos).feat();
        footer_text += formatted_string(_feat_action_desc(actions, feat));
        auto footer = make_shared<Text>();
        footer->set_text(footer_text);
        footer->set_margin_for_crt(1, 0, 0, 0);
        footer->set_margin_for_sdl(20, 0, 0, 0);
        vbox->add_child(std::move(footer));
    }

#ifdef USE_TILE_LOCAL
    vbox->max_size().width = tiles.get_crt_font()->char_width()*80;
#endif
    scroller->set_child(std::move(vbox));

    auto popup = make_shared<ui::Popup>(scroller);

    bool done = false;
    command_type action = CMD_NO_CMD;

    // use on_hotkey_event, not on_event, to preempt the scroller key handling
    popup->on_hotkey_event([&](const KeyEvent& ev) {
        int lastch = ev.key();
        action = _get_action(lastch, actions);
        done = action != CMD_NO_CMD || ui::key_exits_popup(lastch, true);
        return true;
    });

#ifdef USE_TILE_WEB
    tiles.json_open_object();
    tiles.json_open_array("feats");
    for (const auto &feat : feats)
    {
        tiles.json_open_object();
        tiles.json_write_string("title", feat.title);
        tiles.json_write_string("body", trimmed_string(feat.body));
        tiles.json_write_string("quote", trimmed_string(feat.quote));
        tiles.json_open_object("tile");
        tiles.json_write_int("t", feat.tile.tile);
        tiles.json_write_int("tex", get_tile_texture(feat.tile.tile));
        if (feat.tile.ymax != TILE_Y)
            tiles.json_write_int("ymax", feat.tile.ymax);
        tiles.json_close_object();
        tiles.json_close_object();
    }
    tiles.json_close_array();
    tiles.json_write_string("actions", footer_text.tostring());
    tiles.push_ui_layout("describe-feature-wide", 0);
    popup->on_layout_pop([](){ tiles.pop_ui_layout(); });
#endif

    ui::run_layout(std::move(popup), done);
    return _do_feat_action(pos, action);
}

void describe_feature_type(dungeon_feature_type feat)
{
    describe_info inf;
    string name = feature_description(feat, NUM_TRAPS, "", DESC_A,
                                      NUM_BRANCHES);
    string title = uppercase_first(name);
    if (!ends_with(title, ".") && !ends_with(title, "!") && !ends_with(title, "?"))
        title += ".";
    inf.title = title;
    inf.body << getLongDescription(name);
#ifdef USE_TILE
    const tileidx_t idx = tileidx_feature_base(feat);
    tile_def tile = tile_def(idx);
    show_description(inf, &tile);
#else
    show_description(inf);
#endif
}

void get_item_desc(const item_def &item, describe_info &inf)
{
    // Don't use verbose descriptions if the item contains spells,
    // so we can actually output these spells if space is scarce.
    const item_description_mode mode = item.has_spells() ? IDM_PLAIN
                                                         : IDM_DEFAULT;
    string name = zh_item_display(item, DESC_INVENTORY_EQUIP) + ".";
    if (!in_inventory(item))
        name = uppercase_first(name);
    inf.body << name << get_item_description(item, mode);
}

static vector<command_type> _allowed_actions(const item_def& item)
{
    vector<command_type> actions;

    bool here = you.on_current_level && item.pos == you.pos();
    if (!in_inventory(item) && !here && is_travelsafe_square(item.pos))
    {
        // XX might be nice to have a way for this to be visible but grayed
        // out?
        actions.push_back(CMD_MAP_GOTO_TARGET);
        return actions;
    }

    // this is a copy, we can't do anything with it. (Probably via stash
    // search.)
    if (!valid_item_index(item.index()) && !in_inventory(item))
        return actions;

    // XX CMD_ACTIVATE
    switch (item.base_type)
    {
    case OBJ_SCROLLS:
        if (cannot_read_item_reason(&item, true).empty())
            actions.push_back(CMD_READ);
        break;
    case OBJ_POTIONS:
        if (cannot_drink_item_reason(&item, true).empty())
            actions.push_back(CMD_QUAFF);
        break;
    default:
        break;
    }

    if (!in_inventory(item))
    {
        // guaranteed to be at the player's position
        if (!item_is_stationary(item))
            actions.push_back(CMD_PICKUP);
        return actions;
    }

    // evoking from inventory only
    if (cannot_evoke_item_reason(&item, true).empty())
        actions.push_back(CMD_EVOKE);

    if (quiver::slot_to_action(item.link)->is_valid())
        actions.push_back(CMD_QUIVER_ITEM);

    // what is this for?
    if (clua.callbooleanfn(false, "ch_item_wieldable", "i", &item))
        actions.push_back(CMD_WIELD_WEAPON);

    switch (item.base_type)
    {
    case OBJ_WEAPONS:
    case OBJ_STAVES:
        if (!item_is_equipped(item))
        {
            if (item_is_wieldable(item))
                actions.push_back(CMD_WIELD_WEAPON);
        }
        else if (item_equip_slot(item) == SLOT_WEAPON)
            actions.push_back(CMD_UNWIELD_WEAPON);
        break;
    case OBJ_ARMOUR:
        if (item_is_equipped(item))
            actions.push_back(CMD_REMOVE_ARMOUR);
        else
            actions.push_back(CMD_WEAR_ARMOUR);
        break;
    case OBJ_JEWELLERY:
    case OBJ_TALISMANS:
        if (item_is_equipped(item))
            actions.push_back(CMD_REMOVE_JEWELLERY);
        else
            actions.push_back(CMD_WEAR_JEWELLERY);
        break;
    default:
        break;
    }
    actions.push_back(CMD_DROP);
    actions.push_back(CMD_ADJUST_INVENTORY);
    if (!you.has_mutation(MUT_DISTRIBUTED_TRAINING)
        && _is_below_training_target(item, false))
    {
        actions.push_back(CMD_SET_SKILL_TARGET);
    }

    if (!crawl_state.game_is_tutorial())
        actions.push_back(CMD_INSCRIBE_ITEM);

    return actions;
}

static ZhMessage _actions_desc(const vector<command_type>& actions)
{
    static const map<command_type, string> action_ids =
    {
        { CMD_WIELD_WEAPON, "item.action.wield" },
        { CMD_UNWIELD_WEAPON, "item.action.unwield" },
        { CMD_QUIVER_ITEM, "item.action.quiver" },
        { CMD_WEAR_ARMOUR, "item.action.wear_armour" },
        { CMD_REMOVE_ARMOUR, "item.action.remove_armour" },
        { CMD_EVOKE, "item.action.evoke" },
        { CMD_READ, "item.action.read" },
        { CMD_WEAR_JEWELLERY, "item.action.wear_jewellery" },
        { CMD_REMOVE_JEWELLERY, "item.action.remove_jewellery" },
        { CMD_QUAFF, "item.action.quaff" },
        { CMD_PICKUP, "item.action.pickup" },
        { CMD_DROP, "item.action.drop" },
        { CMD_INSCRIBE_ITEM, "item.action.inscribe" },
        { CMD_ADJUST_INVENTORY, "item.action.adjust" },
        { CMD_SET_SKILL_TARGET, "item.action.skill_target" },
        { CMD_MAP_GOTO_TARGET, "item.action.map_goto" },
    };
    bool push_quiver = false;
    vector<ZhMessage> phrases;
    for (command_type cmd : actions)
    {
        if (cmd == CMD_QUAFF) // assumes quaff appears before the potion quiver action
            push_quiver = true;
        if (push_quiver && cmd == CMD_QUIVER_ITEM)
            phrases.push_back(zh_message("item.action.quiver_after_quaff"));
        else
            phrases.push_back(zh_message(action_ids.at(cmd)));
    }

    if (phrases.size() == 1)
        return zh_message("item.actions.list.one",
            {zh_text("action", phrases[0].canonical, phrases[0].localized)});

    string canonical_middle, localized_middle;
    for (size_t i = 1; i + 1 < phrases.size(); ++i)
    {
        if (!canonical_middle.empty())
        {
            canonical_middle += ", ";
            localized_middle += "、";
        }
        canonical_middle += phrases[i].canonical;
        localized_middle += phrases[i].localized;
    }

    if (phrases.size() == 2)
        return zh_message("item.actions.list.two",
            {zh_text("first", phrases[0].canonical, phrases[0].localized),
             zh_text("last", phrases[1].canonical, phrases[1].localized)});

    return zh_message("item.actions.list.many",
        {zh_text("first", phrases[0].canonical, phrases[0].localized),
         zh_text("middle", canonical_middle, localized_middle),
         zh_text("last", phrases.back().canonical, phrases.back().localized)});
}

// Take a key and a list of commands and return the command from the list
// that corresponds to the key. Note that some keys are overloaded (but with
// mutually-exclusive actions), so it's not just a simple lookup.
static command_type _get_action(int key, vector<command_type> actions)
{
    static const map<command_type, int> act_key =
    {
        { CMD_WIELD_WEAPON,     'w' },
        { CMD_UNWIELD_WEAPON,   'u' },
        { CMD_QUIVER_ITEM,      'q' }, // except for potions, see below
        { CMD_WEAR_ARMOUR,      'w' },
        { CMD_REMOVE_ARMOUR,    't' },
        { CMD_EVOKE,            'v' },
        { CMD_READ,             'r' },
        { CMD_WEAR_JEWELLERY,   'p' },
        { CMD_REMOVE_JEWELLERY, 'r' },
        { CMD_QUAFF,            'q' },
        { CMD_DROP,             'd' },
        { CMD_INSCRIBE_ITEM,    'i' },
        { CMD_PICKUP,           'g' },
        { CMD_ADJUST_INVENTORY, '=' },
        { CMD_SET_SKILL_TARGET, 's' },
        { CMD_MAP_GOTO_TARGET,  'g' },
        { CMD_GO_UPSTAIRS,      '<' },
        { CMD_GO_DOWNSTAIRS,    '>' },
        { CMD_MAP_PREV_LEVEL,   '[' },
        { CMD_MAP_NEXT_LEVEL,   ']' },
        { CMD_OPEN_DOOR,        'o' },
        { CMD_CLOSE_DOOR,       'c' },
    };

    key = tolower_safe(key);
    bool push_quiver = false;

    for (auto cmd : actions)
    {
        if (cmd == CMD_QUAFF) // quaff must come first
            push_quiver = true;
        if (push_quiver && cmd == CMD_QUIVER_ITEM && key == 'v' // ugly
            || key == act_key.at(cmd))
        {
            return cmd;
        }
    }

    return CMD_NO_CMD;
}

static level_id _item_level_id(const item_def &item)
{
    level_id loc;
    // set on stash search only
    if (!item.props.exists("level_id"))
        return loc;

    try
    {
        loc = level_id::parse_level_id(item.props["level_id"].get_string());
    }
    catch (const bad_level_id&)
    {
        // die?
    }
    return loc;
}

/**
 * Do the specified action on the specified item.
 *
 * @param item    the item to have actions done on
 * @param action  the action to do
 * @return whether to stay in the inventory menu afterwards
 */
static bool _do_action(item_def &item, const command_type action)
{
    if (action == CMD_NO_CMD)
        return true;

    unwind_bool no_more(crawl_state.show_more_prompt, false);

    // ok in principle on floor items (though I didn't enable the last two)
    switch (action)
    {
    case CMD_MAP_GOTO_TARGET:
        if (in_bounds(item.pos))
        {
            level_id loc = _item_level_id(item); // stash search handling
            if (!loc.is_valid())
                loc = level_id::current(); // may still be during an excursion
            level_pos target(loc, item.pos);
            start_translevel_travel(target);
            return false;
        }
        break;
    case CMD_PICKUP:
        ASSERT(!in_inventory(item) && valid_item_index(item.index()));
        pickup_single_item(item.index(), item.quantity);
        return false;
    case CMD_READ:             read(&item);         return false;
    case CMD_QUAFF:            drink(&item);        return false;
    case CMD_INSCRIBE_ITEM:    inscribe_item(item); return false;
    case CMD_SET_SKILL_TARGET: target_item(item);   return false;
    default:
        break;
    }

    // inv item only
    const int slot = item.link;
    ASSERT_RANGE(slot, 0, ENDOFPACK);

    switch (action)
    {
    case CMD_WIELD_WEAPON:
    case CMD_WEAR_JEWELLERY:
    case CMD_WEAR_ARMOUR:
        try_equip_item(item);
        break;

    case CMD_REMOVE_ARMOUR:
    case CMD_UNWIELD_WEAPON:
    case CMD_REMOVE_JEWELLERY:
        try_unequip_item(item);
        break;

    case CMD_QUIVER_ITEM:
        quiver::set_to_quiver(quiver::slot_to_action(slot), you.quiver_action); // ugh
        break;

    case CMD_DROP:
        // TODO: it would be better if the inscription was checked before the
        // popup closes, but that is hard
        if (!check_warning_inscriptions(you.inv[slot], OPER_DROP))
            return true;
        drop_item(slot, item.quantity);
        break;
    case CMD_ADJUST_INVENTORY: adjust_item(0, &you.inv[slot]);
        break;
    case CMD_EVOKE:
        if (!check_warning_inscriptions(you.inv[slot], OPER_EVOKE))
            return true;
        evoke_item(you.inv[slot]);
        break;
    default:
        ui::error(make_stringf("illegal inventory cmd '%d'", action));
    }
    return false;
}

void target_item(item_def &item)
{
    const skill_type skill = _item_training_skill(item);
    if (skill == SK_NONE)
        return;

    const int target = _item_training_target(item);
    if (target == 0)
        return;

    you.set_training_target(skill, target, true);
    // ensure that the skill is at least enabled
    if (you.train[skill] == TRAINING_DISABLED)
        set_training_status(skill, TRAINING_ENABLED);
    you.train_alt[skill] = you.train[skill];
    reset_training();
}

/**
 *  Display a pop-up describe any item in the game.
 *
 *  @param item       the item to be described.
 *  @param fixup_desc a function (possibly null) to modify the
 *                    description before it's displayed.
 *  @param do_actions display interaction options
 *  @return an action to perform (if any was available or selected)
 *
 */
command_type describe_item_popup(const item_def &item,
                                 function<void (string&)> fixup_desc,
                                 bool do_actions)
{
    if (!item.defined())
        return CMD_NO_CMD;

    ZhLegacyGuard item_detail_guard("detail.item");

    // Dead players use no items.
    do_actions = do_actions && !(you.pending_revival || crawl_state.updating_scores);

    string name = zh_item_display(item, DESC_INVENTORY_EQUIP) + ".";
    if (!in_inventory(item))
        name = uppercase_first(name);

    string desc = "";
    level_id loc = _item_level_id(item);
    if (loc.is_valid() && loc != level_id::current())
    {
        // should be off-level stash search only
        desc += zh_message("item.location.offlevel", {
            zh_key("level", loc.describe(false, true))}).display();
        desc += "\n\n";
    }

    desc += get_item_description(item);

    string quote;
    if (is_unrandom_artefact(item) && item.is_identified())
        quote = _detail_database_text(get_artefact_name(item), true);
    else
        quote = _detail_database_text(item.name(DESC_DBNAME, true, false, false), true);

    if (!(crawl_state.game_is_hints_tutorial()
          || quote.empty()))
    {
        desc += "\n_________________\n\n<darkgrey>" + quote + "</darkgrey>";
    }

    if (crawl_state.game_is_hints())
    {
        desc += "\n\n" + hints_describe_item(item);
    }

    if (fixup_desc)
        fixup_desc(desc);

    formatted_string fs_desc = formatted_string::parse_string_raw(desc);

    spellset spells = item_spellset(item);
    formatted_string spells_desc;
    describe_spellset(spells, &item, spells_desc, nullptr);
#ifdef USE_TILE_WEB
    string desc_without_spells = fs_desc.to_colour_string(LIGHTGRAY);
#endif
    fs_desc += spells_desc;

    vector<command_type> actions;
    if (do_actions)
        actions = _allowed_actions(item);

    auto vbox = make_shared<Box>(Widget::VERT);
    auto title_hbox = make_shared<Box>(Widget::HORZ);

#ifdef USE_TILE
    vector<tile_def> item_tiles;
    get_tiles_for_item(item, item_tiles, true);
    if (item_tiles.size() > 0)
    {
        auto tiles_stack = make_shared<Stack>();
        for (const auto &tile : item_tiles)
        {
            auto icon = make_shared<Image>();
            icon->set_tile(tile);
            tiles_stack->add_child(std::move(icon));
        }
        title_hbox->add_child(std::move(tiles_stack));
    }
#endif

    auto title = make_shared<Text>(formatted_string::parse_string_raw(name));
    title->set_margin_for_sdl(0, 0, 0, 10);
    title_hbox->add_child(std::move(title));

    title_hbox->set_cross_alignment(Widget::CENTER);
    title_hbox->set_margin_for_crt(0, 0, 1, 0);
    title_hbox->set_margin_for_sdl(0, 0, 20, 0);
    vbox->add_child(std::move(title_hbox));

    auto scroller = make_shared<Scroller>();
    auto text = make_shared<Text>(fs_desc.trim());
    text->set_wrap_text(true);
    scroller->set_child(text);
    vbox->add_child(scroller);

    formatted_string footer_text("", CYAN);
    if (!actions.empty())
    {
        if (!spells.empty())
            footer_text += formatted_string::parse_string_raw(
                zh_message("item.actions.select_spell").display(), CYAN);
        footer_text += formatted_string::parse_string_raw(
            _actions_desc(actions).display(), CYAN);
        auto footer = make_shared<Text>();
        footer->set_text(footer_text);
        footer->set_margin_for_crt(1, 0, 0, 0);
        footer->set_margin_for_sdl(20, 0, 0, 0);
        vbox->add_child(std::move(footer));
    }

#ifdef USE_TILE_LOCAL
    vbox->max_size().width = tiles.get_crt_font()->char_width()*80;
#endif

    auto popup = make_shared<ui::Popup>(std::move(vbox));

    bool done = false;
    command_type action = CMD_NO_CMD;
    int lastch; // unused??
    bool show_spell_success = false;
    popup->on_keydown_event([&](const KeyEvent& ev) {
        const auto key = ev.key() == '{' ? 'i' : ev.key();
        lastch = key;
        action = _get_action(key, actions);
        if (action != CMD_NO_CMD || ui::key_exits_popup(key, true))
            done = true;
        else if (scroller->on_event(ev))
            return true;
        else if (key == '!'
                 && (is_equippable_item(item) || is_usable_talisman(item))
                 && item.is_identified())
        {
            string spell_success;
            // Only switch tab if there's any spell rate changes.
            if (!show_spell_success)
            {
                spell_success = _spell_fail_change_description(item, item_is_equipped(item));
                if (spell_success.empty())
                    return false;
            }

            show_spell_success = !show_spell_success;
            if (show_spell_success)
                text->set_text(formatted_string::parse_string_raw(spell_success));
            else
                text->set_text(fs_desc.trim());
#ifdef USE_TILE_WEB
            tiles.json_open_object();
            tiles.json_write_string("body", text->get_text().to_colour_string(LIGHTGREY));
            tiles.ui_state_change("describe-spell-success", -1);
#endif
        }

        const vector<pair<spell_type,char>> spell_map = map_chars_to_spells(spells);
        auto entry = find_if(spell_map.begin(), spell_map.end(),
                [key](const pair<spell_type,char>& e) { return e.second == key; });
        if (entry == spell_map.end())
            return false;
        describe_spell(entry->first, nullptr, &item);
        done = already_learning_spell();
        return true;
    });

#ifdef USE_TILE_WEB
    tiles.json_open_object();
    tiles.json_write_string("title", name);
    desc_without_spells += "SPELLSET_PLACEHOLDER";
    trim_string(desc_without_spells);
    tiles.json_write_string("body", desc_without_spells);
    write_spellset(spells, &item, nullptr);

    tiles.json_write_string("actions", footer_text.tostring());
    tiles.json_open_array("tiles");
    for (const auto &tile : item_tiles)
    {
        tiles.json_open_object();
        tiles.json_write_int("t", tile.tile);
        tiles.json_write_int("tex", get_tile_texture(tile.tile));
        if (tile.ymax != TILE_Y)
            tiles.json_write_int("ymax", tile.ymax);
        tiles.json_close_object();
    }
    tiles.json_close_array();
    tiles.push_ui_layout("describe-item", 0);
    popup->on_layout_pop([](){ tiles.pop_ui_layout(); });
#endif

    ui::run_layout(std::move(popup), done);

    return action;
}

/**
 *  Describe any item in the game and offer interactions if available.
 *
 *  This is split out from the popup because _do_action is necessarily non
 *  const but we would like to offer the description UI for items not in
 *  inventory in places where only a const item_def is available.
 *
 *  @param item       the item to be described.
 *  @param fixup_desc a function (possibly null) to modify the
 *                    description before it's displayed.
 *  @return whether to remain in the outer mode (inventory, `xv`) after the popup.
 *
 */
bool describe_item(item_def &item, function<void (string&)> fixup_desc, bool do_actions)
{
    command_type action = describe_item_popup(item, fixup_desc, do_actions);
    return _do_action(item, action);
}

void inscribe_item(item_def &item)
{
    mprf_nocap(MSGCH_EQUIPMENT, "%s", item.name(DESC_INVENTORY).c_str());

    const bool is_inscribed = !item.inscription.empty();
    string prompt = is_inscribed ? "Replace inscription with what? "
                                 : "Inscribe with what? ";

    char buf[79];
    int ret = msgwin_get_line(prompt, buf, sizeof buf, nullptr,
                              item.inscription);
    if (ret)
    {
        canned_msg(MSG_OK);
        return;
    }

    string new_inscrip = buf;
    trim_string_right(new_inscrip);

    if (item.inscription == new_inscrip)
    {
        canned_msg(MSG_OK);
        return;
    }

    item.inscription = new_inscrip;

    mprf_nocap(MSGCH_EQUIPMENT, "%s", item.name(DESC_INVENTORY).c_str());
    you.wield_change  = true;
    quiver::set_needs_redraw();
}

/**
 * List the simple calculated stats of a given spell, when cast by the player
 * in their current condition.
 *
 * @param spell     The spell in question.
 */
static ZhArg _spell_range_display_arg(spell_type spell)
{
    // Select the semantic absence at the producer; numeric range notation is
    // language-independent. Never parse the final English range string.
    if (spell_range(spell, &you, -1, true) <= 0)
        return zh_message_arg("range", "spell.stats.range.not_applicable");
    const string range = spell_range_string(spell);
    return zh_text("range", range, range);
}

static string _player_spell_stats(const spell_type spell)
{
    string description;
    description += zh_message("spell.level", {
        zh_integer("spell_level", spell_difficulty(spell))}).display();

    const string schools_en = spell_schools_string(spell);
    string schools_zh;
    bool schools_supported = true;
    size_t start = 0;
    while (start <= schools_en.size())
    {
        const size_t end = schools_en.find('/', start);
        const string school = schools_en.substr(start,
            end == string::npos ? string::npos : end - start);
        if (!schools_zh.empty())
            schools_zh += "/";
        const ZhArg school_arg = zh_word_arg("school", "spell.school.",
                                               school, ZhArgType::Name);
        schools_zh += school_arg.localized;
        schools_supported = schools_supported && school_arg.supported;
        if (end == string::npos)
            break;
        start = end + 1;
    }
    const string school_plural = schools_en.find('/') != string::npos ? "s" : "";
    description += zh_message("spell.stats.school", {
        zh_text("s", school_plural, ""),
        ZhArg{"schools", ZhArgType::Text, schools_en, schools_zh,
              schools_supported}}).display();

    if (!crawl_state.need_save
        || (get_spell_flags(spell) & spflag::monster))
    {
        description += "\n";
        return description; // all other info is player-dependent
    }


    string failure;
    if (you.divine_exegesis)
        failure = "0%";
    else if (spell_can_be_enkindled(spell) && you.has_mutation(MUT_MNEMOPHAGE)
             && !you.duration[DUR_ENKINDLED])
    {
        failure = make_stringf("%d%% <darkgrey>(%d%%)</darkgrey>",
                                    failure_rate_to_int(raw_spell_fail(spell)),
                                    failure_rate_to_int(raw_spell_fail(spell, true)));
    }
    else
        failure = failure_rate_to_string(raw_spell_fail(spell));
    description += zh_message("spell.stats.fail", {
        zh_text("failure", failure, failure)}).display();

    const string damage_string = spell_damage_string(spell);
    const string max_dam_string = spell_max_damage_string(spell);
    const int acc = spell_acc(spell);
    // TODO: generalize this pattern? It's very common in descriptions
    const int padding = (acc != -1) ? 8 : damage_string.size() ? 6 : 5;
    const string power = spell_power_string(spell);
    description += zh_message("spell.stats.power", {
        zh_text("indent", string(max(0, padding - 5), ' '),
                string(max(0, padding - 5), ' ')),
        zh_text("power", power, power)}).display();

    if (damage_string != "")
    {
        const string max_dam = spell_max_damage_string(spell);
        const string maximum = max_dam.empty() ? "" : " (max " + max_dam + ")";
        const string localized_maximum = max_dam.empty() ? ""
            : "（最高" + max_dam + "）";
        description += zh_message("spell.stats.damage", {
            zh_text("indent", string(max(0, padding - 6), ' '),
                    string(max(0, padding - 6), ' ')),
            // Dice notation is language-independent; the max label is part
            // of the template and has its own Chinese rendering.
            ZhArg{"damage", ZhArgType::Text, damage_string, damage_string, true},
            ZhArg{"maximum", ZhArgType::Text, maximum, localized_maximum, true}
        }).display();
    }
    if (acc != -1)
    {
        ostringstream acc_str;
        _print_bar(acc, 3, "", acc_str);
        const string accuracy = acc_str.str();
        description += zh_message("spell.stats.accuracy", {
            zh_text("indent", string(max(0, padding - 8), ' '),
                    string(max(0, padding - 8), ' ')),
            zh_text("accuracy", accuracy, accuracy)}).display();
    }

    description += zh_message("spell.stats.range", {
        zh_text("indent", string(max(0, padding - 5), ' '),
                string(max(0, padding - 5), ' ')),
        _spell_range_display_arg(spell)}).display();
    const ZhArg noise_arg = spell_noise_display_arg("noise", spell);
    description += zh_message("spell.stats.noise", {
        zh_text("indent", string(max(0, padding - 5), ' '),
                string(max(0, padding - 5), ' ')),
        noise_arg}).display();
    description += "\n";
    return description;
}

static string _get_skill_defense_change(skill_type skill)
{
    unwind_var<uint8_t> unwind_skill(you.skills[skill]);
    unwind_var<unsigned int> unwind_sp(you.skill_points[skill]);
    unwind_var<unsigned int> unwind_xp(you.total_experience);
    unwind_var<int> unwind_costlevel(you.skill_cost_level);

    const int cur_ac = you.armour_class_scaled(100);
    const int cur_ev = you.evasion_scaled(100, true);
    const int cur_sh = player_displayed_shield_class(100, true);

    const double cur_skill = you.skill(skill, 10, true) * 0.1;
    set_skill_level(skill, cur_skill + 1, true);

    const int new_ac = you.armour_class_scaled(100);
    const int new_ev = you.evasion_scaled(100, true);
    const int new_sh = player_displayed_shield_class(100, true);

    const float ac_diff = (float)(new_ac - cur_ac) / 100.0;
    const float ev_diff = (float)(new_ev - cur_ev) / 100.0;
    const float sh_diff = (float)(new_sh - cur_sh) / 100.0;

    const bool mastering = cur_skill >= 26;
    const string msg = mastering ? "mastering" : "training 1 level of";

    if (skill == SK_ARMOUR)
    {
        return "\n" + zh_message("detail.skill.defence.armour", {
            zh_text("action", msg, mastering ? "精通" : "训练1级"),
            zh_number("ac", ac_diff), zh_number("ev", ev_diff)},
            make_stringf("With your current stats and equipment, %s this skill would increase your AC by %.1f and your EV by %.1f.",
                         msg.c_str(), ac_diff, ev_diff)).display();
    }
    else if (skill == SK_DODGING)
    {
        return "\n" + zh_message("detail.skill.defence.dodging", {
            zh_text("action", msg, mastering ? "精通" : "训练1级"),
            zh_number("ev", ev_diff)},
            make_stringf("With your current stats and equipment, %s this skill would increase your EV by %.1f.",
                         msg.c_str(), ev_diff)).display();
    }
    else if (skill == SK_SHIELDS)
    {
        return "\n" + zh_message("detail.skill.defence.shields", {
            zh_text("action", msg, mastering ? "精通" : "训练1级"),
            zh_number("sh", sh_diff)},
            make_stringf("With your current stats and equipment, %s this skill would increase your SH by %.1f.",
                         msg.c_str(), sh_diff)).display();
    }

    return "";
}

string get_skill_description(skill_type skill, bool need_title)
{
    ZhLegacyGuard skill_detail_guard("detail.skill.producer");
    string lookup = skill_name(skill);
    string result = "";

    if (need_title)
    {
        result = zh_word("skill.name.", lookup);
        result += "\n\n";
    }

    result += _detail_database_text(lookup);

    if ((skill == SK_ARMOUR || skill == SK_DODGING || skill == SK_SHIELDS)
        && you.skills[skill] < MAX_SKILL_LEVEL && !is_useless_skill(skill))
    {
        result += _get_skill_defense_change(skill);
    }
    if (skill == SK_INVOCATIONS)
    {
        if (you.has_mutation(MUT_FORLORN))
        {
            result += "\n" + zh_message("detail.skill.invocations.forlorn").display();
        }
        else if (invo_skill(you.religion) != SK_INVOCATIONS)
        {
            const string god = uppercase_first(apostrophise(god_name(you.religion)));
            const auto god_name_arg = zh_glossary_name("god", "god.name", god_name(you.religion));
            result += "\n" + zh_message("detail.skill.invocations.unaffected", {
                ZhArg("god", ZhArgType::Name, god, god_name_arg.localized,
                      god_name_arg.supported)}).display();
        }
    }
    else if (skill == invo_skill(you.religion))
    {
        const string god = uppercase_first(apostrophise(god_name(you.religion)));
        const auto god_name_arg = zh_glossary_name("god", "god.name", god_name(you.religion));
        const string skill_en = skill_name(skill);
        const auto skill_arg = zh_glossary_name("skill", "skill.name", skill_en);
        result += "\n" + zh_message("detail.skill.invocations.based_on", {
            ZhArg("god", ZhArgType::Name, god, god_name_arg.localized,
                 god_name_arg.supported),
            skill_arg}).display();
    }

    if (is_harmful_skill(skill))
    {
        const string god = uppercase_first(god_name(you.religion));
        const auto god_name_arg = zh_glossary_name("god", "god.name", god_name(you.religion));
        result += "\n" + zh_message("detail.skill.god.dislikes_training", {
            ZhArg("god", ZhArgType::Name, god, god_name_arg.localized,
                 god_name_arg.supported)}).display();
    }

    return result;
}

/// How much ench_power do we think a monster casts this spell with, given a
/// certain spellpower?
static int _mon_hex_pow(const spell_type spell, const monster_info* mi, bool is_wand)
{
    int pow = is_wand ? mons_wand_power(mi->hd, spell)
                      : mons_power_for_hd(spell, mi->spell_hd());

    // Adjust by any power multipliers which may exist in zap definition.
    const zap_type ztype = spell_to_zap(spell);
    if (ztype != NUM_ZAPS)
        pow = zap_ench_power(ztype, pow, true);

    return pow;
}

/**
 * What are the odds of the given spell, cast by a monster with the given
 * spell_hd, affecting the player?
 */
int hex_chance(const spell_type spell, const monster_info* mi, bool is_wand)
{
    const int pow = _mon_hex_pow(spell, mi, is_wand);
    const int will = apply_willpower_bypass(*mi, you.willpower());
    const int chance = hex_success_chance(will, pow, 100, true);
    if (spell == SPELL_STRIP_WILLPOWER)
        return chance + (100 - chance) / 3; // ignores wl 1/3rd of the time
    return chance;
}

/**
 * Describe miscast effects from a spell
 *
 * @param spell
 */
// Compose semantic alternatives before choosing the complete parent sentence.
// Separators are reviewed templates; no assembled English is reverse matched.
static ZhArg _miscast_list_arg(const string &key, const vector<ZhArg> &parts,
                               const string &more_id, const string &final_id)
{
    if (parts.empty())
        return {key, ZhArgType::Text, "", "", true};
    ZhArg result = parts.front();
    result.key = "items";
    for (size_t i = 1; i < parts.size(); ++i)
    {
        const bool last = i + 1 == parts.size();
        ZhArg next = parts[i];
        next.key = last ? "last" : "next";
        result = zh_message_arg("items", last ? final_id : more_id, {result, next});
    }
    result.key = key;
    return result;
}

static vector<ZhArg> _miscast_effect_args(spell_type spell)
{
    const map<spschool, string> damage_ids = {
        { spschool::conjuration, "spell.miscast.flavor.irresistible" },
        { spschool::necromancy, "spell.miscast.flavor.draining" },
        { spschool::fire, "spell.miscast.flavor.fire" },
        { spschool::ice, "spell.miscast.flavor.cold" },
        { spschool::air, "spell.miscast.flavor.electric" },
        { spschool::earth, "spell.miscast.flavor.fragmentation" },
    };
    const map<spschool, string> effect_ids = {
        { spschool::summoning, "spell.miscast.effect.horror" },
        { spschool::translocation, "spell.miscast.effect.anchors" },
        { spschool::hexes, "spell.miscast.effect.slows" },
        { spschool::alchemy, "spell.miscast.effect.poisons" },
        { spschool::forgecraft, "spell.miscast.effect.corrodes" },
    };
    const spschools_type disciplines = get_spell_disciplines(spell);
    vector<ZhArg> effects;
    for (const auto &effect : effect_ids)
        if (disciplines & effect.first)
            effects.push_back(zh_message_arg("effect", effect.second));
    vector<ZhArg> flavours;
    for (const auto &flavour : damage_ids)
        if (disciplines & flavour.first)
            flavours.push_back(zh_message_arg("flavour", flavour.second));
    if (!flavours.empty())
        effects.push_back(zh_message_arg("effect", "spell.miscast.damage_clause", {
            zh_integer("damage", max_miscast_damage(spell)),
            _miscast_list_arg("flavours", flavours,
                "spell.miscast.flavor.list.more", "spell.miscast.flavor.list.final")}));
    return effects;
}

static ZhMessage _miscast_composition_message(spell_type spell)
{
    if (fail_severity(spell) == 0)
        return zh_message("spell.miscast_contamination", {
            ZhArg{"additional", ZhArgType::Text, "", "", true}});
    const vector<ZhArg> effects = _miscast_effect_args(spell);
    const bool multiple = effects.size() > 1;
    return zh_message(multiple ? "spell.miscast.parent.multiple"
                               : "spell.miscast.parent.single", {
        _miscast_list_arg(multiple ? "effects" : "effect", effects,
            "spell.miscast.effect.list.more", "spell.miscast.effect.list.final")});
}

/**
 * Describe mostly non-numeric player-specific information about a spell.
 *
 * (E.g., your god's opinion of it, whether it's in a high-level book that
 * you can't memorise from, whether it's currently useless for whatever
 * reason...)
 *
 * @param spell     The spell in question.
 */
static string _player_spell_desc(spell_type spell)
{
    if (!crawl_state.need_save || (get_spell_flags(spell) & spflag::monster)
        || !is_player_book_spell(spell))
    {
        return ""; // all info is player-dependent
    }

    ostringstream description;

    description << _miscast_composition_message(spell).display();

    if (spell == SPELL_BATTLESPHERE)
    {
        vector<spell_type> battlesphere_spells = player_battlesphere_spells();
        if (battlesphere_spells.empty())
            description << zh_message("spell.player.battlesphere_inactive").display();
        else
        {
            vector<string> spell_names_en, spell_names_zh;
            for (spell_type known_spell : battlesphere_spells)
            {
                const string name = spell_title(known_spell);
                spell_names_en.push_back(name);
                spell_names_zh.push_back(zh_lookup_exact(name));
            }
            description << zh_message("spell.player.battlesphere_fires", {
                ZhArg{"spells", ZhArgType::Text,
                    comma_separated_line(spell_names_en.begin(),
                                         spell_names_en.end(), " or "),
                    join_strings(spell_names_zh.begin(),
                                 spell_names_zh.end(), "、"), true}}).display();
        }
    }

    if (spell == SPELL_SPELLSPARK_SERVITOR)
    {
        spell_type servitor_spell = player_servitor_spell();
        if (servitor_spell == SPELL_NO_SPELL)
            description << zh_message("spell.player.servitor_inactive").display();
        else
        {
            const string name = spell_title(player_servitor_spell());
            description << zh_message("spell.player.servitor_casts", {
                ZhArg{"spell", ZhArgType::Name, name, zh_lookup_exact(name),
                      zh_lookup_exact(name) != name}}).display();
        }
    }
    else if (spell == SPELL_PLATINUM_PARAGON)
    {
        if (you.props.exists(PARAGON_WEAPON_KEY))
        {
            const item_def &weapon = you.props[PARAGON_WEAPON_KEY].get_item();
            description << zh_message("spell.player.paragon_weapon", {
                zh_item_arg("weapon", weapon, DESC_A)}).display();
        }
    }
    else if (you.has_spell(SPELL_SPELLSPARK_SERVITOR) && spell_servitorable(spell))
    {
        if (failure_rate_to_int(raw_spell_fail(spell)) <= 20)
            description << zh_message("spell.player.servitor_imbued.fixed").display();
        else
            description << zh_message("spell.player.servitor_imbued_if").display();
    }

    if (spell == SPELL_IRRADIATE)
        description << zh_message("spell.player.irradiate.fixed").display();

    // Report summon cap
    const int limit = summons_limit(spell, true);
    if (limit)
    {
        // Attempt to clarify that flayed ghosts are NOT included in the cap.
        const string creature = spell == SPELL_MARTYRS_KNELL
            ? "martyred shade" : "creature";
        description << zh_message("spell.player.summon_cap", {
            ZhArg{"count", ZhArgType::Text, number_in_words(limit),
                  to_string(limit), true},
            ZhArg{"creature", ZhArgType::Text, creature,
                  spell == SPELL_MARTYRS_KNELL ? "殉道者影灵" : "生物", true},
            ZhArg{"plural", ZhArgType::Text, limit > 1 ? "s" : "", "",
                  limit > 1}}).display();
    }

    if (god_hates_spell(spell, you.religion))
    {
        const string god = uppercase_first(god_name(you.religion));
        description << zh_message("spell.player.god_opinion", {
            ZhArg{"god", ZhArgType::Name, god, zh_lookup_exact(god),
                  zh_lookup_exact(god) != god},
            zh_text("opinion", "frowns upon", "不悦于")}).display();
    }
    else if (god_likes_spell(spell, you.religion))
    {
        const string god = uppercase_first(god_name(you.religion));
        description << zh_message("spell.player.god_opinion", {
            ZhArg{"god", ZhArgType::Name, god, zh_lookup_exact(god),
                  zh_lookup_exact(god) != god},
            zh_text("opinion", "supports", "支持")}).display();
    }

    if (you.has_mutation(MUT_MNEMOPHAGE) && spell_can_be_enkindled(spell))
        description << zh_message("spell.player.enkindled.fixed").display();

    if (!you_can_memorise(spell))
    {
        const ZhArg reason = desc_cannot_memorise_display_reason(spell);
        description << (you.has_spell(spell)
            ? zh_message("spell.player.cannot_cast_reason", {reason})
            : zh_message("spell.player.cannot_memorise_reason", {reason})).display();
    }
    else if (casting_is_useless(spell, true))
    {
        ZhArg reason = casting_uselessness_display_reason(spell, true);
        reason.canonical = uppercase_first(reason.canonical);
        if (!reason.supported)
            reason.localized = reason.canonical;
        description << zh_message("spell.player.casting_useless", {reason}).display();
    }
    else if (spell_is_useless(spell, true, false))
    {
        const ZhArg reason = spell_uselessness_display_reason(spell, true, false);
        if (reason.message_id == "spell.reason.no_hostiles")
            description << zh_message("spell.player.no_visible_hostiles").display();
        else
            description << zh_message("spell.player.useless_reason", {reason}).display();
    }

    if (spell == SPELL_GRAVE_CLAW && you.has_spell(SPELL_GRAVE_CLAW))
    {
        const int charges = you.props[GRAVE_CLAW_CHARGES_KEY].get_int();
        description << zh_message("spell.player.grave_claw", {
            zh_integer("charges", charges),
            zh_text("plural", charges == 1 ? "" : "s", ""),
            zh_integer("maximum", GRAVE_CLAW_MAX_CHARGES)}).display();
    }

    return description.str();
}


/**
 * Describe a spell, as cast by the player.
 *
 * @param spell     The spell in question.
 * @return          Information about the spell; does not include the title or
 *                  db description, but does include level, range, etc.
 */
string player_spell_desc(spell_type spell)
{
    return _player_spell_stats(spell) + _player_spell_desc(spell);
}

/**
 * Examine a given spell. Set the given string to its description, stats, &c.
 * If it's a book in a spell that the player is holding, mention the option to
 * memorise it.
 *
 * @param spell         The spell in question.
 * @param mon_owner     If this spell is being examined from a monster's
 *                      description, 'spell' is that monster. Else, null.
 * @param description   Set to the description & details of the spell.
 */
static void _get_spell_description(const spell_type spell,
                                  const monster_info *mon_owner,
                                  string &description)
{
    description.reserve(500);

    const string long_descrip = _detail_database_text(string(spell_title(spell))
                                                       + " spell");

    if (!long_descrip.empty())
        description += long_descrip;
    else
    {
        description += zh_source("detail.spell.fixed",
            "This spell has no description. Casting it may therefore be unwise. "
#ifdef DEBUG
            "Instead, go fix it.");
#else
            "Please file a bug report.");
#endif
    }

    if (mon_owner)
    {
        if (spell == SPELL_CONJURE_LIVING_SPELLS)
        {
            const spell_type living_spell = living_spell_type_for(mon_owner->type);
            const string spell_name = spell_title(living_spell);
            const string localized_spell = zh_lookup_exact(spell_name);
            description += zh_message("spell.monster.living_spell", {
                zh_monster_info_arg("actor", *mon_owner, DESC_A),
                ZhArg{"spell", ZhArgType::Name, spell_name,
                      localized_spell, localized_spell != spell_name}}).display();
        }
        else if (spell == SPELL_QUICKSILVER_BOLT)
        {
            if (player_is_debuffable())
            {
                const string state = describe_player_cancellation(true);
                description += zh_message("spell.monster.cancellation", {
                    ZhArg{"state", ZhArgType::Text, state, zh_lookup_exact(state),
                          zh_lookup_exact(state) != state}}).display();
            }
            else
                description += zh_source("detail.spell.fixed",
                    "\nYou currently have no enchantments that could be removed by this.\n");

        }

        const int hd = mon_owner->spell_hd();
        const int range = mons_spell_range_for_hd(spell, hd, mon_owner->is(MB_PLAYER_SERVITOR));
        const int minrange = (spell == SPELL_CALL_DOWN_LIGHTNING
                                || spell == SPELL_FLASHING_BALESTRA
                                || spell == SPELL_BECKONING_GALE ? 3 : 0);

        description += zh_message("spell.monster.range", {
            zh_text("range", range_string(range, -1, minrange),
                    range_string(range, -1, minrange))}).display();

        if (crawl_state.need_save && you_worship(GOD_DITHMENOS))
        {
            if (!valid_marionette_spell(spell))
            {
                description += zh_source("detail.spell.fixed",
                    "\n\n<magenta>This spell cannot be performed via Aphotic Marionette.</magenta>\n");
            }
            else if (spell_has_marionette_override(spell))
            {
                description += zh_source("detail.spell.fixed",
                    "\n\n<magenta>When cast via Aphotic Marionette, this spell will affect the player instead.");
            }
        }

        description += "\n";

        // Report summon cap
        const int limit = summons_limit(spell, false);
        if (limit)
        {
            const string count = number_in_words(limit);
            const string creature = spell == SPELL_MARTYRS_KNELL
                ? "martyred shade" : "creature";
            const string localized_creature = spell == SPELL_MARTYRS_KNELL
                ? "殉道者影灵" : "生物";
            description += zh_message("spell.monster.summon_cap", {
                zh_monster_info_arg("actor", *mon_owner, DESC_THE),
                ZhArg{"count", ZhArgType::Text, count, to_string(limit), true},
                ZhArg{"creature", ZhArgType::Text, creature,
                      localized_creature, true},
                ZhArg{"plural", ZhArgType::Text, limit > 1 ? "s" : "",
                      "", limit > 1}}).display();
        }

        // only display this if the player exists (not in the main menu)
        if (crawl_state.need_save && (get_spell_flags(spell) & spflag::WL_check)
#ifndef DEBUG_DIAGNOSTICS
            && mon_owner->attitude != ATT_FRIENDLY
#endif
            )
        {
            // XXX: This is slightly wrong in the very unlikely case the monster
            //      has a wand and *also* natively knows the spell inside that
            //      wand. But it's quite a bit of refactoring for something that
            //      will almost never happen.
            const bool is_wand = mon_owner->get_wand_spell() == spell;
            string wiz_info;
#ifdef WIZARD
            if (you.wizard)
                wiz_info += make_stringf(" (pow %d)", _mon_hex_pow(spell, mon_owner, is_wand));
#endif
            if (you.immune_to_hex(spell))
                description += zh_message("spell.monster.immune.fixed", {
                    zh_text("suffix", wiz_info, wiz_info)}).display();
            else
                description += zh_message("spell.monster.will_chance", {
                    zh_integer("chance", hex_chance(spell, mon_owner, is_wand)),
                    zh_text("suffix", wiz_info, wiz_info)}).display();
        }

    }
    else
        description += player_spell_desc(spell);

    const string quote = _detail_database_text(
        string(spell_title(spell)) + " spell", true);
    if (!quote.empty())
        description += "_________________\n\n<darkgrey>" + quote + "</darkgrey>";
}

/**
 * Provide the text description of a given spell.
 *
 * @param spell     The spell in question.
 * @param inf[out]  The spell's description is concatenated onto the end of
 *                  inf.body.
 */
#ifdef USE_TILE_LOCAL
void get_spell_desc(const spell_type spell, describe_info &inf)
{
    string desc;
    _get_spell_description(spell, nullptr, desc);
    inf.body << desc;
}
#endif

/**
 * Examine a given spell. List its description and details, and handle
 * memorising the spell in question, if the player is able & chooses to do so.
 *
 * @param spelled   The spell in question.
 * @param mon_owner If this spell is being examined from a monster's
 *                  description, 'mon_owner' is that monster. Else, null.
 */
void describe_spell(spell_type spell, const monster_info *mon_owner,
                    const item_def* item)
{
    UNUSED(item);
    ZhLegacyGuard spell_detail_guard("detail.spell");

    string desc;
    _get_spell_description(spell, mon_owner, desc);

    auto vbox = make_shared<Box>(Widget::VERT);
#ifdef USE_TILE_LOCAL
    vbox->max_size().width = tiles.get_crt_font()->char_width()*80;
#endif

    auto title_hbox = make_shared<Box>(Widget::HORZ);
#ifdef USE_TILE
    auto spell_icon = make_shared<Image>();
    spell_icon->set_tile(tile_def(tileidx_spell(spell)));
    title_hbox->add_child(std::move(spell_icon));
#endif

    string spl_title = zh_word("spell.name.", spell_title(spell));
    trim_string(desc);

    auto title = make_shared<Text>();
    title->set_text(formatted_string::parse_string_raw(spl_title));
    title->set_margin_for_sdl(0, 0, 0, 10);
    title_hbox->add_child(std::move(title));

    title_hbox->set_cross_alignment(Widget::CENTER);
    title_hbox->set_margin_for_crt(0, 0, 1, 0);
    title_hbox->set_margin_for_sdl(0, 0, 20, 0);
    vbox->add_child(std::move(title_hbox));

    auto scroller = make_shared<Scroller>();
    auto text = make_shared<Text>();
    text->set_text(formatted_string::parse_string_raw(desc));
    text->set_wrap_text(true);
    scroller->set_child(std::move(text));
    vbox->add_child(scroller);

    auto popup = make_shared<ui::Popup>(std::move(vbox));

    bool done = false;
    int lastch;
    popup->on_keydown_event([&](const KeyEvent& ev) {
        lastch = ev.key();
        done = ui::key_exits_popup(lastch, true);
        if (scroller->on_event(ev))
            return true;
        return done;
    });

#ifdef USE_TILE_WEB
    tiles.json_open_object();
    auto tile = tile_def(tileidx_spell(spell));
    tiles.json_open_object("tile");
    tiles.json_write_int("t", tile.tile);
    tiles.json_write_int("tex", get_tile_texture(tile.tile));
    if (tile.ymax != TILE_Y)
        tiles.json_write_int("ymax", tile.ymax);
    tiles.json_close_object();
    tiles.json_write_string("title", spl_title);
    tiles.json_write_string("desc", desc);
    tiles.push_ui_layout("describe-spell", 0);
    popup->on_layout_pop([](){ tiles.pop_ui_layout(); });
#endif

    ui::run_layout(std::move(popup), done);
}

/**
 * Examine a given ability. List its description and details.
 *
 * @param ability   The ability in question.
 */
void describe_ability(ability_type ability)
{
    describe_info inf;
    inf.title = ability_name(ability);
    inf.body << get_ability_desc(ability, false);
    tile_def tile = tile_def(tileidx_ability(ability));
    show_description(inf, &tile);
}

/**
 * Examine a given deck.
 */
void describe_deck(deck_type deck)
{
    describe_info inf;

    if (deck == DECK_STACK)
        inf.title = "A stacked deck";
    else
        inf.title = "The " + deck_name(deck);

    inf.body << deck_description(deck);

    show_description(inf);
}

/**
 * Describe a given mutation. List its description and details.
 */
void describe_mutation(mutation_type mut)
{
    describe_info inf;
    // TODO: mutation_name was not designed for use as a title, sometimes has
    // the wrong casing, is often cryptic
    inf.title = uppercase_first(mutation_name(mut)).c_str();

    const bool has_mutation = you.has_mutation(mut);
    if (has_mutation && mutation_max_levels(mut) > 1)
    {
        inf.title += make_stringf(" (level %d/%d)",
                                  you.get_mutation_level(mut),
                                  mutation_max_levels(mut));
    }
    inf.body << get_mutation_desc(mut);

    const tileidx_t base_tile_idx = get_mutation_tile(mut);
    if (base_tile_idx)
    {
        const int offset = (has_mutation
                            ? you.get_mutation_level(mut, false)
                            : mutation_max_levels(mut))
                           - 1;
        const tile_def tile = tile_def(base_tile_idx + offset);
        show_description(inf, &tile);
    }
    else
        show_description(inf);
}

string bane_long_description(bane_type bane, bool ignore_player)
{
    const bool player_has = !ignore_player && you.banes[bane];
    ostringstream output;

    const string key = make_stringf("%s bane", bane_name(bane, true).c_str());
    string lookup = getLongDescription(key);

    if (!lookup.empty())
    {
        hint_replace_cmds(lookup);
        output << lookup;
    }
    else
        output << bane_desc(bane) << "\n";

    if (bane == BANE_DILETTANTE && player_has)
    {
        CrawlVector& vec = you.props[DILETTANTE_SKILL_KEY].get_vector();
        output   << "\nYour " << skill_name(static_cast<skill_type>(vec[0].get_int()))
                 << ", " << skill_name(static_cast<skill_type>(vec[1].get_int()))
                 << ", and " << skill_name(static_cast<skill_type>(vec[2].get_int()))
                 << " are currently affected.\n";
    }

    const int dur = bane_base_duration(bane);
    string dur_str;
    if (dur > BANE_DUR_LONG)
        dur_str = "very long";
    else if (dur > BANE_DUR_MEDIUM)
        dur_str = "long";
    else if (dur > BANE_DUR_SHORT)
        dur_str = "moderate length of";
    else
        dur_str = "short length of";

    output << make_stringf("\nThis bane usually lasts a %s time.\n", dur_str.c_str());

    if (player_has)
    {
        int needed_xl = xl_to_remove_bane(bane);
        string desc = make_stringf("\n<lightmagenta>"
                                   "This bane will be lifted from you when you "
                                   "gain another %.1f XLs worth of experience."
                                   "</lightmagenta>",
                                    (float)needed_xl / 10.0f);
        output << desc;
    }

    return output.str();
}

void describe_bane(bane_type bane)
{
    describe_info inf;
    inf.title = uppercase_first(bane_name(bane));
    inf.body << bane_long_description(bane);

    show_description(inf);
}

static string _describe_draconian(const monster_info& mi)
{
    string description;
    const int subsp = mi.draconian_subspecies();

    if (subsp != mi.type)
    {
        switch (subsp)
        {
        case MONS_BLACK_DRACONIAN:      description += zh_message("monster.draconian.scales.black").display() + " ";   break;
        case MONS_YELLOW_DRACONIAN:     description += zh_message("monster.draconian.scales.yellow").display() + " ";  break;
        case MONS_GREEN_DRACONIAN:      description += zh_message("monster.draconian.scales.green").display() + " ";   break;
        case MONS_PURPLE_DRACONIAN:     description += zh_message("monster.draconian.scales.purple").display() + " ";  break;
        case MONS_RED_DRACONIAN:        description += zh_message("monster.draconian.scales.red").display() + " ";     break;
        case MONS_WHITE_DRACONIAN:      description += zh_message("monster.draconian.scales.white").display() + " ";   break;
        case MONS_GREY_DRACONIAN:       description += zh_message("monster.draconian.scales.grey").display() + " ";    break;
        case MONS_PALE_DRACONIAN:       description += zh_message("monster.draconian.scales.pale").display() + " ";    break;
        default:
            break;
        }
    }

    switch (subsp)
    {
    case MONS_BLACK_DRACONIAN:
        description += zh_message("monster.draconian.desc.black").display();
        break;
    case MONS_YELLOW_DRACONIAN:
        description += zh_message("monster.draconian.desc.yellow").display();
        break;
    case MONS_GREEN_DRACONIAN:
        description += zh_message("monster.draconian.desc.green").display();
        break;
    case MONS_PURPLE_DRACONIAN:
        description += zh_message("monster.draconian.desc.purple").display();
        break;
    case MONS_RED_DRACONIAN:
        description += zh_message("monster.draconian.desc.red").display();
        break;
    case MONS_WHITE_DRACONIAN:
        description += zh_message("monster.draconian.desc.white").display();
        break;
    case MONS_GREY_DRACONIAN:
        description += zh_message("monster.draconian.desc.grey").display();
        break;
    case MONS_PALE_DRACONIAN:
        description += zh_message("monster.draconian.desc.pale").display();
        break;
    default:
        break;
    }

    return description;
}


static string _get_threat_desc(mon_threat_level_type threat)
{
    switch (threat)
    {
    case MTHRT_UNDEF: // ?
    case MTHRT_TRIVIAL: return zh_source("detail.monster.table_value", "Minor");
    case MTHRT_EASY:    return zh_source("detail.monster.table_value", "Low");
    case MTHRT_TOUGH:   return zh_source("detail.monster.table_value", "High");
    case MTHRT_NASTY:   return zh_source("detail.monster.table_value", "Lethal");
    default:            return zh_source("detail.monster.table_value", "Eggstreme");
    }
}

static string _flavour_base_desc(attack_flavour flavour)
{
    static const map<attack_flavour, string> base_descs = {
        { AF_ACID,              "acid damage"},
        { AF_REACH_TONGUE,      "acid damage" },
        { AF_BLINK,             "blink self" },
        { AF_BLINK_WITH,        "blink together with the defender" },
        { AF_COLD,              "cold damage" },
        { AF_CONFUSE,           "cause confusion" },
        { AF_DRAIN,             "drain life" },
        { AF_VAMPIRIC,          "drain health from the living" },
        { AF_DRAIN_SPEED,       "drain speed" },
        { AF_ANTIMAGIC,         "drain magic" },
        { AF_SCARAB,            "drain speed and health" },
        { AF_ELEC,              "electric damage" },
        { AF_FIRE,              "fire damage" },
        { AF_SEAR,              "remove fire resistance" },
        { AF_MINIPARA,          "poison and momentary paralysis" },
        { AF_POISON_PARALYSE,   "poison and paralysis/slowing" },
        { AF_POISON,            "poison" },
        { AF_REACH_STING,       "poison" },
        { AF_POISON_STRONG,     "strong poison" },
        { AF_DISTORT,           "distortion" },
        { AF_RIFT,              "distortion" },
        { AF_RAGE,              "drive defenders berserk" },
        { AF_CHAOTIC,           "chaos" },
        { AF_STEAL,             "steal items" },
        { AF_CRUSH,             "begin ongoing constriction" },
        { AF_REACH,             "" },
        { AF_HOLY,              "extra damage to undead/demons" },
        { AF_PAIN,              "extra pain damage to the living" },
        { AF_ENSNARE,           "ensnare with webbing" },
        { AF_FLOOD,             "flood the defender's lungs" },
        { AF_PURE_FIRE,         "" },
        { AF_VULN,              "reduce willpower" },
        { AF_SHADOWSTAB,        "increased damage when unseen" },
        { AF_DROWN,             "drowning damage" },
        { AF_CORRODE,           "cause corrosion" },
        { AF_TRAMPLE,           "knock back the defender" },
        { AF_WEAKNESS,          "cause weakness" },
        { AF_BARBS,             "embed barbs" },
        { AF_SPIDER,            "summon a spider" },
        { AF_BLOODZERK,         "become enraged on drawing blood" },
        { AF_SLEEP,             "induce sleep" },
        { AF_SWOOP,             "swoops behind the defender beforehand" },
        { AF_FLANK,             "slips behind the defender beforehand" },
        { AF_DRAG,              "drag the defender backwards"},
        { AF_FOUL_FLAME,        "extra damage, especially to the good" },
        { AF_HELL_HUNT,         "summon demonic beasts" },
        { AF_SWARM,             "summon more of itself" },
        { AF_ALEMBIC,           "vent poison clouds" },
        { AF_BOMBLET,           "deploy bomblets" },
        { AF_AIRSTRIKE,         "open air damage" },
        { AF_TRICKSTER,         "drain, daze, or confuse" },
        { AF_REACH_CLEAVE_UGLY, "random ugly thing damage" },
        { AF_DOOM,              "inflict doom" },
        { AF_SLIMIFY,           "slowly slimify the target" },
        { AF_DIM,               "diminish the target's spells" },
        { AF_PLAIN,             "" },
    };

    const string* desc = map_find(base_descs, flavour);
    ASSERT(desc);
    if (desc->empty())
        return "";
    return zh_word("monster.attack.atom.", *desc);
}

static ZhArg _monster_attack_atom_arg(const string &text,
                                      const string &key = "value")
{
    return zh_word_arg(key, "monster.attack.atom.", text);
}

struct mon_attack_info
{
    mon_attack_def definition;
    const item_def* weapon;
    bool operator < (const mon_attack_info &other) const
    {
        return std::tie(definition.type, definition.flavour,
                        definition.damage, weapon)
             < std::tie(other.definition.type, other.definition.flavour,
                        other.definition.damage, other.weapon);
    }
};

/**
 * What weapon is the given monster using for the given attack, if any?
 *
 * @param mi        The monster in question.
 * @param atk       The attack number. (E.g. 0, 1, 2...)
 * @return          The melee weapon being used by the monster for the given
 *                  attack, if any.
 */
static const item_def* _weapon_for_attack(const monster_info& mi, int atk)
{
    // XXX: duplicates monster::weapon()
    if (mi.type == MONS_DRAUGR && atk > 0)
        return nullptr;
    if ((atk % 2) && mi.wields_two_weapons())
    {
        item_def *alt_weap = mi.inv[MSLOT_ALT_WEAPON].get();
        if (alt_weap && is_weapon(*alt_weap))
            return alt_weap;
    }
    item_def* weapon = mi.inv[MSLOT_WEAPON].get();
    if (weapon && is_weapon(*weapon))
        return weapon;
    return nullptr;
}

static mon_attack_info _atk_info(const monster_info& mi, int i)
{
    const mon_attack_def &attack = mi.attack[i];
    const item_def* weapon = nullptr;
    // XXX: duplicates monster::weapon()
    if (attack.type == AT_HIT || attack.type == AT_WEAP_ONLY)
        weapon = _weapon_for_attack(mi, i);
    mon_attack_info attack_info = { attack, weapon };
    return attack_info;
}

// Return a string describing the maximum damage from a monster's weapon brand
static string _brand_damage_string(const monster_info &mi, brand_type brand,
                                   int dam, int wpn_base_dmg = 0)
{
    const string name = brand_type_name(brand, true);
    const ZhArg brand_arg = _monster_attack_atom_arg(name, "brand");
    int brand_dam;
    // Only include damaging brands
    // Heavy is included in base damage calculations instead
    switch (brand)
    {
        case SPWPN_FLAMING:
        case SPWPN_FREEZING:
        case SPWPN_DRAINING:
        case SPWPN_CONCUSSION:
            brand_dam = dam * 3 / 4;
            break;
        case SPWPN_ELECTROCUTION:
            brand_dam = 20;
            break;
        case SPWPN_DISTORTION:
            brand_dam = 26;
            break;
        case SPWPN_HOLY_WRATH:
            // Hopefully this isn't too confusing for non-holy-vuln players
            brand_dam = dam * 15 / 10;
            break;
        case SPWPN_FOUL_FLAME:
            brand_dam = dam * 0.75;
            break;
        case SPWPN_PAIN:
            brand_dam = mi.has_necromancy_spell() ? mi.hd * 2 : mi.hd / 2;
            break;
        case SPWPN_VALOUR:
        {
            const dice_def dmg = zap_damage(ZAP_VALOUR_BEAM, wpn_base_dmg, true, false);
            brand_dam = dmg.num * dmg.size;
            break;
        }
        case SPWPN_ENTANGLING:
            brand_dam = 4;
            break;
        case SPWPN_SUNDERING:
            return zh_message("monster.attack.brand_sundering", {
                zh_integer("damage", dam * 3 / 2)}).display();
        case SPWPN_VENOM:
        case SPWPN_ANTIMAGIC:
        case SPWPN_CHAOS:
            return zh_message("monster.attack.brand_only", {brand_arg}).display();
        default:
            return "";
    }

    return zh_message("monster.attack.brand_damage", {
        zh_integer("damage", brand_dam), brand_arg}).display();
}

// Max damage from a magical staff with a given amount of staff & evo skill
static int _staff_max_damage(stave_type staff, int staff_skill, int evo_skill)
{
    return max(0, (2 * staff_skill + evo_skill) * staff_damage_mult(staff) / 80 - 1);
}

// Describe the damage from a monster's magical staff
static string _monster_staff_damage_string(const monster_info &mi,
                                           stave_type staff)
{
    // From monster::skill
    const int evo_skill = mi.hd;
    int staff_skill;
    if (staff == STAFF_NECROMANCY)
        staff_skill = mi.has_necromancy_spell() ? mi.hd : mi.hd / 2;
    else
        staff_skill = mi.is_actual_spellcaster() ? mi.hd : mi.hd / 3;

    // "earth" tries to communicate the damage reduction when flying
    // XXX "conj" isn't a damage type, but we want to communicate
    // that the damage is flat staff bonus damage somehow.
    string dam_type_string = staff == STAFF_FIRE          ? "fire"
                           : staff == STAFF_COLD          ? "cold"
                           : staff == STAFF_AIR           ? "elec"
                           : staff == STAFF_EARTH         ? "earth"
                           : staff == STAFF_NECROMANCY    ? "drain" // pain?
                           : staff == STAFF_ALCHEMY       ? "poison"
                           /*staff == STAFF_CONJURATION*/ : "conj";

    return zh_message("monster.attack.brand_damage", {
        zh_integer("damage", _staff_max_damage(staff, staff_skill, evo_skill)),
        _monster_attack_atom_arg(dam_type_string, "brand")}).display();
}

struct mon_attack_desc_info
{
    map<mon_attack_info, int> attack_counts;
    brand_type special_flavour;
    bool has_any_flavour;
    bool flavour_without_dam;
    bool plural;
    size_t attk_desc_width;
    size_t damage_width;
    size_t bonus_width;
    vector<string> attack_descriptions;
    vector<string> damage_descriptions;
    vector<string> bonus_descriptions;
};

static void _check_attack_counts_and_flavours(const monster_info &mi,
                                              mon_attack_desc_info &di)
{
    for (int i = 0; i < MAX_NUM_ATTACKS; i++)
    {
        mon_attack_info attack_info = _atk_info(mi, i);
        const mon_attack_def &attack = attack_info.definition;
        if (attack.type == AT_NONE)
            break; // assumes there are no gaps in attack arrays

        // Multi-headed monsters must always have their multi-attack in the
        // first slot (unless they're draugr, where the weapon hit is always
        // first).
        if (mi.has_hydra_multi_attack()
             && i == (mi.type == MONS_DRAUGR ? 1 : 0))
        {
            // XXX: Subtract the copies of this attack that will be found in
            //      remaining attack slots.
            di.attack_counts[attack_info] =
                mi.num_heads - (mi.type == MONS_DRAUGR ? 2 : 3);
        }
        else
            ++di.attack_counts[attack_info];

        if (i > 0)
            di.plural = true;

        const item_def *quiv = mi.inv[MSLOT_MISSILE].get();
        if (quiv && quiv->base_type == OBJ_MISSILES)
        {
            di.plural = true;
            if (quiv->sub_type == MI_DART || quiv->sub_type == MI_THROWING_NET)
            {
                di.has_any_flavour = true;
                di.flavour_without_dam = true;
            }
        }

        // Nessos' special cased poisonous ranged attacks
        if (mi.type == MONS_NESSOS && attack_info.weapon && is_range_weapon(*attack_info.weapon))
        {
            di.has_any_flavour = true;
            di.flavour_without_dam = true;
        }

        if (attack.flavour == AF_PLAIN || attack.flavour == AF_PURE_FIRE)
            continue;

        di.has_any_flavour = true;
        const bool needs_dam = !flavour_triggers_damageless(attack.flavour)
                                && !flavour_has_mobility(attack.flavour)
                                && !flavour_has_reach(attack.flavour);
        if (!needs_dam && attack.flavour != AF_REACH_TONGUE)
            di.flavour_without_dam = true;
    }
}

static void _add_attack_flavour_desc(string& desc, attack_flavour flavour,
                                     const mon_attack_def &attack,
                                     mon_attack_desc_info &di, int flav_dam, int real_dam,
                                     int attk_mult)
{
    if (!desc.empty())
        desc += zh_message("monster.attack.separator").display();

    desc += uppercase_first(_flavour_base_desc(flavour));
    if (flav_dam && attack.flavour != AF_PURE_FIRE)
    {
        desc += zh_message("monster.attack.flavour_max", {
            zh_integer("damage", flav_dam),
            zh_text("each", attk_mult > 1 ? " each" : "",
                    attk_mult > 1 ? "每次" : "")}).display();
    }
    else if (flavour == AF_DRAIN)
        desc += zh_message("monster.attack.drain_max", {
            zh_integer("damage", real_dam / 2)}).display();
    else if (flavour == AF_CRUSH)
    {
        desc += zh_message("monster.attack.damage_range", {
            zh_integer("minimum", attack.damage),
            zh_integer("maximum", attack.damage * 2)}).display();
    }

    if (di.flavour_without_dam
        && !desc.empty()
        && !flavour_triggers_damageless(attack.flavour)
        && !flavour_has_mobility(attack.flavour)
        && !(attack.flavour == AF_REACH_CLEAVE_UGLY))
    {
        desc += zh_message("monster.attack.if_damage_dealt").display();
    }

    if (flavour_has_reach(attack.flavour))
    {
        const char *reach_id = desc.empty() ? "monster.attack.reaches"
            : flavour == AF_REACH_CLEAVE_UGLY ? "monster.attack.cleaves"
                                               : "monster.attack.reaches_semicolon";
        desc += zh_message(reach_id).display();
        desc += zh_message(flavour == AF_RIFT ? "monster.attack.very_far"
                                              : "monster.attack.from_afar").display();
    }
}

// Get all the info required to form one row of the table of attacks.
static void _attacks_table_row(const monster_info &mi, mon_attack_desc_info &di,
                               const mon_attack_info &info, const item_def* wpn)
{
    const mon_attack_def &attack = info.definition;
    const bool ranged = wpn && is_range_weapon(*wpn);

    int attk_mult = di.attack_counts[info];
    di.attack_counts[info] = 0;

    // Part 1: The "Attacks" column
    // Display the name of the attack, along with any weapon used with it

    if (weapon_multihits(wpn))
        attk_mult *= weapon_hits_per_swing(*wpn);
    string attk_name = mon_attack_name_short(attack.type);
    ZhArg attk_arg = _monster_attack_atom_arg(attk_name, "attack");
    attk_arg.canonical = uppercase_first(attk_name);
    if (ranged)
    {
        attk_name = "Shoot";
        attk_arg = _monster_attack_atom_arg(attk_name, "attack");
    }
    string weapon_descriptor = "";
    if (wpn)
        weapon_descriptor = ": " + wpn->name(DESC_PLAIN, true, true, false);
    else if (di.special_flavour != SPWPN_NORMAL)
        weapon_descriptor = ": " + ghost_brand_name(di.special_flavour, mi.type);
    ZhArg weapon_arg = zh_text("weapon", weapon_descriptor, weapon_descriptor);
    if (wpn)
    {
        const ZhArg item_arg = zh_item_arg("weapon", *wpn, DESC_PLAIN);
        weapon_arg.localized = ": " + zh_item_display(*wpn, DESC_PLAIN);
        weapon_arg.supported = item_arg.supported;
    }
    else if (!weapon_descriptor.empty())
    {
        const string brand = weapon_descriptor.substr(2);
        const ZhArg brand_arg = _monster_attack_atom_arg(brand, "value");
        weapon_arg.localized = ": " + brand_arg.localized;
        weapon_arg.supported = brand_arg.supported;
    }
    string attk_desc;
    if (attk_mult > 1)
        attk_desc = zh_message("monster.attack.counted_label", {
            zh_integer("count", attk_mult), attk_arg, weapon_arg}).display();
    else
        attk_desc = zh_message("monster.attack.label",
            {attk_arg, weapon_arg}).display();
    di.attack_descriptions.emplace_back(attk_desc);
    di.attk_desc_width = max(di.attk_desc_width, (size_t)strwidth(attk_desc));

    // Part 2: The "Max Damage" column
    // Display the max damage from the attack (including any weapon)
    // and additionally display max brand damage separately

    int flav_dam = flavour_damage(attack.flavour, mi.hd, false);

    int dam = attack.damage;
    int slaying = mi.slaying();

    if (attack.flavour == AF_PURE_FIRE)
        dam = flav_dam;
    else if (attack.flavour == AF_CRUSH)
        dam = 0;
    else if (attack.flavour == AF_PAIN)
        flav_dam = (mi.props.exists(NECROMANCER_KEY)) ? mi.hd * 2 : mi.hd / 2;
    else if (wpn)
    {
        // From attack::calc_damage
        // damage = 1 + random2(monster attack damage)
        //          + random2(weapon damage) + random2(1 + enchant + slay)
        const int base_dam = property(*wpn, PWPN_DAMAGE);
        dam += brand_adjust_weapon_damage(base_dam, get_weapon_brand(*wpn), false) - 1;
        if (ranged && mons_class_flag(mi.type, M_ARCHER))
            dam += archer_bonus_damage(mi.hd);
        slaying += wpn->plus;
    }
    dam += max(slaying, 0);

    // Show damage modified by effects, if applicable
    int real_dam = dam;
    if (!ranged)
    {
        if (mi.is(MB_STRONG) || mi.is(MB_BERSERK))
            real_dam = real_dam * 3 / 2;
        if (mi.is(MB_TEMPERED))
            real_dam = real_dam * 5 / 4;
        if (mi.is(MB_IDEALISED))
            real_dam = real_dam * 2;
        if (mi.is(MB_WEAK))
            real_dam = real_dam * 2 / 3;
    }
    if (mi.is(MB_TOUCH_OF_BEOGH))
        real_dam = real_dam * 4 / 3;
    if (mi.is(MB_FIGMENT))
        real_dam = real_dam * 2 / 3;

    string dam_str;
    if (dam != real_dam)
        dam_str = zh_message("monster.attack.modified_damage", {
            zh_integer("damage", real_dam), zh_integer("base", dam)}).display();
    else
        dam_str = make_stringf("%d", dam);

    if (attack.flavour == AF_PURE_FIRE)
        dam_str += " " + zh_word("monster.attack.atom.", "fire");

    string brand_str;
    if (wpn)
    {
        if (wpn->base_type == OBJ_WEAPONS)
        {
            brand_str = _brand_damage_string(mi, get_weapon_brand(*wpn),
                                             real_dam, property(*wpn, PWPN_DAMAGE));
        }
        else if (wpn->base_type == OBJ_STAVES)
        {
            brand_str = _monster_staff_damage_string(mi,
                            static_cast<stave_type>(wpn->sub_type));
        }
    }
    else if (di.special_flavour != SPWPN_NORMAL)
        brand_str = _brand_damage_string(mi, di.special_flavour, real_dam);

    string final_dam_str = dam_str + brand_str;
    if (attk_mult > 1)
        final_dam_str += zh_message("monster.attack.each").display();
    di.damage_descriptions.emplace_back(final_dam_str);
    di.damage_width = max(di.damage_width, (size_t)strwidth(final_dam_str));

    // Part 3: The "Bonus" column
    // Describe any additional effects from a monster's attack flavour

    string bonus_desc = "";
    // Attack flavours don't apply to ranged weapon attacks...
    if (!ranged)
    {
        _add_attack_flavour_desc(bonus_desc, attack.flavour, attack, di, flav_dam, real_dam, attk_mult);

        if (mi.is(MB_FIRE_CHAMPION))
        {
            _add_attack_flavour_desc(bonus_desc, AF_FIRE, attack, di,
                                     flavour_damage(AF_FIRE, mi.hd, false), real_dam, attk_mult);
            di.has_any_flavour = true;
        }

        if (mi.is(MB_CHAOS_LACE))
        {
            _add_attack_flavour_desc(bonus_desc, AF_CHAOTIC, attack, di, 0, real_dam, attk_mult);
            di.flavour_without_dam = !di.has_any_flavour;
            di.has_any_flavour = true;
        }
    }
    // ...except Nessos' ranged attacks apply venom as a special effect
    else if (mi.type == MONS_NESSOS)
        bonus_desc += _monster_attack_atom_arg("poison").localized;

    di.bonus_descriptions.emplace_back(bonus_desc);
    di.bonus_width = max(di.bonus_width, (size_t)strwidth(bonus_desc));
}

// Get all the info required to form an attacks table row for the monster's
// throwing weapons, if applicable.
static void _attacks_table_row_throwing(const monster_info &mi,
                                        mon_attack_desc_info &di)
{
    item_def *quiv = mi.inv[MSLOT_MISSILE].get();
    if (!quiv || quiv->base_type != OBJ_MISSILES)
        return;

    const bool is_net = quiv->is_type(OBJ_MISSILES, MI_THROWING_NET);
    const string thrown_en = is_net
        ? quiv->name(DESC_A, false, false, true, false)
        : pluralise(quiv->name(DESC_PLAIN, false, false, true, false));
    const ZhArg thrown_localized = zh_item_arg("item", *quiv,
                                               is_net ? DESC_A : DESC_PLAIN);
    const ZhArg thrown_arg{"item", ZhArgType::Name, thrown_en,
        zh_item_display(*quiv, is_net ? DESC_A : DESC_PLAIN),
        thrown_localized.supported};
    const string throw_str = zh_message("monster.attack.throw_label",
                                        {thrown_arg}).display();
    di.attack_descriptions.emplace_back(throw_str);
    di.attk_desc_width = max(di.attk_desc_width, (size_t)strwidth(throw_str));

    string dam_desc = "0";
    string bonus_desc = "";
    if (quiv->sub_type == MI_THROWING_NET)
        bonus_desc = _monster_attack_atom_arg("Ensnare in a net").localized;
    else if (quiv->sub_type == MI_DART)
    {
        switch (quiv->brand)
        {
        case SPMSL_CURARE:
            dam_desc = zh_message("monster.attack.curare_damage", {
                zh_integer("damage", 12)}).display();
            bonus_desc = _monster_attack_atom_arg("Poison and slowing").localized;
            break;
        case SPMSL_POISONED:
            bonus_desc = _monster_attack_atom_arg("poison").localized;
            break;
        case SPMSL_BLINDING:
            bonus_desc = _monster_attack_atom_arg("Blinding and confusion").localized;
            break;
        case SPMSL_FRENZY:
            bonus_desc = _monster_attack_atom_arg("Drive defenders into a frenzy").localized;
            break;
        case SPMSL_DISPERSAL:
            bonus_desc = _monster_attack_atom_arg("Blink the defender away").localized;
            break;
        case SPMSL_DISJUNCTION:
            bonus_desc = _monster_attack_atom_arg("Blink the defender repeatedly").localized;
        default:
            break;
        }
    }
    else // ordinary missiles
    {
        // Missile attacks use the damage number of a monster's first attack
        const mon_attack_info info = _atk_info(mi, 0);
        const mon_attack_def &attack = info.definition;
        int dam = attack.damage;
        dam += property(*quiv, PWPN_DAMAGE) - 1;
        dam += max(mi.slaying(), 0);
        if (mons_class_flag(mi.type, M_ARCHER))
            dam += archer_bonus_damage(mi.hd);
        string silver_str;
        if (quiv->brand == SPMSL_SILVER)
        {
            string dmg_msg;
            int silver_dam = max(dam / 3,
                                 silver_damages_victim(&you, dam, dmg_msg));
            silver_str = zh_message("monster.attack.silver_damage", {
                zh_integer("damage", silver_dam)}).display();
        }
        dam_desc = make_stringf("%d%s", dam, silver_str.c_str());
    }

    di.damage_descriptions.emplace_back(dam_desc);
    di.bonus_descriptions.emplace_back(bonus_desc);
    di.damage_width = max(di.damage_width, (size_t)strwidth(dam_desc));
    di.bonus_width = max(di.bonus_width, (size_t)strwidth(bonus_desc));
}

// Build the table of attacks, for real
static void _build_table_of_attacks(mon_attack_desc_info &di,
                                    ostringstream &result)
{
    const string attack_header = zh_source("detail.monster.attack_table",
                                           di.plural ? "Attacks" : "Attack");
    const string damage_header = zh_source("detail.monster.attack_table",
                                           "Max Damage");
    const string bonus_header = zh_source("detail.monster.attack_table",
        di.flavour_without_dam ? "Bonus" : "After Damaging Hits");
    auto measure_column = [](vector<string> &cells, const string &header) {
        size_t width = strwidth(header);
        for (auto &cell : cells) {
            width = max(width, (size_t)strwidth(cell));
        }
        return width;
    };
    di.attk_desc_width = measure_column(di.attack_descriptions, attack_header);
    di.damage_width = measure_column(di.damage_descriptions, damage_header);
    di.bonus_width = measure_column(di.bonus_descriptions,
                                    di.has_any_flavour ? bonus_header : "");
    // Hopefully enough width for every possibility
    di.damage_width    = min(di.damage_width, (size_t) 31);
    di.bonus_width     = min(di.bonus_width, 69 - di.damage_width);

    // Table lines can't be longer than 80 chars wide (incl 4 spaces)
    // so cut off the attack description if it's too long.
    // Note: minimum 7 (length of "Attacks")
    di.attk_desc_width = min(di.attk_desc_width,
                             76 - di.damage_width - di.bonus_width);

    // Now we can actually build the table of attacks
    // Note: columns are separated by (a minimum of) 2 spaces

    // First, the table header
    result << padded_str(attack_header,
                         di.attk_desc_width + 2)
           << padded_str(damage_header, di.damage_width + 2);
    if (di.has_any_flavour)
    {
        result << padded_str(bonus_header, di.bonus_width);
    }
    result << "\n";

    // Table body
    for (unsigned int i = 0; i < di.attack_descriptions.size(); ++i)
    {
        result << chop_string(di.attack_descriptions[i], di.attk_desc_width)
               << "  "
               << chop_string(di.damage_descriptions[i], di.damage_width)
               << "  "
               << chop_string(di.bonus_descriptions[i], di.bonus_width)
               << "\n";
    }
}

// Get a description of the monster's to-hit, the player's to-hit against
// the monster, and a table of attacks, for the monster description.
static string _monster_attacks_description(const monster_info& mi)
{
    // Spectral weapons use the wielder's stats to attack, so displaying
    // their 'monster' damage here is just misleading.
    // TODO: display the right number without an awful hack
    if (mi.type == MONS_SPECTRAL_WEAPON)
        return "";

    ostringstream result;
    mon_attack_desc_info di;
    di.special_flavour = SPWPN_NORMAL;

    if (mi.props.exists(SPECIAL_WEAPON_KEY))
    {
        ASSERT(mi.type == MONS_PANDEMONIUM_LORD || mons_is_pghost(mi.type));
        di.special_flavour = (brand_type) mi.props[SPECIAL_WEAPON_KEY].get_int();
    }

    di.has_any_flavour = false;
    di.flavour_without_dam = false;
    di.plural = false;

    _check_attack_counts_and_flavours(mi, di);

    if (di.attack_counts.empty())
        return "";

    _describe_mons_to_hit(mi, result);

    result << "\n";

    // Assign minimum column widths according to the lengths of their headers.
    di.attk_desc_width = di.plural ? 7 : 6;         // "Attack"/"Attacks"
    di.damage_width   = 10;                         // "Max Damage"
    di.bonus_width = !di.has_any_flavour    ? 0     // no bonus column
                   : di.flavour_without_dam ? 5     // "Bonus"
                                            : 19;   // "After Damaging Hits"

    // Get the info for the table of attacks
    for (int i = 0; i < MAX_NUM_ATTACKS; ++i)
    {
        const mon_attack_info info = _atk_info(mi, i);
        if (!di.attack_counts[info])
            continue;

        _attacks_table_row(mi, di, info, info.weapon);

        // For ranged weapons, it's misleading to show attack flavours on the
        // same table row as the ranged weapon damage, since monsters
        // (except Nessos) don't apply their attack flavour to ranged attacks.

        // So that the player can see the attack flavour of the monster's
        // primary melee attack at all times, when the monster has a ranged
        // weapon, we add an extra row for the melee base damage and flavour of
        // the monster's corresponding melee attack.
        if (info.weapon && is_range_weapon(*info.weapon))
            _attacks_table_row(mi, di, info, nullptr);
    }

    // Check for throwing weapons
    _attacks_table_row_throwing(mi, di);

    // Use all the gathered information in `di` to build the table
    _build_table_of_attacks(di, result);

    result << "\n";

    return result.str();
}

#define SPELL_LIST_BEGIN "[SPELL_LIST_BEGIN]"
#define SPELL_LIST_END "[SPELL_LIST_END]"

static string _monster_spells_description(const monster_info& mi, bool mark_spells)
{
    // Show monster spells and spell-like abilities.
    if (!mi.has_spells())
        return "";

    formatted_string description;

    // hacky, refactor so this isn't necessary
    if (mark_spells)
        description += SPELL_LIST_BEGIN;
    describe_spellset(monster_spellset(mi), nullptr, description, &mi);
    if (mark_spells)
        description += SPELL_LIST_END;

    description += formatted_string::parse_string_raw(
        "\n" + zh_message("monster.spell.help").display());
    description += formatted_string::parse_string_raw(zh_message(
        crawl_state.need_save ? "monster.spell.range_warning"
                              : "monster.spell.range_period").display() + "\n");

    return description.to_colour_string();
}

static string _monster_notice_chance(const monster_info& mi)
{
    int perception = mi.perception() * 100;
    int stealth = player_stealth() * 100;

    if (stealth < perception)
        perception = 100;
    else
        perception = perception * 100 / stealth;

    const bool plural = mi.pronoun_plurality();
    const string canonical = uppercase_first(mi.pronoun(PRONOUN_SUBJECTIVE)) + " "
        + conjugate_verb("have", plural) + " a " + to_string(perception)
        + "% chance to notice you each turn.\n";
    return zh_message(plural ? "monster.notice_chance_plural"
                             : "monster.notice_chance",
                      {zh_integer("chance", perception)}, canonical).display();
}

static void _describe_aux_hit_chance(ostringstream &result, vector<string>& auxes, int chance)
{
    result << " and " << chance << "% to hit with your ";
    for (size_t i = 0; i < auxes.size(); ++i)
    {
        if (i > 0 && auxes.size() > 2)
        {
            if (i < auxes.size() - 1)
                result << ", ";
            else
                result << ", and ";
        }
        else if (i == 1 && auxes.size() == 2)
            result << " and ";

        result << auxes[i];
    }
}

/**
 * Calculate and describe the % chance of a player hitting the given monster.
 *
 * @param mi[in]            Player-visible info about the monster in question.
 * @param result[in,out]    The stringstream to append to.
 * @param weapon            The weapon you are hitting them with
 * @param verbose           Uses more flowery language (for monster info pane)
 * @param source            An attack source to use for calculations. An appropriate
 *                          one will be created if not provided.
 * @param distance          Distance from which the attack is being made. If not
 *                          provided, assume distance between player and the target.
 */
ZhArg describe_to_hit_message(const monster_info &mi,
                     const item_def *weapon, bool verbose, attack *source,
                     int distance)
{
    if (weapon != nullptr
        && !(is_weapon(*weapon) || is_throwable(&you, *weapon)))
    {
        return {"chance", ZhArgType::Text, "", ""}; // breadwielding
    }

    const bool melee = weapon == nullptr || !(is_range_weapon(*weapon)
                                              || is_throwable(&you, *weapon));
    int distance_from = distance > 0 ? distance
                                     : you.pos().distance_from(mi.pos);
    // On xv screen, don't show a bigger penalty than player's maximum reach,
    // even if we're the other side of the map. But if we're adjacent and
    // targetting, show correct penalty for 1 tile distance.
    if (melee)
        distance_from = min(distance_from, (int)you.reach_range());
    int acc_pct;
    if (melee)
    {
        melee_attack attk(&you, nullptr);
        acc_pct = to_hit_pct(mi, source ? *source : attk, true, false,
                             distance_from);

        auto chance = describe_hit_chance_message(acc_pct, weapon, verbose, distance_from);

        vector<string> aux_names = get_player_aux_names();
        if (!aux_names.empty())
        {
            acc_pct = to_hit_pct_aux(mi, attk);
            vector<ZhArg> names;
            for (const auto &name : aux_names)
                names.push_back(zh_glossary_name("attack", "target.monster.aux", name));
            auto attacks = zh_message_list("attacks", names);
            ostringstream canonical;
            _describe_aux_hit_chance(canonical, aux_names, acc_pct);
            auto combined = zh_message_arg("chance", "target.hit_chance.aux", {
                chance, zh_integer("hit_percent", acc_pct), attacks});
            combined.canonical = chance.canonical + canonical.str();
            if (!combined.supported)
                combined.localized = combined.canonical;
            chance = combined;
        }

        return chance;
    }
    else
    {
        ranged_attack attk(&you, nullptr, weapon, false);
        const bool penetrating = is_penetrating_attack(*weapon);
        acc_pct = to_hit_pct(mi, attk, false, penetrating, distance_from);
    }

    return describe_hit_chance_message(acc_pct, weapon, verbose, distance_from);
}

/**
 * Describe the given hit chance and write to an string stream
 */
ZhArg describe_hit_chance_message(int hit_chance, const item_def *weapon,
                         bool verbose, int distance_from)
{
    const bool blinded = you.duration[DUR_BLIND];
    const auto hit_arg = zh_integer("hit_percent", hit_chance);
    if (!verbose && blinded)
        return zh_message_arg("chance", "target.hit_chance.distance", {hit_arg});
    else if (!verbose)
        return zh_message_arg("chance", "target.hit_chance", {hit_arg});
    else
    {
        ZhArg weapon_arg;
        string canonical_weapon;
        if (weapon)
        {
            canonical_weapon = weapon->name(DESC_YOUR, false, false, false);
            weapon_arg = zh_item_arg("weapon", *weapon, DESC_YOUR);
            // describe_hit_chance intentionally omits inscriptions.
            weapon_arg.canonical = canonical_weapon;
        }
        else
        {
            canonical_weapon = "your " + you.hand_name(true);
            const string localized = zh_lookup_exact(canonical_weapon);
            weapon_arg = {"weapon", ZhArgType::Name, canonical_weapon,
                          localized, localized != canonical_weapon};
        }
        const auto chance = blinded
            ? zh_message_arg("chance", "target.hit_chance.verbose_blind", {
                hit_arg, weapon_arg, zh_integer("range", distance_from)})
            : zh_message_arg("chance", "target.hit_chance.verbose", {hit_arg, weapon_arg});
        return zh_message_arg("chance", "target.hit_chance.about", {chance});
    }
}

void describe_to_hit(const monster_info &mi, ostringstream &result,
                     const item_def *weapon, bool verbose, attack *source, int distance)
{
    const auto chance = describe_to_hit_message(mi, weapon, verbose, source, distance);
    result << (zh_language_enabled() ? chance.localized : chance.canonical);
}

void describe_hit_chance(int hit_chance, ostringstream &result, const item_def *weapon,
                         bool verbose, int distance_from)
{
    const auto chance = describe_hit_chance_message(hit_chance, weapon, verbose, distance_from);
    result << (zh_language_enabled() ? chance.localized : chance.canonical);
}

static bool _visible_to(const monster_info& mi)
{
    // XXX: this duplicates player::visible_to
    const bool invis_to = you.invisible() && !mi.can_see_invisible()
                          && !you.in_water();
    return mi.attitude == ATT_FRIENDLY || (!mi.is(MB_BLIND) && !invis_to);
}

/**
 * Display the % chance of a the given monster hitting the player.
 *
 * @param mi[in]            Player-visible info about the monster in question.
 * @param result[in,out]    The stringstream to append to.
 */
static void _describe_mons_to_hit(const monster_info& mi, ostringstream &result)
{
    if (crawl_state.game_is_arena() || !crawl_state.need_save)
        return;

    const item_def* weapon = mi.inv[MSLOT_WEAPON].get();
    const bool melee = weapon == nullptr || !is_range_weapon(*weapon);
    const bool skilled = mons_class_flag(mi.type, melee ? M_FIGHTER : M_ARCHER);
    const int base_to_hit = mon_to_hit_base(mi.hd, skilled);
    const int weapon_to_hit = weapon ? weapon->plus + property(*weapon, PWPN_HIT) : 0;
    const int total_base_hit = base_to_hit + weapon_to_hit;

    int post_roll_modifiers = 0;
    if (mi.is(MB_CONFUSED))
        post_roll_modifiers += CONFUSION_TO_HIT_MALUS;

    const bool invisible = !_visible_to(mi);
    if (invisible)
        post_roll_modifiers -= total_base_hit * 35 / 100;
    else
    {
        post_roll_modifiers += TRANSLUCENT_SKIN_TO_HIT_MALUS
                               * you.get_mutation_level(MUT_TRANSLUCENT_SKIN);
        if (you.backlit(false))
            post_roll_modifiers += BACKLIGHT_TO_HIT_BONUS;
        if (you.umbra() && !mi.nightvision())
            post_roll_modifiers += UMBRA_TO_HIT_MALUS;
    }
    // We ignore pproj because monsters never have it passively.

    // We ignore the EV penalty for not being able to see an enemy because, if you
    // can't see an enemy, you can't get a monster description for them. (Except through
    // ?/M, but let's neglect that for now.)
    const int scaled_ev = you.evasion_scaled(100);

    const int to_land = weapon && is_unrandom_artefact(*weapon, UNRAND_SNIPER) ? AUTOMATIC_HIT :
                                                                total_base_hit + post_roll_modifiers;
    const int beat_ev_chance = mon_to_hit_pct(to_land, scaled_ev);

    const int scaled_sh = player_shield_class(100, false);
    const int shield_bypass = mon_shield_bypass(mi.hd);
    // ignore penalty for unseen attacker, as with EV above
    const int beat_sh_chance = mon_beat_sh_pct(shield_bypass, scaled_sh);

    const int hit_chance = beat_ev_chance * beat_sh_chance / 100;
    const bool plural = mi.pronoun_plurality();
    const string canonical = uppercase_first(mi.pronoun(PRONOUN_SUBJECTIVE)) + " "
        + conjugate_verb("have", plural) + " about " + to_string(hit_chance)
        + "% to hit you.\n";
    result << zh_message(plural ? "monster.hit_chance_plural"
                                : "monster.hit_chance",
                         {zh_integer("hit_percent", hit_chance)}, canonical).display();
}

/**
 * Print a bar of +s representing a given stat to a provided stream.
 *
 * @param value[in]         The current value represented by the bar. Clamped
 *                          to zero.
 * @param scale[in]         The value that each + represents.
 * @param name              The name of the bar.
 * @param result[in,out]    The stringstream to append to.
 * @param base_value[in]    The 'base' value represented by the bar, clamped to
 *                          zero. If INT_MAX, is ignored.
 */
static void _print_bar(int value, int scale, const string &name,
                       ostringstream &result, int base_value)
{
    value = max(0, value);
    base_value = max(0, base_value);

    if (base_value == INT_MAX)
        base_value = value;

    if (!name.empty())
        result << name << " ";

    const int display_max = value ? value : base_value;
    const bool currently_disabled = !value && base_value;

    if (currently_disabled)
      result << "none (normally ";

    if (display_max == 0)
        result << "none";
    else
    {
        for (int i = 0; i * scale < display_max; i++)
        {
            result << "+";
            if (i % 5 == 4)
                result << " ";
        }
    }

    if (currently_disabled)
        result << ")";

#ifdef DEBUG_DIAGNOSTICS
    if (!you.suppress_wizard)
    {
        result << " (" << value << ")";
        if (currently_disabled)
            result << " (base: " << base_value << ")";
    }
#endif
}

static string _build_bar(int value, int scale)
{
    // Round up.
    const int pips = (value + scale - 1) / scale;
    if (pips <= 0)
        return "none";
    if (pips > 8) // too many..
        return make_stringf("~%d", pips * scale);

    string bar = "";
    bar.append(min(pips, 4), '+');
    // Add a space in the middle of long bars,
    // for readability.
    if (pips > 4) {
        bar += " ";
        bar.append(min(pips - 4, 4), '+');
    }
    return bar;
}

/**
 * Returns a description of a given monster's WL.
 *
 * @param mi[in]            Player-visible info about the monster in question.
 */
static string _describe_monster_wl(const monster_info& mi)
{
    const int will = mi.willpower();
    if (will == WILL_INVULN)
    {
        if (Options.char_set == CSET_ASCII)
            return "inf";
        return "∞";
    }
    return _build_bar(will, WL_PIP);
}

/**
 * Returns a string describing a given monster's habitat.
 *
 * @param mi[in]            Player-visible info about the monster in question.
 * @return                  The habitat description.
 */
string _monster_habitat_description(const monster_info& mi)
{
    const monster_type type = mons_is_draconian_job(mi.type)
                              ? mi.draconian_subspecies()
                              : mi.type;
    if (mons_class_is_stationary(type))
        return "";

    switch (mons_habitat_type(type, mi.base_type))
    {
    case HT_AMPHIBIOUS:
        return uppercase_first(make_stringf("%s can %s water.\n",
                               mi.pronoun(PRONOUN_SUBJECTIVE),
                               mi.type == MONS_ORC_APOSTLE
                                ? "walk on" : "travel through"));
    case HT_AMPHIBIOUS_LAVA:
        return uppercase_first(make_stringf("%s can travel through lava.\n",
                               mi.pronoun(PRONOUN_SUBJECTIVE)));
    default:
        return "";
    }
}

// Size adjectives
const char* const size_adj[] =
{
    "tiny",
    "very small",
    "small",
    "medium",
    "large",
    "giant",
};
COMPILE_CHECK(ARRAYSZ(size_adj) == NUM_SIZE_LEVELS);

// This is used in monster description and on '%' screen for player size
const char* get_size_adj(const size_type size, bool ignore_medium)
{
    ASSERT_RANGE(size, 0, ARRAYSZ(size_adj));
    if (ignore_medium && size == SIZE_MEDIUM)
        return nullptr; // don't mention medium size
    return size_adj[size];
}

static string _monster_current_target_description(const monster_info &mi)
{
    // is it morally wrong to use pos to get the actual monster? Possibly...
    if (!in_bounds(mi.pos) || !monster_at(mi.pos))
        return "";
    const monster *m = monster_at(mi.pos);

    const char* pronoun = mi.pronoun(PRONOUN_SUBJECTIVE);
    const bool plural = mi.pronoun_plurality();
    const string subject_canonical = uppercase_first(pronoun);
    const ZhArg subject("subject", ZhArgType::Name, subject_canonical, "它");
    const ZhArg verb("verb", ZhArgType::Text,
                     conjugate_verb("are", plural), "", true);

    ostringstream result;
    if (mi.is(MB_ALLY_TARGET))
    {
        auto allies = find_allies_targeting(*m);
        if (allies.size() == 1)
        {
            const string canonical = subject_canonical + " "
                + conjugate_verb("are", plural) + " currently targeted by "
                + allies[0]->name(DESC_YOUR) + ".";
            result << zh_message("monster.targeted_by_one", {
                subject, verb, zh_actor_arg("ally", allies[0], DESC_YOUR)
            }, canonical).display() << "\n";
        }
        else
        {
            string canonical = subject_canonical + " "
                + conjugate_verb("are", plural) + " currently targeted by:\n";
            string localized;
            for (auto *a : allies)
            {
                const ZhArg ally = zh_actor_arg("ally", a, DESC_YOUR);
                canonical += "  " + ally.canonical + "\n";
                localized += "　" + ally.localized + "\n";
            }
            result << zh_message("monster.targeted_by_many", {
                subject, verb, ZhArg("items", ZhArgType::Text,
                                     canonical.substr(canonical.find(":\n") + 2),
                                     localized, true)
            }, canonical).display();
        }
    }

    // TODO: this might be ambiguous, give a relative position?
    if (mi.attitude == ATT_FRIENDLY && m->get_foe())
    {
        const string canonical = subject_canonical + " "
            + conjugate_verb("are", plural) + " currently targeting "
            + m->get_foe()->name(DESC_THE) + ".";
        result << zh_message("monster.targeting_foe", {
            subject, verb, zh_actor_arg("foe", m->get_foe(), DESC_THE)
        }, canonical).display() << "\n";
    }

    return result.str();
}

struct TableCell
{
    string   label;
    string   value;
    colour_t colour;
};

static string _detail_table_label(const string &label)
{
    static const map<string, pair<const char *, const char *>> reviewed = {
        {"Max HP", {"detail.monster.table_label", "Max HP"}},
        {"Will", {"detail.monster.table_label", "Will"}},
        {"AC", {"detail.monster.table_label", "AC"}},
        {"EV", {"detail.monster.table_label", "EV"}},
        {"SH", {"detail.monster.table_label", "SH"}},
        {"Threat", {"detail.monster.table_label", "Threat"}},
        {"Class", {"detail.monster.table_label", "Class"}},
        {"Size", {"detail.monster.table_label", "Size"}},
        {"Int", {"detail.monster.table_label", "Int"}},
        {"Regen", {"detail.monster.table_label", "Regen"}},
        {"Melee dmg", {"detail.form.table_label", "Melee dmg"}},
        {"Bite speed", {"detail.form.table_label", "Bite speed"}},
        {"Elec chance", {"detail.form.table_label", "Elec chance"}},
        {"Aux chance", {"detail.form.table_label", "Aux chance"}},
        {"Stealth", {"detail.form.table_label", "Stealth"}},
        {"Reach", {"detail.form.table_label", "Reach"}},
        {"Barding", {"detail.form.table_label", "Barding"}},
        {"Claws", {"detail.form.table_label", "Claws"}},
        {"Melee damage", {"detail.form.table_label", "Melee damage"}},
        {"SInv", {"detail.form.table_label", "SInv"}},
        {"Str", {"detail.form.table_label", "Str"}},
        {"Dex", {"detail.form.table_label", "Dex"}},
    };
    const auto it = reviewed.find(label);
    if (it == reviewed.end())
        return label; // compact resistance labels (rF, rC, ...) are symbols
    return zh_source(it->second.first, it->second.second);
}

// TODO: This is similar to column_composer. Deduplicate?
class TablePrinter
{
private:
    vector<vector<TableCell>> rows;
    int fixed_column_num;
    int fixed_column_width;

public:
    TablePrinter()
        : fixed_column_num(0), fixed_column_width(0)
    {}

    TablePrinter(int column_num, int total_width)
        : fixed_column_num(column_num), fixed_column_width(total_width / column_num)
    {}

    void AddRow()
    {
        rows.push_back({});
    }

    void AddCell(string label = "", string value = "", colour_t colour = LIGHTGREY)
    {
        if (fixed_column_num > 0 && (int)rows[rows.size() - 1].size() >= fixed_column_num)
            AddRow();
        rows[rows.size() - 1].push_back({_detail_table_label(label), value, colour});
    }

    int NumCells() const
    {
        int count = 0;
        for (const auto& row : rows)
            count += row.size();

        return count;
    }

    void Print(ostringstream &result)
    {
        vector<int> labels_lengths_by_col;
        for (size_t row = 0; row < rows.size(); ++row)
        {
            for (size_t col = 0; col < rows[row].size(); ++col)
            {
                const int label_len = strwidth(rows[row][col].label);
                if (col == labels_lengths_by_col.size())
                    labels_lengths_by_col.push_back(label_len);
                else
                    labels_lengths_by_col[col] = max(labels_lengths_by_col[col], label_len);
            }
        }
        const int cell_len = fixed_column_width > 0 ? fixed_column_width
                                : 80 / max(1, (int)labels_lengths_by_col.size());

        for (const auto &row : rows)
        {
            vector<vector<string>> cells;
            size_t line_count = 1;
            for (size_t col = 0; col < row.size(); ++col)
            {
                const TableCell &cell = row[col];
                vector<string> lines;
                if (!cell.label.empty())
                {
                    const int label_len = min(labels_lengths_by_col[col],
                                              max(0, cell_len - 3));
                    string body = padded_str(cell.label, label_len, true)
                                  + ": " + cell.value;
                    // Long translated labels and large values must stay in
                    // their column. Wrap rather than overwrite the next cell
                    // or discard the value at the panel's right edge.
                    while (!body.empty())
                        lines.push_back(wordwrap_line(body, cell_len, false, false));
                }
                line_count = max(line_count, lines.size());
                cells.push_back(lines);
            }
            for (size_t line = 0; line < line_count; ++line)
            {
                for (size_t col = 0; col < row.size(); ++col)
                {
                    const auto &lines = cells[col];
                    const string text = line < lines.size() ? lines[line] : "";
                    result << colourize_str(padded_str(text, cell_len), row[col].colour);
                }
                result << "\n";
            }
        }
    }
};

// Converts a numeric resistance to its symbolic counterpart.
// Can handle any maximum level. The default is for single level resistances
// (the most common case). Negative resistances are allowed.
// Resistances with a maximum of up to 4 are spaced (arbitrary choice), and
// starting at 5 levels, they are continuous.
// params:
//  level : actual resistance level
//  max : maximum number of levels of the resistance
//  immune : overwrites normal pip display for full immunity
string desc_resist(int level, int max, bool immune, bool allow_spacing)
{
    if (max < 1)
        return "";

    if (immune)
        return Options.char_set == CSET_ASCII ? "inf" : "\u221e "; //"∞"

    string sym;
    const bool spacing = allow_spacing && max < 5;

    while (max > 0)
    {
        if (level == 0)
            sym += ".";
        else if (level > 0)
        {
            sym += "+";
            --level;
        }
        else // negative resistance
        {
            sym += "x";
            ++level;
        }
        sym += (spacing) ? " " : "";
        --max;
    }
    return sym;
}

static string _res_name(mon_resist_flags res)
{
    switch (res)
    {
    case MR_RES_FIRE:   return "rF";
    case MR_RES_COLD:   return "rC";
    case MR_RES_POISON: return "rPois";
    case MR_RES_ELEC:   return "rElec";
    case MR_RES_NEG:    return "rNeg";
    case MR_RES_CORR:   return "rCorr";
    default:            return "rEggplant";
    }
}

static void _desc_mon_resist(TablePrinter &pr,
                             resists_t resist_set, mon_resist_flags res)
{
    const int level = get_resist(resist_set, res);
    const int max = (res == MR_RES_POISON || res == MR_RES_ELEC) ? 1 : 3; // lies
    const string desc = desc_resist(level, max, level == 3, false);
    pr.AddCell(_res_name(res), desc, level ? LIGHTGREY : DARKGREY);
}

static void _add_resist_desc(TablePrinter &pr, resists_t resist_set)
{
    const mon_resist_flags common_resists[] =
        { MR_RES_FIRE, MR_RES_COLD, MR_RES_POISON, MR_RES_NEG, MR_RES_ELEC };

    bool found = false;
    for (mon_resist_flags rflags : common_resists)
        if (get_resist(resist_set, rflags))
            found = true;
    if (!found)
        return;

    pr.AddRow();
    for (mon_resist_flags rflags : common_resists)
        _desc_mon_resist(pr, resist_set, rflags);
}

static void _desc_mon_death_explosion(ostringstream &result,
                                      const monster_info &mi)
{
    if (mi.type == MONS_LURKING_HORROR)
        return; // no damage number
    const dice_def dam = mon_explode_dam(mi.type, mi.hd);
    result << zh_message("monster.special.explosion_damage",
        {zh_integer("dice", dam.num), zh_integer("sides", dam.size)}).display();
}

static ZhArg _monster_player_hit_message(const monster_info& mi)
{
    auto chance = describe_to_hit_message(mi, you.weapon(), true);
    chance.key = "chance";
    return zh_message_arg("hit", mi.incapacitated()
        ? "target.monster.detail.player_hit.incapacitated"
        : mi.base_ev != mi.ev ? "target.monster.detail.player_hit.current"
                              : "target.monster.detail.player_hit.plain", {chance});
}

static ZhArg _monster_detail_size_message(size_type size)
{
    switch (size)
    {
    case SIZE_TINY: return zh_message_arg("size", "target.monster.detail.size.tiny");
    case SIZE_LITTLE: return zh_message_arg("size", "target.monster.detail.size.little");
    case SIZE_SMALL: return zh_message_arg("size", "target.monster.detail.size.small");
    case SIZE_MEDIUM: return zh_message_arg("size", "target.monster.detail.size.medium");
    case SIZE_LARGE: return zh_message_arg("size", "target.monster.detail.size.large");
    case SIZE_GIANT: return zh_message_arg("size", "target.monster.detail.size.giant");
    default: die("Invalid monster body size");
    }
}

static ZhArg _monster_door_message(const monster_info& mi)
{
    auto subject = zh_word_arg("subject", "target.monster.pronoun.",
                              mi.pronoun(PRONOUN_SUBJECTIVE), ZhArgType::Name);
    if (mi.itemuse() > MONUSE_NOTHING && mi.itemuse() != NUM_MONUSE
        && !mons_class_is_stationary(mi.type)
        && !mon_shape_is_humanoid(get_mon_shape(mi.type)))
    {
        return zh_message_arg("doors", "target.monster.detail.doors.despite", {
            zh_word_arg("possessive", "target.monster.pronoun.",
                        mi.pronoun(PRONOUN_POSSESSIVE)), subject});
    }
    subject.canonical = uppercase_first(subject.canonical);
    const char *id = nullptr;
    if (mi.itemuse() > MONUSE_NOTHING && mi.itemuse() != NUM_MONUSE
        && !mons_class_is_stationary(mi.type))
        id = "target.monster.detail.doors.open";
    else if (mons_class_flag(mi.type, M_CRASH_DOORS))
        id = "target.monster.detail.doors.crash";
    else if (mons_class_flag(mi.type, M_EAT_DOORS))
        id = "target.monster.detail.doors.eat";
    if (id)
        return zh_message_arg("doors", id, {subject});
    return {"doors", ZhArgType::Text, "", ""};
}

static ZhArg _monster_detail_title_message(const monster_info& mi, const string& title)
{
    if (!title.empty())
        return zh_message_arg("title", "target.monster.detail.title.fixed", {
            zh_glossary_name("title", "monster.title", title)});
    auto name = zh_monster_info_arg("monster", mi, DESC_A);
    name.canonical = uppercase_first(mi.full_name(DESC_A));
    if (!name.supported)
        name.localized = name.canonical;
    return zh_message_arg("title", "target.monster.detail.title.name", {name});
}

// Describe a monster's (intrinsic) resistances, speed and a few other
// attributes.
static string _special_detail_display(const ZhArg& value)
{
    return ZhMessage{value.message_id, value.canonical,
                     value.supported ? value.localized : value.canonical}.display();
}

static ZhArg _special_monster_subject(const monster_info& mi)
{
    auto subject = zh_word_arg("subject", "target.monster.pronoun.",
                              mi.pronoun(PRONOUN_SUBJECTIVE), ZhArgType::Name);
    subject.canonical = uppercase_first(subject.canonical);
    if (!subject.supported) subject.localized = subject.canonical;
    return subject;
}

static ZhArg _special_resist_atom(mon_resist_flags resist)
{
    const char* id = nullptr;
    switch (resist)
    {
    case MR_RES_STEAM: id = "monster.special.resist.atom.steam"; break;
    case MR_RES_CORR: id = "monster.special.resist.atom.corrosion"; break;
    case MR_RES_DAMNATION: id = "monster.special.resist.atom.damnation"; break;
    case MR_RES_MIASMA: id = "monster.special.resist.atom.miasma"; break;
    case MR_RES_TORMENT: id = "monster.special.resist.atom.torment"; break;
    default: die("Invalid special monster resistance");
    }
    return zh_message_arg("attack", id);
}

static ZhArg _special_resist_list(const vector<ZhArg>& items)
{
    ZhArg result("resists", ZhArgType::Text, "", "");
    for (size_t i = 0; i < items.size(); ++i)
    {
        if (i == 0)
            result = items[i];
        else
        {
            result.key = "first";
            auto next = items[i]; next.key = "second";
            result = zh_message_arg("resists", i + 1 == items.size()
                ? "monster.special.list.semicolon_and" : "monster.special.list.semicolon",
                {result, next});
        }
    }
    result.key = "resists";
    return result;
}

static ZhArg _monster_habitat_message(const monster_info& mi)
{
    const monster_type type = mons_is_draconian_job(mi.type)
                              ? mi.draconian_subspecies() : mi.type;
    if (mons_class_is_stationary(type))
        return {"habitat", ZhArgType::Text, "", ""};
    const auto subject = _special_monster_subject(mi);
    switch (mons_habitat_type(type, mi.base_type))
    {
    case HT_AMPHIBIOUS:
        return zh_message_arg("habitat", mi.type == MONS_ORC_APOSTLE
            ? "monster.special.habitat.walk_water" : "monster.special.habitat.water", {subject});
    case HT_AMPHIBIOUS_LAVA:
        return zh_message_arg("habitat", "monster.special.habitat.lava", {subject});
    default:
        return {"habitat", ZhArgType::Text, "", ""};
    }
}

static ZhArg _monster_speed_message(const monster_info& mi)
{
    const int speed = mi.base_speed();
    if (!speed)
        return {"speed", ZhArgType::Text, "", ""};
    const mon_energy_usage default_energy = DEFAULT_ENERGY;
    const int travel_delay = mi.menergy.move * 10 / speed;
    const int travel_delay_diff = mons_class_flag(mi.type, M_STATIONARY) ? 0
        : travel_delay - player_movement_speed(false, false);
    if (speed == 10 && mi.menergy == default_energy && !travel_delay_diff)
        return {"speed", ZhArgType::Text, "", ""};
    auto result = zh_message_arg("speed", "monster.special.speed.base",
                                 {zh_integer("speed", speed * 10)});
    vector<ZhArg> unusuals;
    auto add_energy = [&](int energy, const char* id) {
        if (energy != 10)
        {
            ASSERT(energy);
            unusuals.push_back(zh_message_arg("action", id,
                {zh_integer("speed", speed * 100 / energy)}));
        }
    };
    add_energy(mi.menergy.attack, "monster.special.speed.attack");
    add_energy(mi.menergy.missile, "monster.special.speed.shoot");
    add_energy(mi.menergy.move, "monster.special.speed.travel");
    if (mi.menergy.swim != mi.menergy.move)
        add_energy(mi.menergy.swim, "monster.special.speed.swim");
    add_energy(mi.menergy.spell, mi.is_priest() ? "monster.special.speed.pray"
                                             : "monster.special.speed.magic");
    if (!unusuals.empty())
    {
        // The engine uses comma separators for every energy entry, including
        // the last; keep this immutable structure separate from prose lists.
        ZhArg actions("actions", ZhArgType::Text, "", "");
        for (const auto& action : unusuals)
        {
            if (actions.canonical.empty())
                actions = action;
            else
            {
                actions.key = "first";
                auto next = action; next.key = "second";
                actions = zh_message_arg("actions", "target.monster.join.comma", {actions, next});
            }
        }
        actions.key = "actions";
        result = zh_message_arg("speed", "monster.special.speed.energy", {result, actions});
    }
    if (mi.type == MONS_SIXFIRHY || mi.type == MONS_JIANGSHI)
        result = zh_message_arg("speed", "monster.special.speed.pauses", {result});
    else if (travel_delay_diff)
        result = zh_message_arg("speed", travel_delay_diff > 0
            ? "monster.special.speed.slower" : "monster.special.speed.faster", {result});
    return result;
}

static string _monster_intrinsic_prose(const monster_info& mi, resists_t resist)
{
    ostringstream result;
    const mon_resist_flags special_resists[] =
    {
        MR_RES_STEAM,     MR_RES_CORR,
        MR_RES_DAMNATION, MR_RES_MIASMA,  MR_RES_TORMENT,
    };

    vector<ZhArg> extreme_resists;
    vector<ZhArg> high_resists;
    vector<ZhArg> base_resists;
    vector<ZhArg> suscept;

    for (mon_resist_flags rflags : special_resists)
    {
        int level = get_resist(resist, rflags);

        if (level != 0)
        {
            const auto attackname = _special_resist_atom(rflags);
            if (rflags == MR_RES_DAMNATION || rflags == MR_RES_TORMENT)
                level = 3; // one level is immunity
            level = max(level, -1);
            level = min(level,  3);
            switch (level)
            {
                case -1:
                    suscept.emplace_back(attackname);
                    break;
                case 1:
                    base_resists.emplace_back(attackname);
                    break;
                case 2:
                    high_resists.emplace_back(attackname);
                    break;
                case 3:
                    extreme_resists.emplace_back(attackname);
                    break;
            }
        }
    }

    if (mi.is(MB_UNBLINDABLE))
        extreme_resists.push_back(zh_message_arg("attack", "monster.special.resist.atom.blinding"));
    // Resists flooding but still dies on falling into deep water.
    if (mi.is(MB_RES_DROWN))
        base_resists.push_back(zh_message_arg("attack", "monster.special.resist.atom.drowning"));

    if (mi.props.exists(CLOUD_IMMUNE_MB_KEY) && mi.props[CLOUD_IMMUNE_MB_KEY])
        extreme_resists.push_back(zh_message_arg("attack", "monster.special.resist.atom.clouds"));

    vector<ZhArg> resist_descriptions;
    if (!extreme_resists.empty())
        resist_descriptions.push_back(zh_message_arg("resist", "monster.special.resist.clause.immune",
            {zh_message_list("attacks", extreme_resists)}));
    if (!high_resists.empty())
        resist_descriptions.push_back(zh_message_arg("resist", "monster.special.resist.clause.high",
            {zh_message_list("attacks", high_resists)}));
    if (!base_resists.empty())
        resist_descriptions.push_back(zh_message_arg("resist", "monster.special.resist.clause.base",
            {zh_message_list("attacks", base_resists)}));

    const auto subject = _special_monster_subject(mi);
    const bool plural = mi.pronoun_plurality();

    if (mi.has_unusual_items())
    {
        vector<ZhArg> items;
        for (unsigned int i = 0; i <= MSLOT_LAST_VISIBLE_SLOT; ++i)
        {
            if (!mi.inv[i] || !item_is_unusual(*mi.inv[i])) continue;
            auto item = zh_item_arg("item", *mi.inv[i], DESC_A);
            item.canonical = mi.inv[i]->name(DESC_A, false, false, true, false);
            if (!item.supported) item.localized = item.canonical;
            items.push_back(item);
        }
        result << (!mons_class_is_animated_weapon(mi.type)
            ? zh_message(plural ? "monster.special.items.plural" : "monster.special.items.singular",
                         {subject, zh_message_list("items", items)})
            : zh_message(plural ? "monster.special.animated_item.plural" : "monster.special.animated_item.singular",
                         {subject})).display();
    }

    if (!resist_descriptions.empty())
        result << zh_message(plural ? "monster.special.resists.plural" : "monster.special.resists.singular",
                             {subject, _special_resist_list(resist_descriptions)}).display();

    // Is monster susceptible to anything? (On a new line.)
    if (!suscept.empty())
        result << zh_message(plural ? "monster.special.susceptible.plural" : "monster.special.susceptible.singular",
                             {subject, zh_message_list("attacks", suscept)}).display();
    if (mi.is(MB_CHAOTIC))
        result << zh_message(plural ? "monster.special.chaotic.plural" : "monster.special.chaotic.singular", {subject}).display();
    if (mons_class_flag(mi.type, M_STATIONARY) && !mons_is_tentacle_or_tentacle_segment(mi.type))
        result << zh_message("monster.special.stationary", {subject}).display();
    if (mons_class_flag(mi.type, M_COLD_BLOOD) && get_resist(resist, MR_RES_COLD) <= 0)
        result << zh_message(plural ? "monster.special.cold_blooded.plural" : "monster.special.cold_blooded.singular", {subject}).display();
    if (mi.can_see_invisible())
        result << zh_message("monster.special.see_invisible", {subject}).display();
    if (mons_class_flag(mi.type, M_BURROWS))
        result << zh_message("monster.special.burrow", {subject}).display();
    if (mons_class_flag(mi.type, M_ACID_SPLASH))
        result << zh_message(plural ? "monster.special.acid_splash.plural" : "monster.special.acid_splash.singular", {subject}).display();
    if (mons_class_flag(mi.type, M_INSUBSTANTIAL))
        result << zh_message(plural ? "monster.special.insubstantial.plural" : "monster.special.insubstantial.singular", {subject}).display();
    else if (mons_class_flag(mi.type, M_AMORPHOUS))
        result << zh_message(plural ? "monster.special.amorphous.plural" : "monster.special.amorphous.singular", {subject}).display();

    // XXX: could mention "immune to dazzling" here, but that's spammy, since
    // it's true of such a huge number of monsters. (undead, statues, plants).
    // Might be better to have some place where players can see holiness &
    // information about holiness.......?

    if (mi.type == MONS_SHADOWGHAST)
        result << zh_message(plural ? "monster.special.shadowghast.plural" : "monster.special.shadowghast.singular", {subject}).display();
    if (mi.type == MONS_ROYAL_JELLY)
    {
        result << zh_message("monster.special.royal_jelly.damage").display();
        result << zh_message("monster.special.royal_jelly.polymorph").display();
    }
    if (mi.type == MONS_STAR_JELLY)
    {
        const dice_def dmg = zap_damage(ZAP_SHOOTING_STAR, 150, true, false);
        result << zh_message("monster.special.star_damage",
            {zh_integer("dice", dmg.num), zh_integer("sides", dmg.size)}).display();
    }
    if (mi.airborne())
        result << zh_message("monster.special.fly", {subject}).display();

    if (in_good_standing(GOD_ZIN, 0) && !mi.pos.origin() && monster_at(mi.pos))
    {
        recite_counts retval;
        monster *m = monster_at(mi.pos);
        auto eligibility = zin_check_recite_to_single_monster(m, retval);
        if (eligibility == RE_INELIGIBLE)
            result << zh_message("monster.special.zin_ineligible", {subject}).display();
        else if (eligibility == RE_TOO_STRONG)
            result << zh_message(plural ? "monster.special.zin_strong.plural" : "monster.special.zin_strong.singular", {subject}).display();
        else
            result << zh_message("monster.special.zin_eligible", {subject}).display();
        if (you.wizard)
            result << zh_message("monster.special.zin_debug",
                {zh_integer("power", zin_recite_power()), zh_integer("hd", mi.hd)}).display();
        result << "\n";
    }

    if (mon_explodes_on_death(mi.type))
        _desc_mon_death_explosion(result, mi);

    if (mi.type == MONS_BATTLESPHERE)
    {
        const dice_def dam = battlesphere_damage_from_hd(mi.hd);
        result << zh_message("monster.special.projectile_damage",
            {zh_integer("dice", dam.num), zh_integer("sides", dam.size)}).display();
    }

    // Flying monsters can't be forced to fall into liquids these days.
    if (!(mi.airborne()))
        result << _special_detail_display(_monster_habitat_message(mi));


    return result.str();
}

static string _monster_stat_description(const monster_info& mi, bool mark_spells)
{
    if (mons_is_sensed(mi.type) || mons_is_projectile(mi.type))
        return "";

    ostringstream result;

    TablePrinter pr;

    pr.AddRow();
    pr.AddCell("Max HP", mi.get_max_hp_desc());
    pr.AddCell("Will", _describe_monster_wl(mi));
    pr.AddCell("AC", _build_bar(mi.ac, 5));
    pr.AddCell("EV", _build_bar(mi.base_ev, 5));
    if (mi.sh / 2 > 0)  // rescale to match player SH
        pr.AddCell("SH", _build_bar(mi.sh / 2, 5));
    else
        pr.AddCell(); // ensure alignment

    const resists_t resist = mi.resists();
    _add_resist_desc(pr, resist);

    // Less important common properties. Arguably should be lower down.
    const size_type sz = mi.body_size();
    const auto size_message = _monster_detail_size_message(sz);
    const string size_desc = ZhMessage{size_message.message_id, size_message.canonical,
                                       size_message.localized}.display();
    const auto holiness = mons_class_holiness(mi.type);
    const string holiness_name = holiness == MH_NONLIVING ? "Nonliv."
                                             : uppercase_first(single_holiness_description(holiness));
    const string holi = zh_source("detail.monster.table_value", holiness_name.c_str());
    pr.AddRow();
    if (mi.threat != MTHRT_UNDEF && !mons_class_is_peripheral(mi.type))
        pr.AddCell("Threat", _get_threat_desc(mi.threat));
    else // ?/m
        pr.AddCell(); // ensure alignment
    pr.AddCell("Class", uppercase_first(holi).c_str());
    pr.AddCell("Size", size_desc.c_str());
    pr.AddCell("Int", zh_source("detail.monster.table_value",
                                     intelligence_description(mi.intel())));
    if (mi.is(MB_SICK) || mi.is(MB_NO_REGEN))
        pr.AddCell("Regen", zh_source("detail.monster.table_value", "None"));
    else if (mons_class_fast_regen(mi.type) || mi.is(MB_REGENERATION))
        pr.AddCell("Regen", zh_message("monster.special.regen", {zh_integer("rate", mi.regen_rate(1))}).display());
                                        // (Wait, what's a 'turn'?)

    pr.Print(result);

    result << _special_detail_display(_monster_speed_message(mi)) << "\n\n";

    if (crawl_state.game_started)
    {
        const auto hit = _monster_player_hit_message(mi);
        result << ZhMessage{hit.message_id, hit.canonical, hit.localized}.display();
    }
    result << _monster_attacks_description(mi);
    if (crawl_state.game_started)
    {
        if (mi.attitude == ATT_HOSTILE && (mi.is(MB_SLEEPING) || mi.is(MB_DORMANT)
        || mi.is(MB_UNAWARE) || mi.is(MB_WANDERING)))
        {
            result << _monster_notice_chance(mi);
        }
    }

    result << _monster_intrinsic_prose(mi, resist);

    const auto doors = _monster_door_message(mi);
    result << ZhMessage{doors.message_id, doors.canonical, doors.localized}.display();
    result << _monster_spells_description(mi, mark_spells);

    return result.str();
}

branch_type serpent_of_hell_branch(monster_type m)
{
    switch (m)
    {
    case MONS_SERPENT_OF_HELL_COCYTUS:
        return BRANCH_COCYTUS;
    case MONS_SERPENT_OF_HELL_DIS:
        return BRANCH_DIS;
    case MONS_SERPENT_OF_HELL_TARTARUS:
        return BRANCH_TARTARUS;
    case MONS_SERPENT_OF_HELL:
        return BRANCH_GEHENNA;
    default:
        die("bad serpent of hell monster_type");
    }
}

string serpent_of_hell_flavour(monster_type m)
{
    return lowercase_string(branches[serpent_of_hell_branch(m)].shortname);
}

static string _desc_foxfire_dam(const monster_info &mi)
{
    bolt beam;
    zappy(ZAP_FOXFIRE, mi.hd, mi.attitude != ATT_FRIENDLY, beam);
    return make_stringf("%dd%d", beam.damage.num, beam.damage.size);
}

static string _desc_shooting_star_dam(const monster_info &mi)
{
    bolt beam;
    zappy(ZAP_SHOOTING_STAR, mi.hd, mi.attitude != ATT_FRIENDLY, beam);
    return make_stringf("%dd%d", beam.damage.num, beam.damage.size);
}

// getLongDescription/getQuoteString can return the active translation. Read
// canonical source literals first, then use only the reviewed exact-entry map.
static string _monster_db_source(const char *context, const string &key)
{
    if (string(context) == "detail.monster.status_text")
        return trimmed_string(zh_database_description(key, context));
    string source;
    {
        ZhTranslationPause pause;
        // Trim paragraph edges only; preserve internal layout and source keys.
        source = trimmed_string(getLongDescription(key));
    }
    return zh_source(context, source.c_str());
}

static string _monster_quote_source(const string &key)
{
    string source;
    {
        ZhTranslationPause pause;
        source = trimmed_string(getQuoteString(key));
    }
    return zh_source("detail.monster.quote", source.c_str());
}

// Fetches the monster's database description and reads it into inf.
void get_monster_db_desc(const monster_info& mi, describe_info &inf,
                         bool &has_stat_desc, bool mark_spells)
{
    string title_source = inf.title;
    if (title_source.empty())
    {
        const ZhTranslationPause canonical;
        title_source = getMiscString(mi.common_name(DESC_DBNAME) + " title");
    }
    const auto title_message = _monster_detail_title_message(mi, title_source);
    inf.title = ZhMessage{title_message.message_id, title_message.canonical,
                          title_message.localized}.display();

    string db_name;

    if (mi.props.exists(DBNAME_KEY))
        db_name = mi.props[DBNAME_KEY].get_string();
    else if (mi.mname.empty())
        db_name = mi.db_name();
    else
        db_name = mi.full_name(DESC_PLAIN);

    if (mons_species(mi.type) == MONS_SERPENT_OF_HELL)
        db_name += " " + serpent_of_hell_flavour(mi.type);
    if (mi.type == MONS_ORC_APOSTLE && mi.attitude == ATT_FRIENDLY)
        db_name = "orc apostle follower";

    // Don't get description for player ghosts.
    if (mi.type != MONS_PLAYER_GHOST && mi.type != MONS_PLAYER_ILLUSION)
    {
        // This is one fixed database entry, not an assembled sentence.
        inf.body << _monster_db_source("detail.monster.lore", db_name);
    }

    // And quotes {due}
    inf.quote = _monster_quote_source(db_name);

    string symbol;
    symbol += get_monster_data(mi.type)->basechar;
    if (isaupper(symbol[0]))
        symbol = "cap-" + symbol;

    string quote2;
    if (!mons_is_unique(mi.type))
    {
        string symbol_prefix = "__" + symbol + "_prefix";
        inf.prefix = _monster_db_source("detail.monster.lore", symbol_prefix);

        string symbol_suffix = "__" + symbol + "_suffix";
        quote2 = _monster_quote_source(symbol_suffix);
    }

    if (!inf.quote.empty() && !quote2.empty())
        inf.quote += "\n";
    inf.quote += quote2;

    const string it = mi.pronoun(PRONOUN_SUBJECTIVE);
    const string it_o = mi.pronoun(PRONOUN_OBJECTIVE);
    const string It = uppercase_first(it);
    const string is = conjugate_verb("are", mi.pronoun_plurality());

    switch (mi.type)
    {
    case MONS_RED_DRACONIAN:
    case MONS_WHITE_DRACONIAN:
    case MONS_GREEN_DRACONIAN:
    case MONS_PALE_DRACONIAN:
    case MONS_BLACK_DRACONIAN:
    case MONS_YELLOW_DRACONIAN:
    case MONS_PURPLE_DRACONIAN:
    case MONS_GREY_DRACONIAN:
    case MONS_DRACONIAN_SHIFTER:
    case MONS_DRACONIAN_SCORCHER:
    case MONS_DRACONIAN_ANNIHILATOR:
    case MONS_DRACONIAN_STORMCALLER:
    case MONS_DRACONIAN_MONK:
    case MONS_DRACONIAN_KNIGHT:
    {
        inf.body << "\n" << _describe_draconian(mi) << "\n";
        break;
    }

    case MONS_PLAYER_GHOST:
    {
        const string ghost = get_ghost_description(mi);
        inf.body << zh_message("monster.detail.ghost", {
            ZhArg("ghost", ZhArgType::Name, ghost, ghost, false)}).display() << "\n";
        if (mi.props.exists(MIRRORED_GHOST_KEY))
            inf.body << zh_message("monster.detail.spooky").display() << "\n";
        break;
    }

    case MONS_PLAYER_ILLUSION:
    {
        const string ghost = get_ghost_description(mi);
        inf.body << zh_message("monster.detail.illusion", {
            ZhArg("ghost", ZhArgType::Name, ghost, ghost, false)}).display() << "\n";
        break;
    }

    case MONS_PANDEMONIUM_LORD:
    {
        const string description = _describe_demon(mi.mname, mi.airborne(), mi.ghost_colour);
        inf.body << zh_message("monster.detail.pan_lord", {
            ZhArg("description", ZhArgType::Text, description, description, false)},
            description).display() << "\n";
        break;
    }

    case MONS_MUTANT_BEAST:
        // vault renames get their own descriptions
        if (mi.mname.empty() || !mi.is(MB_NAME_REPLACE))
            inf.body << _describe_mutant_beast(mi) << "\n";
        break;

    case MONS_BLOCK_OF_ICE:
        if (mi.is(MB_SLOWLY_DYING))
            inf.body << "\n" << zh_message("monster.detail.melting").display() << "\n";
        break;

    case MONS_BRIAR_PATCH: // death msg uses "crumbling"
    case MONS_PILLAR_OF_SALT:
        // XX why are these "quick" here but "slow" elsewhere??
        if (mi.is(MB_SLOWLY_DYING))
            inf.body << "\n" << zh_message("monster.detail.crumbling").display() << "\n";
        break;

    case MONS_FOXFIRE:
    {
        const string damage = _desc_foxfire_dam(mi);
        const string canonical = "It deals " + damage + " fire damage.";
        inf.body << "\n" << zh_message("monster.detail.foxfire_damage", {
            ZhArg("damage", ZhArgType::Text, damage, damage, true)}, canonical).display() << "\n";
        break;
    }

    case MONS_SHOOTING_STAR:
    {
        const string damage = _desc_shooting_star_dam(mi);
        const string canonical = "It deals " + damage + " damage.";
        inf.body << "\n" << zh_message("monster.detail.shooting_star_damage", {
            ZhArg("damage", ZhArgType::Text, damage, damage, true)}, canonical).display() << "\n";
        break;
    }

    case MONS_PROGRAM_BUG:
    {
        inf.body << zh_message("monster.special.program_bug").display() << "\n";
        break;
    }

    default:
        break;
    }

    if (mons_class_is_fragile(mi.type))
    {
        if (mi.is(MB_CRUMBLING))
            inf.body << "\n" << zh_message("monster.detail.crumbling").display() << "\n";
        else if (mi.is(MB_WITHERING))
            inf.body << "\n" << zh_message("monster.detail.withering").display() << "\n";
        else if (mi.holi & (MH_NONLIVING))
            inf.body << "\n" << zh_message("monster.detail.struck_crumble").display() << "\n";
        else
            inf.body << "\n" << zh_message("monster.detail.struck_die").display() << "\n";
    }

    if (!mons_is_unique(mi.type))
    {
        string symbol_suffix = "__";
        symbol_suffix += symbol;
        symbol_suffix += "_suffix";

        const string suffix = _monster_db_source("detail.monster.lore", symbol_suffix);
        const string suffix_examine = _monster_db_source(
            "detail.monster.lore", symbol_suffix + "_examine");

        if (!suffix.empty())
            inf.body << "\n" << suffix;
        if (!suffix_examine.empty())
            inf.body << suffix_examine;
    }

    const int curse_power = mummy_curse_power(mi.type);
    if (curse_power && !mi.is(MB_SUMMONED))
    {
        const string canonical = It + " will inflict a "
            + (curse_power > 10 ? "powerful " : "")
            + "necromantic curse on " + mi.pronoun(PRONOUN_POSSESSIVE)
            + " foe when destroyed.";
        inf.body << "\n" << zh_message(curse_power > 10
            ? "monster.detail.powerful_curse" : "monster.detail.curse",
            {}, canonical).display() << "\n";
    }

    // Get information on resistances, speed, etc.
    string result = _monster_stat_description(mi, mark_spells);
    if (!result.empty())
    {
        inf.body << "\n" << result;
        has_stat_desc = true;
    }

    bool did_stair_use = false;
    if (!mons_class_can_use_stairs(mi.type))
    {
        const string canonical = It + " " + is + " incapable of using stairs.";
        inf.body << zh_message("monster.detail.stairs", {}, canonical).display() << "\n";
        did_stair_use = true;
    }

    result = _monster_current_target_description(mi);
    if (!result.empty())
        inf.body << "\n" << result;

    if (mi.is(MB_SUMMONED))
    {
        string canonical = "This monster has been ";
        string intro_zh;

        // XXX: Expand this for better descriptions of some other types of
        //      non-abjurable summons?
        if (mi.is(MB_ABJURABLE))
        {
            canonical += "temporarily summoned to this location. ";
            intro_zh = "该怪物被暂时召唤至此。 ";
        }
        else if (mi.is(MB_MINION))
        {
            canonical += "created by magic and is temporary. ";
            intro_zh = "该怪物由魔法创造，只会暂时存在。 ";
        }

        // TODO: hacks; convert angered_by_attacks to a monster_info check
        // (but on the other hand, it is really limiting to not have access
        // to the monster...)
        const bool angered = !mi.pos.origin() && monster_at(mi.pos)
            && monster_at(mi.pos)->angered_by_attacks()
            && mi.attitude == ATT_FRIENDLY;
        string outcome_zh;
        if (angered)
        {
            canonical += "If angered " + it
                + " will immediately vanish, yielding no experience or items";
            outcome_zh = "若激怒该怪物，它会立即消失，不提供经验或物品";
        }
        else
        {
            canonical += "Killing " + it_o + " yields no experience or items";
            outcome_zh = "杀死该怪物不会获得经验或物品";
        }

        string stairs_zh;
        if (!did_stair_use)
        {
            canonical += "; " + it + " " + is + " incapable of using stairs";
            stairs_zh = "；该怪物无法使用楼梯";
        }

        canonical += ".";
        inf.body << "\n" << zh_message("monster.detail.summoned_status", {
            zh_text("intro", string("This monster has been ")
                + (mi.is(MB_ABJURABLE) ? "temporarily summoned to this location. "
                    : mi.is(MB_MINION) ? "created by magic and is temporary. " : ""),
                intro_zh),
            zh_text("outcome", angered
                ? "If angered " + it + " will immediately vanish, yielding no experience or items"
                : "Killing " + it_o + " yields no experience or items", outcome_zh),
            zh_text("stairs", did_stair_use ? ""
                : "; " + it + " " + is + " incapable of using stairs", stairs_zh)
        }, canonical).display() << "\n";
    }
    else if (mi.is(MB_NO_REWARD))
        inf.body << "\n" << zh_message("monster.detail.no_reward").display();
    else if (mons_class_leaves_hide(mi.type))
    {
        const string canonical = "If " + it + " " + is
            + " slain, it may be possible to recover "
            + mi.pronoun(PRONOUN_POSSESSIVE)
            + " hide, which can be used as armour.";
        inf.body << "\n" << zh_message("monster.detail.hide", {}, canonical).display() << "\n";
    }

    if (!inf.quote.empty())
        inf.quote += "\n";

#ifdef DEBUG_DIAGNOSTICS
    if (you.suppress_wizard)
        return;
    if (mi.pos.origin() || !monster_at(mi.pos))
        return; // not a real monster
    monster& mons = *monster_at(mi.pos);

    if (mons.has_originating_map())
    {
        inf.body << make_stringf("\nPlaced by map: %s",
                                 mons.originating_map().c_str());
    }

    inf.body << "\nMonster health: "
             << mons.hit_points << "/" << mons.max_hit_points << "\n";

    const actor *mfoe = mons.get_foe();
    inf.body << "Monster foe: "
             << (mfoe? mfoe->name(DESC_PLAIN, true)
                 : "(none)");

    vector<string> attitude;
    if (mons.friendly())
        attitude.emplace_back("friendly");
    if (mons.neutral())
        attitude.emplace_back("neutral");
    if (mons.good_neutral())
        attitude.emplace_back("good_neutral");
    if (mons.pacified())
        attitude.emplace_back("pacified");
    if (mons.wont_attack())
        attitude.emplace_back("wont_attack");
    if (!attitude.empty())
    {
        string att = comma_separated_line(attitude.begin(), attitude.end(),
                                          "; ", "; ");
        if (mons.has_ench(ENCH_FRENZIED))
            inf.body << "; frenzied and wild (otherwise " << att << ")";
        else
            inf.body << "; " << att;
    }
    else if (mons.has_ench(ENCH_FRENZIED))
        inf.body << "; frenzied and wild";

    inf.body << "\n\nHas holiness: ";
    inf.body << holiness_description(mi.holi);
    inf.body << ".";

    const monster_spells &hspell_pass = mons.spells;
    bool found_spell = false;

    for (unsigned int i = 0; i < hspell_pass.size(); ++i)
    {
        if (!found_spell)
        {
            inf.body << "\n\nMonster Spells:\n";
            found_spell = true;
        }

        inf.body << "    " << i << ": "
                 << spell_title(hspell_pass[i].spell)
                 << " (";
        if (hspell_pass[i].flags & MON_SPELL_EMERGENCY)
            inf.body << "emergency, ";
        if (hspell_pass[i].flags & MON_SPELL_NATURAL)
            inf.body << "natural, ";
        if (hspell_pass[i].flags & MON_SPELL_MAGICAL)
            inf.body << "magical, ";
        if (hspell_pass[i].flags & MON_SPELL_WIZARD)
            inf.body << "wizard, ";
        if (hspell_pass[i].flags & MON_SPELL_PRIEST)
            inf.body << "priest, ";
        if (hspell_pass[i].flags & MON_SPELL_VOCAL)
            inf.body << "vocal, ";
        if (hspell_pass[i].flags & MON_SPELL_BREATH)
            inf.body << "breath, ";
        inf.body << (int) hspell_pass[i].freq << ")";
    }

    bool has_item = false;
    for (mon_inv_iterator ii(mons); ii; ++ii)
    {
        if (!has_item)
        {
            inf.body << "\n\nMonster Inventory:\n";
            has_item = true;
        }
        inf.body << "    " << ii.slot() << ": "
                 << ii->name(DESC_A, false, true);
    }

    if (mons.props.exists(BLAME_KEY))
    {
        inf.body << "\n\nMonster blame chain:\n";

        const CrawlVector& blame = mons.props[BLAME_KEY].get_vector();

        for (const auto &entry : blame)
            inf.body << "    " << entry.get_string() << "\n";
    }
    inf.body << "\n\n" << debug_constriction_string(&mons);
#endif
}

static formatted_string _get_monster_status_descriptions(const monster_info& mi)
{
    vector<ZhArg> descriptors = get_monster_status_descriptor_messages(mi);
    if (descriptors.empty())
        return formatted_string();

    ostringstream out;
    for (const auto& tag : descriptors)
    {
        const string key = make_stringf("%s monstatus", tag.canonical.c_str());
        string lookup = _monster_db_source("detail.monster.status_text", key);
        if (lookup.empty())
            continue;

        // Some status entries are database references rather than prose.
        // Never expose the internal [[...]] key as player-facing text.
        if (lookup.find("[[") != string::npos)
        {
            zh_source("detail.monster.status_reference", lookup.c_str());
            continue;
        }

        out << "<w>状态：</w>\n";

        // Wordwrap and indent slightly.
        linebreak_string(lookup, 77);
        lookup = replace_all(lookup, "\n", "\n   ");

        out << "   " << lookup << "\n\n";
    }

    return formatted_string::parse_string_raw(out.str());
}

int describe_monster(const monster_info &mi, const string& /*footer*/)
{
    ZhLegacyGuard legacy_guard("detail.monster");
    bool has_stat_desc = false;
    describe_info inf;
    formatted_string desc;

#ifdef USE_TILE_WEB
    // mark the spellset (XX, separate mi field?)
    get_monster_db_desc(mi, inf, has_stat_desc, true);
#else
    get_monster_db_desc(mi, inf, has_stat_desc);
#endif

    spellset spells = monster_spellset(mi);

    auto vbox = make_shared<Box>(Widget::VERT);
    auto title_hbox = make_shared<Box>(Widget::HORZ);

#ifdef USE_TILE_LOCAL
    auto dgn = make_shared<Dungeon>();
    dgn->width = dgn->height = 1;
    dgn->buf().add_monster(mi, 0, 0);
    title_hbox->add_child(std::move(dgn));
#endif

    auto title = make_shared<Text>();
    title->set_text(formatted_string::parse_string_raw(inf.title));
    title->set_margin_for_sdl(0, 0, 0, 10);
    title_hbox->add_child(std::move(title));

    title_hbox->set_cross_alignment(Widget::CENTER);
    title_hbox->set_margin_for_crt(0, 0, 1, 0);
    title_hbox->set_margin_for_sdl(0, 0, 20, 0);
    vbox->add_child(std::move(title_hbox));

    // The database body has already been selected/localized at its source.
    // Do not route it through formatted_string(string)'s legacy matcher.
    desc += formatted_string::parse_string_raw(inf.body.str());
    if (crawl_state.game_is_hints())
    {
        const string hint = hints_describe_monster_display(mi, has_stat_desc);
        if (!hint.empty())
            desc += formatted_string::parse_string_raw(hint);
    }
    // Footer text is likewise already localized or explicitly source-keyed.
    desc += formatted_string::parse_string_raw(inf.footer);
    string raw_desc = trimmed_string(desc); // forces us back to a colour string

#ifdef USE_TILE_WEB
    // the spell list is delimited so that we can later replace this substring
    // with a placeholder marker; remove the delimiters for console display
    desc = formatted_string::parse_string_raw(
        replace_all(
            replace_all(raw_desc, SPELL_LIST_BEGIN, ""),
            SPELL_LIST_END, ""));
#else
    desc = formatted_string::parse_string_raw(raw_desc);
#endif

    const formatted_string quote = formatted_string::parse_string_raw(
        trimmed_string(inf.quote));
    const formatted_string status_desc = _get_monster_status_descriptions(mi);


    auto desc_sw = make_shared<Switcher>();
    auto more_sw = make_shared<Switcher>();
    desc_sw->current() = 0;
    more_sw->current() = 0;

    const string mores[3] =
    {
        "[<w>!</w>]: <w>说明</w>",
        "[<w>!</w>]: 说明",
        "[<w>!</w>]: 说明",
    };

    const formatted_string *content[3] = { &desc, &status_desc, &quote };
    const int num_modes = 1 + !status_desc.empty() + !inf.quote.empty();

    for (int i = 0; i < 3; i++)
    {
        // Skip absent information.
        if (i == 1 && status_desc.empty())
            continue;
        if (i == 2 && inf.quote.empty())
            break;

        auto text = make_shared<Text>(content[i]->trim());
        auto scroller = make_shared<Scroller>();
        text->set_wrap_text(true);
        scroller->set_child(text);
        desc_sw->add_child(std::move(scroller));

        string more = make_stringf("%s%s%s", mores[i].c_str(),
            !status_desc.empty()
                ? i == 1 ? "|<w>状态</w>" : "|状态"
                : "",
            !inf.quote.empty()
                ? i == 2 ? "|<w>引言</w>" : "|引言"
                : "");

        more_sw->add_child(make_shared<Text>(
                formatted_string::parse_string_raw(more)));
    }

    more_sw->set_margin_for_sdl(20, 0, 0, 0);
    more_sw->set_margin_for_crt(1, 0, 0, 0);
    desc_sw->expand_h = false;
    desc_sw->align_x = Widget::STRETCH;
    vbox->add_child(desc_sw);
    if (!inf.quote.empty() || !status_desc.empty())
        vbox->add_child(more_sw);

#ifdef USE_TILE_LOCAL
    vbox->max_size().width = tiles.get_crt_font()->char_width()*80;
#endif

    auto popup = make_shared<ui::Popup>(std::move(vbox));

    bool done = false;
    int lastch;
    popup->on_keydown_event([&](const KeyEvent& ev) {
        const auto key = ev.key();
        lastch = key;
        done = ui::key_exits_popup(key, true);
        if (key == '!')
        {
            // Cycle mode (skipping absent ones)
            int n = (desc_sw->current() + 1);
            if (n >= num_modes)
                n = 0;

            desc_sw->current() = more_sw->current() = n;
#ifdef USE_TILE_WEB
            tiles.json_open_object();
            tiles.json_write_int("pane", n);
            tiles.ui_state_change("describe-monster", 0);
#endif
        }
        if (desc_sw->current_widget()->on_event(ev))
            return true;
        const vector<pair<spell_type,char>> spell_map = map_chars_to_spells(spells);
        auto entry = find_if(spell_map.begin(), spell_map.end(),
                [key](const pair<spell_type,char>& e) { return e.second == key; });
        if (entry == spell_map.end())
            return false;
        describe_spell(entry->first, &mi, nullptr);
        return true;
    });

#ifdef USE_TILE_WEB
    tiles.json_open_object();
    tiles.json_write_string("title", inf.title);

    string desc_without_spells = raw_desc;
    if (!spells.empty())
    {
        // TODO: webtiles could could just look for these delimiters? But I'm
        // fixing a bug very close to release so I'm not going to change this
        // now -advil
        auto start = desc_without_spells.find(SPELL_LIST_BEGIN);
        auto end = desc_without_spells.find(SPELL_LIST_END);
        if (start == string::npos || end == string::npos || start >= end)
            desc_without_spells += "\n\nBUGGY SPELLSET\n\nSPELLSET_PLACEHOLDER";
        else
        {
            const size_t len = end + (string(SPELL_LIST_END) + "\n").size() - start;
            desc_without_spells.replace(start, len, "SPELLSET_PLACEHOLDER");
        }
    }
    tiles.json_write_string("body", desc_without_spells);
    tiles.json_write_string("quote", quote);
    tiles.json_write_string("status", status_desc.to_colour_string());
    write_spellset(spells, nullptr, &mi);

    {
        tileidx_t t    = tileidx_monster(mi);
        tileidx_t t0   = t & TILE_FLAG_MASK;
        tileidx_t flag = t & (~TILE_FLAG_MASK);

        if (!mons_class_is_stationary(mi.type) || mi.type == MONS_TRAINING_DUMMY)
        {
            tileidx_t mcache_idx = mcache.register_monster(mi);
            t = flag | (mcache_idx ? mcache_idx : t0);
            t0 = t & TILE_FLAG_MASK;
        }

        tiles.json_write_int("fg_idx", t0);
        tiles.json_write_name("flag");
        tiles.write_tileidx(flag);
        tiles.json_write_icons(status_icons_for(mi));

        if (t0 >= TILEP_MCACHE_START)
        {
            mcache_entry *entry = mcache.get(t0);
            if (entry)
                tiles.send_mcache(entry, false);
            else
            {
                tiles.json_write_comma();
                tiles.write_message("\"doll\":[[%d,%d]]", TILEP_MONS_UNKNOWN, TILE_Y);
                tiles.json_write_null("mcache");
            }
        }
        else if (get_tile_texture(t0) == TEX_PLAYER)
        {
            tiles.json_write_comma();
            tiles.write_message("\"doll\":[[%u,%d]]", (unsigned int) t0, TILE_Y);
            tiles.json_write_null("mcache");
        }
    }
    tiles.push_ui_layout("describe-monster", 1);
    popup->on_layout_pop([](){ tiles.pop_ui_layout(); });
#endif

    ui::run_layout(std::move(popup), done);

    return lastch;
}

static const char* xl_rank_names[] =
{
    "weakling",
    "amateur",
    "novice",
    "journeyman",
    "adept",
    "veteran",
    "master",
    "legendary"
};

static string _xl_rank_name(const int xl_rank)
{
    const string rank = xl_rank_names[xl_rank];

    return article_a(rank);
}

string short_ghost_description(const monster *mon, bool abbrev)
{
    ASSERT(mons_is_pghost(mon->type));

    const ghost_demon &ghost = *(mon->ghost);
    const char* rank = xl_rank_names[ghost_level_to_rank(ghost.xl)];

    string desc = make_stringf("%s %s %s", rank,
                               species::name(ghost.species).c_str(),
                               get_job_name(ghost.job));

    if (abbrev || strwidth(desc) > 40)
    {
        desc = make_stringf("%s %s%s",
                            rank,
                            species::get_abbrev(ghost.species),
                            get_job_abbrev(ghost.job));
    }

    return desc;
}

// Describes the current ghost's previous owner. The caller must
// prepend "The apparition of" or whatever and append any trailing
// punctuation that's wanted.
string get_ghost_description(const monster_info &mi, bool concise)
{
    ostringstream gstr;

    const species_type gspecies = mi.i_ghost.species;

    string title = mi.i_ghost.title;
#if TAG_MAJOR_VERSION == 34
    if (title.empty())
    {
        title = skill_title_by_rank(mi.i_ghost.best_skill,
                        mi.i_ghost.best_skill_rank,
                        gspecies,
                        get_species_def(gspecies).d,
                        get_species_def(gspecies).s,
                        get_species_def(gspecies).i,
                        mi.i_ghost.religion,
                        10 + mi.i_ghost.xl_rank * 27,
                        false);
    }
#endif

    gstr << mi.mname << " the "
         << title
         << ", " << _xl_rank_name(mi.i_ghost.xl_rank) << " ";

    if (concise)
    {
        gstr << species::get_abbrev(gspecies)
             << get_job_abbrev(mi.i_ghost.job);
    }
    else
    {
        gstr << species::name(gspecies)
             << " "
             << get_job_name(mi.i_ghost.job);
    }

    if (mi.i_ghost.religion != GOD_NO_GOD)
    {
        gstr << " of "
             << god_name(mi.i_ghost.religion);
    }

    return gstr.str();
}

void describe_skill(skill_type skill)
{
    ZhLegacyGuard skill_detail_guard("detail.skill");
    describe_info inf;
    const string skill_en = skill_name(skill);
    const auto skill_arg = zh_glossary_name("skill", "skill.name", skill_en);
    inf.title = zh_language_enabled() ? skill_arg.localized : skill_arg.canonical;
    inf.body << get_skill_description(skill, false);
    tile_def tile = tile_def(tileidx_skill(skill, TRAINING_ENABLED));
    show_description(inf, &tile, true);
}

#ifdef USE_TILE_LOCAL // only used in tiles
string get_command_description(const command_type cmd, bool terse)
{
    string lookup = command_to_name(cmd);

    if (!terse)
        lookup += " verbose";

    string result = getLongDescription(lookup);
    if (result.empty())
    {
        if (!terse)
        {
            // Try for the terse description.
            result = get_command_description(cmd, true);
            if (!result.empty())
                return result + ".";
        }
        return command_to_name(cmd);
    }

    return result.substr(0, result.length() - 1);
}
#endif

static string _format_data_label(int value, bool show_sign, bool is_percent,
                                 int divisor = 0, int decimal_places = 0)
{
    const bool red = value < 0;

    if (divisor > 0)
    {
        float fvalue = (float)value / (float) divisor;
        const string fstring = (show_sign ? "%s%+." : "%s%.") +
                                to_string(decimal_places) + "f%s%s";

        return make_stringf(fstring.c_str(), red ? "<red>" : "",
                                             fvalue, is_percent ?  "%" : "",
                                             red ? "</red>" : "");
    }

    const char* fstring = show_sign ? "%s%+d%s%s" : "%s%d%s%s";
    return make_stringf(fstring, red ? "<red>" : "",
                                 value, is_percent ?  "%" : "",
                                 red ? "</red>" : "");
}

static void _maybe_note_armour_modifier(vector<vector<string>>& items,
                                        const Form& form,
                                        const int skill[3])
{
    int mult[3];
    for (int i = 0; i < 3; ++i)
        mult[i] = form.get_body_ac_mult(skill[i]);

    if (mult[0] == 0 && mult[1] == 0 && mult[2] == 0)
        return;

    const item_def *body_armour = you.body_armour();
    const int base_ac = body_armour ? you.base_ac_from(*body_armour, 100, false)
                                    : 0;

    int change[3];
    for (int i = 0; i < 3; ++i)
        change[i] = base_ac * mult[i] / 100;

    vector<string> labels;
    labels.push_back("Body Armour AC");

    for (int i = 0; i < 3; ++i)
    {
        if (mult[i] != 0)
        {
            labels.push_back(_format_data_label(change[i], true, false, 100, 1)
                             + " ("
                             + _format_data_label(mult[i], true, true)
                             + ")");
        }
        else
            labels.push_back("0");
    }

    items.push_back(labels);
}

static void _maybe_note_form_dice(vector<vector<string>>& items,
                                  function<dice_def(int)> func, string label,
                                  const int skill[3], const string suffix = "")
{
    dice_def data[3];
    for (int i = 0; i < 3; ++i)
        data[i] = func(skill[i]);

    // This parameter is never non-zero, so don't bother noting is.
    if (data[0].num == 0 && data[1].num == 0 && data[2].num == 0)
    return;

    vector<string> labels;
    labels.push_back(label);
    labels.push_back(make_stringf("%dd%d%s", data[0].num, data[0].size, suffix.c_str()));
    labels.push_back(make_stringf("%dd%d%s", data[1].num, data[1].size, suffix.c_str()));
    labels.push_back(make_stringf("%dd%d%s", data[2].num, data[2].size, suffix.c_str()));

    items.push_back(labels);
}

static void _maybe_note_airstrike_damage(vector<vector<string>>& items,
                                         const int skill[3])
{
    dice_def data[3][2];
    for (int i = 0; i < 3; ++i)
    {
        data[i][0] = player_airstrike_melee_damage(0, skill[i]);
        data[i][1] = player_airstrike_melee_damage(7, skill[i]);
    }

    vector<string> labels;
    labels.push_back("Airstrike Dmg");
    labels.push_back(make_stringf("(%d-%d)d%d", data[0][0].num, data[0][1].num, data[0][0].size));
    labels.push_back(make_stringf("(%d-%d)d%d", data[1][0].num, data[1][1].num, data[1][0].size));
    labels.push_back(make_stringf("(%d-%d)d%d", data[2][0].num, data[2][1].num, data[2][0].size));

    items.push_back(labels);
}

/**
 * Possibly add a column of data to the form properties table.
 *
 * @param items The list of table entries to append this property to.
 * @param func  A function that takes shapeshifting skill to return numerical
 *              values (ie: Form::get_base_unarmed_damage).
 * @param skill In order: [minimum, maximum, and current] shapeshifting skill
 *              for this form.
 * @param flat_factor A flat number to subtract from the return value of func.
 *                    (eg: so that "100%" HP can be converted into "+0%".)
 * @param is_percent Whether to add a percentage sign to each entry.
 * @param show_sign  Whether to show +/- in front of each entry.
 * @param divisor   A number to divide the return value of func by.
 * @param decimal_places How many decimal places to show for dividing numbers?
 */
static void _maybe_populate_form_table(vector<vector<string>>& items,
                                       function<int(int)> func, string label,
                                       const int skill[3],
                                       int flat_factor = 0, bool is_percent = false,
                                       bool show_sign = true,
                                       int divisor = 1, int decimal_places = 0)
{
    int data[3];
    // Collect the data values. (Apply the divisor immediately if we're doing
    // int division; otherwise, apply it in _format_data_label)
    for (int i = 0; i < 3; ++i)
        data[i] = (func(skill[i]) + flat_factor) / (decimal_places ? 1 : divisor);

    // This parameter is never non-zero, so don't bother noting is.
    if (data[0] == 0 && data[1] == 0 && data[2] == 0)
        return;

    vector<string> labels;
    labels.push_back(label);
    labels.push_back(_format_data_label(data[0], show_sign, is_percent, decimal_places ? divisor : 0, decimal_places));
    labels.push_back(_format_data_label(data[1], show_sign, is_percent, decimal_places ? divisor : 0, decimal_places));
    labels.push_back(_format_data_label(data[2], show_sign, is_percent, decimal_places ? divisor : 0, decimal_places));

    items.push_back(labels);
}

static void _desc_form_resist(TablePrinter& pr, mon_resist_flags resist, int amount)
{
    // Don't bother mentioning non-existant resists
    if (amount == 0)
        return;

    const int max = (resist == MR_RES_POISON || resist == MR_RES_ELEC || resist == MR_RES_CORR)
                        ? 1 : 3;
    const string desc = desc_resist(amount, max, amount == 3, false);
    pr.AddCell(_res_name(resist), desc, amount < 0 ? RED : LIGHTGREY);
}

static void _desc_form_val(TablePrinter& pr, string label, int val)
{
    if (val == 0)
        return;

    pr.AddCell(label, make_stringf("%+d", val).c_str(), val < 0 ? RED : LIGHTGREY);
}

static string _form_atom(const char *domain, const string &source, bool &supported)
{
    const ZhArg atom = zh_word_arg("value", domain, source, ZhArgType::Name);
    supported = supported && atom.supported;
    return zh_language_enabled() ? atom.localized : atom.canonical;
}

// Four semantic columns, independent of the number of scaling properties.
static vector<int> _form_table_widths(const vector<vector<string>> &items)
{
    vector<int> widths(4, 6);
    for (const auto &row : items)
        for (int col = 0; col < 4; ++col)
            widths[col] = max(widths[col], min(col == 0 ? 28 : 16,
                formatted_string::parse_string_raw(row[col]).width() + 2));
    return widths;
}

static string _render_form_scaling_table(const vector<vector<string>> &items)
{
    const vector<int> widths = _form_table_widths(items);
    const int total = widths[0] + widths[1] + widths[2] + widths[3];
    ostringstream out;
    out << string(total, '_') << "\n\n";
    for (size_t row = 0; row < items.size(); ++row)
    {
        vector<vector<formatted_string>> cells(4);
        size_t height = 1;
        for (int col = 0; col < 4; ++col)
        {
            const string text = row == 0 || col == 3
                ? "<white>" + items[row][col] + "</white>" : items[row][col];
            formatted_string::parse_string_to_multiple_raw(text, cells[col],
                                                          widths[col] - 2);
            height = max(height, cells[col].size());
        }
        for (size_t line = 0; line < height; ++line)
        {
            for (int col = 0; col < 4; ++col)
            {
                const formatted_string cell = line < cells[col].size()
                    ? cells[col][line] : formatted_string();
                out << cell.to_colour_string()
                    << string(max(0, widths[col] - cell.width()), ' ');
            }
            out << "\n";
        }
        if (row == 0)
            out << string(total, '-') << "\n";
    }
    return out.str();
}

static ZhArg _form_holiness_arg(mon_holy_type holiness)
{
    string canonical;
    string localized;
    bool supported = true;
    for (const auto bit : mon_holy_type::range())
    {
        if (!(holiness & bit))
            continue;
        const string name = holiness_name(bit);
        const ZhArg atom = zh_word_arg("holiness", "monster.table.",
                                      uppercase_first(name), ZhArgType::Name);
        if (!canonical.empty())
        {
            canonical += ",";
            localized += "、";
        }
        canonical += name;
        localized += atom.localized;
        supported = supported && atom.supported;
    }
    return {"holiness", ZhArgType::Text, uppercase_first(canonical), localized,
            supported};
}

static string _describe_talisman_form_impl(transformation form_type, bool &supported)
{
    const Form* form = get_form(form_type);

    // First comes the big table of scaling values, at min, max and current
    // skill; we get values at the latter by passing -1 to the various form
    // methods.
    const int skill[3] = {form->min_skill, form->max_skill, -1};
    vector<vector<string>> items;

    items.push_back({" ", "Min", "Max", "Cur"});

    const int shapeshifting = you.skill(SK_SHAPESHIFTING, 10);
    const string skill_string = make_stringf("%d.%d", shapeshifting / 10, shapeshifting % 10);
    const string cur_skill = (shapeshifting < 10*form->min_skill ? make_stringf("<red>%s</red>", skill_string.c_str())
                             : (shapeshifting >= 10*form->max_skill ? make_stringf("[%d]", form->max_skill)
                             : skill_string));
    items.push_back({"Skill", to_string(skill[0]), to_string(skill[1]), cur_skill});

    _maybe_populate_form_table(items, bind(&Form::mult_hp, form, 100, true, placeholders::_1), "HP", skill, -100, true, true, 1);
    _maybe_populate_form_table(items, bind(&Form::get_base_unarmed_damage, form, false, placeholders::_1), "UC Base Dmg", skill, -3);
    _maybe_populate_form_table(items, bind(&Form::get_ac_bonus, form, placeholders::_1), "AC", skill, 0, false, true, 100, 1);
    _maybe_populate_form_table(items, bind(&Form::ev_bonus, form, placeholders::_1), "EV", skill, 0, false, true, 100, 1);
    _maybe_populate_form_table(items, bind(&Form::max_mp_bonus, form, placeholders::_1), "MP", skill);
    _maybe_populate_form_table(items, bind(&Form::slay_bonus, form, false, placeholders::_1), "Slay", skill);
    _maybe_populate_form_table(items, bind(&Form::regen_bonus, form, placeholders::_1), "Regen", skill, 0, false, true, 100, 2);
    _maybe_populate_form_table(items, bind(&Form::mp_regen_bonus, form, placeholders::_1), "MP Regen", skill, 0, false, true, 100, 2);
    _maybe_populate_form_table(items, bind(&Form::get_web_chance, form, placeholders::_1), "Ensnare Chance", skill, 0, true, false);
    _maybe_note_armour_modifier(items, *form, skill);

    _maybe_note_form_dice(items, bind(&Form::get_special_damage, form, false, placeholders::_1), form->special_dice_name, skill,
                          form_type == transformation::dragon && !species::is_draconian(you.species) ? " (x2)" : "");

    if (form_type == transformation::maw)
    {
        _maybe_populate_form_table(items, bind(&Form::get_aux_damage, form, false, placeholders::_1), "Bite Dmg", skill, 0, false, false);
        _maybe_populate_form_table(items, bind(&Form::get_effect_size, form, placeholders::_1), "Devour Regen", skill, 0, false, true, 100, 2);
    }
    if (form_type == transformation::blade)
    {
        _maybe_populate_form_table(items, bind(&Form::get_aux_damage, form, false, placeholders::_1), "Blade Dmg", skill, 0, false, false);
        _maybe_populate_form_table(items, bind(&Form::get_effect_size, form, placeholders::_1), "Parry SH", skill, 0, false, false);
    }
    if (form_type == transformation::hive)
        _maybe_populate_form_table(items, bind(&Form::get_effect_size, form, placeholders::_1), "# of Bees", skill, 0, false, false, 10, 1);
    if (form_type == transformation::sphinx)
        _maybe_note_airstrike_damage(items, skill);
    if (form_type == transformation::werewolf)
    {
        _maybe_populate_form_table(items, bind(&Form::get_werefury_kill_bonus, form, placeholders::_1), "+Slay/Kill", skill, 0, false, false, 10, 1);
        _maybe_populate_form_table(items, bind(&Form::get_takedown_multiplier, form, placeholders::_1), "Takedown Dmg", skill, 0, true, true);
        _maybe_populate_form_table(items, bind(&Form::get_howl_power, form, placeholders::_1), "Howl Power", skill, 0, false, false);
    }
    if (form_type == transformation::walking_scroll)
        _maybe_populate_form_table(items, bind(walking_scroll_skill_bonus, 10, placeholders::_1), "Spell Skill Boost", skill, 0, false, true, 10, 1);
    if (form_type == transformation::fortress_crab)
        _maybe_populate_form_table(items, bind(&Form::get_effect_size, form, placeholders::_1), "Rust Breath Size", skill, 0, false, false);
    if (form_type == transformation::medusa)
    {
        _maybe_populate_form_table(items, bind(&Form::get_effect_size, form, placeholders::_1), "Tendril targets", skill, 0, false, false, 10, 1);
        _maybe_populate_form_table(items, bind(&Form::get_effect_chance, form, placeholders::_1), "Petrify chance", skill, 0, true, false);
    }
    if (form_type == transformation::vampire)
    {
        _maybe_populate_form_table(items, bind(&Form::get_effect_size, form, placeholders::_1), "Bat Swarm Recharge", skill, 0, true, false);
        _maybe_populate_form_table(items, bind(&Form::get_effect_chance, form, placeholders::_1), "Daze Power", skill, 0, false, false);
    }

    for (int col = 1; col < 4; ++col)
        items[0][col] = _form_atom("form.table.", items[0][col], supported);
    for (size_t row = 1; row < items.size(); ++row)
    {
        const string &label = items[row][0];
        const char *domain = label == "AC" || label == "EV" || label == "Regen"
            ? "monster.table." : "form.table.";
        items[row][0] = _form_atom(domain, label, supported);
    }
    ostringstream description;
    description << _render_form_scaling_table(items);
    if (form->holiness)
    {
        const ZhArg holiness = _form_holiness_arg(form->holiness);
        supported = supported && holiness.supported;
        description << "\n" << zh_message("item.talisman.form.class_line",
                                           {holiness}).display();
    }

    // Now add various one-off bits of (generally non-scaling) data after that
    TablePrinter pr(4, 80);
    pr.AddRow();

    if (form->size != SIZE_CHARACTER)
        pr.AddCell("Size", _form_atom("form.size.", get_size_adj(form->size), supported));

    _desc_form_val(pr, "Str", form->str_mod);
    _desc_form_val(pr, "Dex", form->dex_mod);

    _desc_form_resist(pr, MR_RES_FIRE, form->res_fire());
    _desc_form_resist(pr, MR_RES_COLD, form->res_cold());

    // The player being nonliving implies poison immunity, but *not* negative
    // energy immunity.
    if (bool(form->holiness & (MH_NONLIVING | MH_UNDEAD)))
        _desc_form_resist(pr, MR_RES_POISON, 3);
    else
        _desc_form_resist(pr, MR_RES_POISON, form->res_pois());

    _desc_form_resist(pr, MR_RES_NEG, form->res_neg());
    _desc_form_resist(pr, MR_RES_ELEC, form->res_elec());
    _desc_form_resist(pr, MR_RES_CORR, form->res_corr());

    // Various ad hoc properties of individual forms
    if (form_type == transformation::statue)
    {
        pr.AddCell("Melee dmg", "+50%");
        pr.AddCell("EV", "-20%", RED);
    }
    else if (form_type == transformation::maw)
        pr.AddCell("Bite speed", "15 aut");
    else if (form_type == transformation::eel_hands)
        pr.AddCell("Elec chance", "50%");
    else if (form_type == transformation::blade)
        pr.AddCell("Aux chance", "60% (x2)");
    else if (form_type == transformation::death)
        pr.AddCell("Will", "+");
    else if (form_type == transformation::vampire)
        pr.AddCell("Stealth", "++");
    else if (form_type == transformation::spider)
        pr.AddCell("Stealth", "+");
    else if (form_type == transformation::aqua)
        pr.AddCell("Reach", "+2");
    else if (form_type == transformation::sphinx)
    {
        if (!you.has_mutation(MUT_NO_ARMOUR))
            pr.AddCell("Barding", zh_source("detail.form.table_value", "Yes"));
        pr.AddCell("Will", "+");
    }
    else if (form_type == transformation::werewolf)
    {
        pr.AddCell("Will", "-", RED);
        pr.AddCell("Claws", "3");
    }
    else if (form_type == transformation::walking_scroll
             || form_type == transformation::flux)
    {
        pr.AddCell("Melee damage", "-50%", RED);
    }

    if (form_type == transformation::vampire || form_type == transformation::sphinx)
        pr.AddCell("SInv", "+");

    // Don't output extra blank lines if there's no content.
    if (pr.NumCells() > 0)
    {
        description << "\n";
        pr.Print(description);
    }

    // Source atoms come from equipment slots, never a parsed English list.
    const vector<string> melded = form->melded_equipment_names();
    if (!melded.empty())
    {
        string localized;
        for (const string &slot : melded)
        {
            if (!localized.empty())
                localized += "、";
            localized += _form_atom("form.meld.", slot, supported);
        }
        description << "\n" << zh_message("item.talisman.form.meld_line", {
            ZhArg{"items", ZhArgType::Text,
                comma_separated_line(melded.begin(), melded.end(), ", "),
                localized, supported}}).display() << "\n";
    }

    // Mutation suppression info
    vector<string> changes;
    if (form->changes_anatomy)
        changes.emplace_back("Anatomy");
    if (form->changes_substance)
        changes.emplace_back("Substance");
    if (form->has_blood == FC_FORBID)
        changes.emplace_back("Blood");
    if (form->has_bones == FC_FORBID)
        changes.emplace_back("Bones");
    if (form_type == transformation::eel_hands)
        changes.emplace_back("Hands");

    if (!changes.empty())
    {
        string localized;
        for (const string &change : changes)
        {
            if (!localized.empty())
                localized += "、";
            localized += _form_atom("form.mutation.", change, supported);
        }
        description << "\n" << zh_message("item.talisman.form.mutations_suppressed", {
            ZhArg{"mutations", ZhArgType::Text,
                comma_separated_line(changes.begin(), changes.end(), ", "),
                localized, supported}}).display() << "\n";
    }
    description << string(60, '_') << "\n";
    return description.str();
}

static string _describe_talisman_form(transformation form_type)
{
    const ZhLegacyGuard boundary("detail.form");
    string canonical;
    bool canonical_supported = true;
    {
        ZhTranslationPause english;
        canonical = _describe_talisman_form_impl(form_type, canonical_supported);
    }
    if (!zh_language_enabled())
        return canonical;
    bool supported = true;
    const string localized = _describe_talisman_form_impl(form_type, supported);
    if (supported)
        return localized;
    return zh_message("item.talisman.form_english_fallback", {
        ZhArg{"description", ZhArgType::Text, canonical, canonical, false}}).display();
}

static string _describe_talisman(const item_def &item, bool verbose)
{
    ostringstream description;

    if (verbose && !is_useless_item(item, false) && item.sub_type != TALISMAN_PROTEAN)
        description << "\n" << _describe_talisman_form(form_for_talisman(item));

    // Artefact properties.
    string art_desc = _artefact_descrip(item);
    if (!art_desc.empty())
        description << "\n" << art_desc << "\n";

    if (verbose)
    {
        string desc;
        _append_skill_needed(desc, item, false, "   ");
        description << desc;

        if (is_useless_item(item, false))
            _uselessness_desc(description, item);
        else if (item.sub_type != TALISMAN_PROTEAN)
        {
            if (crawl_state.need_save && item.is_identified())
                description << _equipment_property_change(item);
        }
    }

    return description.str();
}

/**
 * Provide auto-generated information about the given cloud type. Describe
 * opacity & related factors.
 *
 * @param cloud_type        The cloud_type in question.
 * @return e.g. "\nThis cloud is opaque; one tile will not block vision, but
 *      multiple will. \n\nClouds of this kind the player makes will vanish very
 *      quickly once outside the player's sight."
 */
string extra_cloud_info(cloud_type cloud_type)
{
    const bool opaque = is_opaque_cloud(cloud_type);
    const string opacity_info = !opaque ? "" :
        "\nThis cloud is opaque; one tile will not block vision, but "
        "multiple will.\n";
    const string vanish_info
        = make_stringf("\nClouds of this kind an adventurer makes will vanish"
                       " %s once outside their sight.\n",
                       opaque ? "quickly" : "almost instantly");
    return opacity_info + vanish_info;
}

string player_species_name()
{
    if (you_worship(GOD_BEOGH))
        return species::orc_name(you.species);
    return species::name(you.species);
}
