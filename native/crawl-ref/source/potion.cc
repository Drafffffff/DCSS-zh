/**
 * @file
 * @brief Potion and potion-like effects.
**/

#include "AppHdr.h"
#include "zh-display-name.h"

#include "potion.h"
#include "zh-message.h"

#include <cstdio>
#include <cstring>
#include <unordered_map>

#include "act-iter.h"
#include "art-enum.h"
#include "cloud.h"
#include "english.h"
#include "god-conduct.h"
#include "god-passive.h"
#include "god-wrath.h" // reduce_xp_penance
#include "hints.h"
#include "item-name.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "item-use.h"
#include "items.h"
#include "message.h"
#include "mutation.h"
#include "nearby-danger.h"
#include "player-stats.h"
#include "potion-type.h"
#include "prompt.h"
#include "religion.h"
#include "skill-menu.h"
#include "spl-goditem.h"
#include "stringutil.h"
#include "transform.h"
#include "view.h"
#include "xom.h"

static int _scale_pot_duration(int base, bool is_potion)
{
    if (!is_potion || !you.has_mutation(MUT_EFFICIENT_METABOLISM))
        return base;
    return base * 2;
}

int _xom_factor(bool was_known);

PotionEffect::PotionEffect(const potion_type pot)
    : potion_name(potion_type_name(pot)), kind(pot)
{ }

static string _potion_reason(const char *id, ZhArg *display)
{
    const ZhArg value = zh_message_arg("reason", id);
    if (display)
        *display = value;
    return value.canonical;
}

bool PotionEffect::can_quaff(string */*reason*/, bool /*temp*/, ZhArg */*display*/) const
{
    return true;
}

bool PotionEffect::quaff(bool was_known) const
{
    if (was_known && !check_known_quaff())
        return false;

    effect();
    return true;
}

bool PotionEffect::check_known_quaff() const
{
    ZhArg reason;
    if (!can_quaff(nullptr, true, &reason))
    {
        mpr(ZhMessage{"", reason.canonical, reason.localized});
        return false;
    }
    return true;
}

class PotionCuring : public PotionEffect
{
private:
    PotionCuring() : PotionEffect(POT_CURING) { }
    DISALLOW_COPY_AND_ASSIGN(PotionCuring);
public:
    static const PotionCuring &instance()
    {
        static PotionCuring inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        // no species that can quaff at all have permanent restrictions for
        // curing
        if (!temp)
            return true;

        // cure status effects, allowed even in death's door
        if (you.duration[DUR_CONF]
                    || you.duration[DUR_POISONING])
        {
            return true;
        }
        // heal
        if (you.duration[DUR_DEATHS_DOOR])
        {
            if (reason)
                *reason = _potion_reason("item.reason.drink.heal_deaths_door", display);
            return false;
        }
        if (!you.can_potion_heal(true) || temp && you.hp == you.hp_max)
        {
            // It's not useless to drink at full health if you could hit things.
            if (you.has_mutation(MUT_DRUNKEN_BRAWLING) && has_drunken_brawl_targets())
                return true;

            if (reason)
                *reason = _potion_reason("item.reason.drink.no_ailments", display);
            return false;
        }
        return true;
    }

    bool effect(bool=true, int=40, bool is_potion = true) const override
    {
        const bool ddoor = you.duration[DUR_DEATHS_DOOR];

        if ((you.can_potion_heal() || !is_potion) && !ddoor)
        {
            const int base = 5 + random2(7);
            int amount = base;
            if (is_potion)
                amount = you.scale_potion_healing(amount);
            inc_hp(amount);
        }

        if (ddoor)
            mpr(zh_message("operation.potion.curing.queasy"));
        else if (you.can_potion_heal()
                 || !is_potion
                 || you.duration[DUR_POISONING]
                 || you.duration[DUR_CONF])
        {
            if (is_potion)
                print_potion_heal_message();
            canned_msg(MSG_GAIN_HEALTH);
        }
        else
            mpr(zh_message("operation.potion.curing.inert"));
        // need to redraw from yellow to green even if no hp was gained
        if (you.duration[DUR_POISONING])
            you.redraw_hit_points = true;
        you.duration[DUR_POISONING] = 0;
        you.duration[DUR_CONF] = 0;
        return true;
    }
};

