#include "AppHdr.h"

#include "zh-display-name.h"

#include "artefact.h"
#include "branch.h"
#include "item-name.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "items.h"
#include "invent.h"
#include "mon-info.h"
#include "monster.h"
#include "place.h"
#include "skills.h"
#include "spl-util.h"
#include "stringutil.h"
#include "zh-localization.h"

#include <cstdlib>
#include <fstream>
#include <mutex>
#include <set>

namespace
{
std::string exact_component(const std::string &english)
{
    if (english.empty())
        return {};
    const std::string translated = zh_lookup_exact(english);
    return translated == english ? std::string() : translated;
}

void audit_name_fallback(const std::string &domain,
                         const std::string &canonical)
{
    if (canonical.empty())
        return;
    const char *path = std::getenv("DCSS_ZH_NAME_MISSING");
    if (!path || !*path)
        return;

    static std::mutex mutex;
    static std::set<std::string> written;
    std::string escaped;
    for (char ch : canonical)
    {
        if (ch == '\\' || ch == '\t' || ch == '\n' || ch == '\r')
            escaped += '\\';
        if (ch == '\t')
            escaped += 't';
        else if (ch == '\n')
            escaped += 'n';
        else if (ch == '\r')
            escaped += 'r';
        else
            escaped += ch;
    }
    const std::string record = domain + "\t" + escaped;
    std::lock_guard<std::mutex> lock(mutex);
    if (!written.insert(record).second)
        return;

    std::ofstream output(path, std::ios::app);
    if (output)
        output << record << '\n';
}

std::string description_prefix(description_level_type desc, bool friendly)
{
    if (desc == DESC_YOUR || (friendly && desc == DESC_THE))
        return "你的";
    return {};
}

std::string possessive_suffix()
{
    return "的";
}

std::string item_classifier(const item_def &item)
{
    switch (item.base_type)
    {
    case OBJ_MISSILES:
        switch (item.sub_type)
        {
        case MI_DART:
        case MI_BOOMERANG: return "枚";
        case MI_JAVELIN: return "支";
        case MI_STONE:
        case MI_LARGE_ROCK: return "块";
        case MI_THROWING_NET: return "张";
#if TAG_MAJOR_VERSION == 34
        case MI_NEEDLE:
        case MI_SLUG: return "枚";
        case MI_ARROW:
        case MI_BOLT: return "支";
        case MI_SLING_BULLET: return "颗";
#endif
        default: return {};
        }
    case OBJ_WANDS:    return "根";
    case OBJ_BOOKS:    return "本";
    case OBJ_MISCELLANY: return "件";
    case OBJ_STAVES:    return "根";
    case OBJ_WEAPONS:   return "把";
    case OBJ_ARMOUR:    return "件";
    case OBJ_POTIONS:   return "瓶";
    case OBJ_SCROLLS:   return "张";
    case OBJ_JEWELLERY: return "枚";
    default:            return {};
    }
}

std::string semantic_item_base(const item_def &item)
{
    switch (item.base_type)
    {
    case OBJ_WEAPONS:
    case OBJ_ARMOUR:
        // The class/subtype is visible even when a weapon or armour's
        // enchantment and ego are not identified. Avoid custom name props.
        return item_base_name(item.base_type, item.sub_type);
    case OBJ_MISSILES:
        return missile_name(static_cast<missile_type>(item.sub_type));
    case OBJ_STAVES:
        return std::string("staff of ")
               + staff_type_name(static_cast<stave_type>(item.sub_type));
    case OBJ_WANDS:
        return std::string("wand of ") + sub_type_string(item, true);
    case OBJ_MISCELLANY:
        return sub_type_string(item, true);
    case OBJ_BOOKS:
        // Manuals and parchments require independently translated skill/spell
        // names. Never look up their assembled English title.
        if (item.sub_type == BOOK_MANUAL || item.sub_type == BOOK_PARCHMENT)
            return {};
        return sub_type_string(item, true);
    case OBJ_TALISMANS:
        return talisman_type_name(item.sub_type);
    case OBJ_POTIONS:
        return std::string("potion of ") + potion_type_name(item.sub_type);
    case OBJ_SCROLLS:
        return std::string("scroll of ") + scroll_type_name(item.sub_type);
    case OBJ_JEWELLERY:
        // jewellery_effect_name is the semantic effect label; the class is
        // selected from the subtype, never inferred from item.name().
        return std::string(jewellery_is_amulet(item.sub_type) ? "amulet of "
                                                              : "ring of ")
               + jewellery_effect_name(item.sub_type, false);
    default:
        return {};
    }
}

std::string cosmetic_item_modifier(const item_def &item,
                                  description_level_type desc,
                                  bool &supported)
{
    supported = true;
    if (item.is_identified() || desc == DESC_BASENAME
        || desc == DESC_QUALNAME || desc == DESC_DBNAME)
        return {};

    const auto reviewed = [&](const char *english) {
        std::string translated = exact_component(english);
        if (translated.empty())
            supported = false;
        return translated;
    };

    const iflags_t appearance = get_equip_desc(item);
    if (item.base_type == OBJ_WEAPONS)
    {
        if (appearance == ISFLAG_RUNED)
            return reviewed("runed") + " ";
        if (appearance == ISFLAG_GLOWING)
            return reviewed("glowing") + " ";
        return {};
    }

    if (item.base_type != OBJ_ARMOUR)
        return {};

    if (appearance == ISFLAG_EMBROIDERED_SHINY)
    {
        switch (item.sub_type)
        {
        case ARM_ROBE: case ARM_CLOAK: case ARM_GLOVES: case ARM_BOOTS:
        case ARM_SCARF: case ARM_HAT:
            return reviewed("embroidered") + " ";
        case ARM_LEATHER_ARMOUR: case ARM_ANIMAL_SKIN:
            return reviewed("dyed") + " ";
        default:
            return reviewed("shiny") + " ";
        }
    }
    if (appearance == ISFLAG_RUNED)
        return reviewed("runed") + " ";
    if (appearance == ISFLAG_GLOWING)
        return reviewed("glowing") + " ";
    return {};
}

std::string translated_item_name(const item_def &item,
                                 description_level_type desc,
                                 const std::string &canonical,
                                 bool &supported)
{
    supported = true;
    const auto fallback = [&]() {
        supported = false;
        audit_name_fallback("item", canonical);
        return canonical;
    };
    // Unknown identities, artefacts and status-heavy names stay wholly
    // canonical unless every visible semantic component is covered.
    if (desc == DESC_NONE || desc == DESC_DBNAME
        || desc == DESC_BASENAME || desc == DESC_QUALNAME
        || is_artefact(item) || item.cursed() || !item.inscription.empty()
        || item.props.exists(ITEM_NAME_KEY))
        return fallback();

    // Unidentified weapon and armour base types are explicitly visible in
    // item-name.cc. Other unidentified classes can conceal their subtype.
    if (!item.is_identified() && item.base_type != OBJ_WEAPONS
        && item.base_type != OBJ_ARMOUR)
        return fallback();

    const std::string base_en = semantic_item_base(item);
    std::string base_zh = exact_component(base_en);
    // Fixed book titles are stored as lowercase database keys in the reviewed
    // glossary. Normalize only these enum-derived keys, never final names or
    // user/custom/artefact titles.
    if (base_zh.empty() && item.base_type == OBJ_BOOKS && !base_en.empty())
        base_zh = exact_component(lowercase_string(base_en));
    if (item.base_type == OBJ_BOOKS && item.sub_type == BOOK_MANUAL)
    {
        const ZhArg skill = zh_glossary_name("skill", "skill.name",
            skill_name(static_cast<skill_type>(item.plus)));
        if (!skill.supported)
            return fallback();
        base_zh = zh_message("item.book.display.manual", {skill}).localized;
    }
    else if (item.base_type == OBJ_BOOKS && item.sub_type == BOOK_PARCHMENT)
    {
        if (item.plus == 0)
            base_zh = exact_component("parchment");
        else
        {
            const ZhArg spell = zh_word_arg("spell", "spell.name.",
                spell_title(static_cast<spell_type>(item.plus)), ZhArgType::Name);
            if (!spell.supported)
                return fallback();
            base_zh = zh_message("item.book.display.parchment", {spell}).localized;
        }
    }
    if (base_zh.empty())
        return fallback();

    if (item.base_type == OBJ_WANDS && item.charges > 0)
        base_zh = zh_message("item.wand.display.charges", {
            ZhArg{"name", ZhArgType::Name, base_en, base_zh, true},
            zh_integer("charges", item.charges)}).localized;
    else if (item.base_type == OBJ_MISCELLANY)
    {
        const auto name = [&]() {
            return ZhArg{"name", ZhArgType::Name, base_en, base_zh, true};
        };
        if (item.sub_type == MISC_ZIGGURAT && you.zigs_completed > 0)
            base_zh = zh_message("item.miscellany.display.ziggurat_progress", {
                zh_integer("count", you.zigs_completed), name()}).localized;
        else if (is_xp_evoker(item) && in_inventory(item))
            base_zh = zh_message("item.miscellany.display.evoker_plus", {
                zh_integer("level", evoker_plus(item.sub_type)), name()}).localized;
        if (is_xp_evoker(item) && !evoker_charges(item.sub_type))
            base_zh = zh_message("item.miscellany.display.inert", {name()}).localized;
        else if (is_xp_evoker(item) && evoker_max_charges(item.sub_type) > 1)
            base_zh = zh_message("item.miscellany.display.charges", {
                name(), zh_integer("charges", evoker_charges(item.sub_type)),
                zh_integer("maximum", evoker_max_charges(item.sub_type))}).localized;
    }

    std::string brand_zh;
    if (item.base_type == OBJ_WEAPONS && item.is_identified())
    {
        const brand_type brand = get_weapon_brand(item);
        if (brand != SPWPN_NORMAL)
        {
            brand_zh = exact_component(weapon_brand_name(item, false));
            if (brand_zh.empty())
                return fallback();
        }
        else if (get_equip_desc(item))
        {
            brand_zh = exact_component("enchanted");
            if (brand_zh.empty())
                return fallback();
        }
    }
    else if (item.base_type == OBJ_ARMOUR && item.is_identified())
    {
        const std::string property = armour_ego_name(item, false);
        if (!property.empty())
        {
            brand_zh = exact_component(property);
            if (brand_zh.empty())
                return fallback();
        }
    }
    else if (item.base_type == OBJ_MISSILES && item.is_identified())
    {
        const std::string brand = missile_brand_name(item, MBN_NAME);
        if (brand[0] != '\0')
        {
            brand_zh = exact_component(brand);
            if (brand_zh.empty())
                return fallback();
        }
    }

    std::string result;
    if (desc == DESC_ITS)
        result = "它的";
    else
        result = description_prefix(desc, false);

    const bool inventory_name = desc == DESC_INVENTORY
                                || desc == DESC_INVENTORY_EQUIP;
    if (inventory_name && in_inventory(item))
        result = std::string(1, static_cast<char>(item.slot)) + " - ";

    bool cosmetic_supported = true;
    const std::string cosmetic = cosmetic_item_modifier(item, desc,
                                                        cosmetic_supported);
    if (!cosmetic_supported)
        return fallback();
    if (item.quantity > 1 && desc != DESC_BASENAME && desc != DESC_DBNAME
        && desc != DESC_QUALNAME)
    {
        const std::string classifier = item_classifier(item);
        if (classifier.empty())
            return fallback();
        result += std::to_string(item.quantity) + classifier;
    }

    bool show_plus = false;
    if (item.is_identified() && desc != DESC_DBNAME && desc != DESC_QUALNAME)
    {
        if (item.base_type == OBJ_WEAPONS)
            show_plus = true;
        else if (item.base_type == OBJ_ARMOUR)
            show_plus = armour_is_enchantable(item);
        else if (item.base_type == OBJ_JEWELLERY)
            show_plus = jewellery_has_pluses(item);
    }
    if (show_plus)
    {
        result += item.plus >= 0 ? "+" : "-";
        result += std::to_string(item.plus >= 0 ? item.plus : -item.plus);
    }
    result += cosmetic;
    result += base_zh;
    if (!brand_zh.empty())
        result += "（" + brand_zh + "）";

    if (desc == DESC_INVENTORY_EQUIP && in_inventory(item))
    {
        std::string state;
        const equipment_slot slot = item_equip_slot(item);
        if (slot != SLOT_UNUSED)
        {
            if (item_is_melded(item))
                state = exact_component("melded");
            else if (slot == SLOT_WEAPON && is_weapon(item))
                state = exact_component("weapon");
            else if (slot == SLOT_WEAPON_OR_OFFHAND && is_weapon(item))
                state = exact_component("offhand");
            else if (slot == SLOT_GIZMO)
                state = exact_component("installed");
            else if (slot == SLOT_HAUNTED_AUX)
                state = exact_component("haunted");
            else
                state = exact_component("worn");

            if (state.empty())
                return fallback();
        }
        else if (item.base_type == OBJ_TALISMANS && you.active_talisman() == &item)
            state = exact_component("worn");
        else if (you.quiver_action.item_is_quivered(item))
            state = exact_component("quivered");

        if (!state.empty())
            result += "（" + state + "）";
    }

    return result;
}
}

