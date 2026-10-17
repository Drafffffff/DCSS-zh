#include "AppHdr.h"

#include "zh-display-name.h"

#include "artefact.h"
#include "item-name.h"
#include "item-prop.h"
#include "items.h"
#include "mon-info.h"
#include "monster.h"
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

std::string item_classifier(object_class_type type)
{
    switch (type)
    {
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
        return item_base_name(item);
    case OBJ_MISSILES:
        return missile_name(static_cast<missile_type>(item.sub_type));
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
    if (desc == DESC_NONE || desc == DESC_DBNAME || desc == DESC_ITS
        || desc == DESC_INVENTORY || desc == DESC_INVENTORY_EQUIP
        || desc == DESC_BASENAME || desc == DESC_QUALNAME
        || !item.is_identified()
        || is_artefact(item) || item.cursed() || !item.inscription.empty())
        return fallback();

    const std::string base_en = semantic_item_base(item);
    std::string base_zh = exact_component(base_en);
    if (base_zh.empty())
        return fallback();

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

    std::string result = description_prefix(desc, false);
    if (item.quantity > 1 && desc != DESC_BASENAME && desc != DESC_DBNAME
        && desc != DESC_QUALNAME)
    {
        const std::string classifier = item_classifier(item.base_type);
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
    if (!brand_zh.empty())
    {
        if (item.base_type == OBJ_ARMOUR)
            result += base_zh + "（" + brand_zh + "）";
        else
            result += brand_zh + base_zh;
    }
    else
        result += base_zh;

    return result;
}
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
                    localized += "的";
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
                    localized += "的";
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