class PotionHealWounds : public PotionEffect
{
private:
    PotionHealWounds() : PotionEffect(POT_HEAL_WOUNDS) { }
    DISALLOW_COPY_AND_ASSIGN(PotionHealWounds);
public:
    static const PotionHealWounds &instance()
    {
        static PotionHealWounds inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        // note: equip, i.e. vines, leads to temp uselessness. Should this act
        // as permauselessness?
        if (!you.can_potion_heal(temp))
        {
            if (reason)
            {
                if (!temp || !you.can_potion_heal(false))
                    *reason = _potion_reason("item.reason.drink.cannot_heal_potions", display);
                else
                    *reason = _potion_reason("item.reason.drink.cannot_currently_heal", display);
            }
            return false;
        }
        if (temp && you.duration[DUR_DEATHS_DOOR])
        {
            if (reason)
                *reason = _potion_reason("item.reason.drink.heal_deaths_door", display);
            return false;
        }
        if (temp && you.hp == you.hp_max)
        {
            // It's not useless to drink at full health if you could hit things.
            if (you.has_mutation(MUT_DRUNKEN_BRAWLING) && has_drunken_brawl_targets())
                return true;

            if (reason)
                *reason = _potion_reason("item.reason.drink.health_full", display);
            return false;
        }
        return true;
    }

    bool effect(bool=true, int=40, bool is_potion = true) const override
    {
        if (you.duration[DUR_DEATHS_DOOR])
        {
            mpr(zh_message("operation.potion.heal_wounds.queasy"));
            return false;
        }
        if (!you.can_potion_heal() && is_potion)
        {
            mpr(zh_message("operation.potion.heal_wounds.inert"));
            return false;
        }

        const int base = 10 + random2avg(28, 3);
        int amount = base;
        if (is_potion)
            amount = you.scale_potion_healing(amount);
        inc_hp(amount);
        if (is_potion)
            print_potion_heal_message();
        mpr(zh_message("operation.potion.heal_wounds.better"));
        return true;
    }
};

class PotionHaste : public PotionEffect
{
private:
    PotionHaste() : PotionEffect(POT_HASTE) { }
    DISALLOW_COPY_AND_ASSIGN(PotionHaste);
public:
    static const PotionHaste &instance()
    {
        static PotionHaste inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool /* temp */ = true, ZhArg *display = nullptr) const override
    {
        if (you.stasis())
        {
            if (reason)
                *reason = _potion_reason("item.reason.drink.haste_stasis", display);
            return false;
        }
        else if (have_passive(passive_t::no_haste))
        {
            if (reason)
                *reason = _potion_reason("item.reason.drink.chei_no_haste", display);
            return false;
        }
        return true;
    }

    bool effect(bool=true, int=0, bool is_potion = true) const override
    {
        const int dur = _scale_pot_duration(random_range(26, 40), is_potion);
        return haste_player(dur);
    }

    bool quaff(bool was_known) const override
    {
        if (was_known && !check_known_quaff())
            return false;

        effect(); // Chei prevents haste in haste_player().
        return true;
    }
};

class PotionMight : public PotionEffect
{
private:
    PotionMight() : PotionEffect(POT_MIGHT) { }
    DISALLOW_COPY_AND_ASSIGN(PotionMight);
public:
    static const PotionMight &instance()
    {
        static PotionMight inst; return inst;
    }

    bool effect(bool=true, int pow = 40, bool is_potion = true) const override
    {
        const bool were_mighty = you.duration[DUR_MIGHT] > 0;

        mpr(zh_message(were_mighty ? "operation.potion.might.stronger" : "operation.potion.might.fresh"), MSGCH_DURATION);
        const int dur = _scale_pot_duration(35 + random2(pow), is_potion);
        you.increase_duration(DUR_MIGHT, dur);
        return true;
    }
};

class PotionBrilliance : public PotionEffect
{
private:
    PotionBrilliance() : PotionEffect(POT_BRILLIANCE) { }
    DISALLOW_COPY_AND_ASSIGN(PotionBrilliance);
public:
    static const PotionBrilliance &instance()
    {
        static PotionBrilliance inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        if (you_worship(GOD_TROG))
        {
            // technically can work under Trog, but it does nothing; so give
            // an informative message instead.
            if (reason)
                *reason = _potion_reason("item.reason.drink.trog_no_spellcasting", display);
            return false;
        }
        if (temp && you.unrand_equipped(UNRAND_FOLLY))
        {
            if (reason)
                *reason = _potion_reason("item.reason.drink.brilliance_active", display);
            return false;
        }
        return true;
    }