ZhArg zh_place_arg(const std::string &key, const level_id &place)
{
    const std::string canonical = prep_branch_level_name(place);
    const ZhArg branch = zh_word_arg("branch", "place.branch.",
        branches[place.branch].longname, ZhArgType::Name);
    const ZhMessage location = brdepth[place.branch] == 1
        ? zh_message("place.display.named", {branch})
        : zh_message("place.display.level",
                     {branch, zh_integer("depth", place.depth)});
    return {key, ZhArgType::Text, canonical, location.localized,
            branch.supported};
}

ZhArg zh_item_base_arg(const std::string &key, const item_def &item)
{
    const std::string canonical = item_base_name(item);
    if (item.props.exists(ITEM_NAME_KEY))
    {
        audit_name_fallback("item.base", canonical);
        return {key, ZhArgType::Name, canonical, canonical, false};
    }
    return zh_glossary_name(key, "item.base", canonical);
}

ZhArg zh_monster_type_arg(const std::string &key, monster_type type)
{
    return zh_glossary_name(key, "monster.name", mons_type_name(type, DESC_PLAIN));
}

ZhArg zh_monster_arg(const std::string &key, const monster &mon,
                     description_level_type desc)
{
    const std::string canonical = mon.name(desc);
    std::string localized = canonical;
    bool supported = true;

    if (mon.observable() && desc != DESC_DBNAME && desc != DESC_NONE)
    {
        monster_info info(&mon, MILEV_NAME);
        if (info.has_proper_name())
        {
            // A proper name is one semantic field. Preserve unknown spellings
            // exactly; translate it only when the whole name is a glossary key.
            const std::string proper = info.proper_name(DESC_PLAIN);
            const std::string proper_zh = exact_component(proper);
            if (!proper_zh.empty())
            {
                localized = proper_zh;
                if (desc == DESC_ITS)
                    localized += possessive_suffix();
            }
            else
                audit_name_fallback("proper-preserved", canonical);
        }
        else
        {
            const std::string species = mons_type_name(mon.type, DESC_PLAIN);
            const std::string species_zh = exact_component(species);
            // This equality is a semantic guard: no special form, status,
            // custom qualifier or generated name may be silently discarded.
            if (!species_zh.empty()
                && info.common_name(DESC_PLAIN) == species)
            {
                localized = description_prefix(desc, mon.friendly()) + species_zh;
                if (desc == DESC_ITS)
                    localized += possessive_suffix();
            }
            else
            {
                supported = false;
                audit_name_fallback("monster", canonical);
            }
        }
        if (localized == canonical && !info.has_proper_name())
        {
            supported = false;
            audit_name_fallback("monster", canonical);
        }
    }
    else if (desc != DESC_DBNAME && desc != DESC_NONE && !mon.observable())
    {
        supported = false;
        audit_name_fallback("visibility-preserved", canonical);
    }

    return {key, ZhArgType::Name, canonical, localized, supported};
}

