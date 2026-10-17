# Luna potion-use message review

Scope: player-facing fixed messages, full branch templates, confirmations, newly identified potion output, and fungus-spore messages in `native/crawl-ref/source/potion.cc`. This is a translation catalog proposal only; it does not change C++ or choose runtime routing. `luna-item-potion-messages.json` contains complete canonical/Chinese oracle cases for every new catalog message, including all finite spore labels.

## Reused restriction reasons

`PotionEffect::check_known_quaff()` emits `can_quaff()`'s reason as a standalone message. To avoid duplicate definitions, these use the existing typed `item.reason.drink.*` definitions in `luna-consumable-display-messages.json`:

- Curing / healing: `heal_deaths_door`, `no_ailments`, `cannot_heal_potions`, `cannot_currently_heal`, `health_full`.
- Haste / brilliance / cancellation / magic: `haste_stasis`, `chei_no_haste`, `trog_no_spellcasting`, `brilliance_active`, `nothing_to_cancel`, `no_magic_restore`, `magic_full`.
- Berserk: `already_berserk`, `berserk_recovering`, `death_door_blood_rage`, `mesmerised_rage`, `too_calm_rage`, `undead_blood_rage`, `stasis_rage`.
- Mutation: `cannot_mutate_currently`, `cannot_mutate_permanently`.

The source-level mapping is direct: each `_potion_reason("item.reason.drink.X", display)` selects that existing ID, while `_can_mutate()` chooses the two mutation IDs based on `you.can_safely_mutate(false)`. `PotionBerserk::can_quaff()` delegates to `you.can_go_berserk()`, which owns its listed drink-restriction IDs. Lignify delegates to `cant_transform_display_reason()`; its shared transformation reason catalog remains the source of those messages. The catalog intentionally does not redeclare any of these IDs.

## Branch and argument review

- `PotionMight::effect`: `were_mighty` selects complete `might.fresh` or `might.stronger` sentences; no comparative fragment is passed to Chinese.
- `PotionBrilliance::effect` and `PotionAttraction::effect`: active status selects complete first-use / stronger sentences.
- `PotionAmbrosia::effect`: `you.duration[DUR_AMBROSIA]` selects the fresh or “more invigorated” complete sentence.
- `PotionInvisibility::effect`: non-backlit first/further invisibility are separate complete templates. Backlit branch keeps `{degree}` (`"more "` or empty), possessive source (`"the"` only for the radius -1 halo, otherwise `"your"`), and the comma-separated affliction list as named `text` args. Affliction list is constructed from active halo, contamination, corona, liquid flames, quad damage, and flux-form conditions. These are explanatory dynamic lists, not a closed enum.
- `PotionMagic::effect`: `{armour}` is `body_armour()->name(DESC_THE, false, false, false)`; typed as `name`.
- `_handle_potion_fungus`: the source's finite `_spore_msg` vocabulary is represented by complete sentence IDs, not a raw English fragment: curing→治愈, healing→治疗, quickening→加速, strenghtening→强化, amplifying→增效, enlightening→启迪, invisible→隐形, magical→魔法, infuriating→激怒, bolstering→强韧. Preserve source spelling `strenghtening` in canonical data; it is an existing source typo.
- `quaff_potion`: newly identified potion argument is `potion.name(DESC_QUALNAME)` (`name`); the catalog template retains the original “It was …” construction.
- `PotionLignify::quaff`: `{cloud}` is `cloud_type_name(cloud)` (`text`) in the damaging-cloud confirmation. The prompt only occurs after the known-potion restriction check, and excludes mephitic and poison clouds.
- `PotionMutation::quaff`: three complete prompt variants cover resistance, Zin disapproval, and both together. The condition composition is in source, so callers select the exact complete template instead of appending English fragments.

## Fixed messages included

Potion-specific direct outputs covered include curing/healing failure feedback; cancellation and contamination feedback; ambrosia fallback; experience feedback; magic restoration feedback; lifeless undead berserk feedback; lignification feedback; mutation feedback; moonshine feedback; resistance feedback; alchemy extraction; and newly identified potion output. The source lines and semantic anchors are recorded alongside each message in the JSON.

## Explicit boundaries

This does not claim all potion effect prose is covered. It intentionally excludes indirect shared output emitted by `print_potion_heal_message()`, `canned_msg()`, `haste_player()`, `fly_player()`, `transform()`, `debuff_player()`, `you.go_berserk()`, god-message/conduct helpers, skill-menu/level-up flows, and monster-target effects caused by potion fungus. It also excludes potion-specific monster/player effect prose outside `potion.cc`, and internal reason/control strings not emitted to the player. These are separate producer boundaries and need their own source audit before claiming full potion-effect coverage.

## Typed invisibility children and temporary confirmation

The backlit invisibility sentence now has explicitly finite child IDs so the producer can build typed args without passing untranslated English fragments:

- `operation.potion.invisibility.degree.more` = source `"more "`; `degree.none` = empty source value.
- `operation.potion.invisibility.possessive.the` = `"the"`; `possessive.your` = `"your"`.
- `operation.potion.invisibility.affliction.*` covers exactly `halo`, `magical contamination`, `corona`, `liquid flames`, `!!!QUAD DAMAGE!!!`, and `form`. These values are composed with `zh_message_list`; the list helper preserves canonical English punctuation and uses Chinese list punctuation. For example, a full six-item list renders canonically as “halo, magical contamination, corona, liquid flames, !!!QUAD DAMAGE!!! and form” and locally as “光环、魔法污染、日冕光环、液火、!!!四倍伤害!!!及形态”.

`operation.potion.invisibility.affliction` accepts `degree`, `possessive`, and the already composed `afflictions` list as `text`. The Chinese sentence uses “来自{possessive}{afflictions}的光芒” to avoid a literal/awkward double “的” construction. Its oracle includes both two-item and complete six-item list cases, and each finite child has its own canonical/localized oracle.

`operation.potion.invisibility.confirm_temporary` represents the full `{reason} Use anyway?` prompt assembled in `PotionInvisibility::check_known_quaff()`. Its `reason` is the typed `can_quaff()` display arg from `invis_allowed`; the oracle uses the existing temporary backlit reason (“You are backlit; invisibility will do you no good right now.”). The translated suffix is attached to the complete Chinese reason with natural spacing/punctuation.