    bool effect(bool=true, int pow = 40, bool is_potion = true) const override
    {
        const bool were_brilliant = you.duration[DUR_BRILLIANCE] > 0;

        mpr(zh_message(were_brilliant ? "operation.potion.brilliance.stronger" : "operation.potion.brilliance.fresh"), MSGCH_DURATION);
        const int dur = _scale_pot_duration(35 + random2(pow), is_potion);
        you.increase_duration(DUR_BRILLIANCE, dur);
        return true;
    }
};

class PotionAttraction : public PotionEffect
{
private:
    PotionAttraction() : PotionEffect(POT_ATTRACTION) { }
    DISALLOW_COPY_AND_ASSIGN(PotionAttraction);
public:
    static const PotionAttraction &instance()
    {
        static PotionAttraction inst; return inst;
    }

    // note on uselessness: this potion works by status, so should still be
    // allowed with no monsters in LOS. Because it is marked as dangerous,
    // it always prompts. XX maybe add info to the prompt?

    bool effect(bool=true, int pow = 40, bool is_potion = true) const override
    {
        const bool was_attractive = you.duration[DUR_ATTRACTIVE] > 0;

        mpr(zh_message(was_attractive ? "operation.potion.attraction.stronger" : "operation.potion.attraction.fresh"), MSGCH_DURATION);

        const int dur = _scale_pot_duration((20 + random2(pow)/2), is_potion);
        you.increase_duration(DUR_ATTRACTIVE, dur);
        return true;
    }
};


class PotionEnlightenment : public PotionEffect
{
private:
    PotionEnlightenment() : PotionEffect(POT_ENLIGHTENMENT) { }
    DISALLOW_COPY_AND_ASSIGN(PotionEnlightenment);
public:
    static const PotionEnlightenment &instance()
    {
        static PotionEnlightenment inst; return inst;
    }

    bool effect(bool=true, int pow = 40, bool is_potion = true) const override
    {
        fly_player(pow);
        // Try to sync up the flying and the enlightenment.
        // ...sorry about this.
        const int dur =  max(you.duration[DUR_FLIGHT],
                             max(you.duration[DUR_ENLIGHTENED],
                                _scale_pot_duration(25 + random2(pow), is_potion)));

        you.duration[DUR_ENLIGHTENED] = dur;
        return true;
    }
};

class PotionCancellation : public PotionEffect
{
private:
    PotionCancellation() : PotionEffect(POT_CANCELLATION) { }
    DISALLOW_COPY_AND_ASSIGN(PotionCancellation);
public:
    static const PotionCancellation &instance()
    {
        static PotionCancellation inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp=true, ZhArg *display = nullptr) const override
    {
        if (temp && !player_is_cancellable())
        {
            if (reason)
                *reason = _potion_reason("item.reason.drink.nothing_to_cancel", display);
            return false;
        }

        return true;
    }

    bool effect(bool=true, int=40, bool=true) const override
    {
        debuff_player(true);
        mpr(zh_message("operation.potion.cancellation.purged"));
        if (you.magic_contamination > 0)
        {
            contaminate_player(-1 * random_range(250, 1000));
            if (you.magic_contamination > 0)
                mpr(zh_message("operation.potion.cancellation.contamination_less"));
        }
        return true;
    }
};

class PotionAmbrosia : public PotionEffect
{
private:
    PotionAmbrosia() : PotionEffect(POT_AMBROSIA) { }
    DISALLOW_COPY_AND_ASSIGN(PotionAmbrosia);
public:
    static const PotionAmbrosia &instance()
    {
        static PotionAmbrosia inst; return inst;
    }

    bool effect(bool=true, int=40, bool is_potion = true) const override
    {
        const int ambrosia_turns = _scale_pot_duration(3 + random2(8), is_potion);
        if (confuse_player(ambrosia_turns, false, true))
        {
            print_potion_heal_message();
            mpr(zh_message(you.duration[DUR_AMBROSIA] ? "operation.potion.ambrosia.more" : "operation.potion.ambrosia.fresh"));
            you.increase_duration(DUR_AMBROSIA, ambrosia_turns);
            return true;
        }

        // should be unreachable: nothing blocks intentional confusion. (If
        // this ever changes, consider adding a `can_quaff`)
        mpr(zh_message("operation.potion.ambrosia.brief"));
        return false;
    }
};