ZhArg zh_monster_info_arg(const std::string &key, const monster_info &info,
                          description_level_type desc)
{
    // The snapshot contains only information the player is allowed to know.
    // Do not reconstruct a live monster, or reveal a hidden true species.
    const std::string canonical = info.full_name(desc);
    if (desc == DESC_DBNAME || desc == DESC_NONE)
        return {key, ZhArgType::Name, canonical, canonical, false};
    if (info.has_proper_name())
    {
        const std::string translated = exact_component(info.proper_name(DESC_PLAIN));
        if (translated.empty())
        {
            audit_name_fallback("proper-preserved", canonical);
            return {key, ZhArgType::Name, canonical, canonical, true};
        }
        return {key, ZhArgType::Name, canonical,
                translated + (desc == DESC_ITS ? possessive_suffix() : ""), true};
    }
    const std::string species = mons_type_name(info.type, DESC_PLAIN);
    const std::string translated = exact_component(species);
    if (!translated.empty() && info.common_name(DESC_PLAIN) == species)
    {
        std::string localized = description_prefix(desc, info.attitude == ATT_FRIENDLY) + translated;
        // Reuse the reviewed possessive suffix from the live-monster renderer.
        if (desc == DESC_ITS)
            localized += possessive_suffix();
        return {key, ZhArgType::Name, canonical, localized, true};
    }
    audit_name_fallback("monster-info", canonical);
    return {key, ZhArgType::Name, canonical, canonical, false};
}