class PotionInvisibility : public PotionEffect
{
private:
    PotionInvisibility() : PotionEffect(POT_INVISIBILITY) { }
    DISALLOW_COPY_AND_ASSIGN(PotionInvisibility);
public:
    static const PotionInvisibility &instance()
    {
        static PotionInvisibility inst; return inst;
    }

    bool effect(bool=true, int pow = 40, bool is_potion = true) const override
    {
        if (you.backlit())
        {
            vector<ZhArg> afflictions;
            if (you.haloed() && !you.umbraed())
                afflictions.push_back(zh_message_arg("affliction",
                    "operation.potion.invisibility.affliction.halo"));
            if (player_harmful_contamination())
                afflictions.push_back(zh_message_arg("affliction",
                    "operation.potion.invisibility.affliction.magical_contamination"));
            if (you.duration[DUR_CORONA])
                afflictions.push_back(zh_message_arg("affliction",
                    "operation.potion.invisibility.affliction.corona"));
            if (you.duration[DUR_STICKY_FLAME])
                afflictions.push_back(zh_message_arg("affliction",
                    "operation.potion.invisibility.affliction.liquid_flames"));
            if (you.duration[DUR_QUAD_DAMAGE])
                afflictions.push_back(zh_message_arg("affliction",
                    "operation.potion.invisibility.affliction.quad_damage"));
            if (you.form == transformation::flux)
                afflictions.push_back(zh_message_arg("affliction",
                    "operation.potion.invisibility.affliction.form"));
            mpr(zh_message("operation.potion.invisibility.affliction", {
                zh_word_arg("degree", "operation.potion.invisibility.degree.",
                    you.duration[DUR_INVIS] ? "more " : ""),
                zh_word_arg("possessive", "operation.potion.invisibility.possessive.",
                    you.haloed() && you.halo_radius() == -1 ? "the" : "your"),
                zh_message_list("afflictions", afflictions)}), MSGCH_DURATION);
        }
        else
        {
            mpr(zh_message(!you.duration[DUR_INVIS] ? "operation.potion.invisibility.first"
                                                      : "operation.potion.invisibility.further"), MSGCH_DURATION);
        }

        const int dur = _scale_pot_duration(15 + random2(pow), is_potion);
        you.increase_duration(DUR_INVIS, dur, 100);
        return true;
    }

    bool check_known_quaff() const override
    {
        ZhArg reason;
        // invis can be drunk while temp useless, if the player accepts at the
        // prompt
        if (!can_quaff(nullptr, false, &reason))
        {
            mpr(ZhMessage{"", reason.canonical, reason.localized});
            return false;
        }
        if (!can_quaff(nullptr, true, &reason)
             && !yesno(zh_message("operation.potion.invisibility.confirm_temporary", {reason}), false, 'n'))
        {
            canned_msg(MSG_OK);
            return false;
        }
        if (Options.show_invis_targeter && !invisibility_target_check("Confirm quaff"))
        {
            canned_msg(MSG_OK);
            return false;
        }

        return true;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        // quaffing invis
        return invis_allowed(true, reason, temp, display);
    }
};

class PotionExperience : public PotionEffect
{
private:
    PotionExperience() : PotionEffect(POT_EXPERIENCE) { }
    DISALLOW_COPY_AND_ASSIGN(PotionExperience);
public:
    static const PotionExperience &instance()
    {
        static PotionExperience inst; return inst;
    }

    bool effect(bool=true, int pow = 40, bool=true) const override
    {
        if (player_under_penance(GOD_HEPLIAKLQANA))
        {
            simple_god_message(" appreciates the memories.", false,
                               GOD_HEPLIAKLQANA);
            reduce_xp_penance(GOD_HEPLIAKLQANA,
                              750 * you.experience_level * pow / 40);
            return true;
        }

        if (you.experience_level < you.get_max_xl())
        {
            const int levels = min(you.get_max_xl(), pow / 40);
            mpr(zh_message("operation.potion.experience.level"));
            // Defer calling level_change() until later in drink() to prevent
            // SIGHUP abuse.
            adjust_level(levels, true);
        }
        else
            mpr(zh_message("operation.potion.experience.memories"));

        // these are included in default force_more_message
        const int exp = 7500 * you.experience_level * pow / 40;
        if (you.has_mutation(MUT_DISTRIBUTED_TRAINING))
        {
            you.exp_available += exp;
            train_skills();
        }
        else
            skill_menu(SKMF_EXPERIENCE, exp);

        // the player might meet training targets and need to choose
        // skills
        check_selected_skills();

        return true;
    }
};

class PotionMagic : public PotionEffect
{
private:
    PotionMagic() : PotionEffect(POT_MAGIC) { }
    DISALLOW_COPY_AND_ASSIGN(PotionMagic);
public:
    static const PotionMagic &instance()
    {
        static PotionMagic inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        if (you.has_mutation(MUT_HP_CASTING) || temp && !you.max_magic_points)
        {
            if (reason)
                *reason = _potion_reason("item.reason.drink.no_magic_restore", display);
            return false;
        }
        else if (temp && you.magic_points == you.max_magic_points)
        {
            // It's not useless to drink at full health if you could hit things.
            if (you.has_mutation(MUT_DRUNKEN_BRAWLING) && has_drunken_brawl_targets())
                return true;

            if (reason)
                *reason = _potion_reason("item.reason.drink.magic_full", display);
            return false;
        }
        return true;
    }

    bool effect(bool=true, int = 40, bool is_potion = true) const override
    {
        int amount = is_potion ? you.scale_potion_mp_healing(POT_MAGIC_MP)
                               : POT_MAGIC_MP;
        inc_mp(amount);
        if (you.has_mutation(MUT_HP_CASTING))
            mpr(zh_message("operation.potion.magic.no_effect"));
        else
        {
            if (is_potion && you.unrand_equipped(UNRAND_KRYIAS))
            {
                mpr(zh_message("operation.potion.magic.armour_enhances", {zh_item_arg("armour", *you.body_armour(), DESC_THE)}));
            }
            else if (is_potion && you.has_mutation(MUT_DOUBLE_POTION_HEAL))
                mpr(zh_message("operation.potion.magic.savour"));

            mpr(zh_message("operation.potion.magic.courses"));
        }
        return true;
    }
};

class PotionBerserk : public PotionEffect
{
private:
    PotionBerserk() : PotionEffect(POT_BERSERK_RAGE) { }
    DISALLOW_COPY_AND_ASSIGN(PotionBerserk);
public:
    static const PotionBerserk &instance()
    {
        static PotionBerserk inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        return you.can_go_berserk(true, true, true, reason, temp, display);
    }

    bool effect(bool was_known = true, int = 40, bool is_potion = true) const override
    {
        if (you.is_lifeless_undead())
        {
            mpr(zh_message("operation.potion.berserk.irritated"));
            return false;
        }

        // Duration scaling is handled in go_berserk().
        you.go_berserk(was_known, is_potion);
        return true;
    }

    bool quaff(bool was_known) const override
    {
        if (was_known
            && (!check_known_quaff() || !berserk_check_wielded_weapon()))
        {
            return false;
        }

        if (effect(was_known))
            xom_is_stimulated(50);
        return true;
    }
};

/**
 * Is the player able to mutate (temporarily or permanently) & thus unable
 * to drink a mutation-causing potion?  This is a wrapper on `you.can_safely_mutate`.
 *
 * @param reason Pointer to a string where the reason will be stored if unable
 *               to mutate
 * @returns true if the player is able to mutate right now, otherwise false.
 */
static bool _can_mutate(string *reason, bool temp, ZhArg *display)
{
    if (you.can_safely_mutate(temp))
        return true;

    if (reason)
    {
        const bool temporary = you.can_safely_mutate(false);
        const ZhArg value = zh_message_arg("reason", temporary
            ? "item.reason.drink.cannot_mutate_currently"
            : "item.reason.drink.cannot_mutate_permanently");
        *reason = value.canonical;
        if (display)
            *display = value;
    }
    return false;
}

class PotionResistance : public PotionEffect
{
private:
    PotionResistance() : PotionEffect(POT_RESISTANCE) { }
    DISALLOW_COPY_AND_ASSIGN(PotionResistance);
public:
    static const PotionResistance &instance()
    {
        static PotionResistance inst; return inst;
    }

    bool effect(bool=true, int pow = 40, bool is_potion = true) const override
    {
        mpr(zh_message("operation.potion.resistance.protected"), MSGCH_DURATION);
        const int add = _scale_pot_duration(35 + random2(pow), is_potion);;
        you.increase_duration(DUR_RESISTANCE, add);
        return true;
    }
};