ZhArg zh_item_arg(const std::string &key, const item_def &item,
                  description_level_type desc)
{
    const std::string canonical = item.name(desc);
    bool supported = true;
    std::string localized = translated_item_name(item, desc, canonical, supported);
    return {key, ZhArgType::Name, canonical, localized, supported};
}

ZhArg zh_actor_arg(const std::string &key, const actor *who,
                   description_level_type desc)
{
    if (!who)
        return {key, ZhArgType::Name, {}, {}};
    if (who->is_player())
    {
        const std::string canonical = who->name(desc);
        std::string localized;
        if (desc == DESC_YOUR || desc == DESC_ITS)
            localized = "你的";
        else if (key == "self" || key == "yourself")
            localized = "你自己";
        else
            localized = "你";
        return {key, ZhArgType::Name, canonical, localized, true};
    }
    if (const monster *mon = who->as_monster())
        return zh_monster_arg(key, *mon, desc);

    const std::string canonical = who->name(desc);
    audit_name_fallback("actor", canonical);
    return {key, ZhArgType::Name, canonical, canonical, false};
}

std::string zh_monster_display(const monster &mon, description_level_type desc)
{
    const ZhArg arg = zh_monster_arg("name", mon, desc);
    return zh_language_enabled() ? arg.localized : arg.canonical;
}

std::string zh_item_display(const item_def &item, description_level_type desc)
{
    const ZhArg arg = zh_item_arg("name", item, desc);
    return zh_language_enabled() ? arg.localized : arg.canonical;
}