class PotionLignify : public PotionEffect
{
private:
    PotionLignify() : PotionEffect(POT_LIGNIFY) { }
    DISALLOW_COPY_AND_ASSIGN(PotionLignify);
public:
    static const PotionLignify &instance()
    {
        static PotionLignify inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        const ZhArg treason = cant_transform_display_reason(transformation::tree,
                                                               false, temp);
        if (display)
            *display = treason;
        if (treason.canonical.empty())
            return true;

        if (reason)
            *reason = treason.canonical;
        return false;
    }

    bool effect(bool was_known = true, int=40, bool is_potion = true) const override
    {
        if (you.form == transformation::death) // Gozag potion petition
        {
            mpr(zh_message("operation.potion.lignify.too_dead"));
            return false;
        }
        const int dur = _scale_pot_duration(15 + random2(30) + random2(15), is_potion);
        return transform(dur, transformation::tree, !was_known);
    }

    bool quaff(bool was_known) const override
    {
        if (was_known)
        {
            if (!check_known_quaff())
                return false;

            const cloud_type cloud = cloud_type_at(you.pos());
            if (cloud_damages_over_time(cloud, false)
                // Tree form is immune to these two.
                && cloud != CLOUD_MEPHITIC && cloud != CLOUD_POISON
                && !yesno(zh_message("operation.potion.lignify.cloud_confirm",
                    {zh_word_arg("cloud", "movement.confirm.cloud_name.", cloud_type_name(cloud))}), false, 'n'))
            {
                canned_msg(MSG_OK);
                return false;
            }
        }

        if (effect(was_known))
        {
            you.transform_uncancellable = true;
            did_god_conduct(DID_CHAOS, 10, was_known);
        }
        else
            mpr(zh_message("operation.potion.lignify.woody"));
        return true;
    }
};

const int MIN_REMOVED = 2;
const int MAX_REMOVED = 3;
const int MIN_ADDED = 1;
const int MAX_ADDED = 3;

class PotionMutation : public PotionEffect
{
private:
    PotionMutation() : PotionEffect(POT_MUTATION) { }
    DISALLOW_COPY_AND_ASSIGN(PotionMutation);
public:
    static const PotionMutation &instance()
    {
        static PotionMutation inst; return inst;
    }

    bool can_quaff(string *reason = nullptr, bool temp = true, ZhArg *display = nullptr) const override
    {
        return _can_mutate(reason, temp, display);
    }

    bool effect(bool = true, int = 40, bool = true) const override
    {
        if (have_passive(passive_t::cleanse_mut_potions))
            simple_god_message(" cleanses your potion of mutation!");
        else
            mpr(zh_message("operation.potion.mutation.strange"));
        bool mutated = false;
        int remove_mutations = random_range(MIN_REMOVED, MAX_REMOVED);
        int add_mutations = random_range(MIN_ADDED, MAX_ADDED);

        // Remove mutations.
        for (int i = 0; i < remove_mutations; i++)
            mutated |= delete_mutation(RANDOM_MUTATION, "potion of mutation", false);
        if (have_passive(passive_t::cleanse_mut_potions))
            return mutated;
        // Add mutations.
        for (int i = 0; i < add_mutations; i++)
            mutated |= mutate(RANDOM_MUTATION, "potion of mutation", false);
        // Sometimes one good mutation.
        if (coinflip())
        {
            mutated |= mutate(RANDOM_GOOD_MUTATION, "potion of mutation",
                              false);
        }

        learned_something_new(HINT_YOU_MUTATED);
        return mutated;
    }


    bool quaff(bool was_known) const override
    {
        if (was_known && !check_known_quaff())
            return false;

        const bool zin_check = you_worship(GOD_ZIN)
                            && !have_passive(passive_t::cleanse_mut_potions);
        const ZhMessage msg = zh_message(you.rmut_from_item()
            ? zin_check ? "operation.potion.mutation.resistant_zin_confirm" : "operation.potion.mutation.resistant_confirm"
            : "operation.potion.mutation.zin_confirm");
        if (was_known && (zin_check || you.rmut_from_item())
                      && !yesno(msg, false, 'n'))
        {
            canned_msg(MSG_OK);
            return false;
        }

        effect();
        if (zin_check)
            did_god_conduct(DID_DELIBERATE_MUTATING, 15, was_known);
        return true;
    }
};

class PotionMoonshine : public PotionEffect
{
private:
    PotionMoonshine() : PotionEffect(POT_MOONSHINE) { }
    DISALLOW_COPY_AND_ASSIGN(PotionMoonshine);
public:
    static const PotionMoonshine &instance()
    {
        static PotionMoonshine inst; return inst;
    }

    bool effect(bool=true, int=40, bool is_potion = true) const override
    {
        mpr(zh_message("operation.potion.moonshine.tipsy"));
        const int dur = _scale_pot_duration(random_range(10, 25), is_potion);
        you.increase_duration(DUR_VERTIGO, dur, 50);
        return true;
    }

    bool quaff(bool was_known) const override
    {
        if (effect())
            xom_is_stimulated( 50 / _xom_factor(was_known));
        return true;
    }
};

static const unordered_map<potion_type, const PotionEffect*, std::hash<int>> potion_effects = {
    { POT_CURING, &PotionCuring::instance(), },
    { POT_HEAL_WOUNDS, &PotionHealWounds::instance(), },
    { POT_HASTE, &PotionHaste::instance(), },
    { POT_MIGHT, &PotionMight::instance(), },
    { POT_BRILLIANCE, &PotionBrilliance::instance(), },
    { POT_ATTRACTION, &PotionAttraction::instance(), },
    { POT_ENLIGHTENMENT, &PotionEnlightenment::instance(), },
    { POT_CANCELLATION, &PotionCancellation::instance(), },
    { POT_AMBROSIA, &PotionAmbrosia::instance(), },
    { POT_INVISIBILITY, &PotionInvisibility::instance(), },
    { POT_MOONSHINE, &PotionMoonshine::instance(), },
    { POT_EXPERIENCE, &PotionExperience::instance(), },
    { POT_MAGIC, &PotionMagic::instance(), },
    { POT_BERSERK_RAGE, &PotionBerserk::instance(), },
    { POT_MUTATION, &PotionMutation::instance(), },
    { POT_RESISTANCE, &PotionResistance::instance(), },
    { POT_LIGNIFY, &PotionLignify::instance(), },
};

const PotionEffect* get_potion_effect(potion_type pot)
{
    switch (pot)
    {
    default:
        return potion_effects.at(pot);
    CASE_REMOVED_POTIONS(pot);
    }
}

static const map<potion_type, string> _spore_msg =
{
    { POT_CURING, "curing" },
    { POT_HEAL_WOUNDS, "healing" },
    { POT_HASTE, "quickening", },
    { POT_MIGHT, "strenghtening", },
    { POT_BRILLIANCE, "amplifying" },
    { POT_ENLIGHTENMENT, "enlightening" },
    { POT_INVISIBILITY, "invisible" },
    { POT_MAGIC, "magical" },
    { POT_BERSERK_RAGE, "infuriating" },
    { POT_RESISTANCE, "bolstering" },
};

static void _handle_potion_fungus(potion_type potion)
{
    // Baseline chance not to trigger.
    if (!one_chance_in(3))
        return;

    // Now check if there are any monsters in sight which could benefit from
    // this potion.
    vector<monster*> targs;
    for (monster_near_iterator mi(you.pos()); mi; ++mi)
        if (mons_benefits_from_potion(**mi, potion))
            targs.push_back(*mi);

    // Don't print a message if nothing will happen.
    if (targs.empty())
        return;

    draw_ring_animation(you.pos(), you.current_vision, WHITE, CYAN, true, 10);

    // Affect a percentage of nearby targets, but always at least one.
    shuffle_array(targs);
    int num_affected = min((int)targs.size(), random_range(targs.size() * 4 / 10 + 1,
                                                           targs.size() * 9 / 10 + 1));


    mpr(zh_message("operation.potion.fungus.spores." + _spore_msg.at(potion)));


    for (int i = 0; i < num_affected; ++i)
        mons_potion_effect(*targs[i], potion, you);
}

/**
 * Quaff a potion, identifying it if appropriate & triggering its effects on
 * the player. Does not handle decrementing item quantities.
 *
 * @param potion    The potion (stack) being quaffed.
 * @param force     Whether to consume the potion even if it is known to be useless.
 * @return          true if the potion was used; false if the player aborted.
 */
bool quaff_potion(item_def &potion, bool force)
{
    const bool was_known = item_type_known(potion);

    if (!was_known)
    {
        identify_item(potion);
        mpr(zh_message("operation.potion.unknown_identified", {zh_item_quantity_arg("potion", potion, 1, DESC_A)}));
    }

    const potion_type ptyp = static_cast<potion_type>(potion.sub_type);
    if (get_potion_effect(ptyp)->quaff(was_known && !force))
    {
        if (you.wearing(OBJ_JEWELLERY, AMU_CHEMISTRY, false, true)
            && you.magic_points < you.max_magic_points)
        {
            mpr(zh_message("operation.potion.alchemy.extract"));
            inc_mp(random_range(5, 9));
        }

        if (you.has_mutation(MUT_POTION_FUNGUS))
            _handle_potion_fungus(ptyp);

        return true;
    }

    return false;
}

/**
 * Trigger an effect on the player corresponding to the given potion type.
 *
 * @param effect        The type of potion in question.
 * @param pow           The power of the effect. (Only relevant for some pots.)
 * @param was_known     Whether the player should be held responsible.
 */
void potionlike_effect(potion_type effect, int pow, bool was_known)
{
    get_potion_effect(effect)->effect(was_known, pow, false);
}

int _xom_factor(bool was_known)
{
    // Knowingly drinking bad potions is much less amusing.
    int xom_factor = 1;
    if (was_known)
    {
        xom_factor *= 2;
        if (!player_in_a_dangerous_place())
            xom_factor *= 3;
    }
    return xom_factor;
}

// Returns true if a given monster could currently gain some benefit from a
// given potion effect. (Among those implemented for monsters).
bool mons_benefits_from_potion(const monster& mon, potion_type potion)
{
    switch (potion)
    {
        case POT_HASTE:
            return !mon.has_ench(ENCH_HASTE) && !mon.stasis();

        case POT_MIGHT:
            return !mon.has_ench(ENCH_MIGHT) && mons_has_attacks(mon);

        case POT_BRILLIANCE:
            return !mon.has_ench(ENCH_EMPOWERED_SPELLS) && mon.antimagic_susceptible();

        case POT_HEAL_WOUNDS:
            return mon.hit_points < mon.max_hit_points;

        case POT_CURING:
            return mon.hit_points < mon.max_hit_points
                    || mon.has_ench(ENCH_POISON)
                    || mon.has_ench(ENCH_CONFUSION);

        case POT_ENLIGHTENMENT:
            return !mon.has_ench(ENCH_FLIGHT) || !mon.has_ench(ENCH_STRONG_WILLED);

        case POT_INVISIBILITY:
            return !mon.has_ench(ENCH_INVIS) && !mon.backlit();

        case POT_MAGIC:
            return mon.has_ench(ENCH_ANTIMAGIC);

        case POT_BERSERK_RAGE:
            return !mon.has_ench(ENCH_BERSERK) && mon.can_go_berserk();

        case POT_RESISTANCE:
            return !mon.has_ench(ENCH_RESISTANCE);

        default:
            return false;
    }
}

void mons_potion_effect(monster& mon, potion_type potion, const actor& source)
{
    switch (potion)
    {
        case POT_HASTE:
            enchant_actor_with_flavour(&mon, &source, BEAM_HASTE);
            break;

        case POT_MIGHT:
            enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
            break;

        case POT_BRILLIANCE:
            simple_monster_message(mon, " magic is enhanced!", true);
            mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
            break;

        case POT_HEAL_WOUNDS:
            simple_monster_message(mon, " is healed!");
            mon.heal(random_range(30, 50));
            break;

        case POT_CURING:
            simple_monster_message(mon, " is healed!");
            mon.heal(random_range(10, 20));
            mon.del_ench(ENCH_POISON);
            mon.del_ench(ENCH_CONFUSION);
            break;

        case POT_ENLIGHTENMENT:
        {
            simple_monster_message(mon, " is enlightened!");
            const int dur = random_range(300, 450);
            mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
            mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
        }
            break;

        case POT_INVISIBILITY:
            enchant_actor_with_flavour(&mon, &source, BEAM_INVISIBILITY);
            break;

        case POT_MAGIC:
            mon.del_ench(ENCH_ANTIMAGIC);
            break;

        case POT_BERSERK_RAGE:
            mon.go_berserk(false);
            break;

        case POT_RESISTANCE:
            enchant_actor_with_flavour(&mon, &source, BEAM_RESISTANCE);
            break;

        default:
            break;
    }
}
