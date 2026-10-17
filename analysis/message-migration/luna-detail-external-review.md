# Luna external detail producers: reviewed batch

This batch covers the curse-skill detail producer, the talisman form table, and the visible search-prefix labels. It does not migrate code. `hints_describe_item()` is mapped below as a follow-up unit because its prose is a large set of interdependent branches and cannot safely be represented by a single template.

## `desc_curse_skills()` — Ashenzari curse skill details

Source: `native/crawl-ref/source/god-abil.cc`, `_ashenzari_curses` around 2136–2229 and `desc_curse_skills()` at 2229. The function selects `curse_data.name`, filters `curse_data.boosted` by `you.can_currently_train`, then constructs `category + ": " + comma_separated_fn(trainable, skill_name)`. The complete detail output is assembled in `describe.cc::_describe_item_curse` with the existing reviewed header `item.curse.skills.fixed` and list template `item.curse.skills_list`.

The new IDs in `luna-detail-external-messages.json` provide all ten source category atoms, `item.curse.skills.entry`, and `item.curse.skills.empty`. `desc_curse_skills()` can yield no skills after the `can_currently_train` filter, so use the empty template for that branch rather than rendering an empty list with a dangling colon. The empty template is an item for the existing `item.curse.skills_list` wrapper: the item itself has no terminal Chinese full stop, and the wrapper owns the final punctuation. The 34 possible skill names are already covered by the reviewed `skill.name.*` entries; use those atoms and join localized skills with `、`. If a category or skill atom is missing, the complete message should fall back to English. Do not translate the combined English category/list as a source key. Existing header/list IDs should be reused; they are not duplicated in this batch.

Categories were checked against the source map: Melee Combat (7 skills), Ranged Combat (2), Elements (4), Sorcery (2), Companions (3), Beguiling (2), Introspection (2), Fortitude (2), Cunning (2), and Devices (2). `Melee Combat` is translated as “近战”; the narrower source-level group is clear from the attached skill list. “奥术” is used for Sorcery, while the separately categorized spell schools remain their own concepts.

## `_describe_talisman_form()` — form scaling and properties table

Source: `native/crawl-ref/source/describe.cc`, `_describe_talisman_form()` at about 8130. The producer generates a four-column scaling table, optional class line, optional size and stat/resistance rows, form-specific ad hoc rows, melding information, mutation suppression, and divider lines. The JSON adds reviewed source atoms for every scaling/ad hoc row label emitted by the current function, plus structural templates for header, data row, class line, size line, melding line, and mutation-suppression line.

Reuse existing atoms rather than duplicate them: `monster.table.{ac,ev,will,class,size,regen}` and `form.table.{str,dex,...}`. Existing holiness value atoms (`monster.table_value` IDs) should be used for `holiness_description()`. Resistance labels (`rF`, `rC`, `rPois`, `rElec`, `rNeg`, `rCorr`, `rEggplant`) are compact game notation and stay unchanged. Numeric cells and existing markup such as `<red>…</red>` stay structural values; do not pass the entire rendered row back through legacy translation.

The newly added labels include the base scaling labels and every conditional label observed in `_describe_talisman_form`, `_maybe_note_armour_modifier`, `_maybe_note_form_dice`, and `_maybe_note_airstrike_damage`: `Skill`, `Min`, `Max`, `Cur`, `HP`, `UC Base Dmg`, `MP`, `Slay`, `MP Regen`, `Ensnare Chance`, `Body Armour AC`, all nine form special-dice names from `form-data.h`, `Airstrike Dmg`, `Jolt damage`, `Burstshroom damage`, `+Slay/Kill` (previously omitted), and conditional maw/blade/hive/werewolf/scroll/crab/medusa/vampire rows. `AC`, `EV`, `Regen`, `Will`, `Class`, `Size`, `Str`, and `Dex` already have reviewed source atoms.

A full pass over every non-null `special_dice_name` initializer in `form-data.h` confirms nine labels: `Breath Dmg`, `Blinkbolt Dmg`, `Quill Dmg`, `Contam Dmg`, `Frigid Wall Dmg`, `Watery Grave Dmg`, `Flare Dmg`, `Jolt damage`, and `Burstshroom damage`; all nine now have dedicated source-label IDs. The two final initializers were at lines 738 and 756 and are covered by added row oracles. A full pass over the talisman scaling and conditional producers in `_describe_talisman_form()` also confirms the label set listed above, including the werewolf `+Slay/Kill` row. Source recheck confirms `get_size_adj()` has exactly six values (`tiny`, `very small`, `small`, `medium`, `large`, `giant`); all six atoms are present. `holiness_description()` joins all set holiness bits with commas, so the class-line parameter is `text` and must be composed from the already reviewed Natural/Holy/Undead/Demonic/Nonliving/Plant atoms in bit order, then joined in Chinese. Never model it as one `name` atom or split a final English string. Its `holiness_name()` fallback is the literal `bug`; that sentinel is not safe to translate as the UI word “错误”, so an implementation should use whole-line English fallback if it occurs. Semantic atoms are also included for the equipment/mutation strings returned or assembled by `melding_description(true)` and the `changes` vector. The aggregate meld phrases (“All Equipment”, “All Weapons and Armour”) must be treated as complete semantic atoms; individual equipment slot atoms may be joined only where the helper actually returns a component list. Keep the original form/slot selection logic in C++ and do not infer structure from a final English sentence.

Formatting oracle cases cover a negative colored cell, class/holiness, size, meld aggregation, and mutation suppression. The table layout still owns spacing, padding, colors and divider placement; the templates do not prescribe terminal width.

## Item-detail tail labels

`describe.cc::get_item_description()` emits `Stash search prefixes:` before the Lua search-prefix output and `Menu/colouring prefixes:` before the optional menu prefix. The two labels are now independent fixed IDs. The following Lua/search/color tokens are deliberately not parameters to these labels and must remain untouched.

## `hints_describe_item()` — defer as one source-branch migration

Source: `native/crawl-ref/source/hints.cc`, `hints_describe_item()` at about 2057, with helpers `_hints_target_mode()`, `_hints_abilities()`, and `_hints_throw_stuff()`. The caller in `describe.cc` currently treats the generated result as a complete English fallback. This producer is too branch-heavy for safe partial phrase substitution: it builds tutorial-colored paragraphs, injects key/mouse commands, and branches on item identification, equipment state, target mode, tiles/web build, player skills/god, and item plurality. Do not add a generic “translate the finished hints string” source template.

Branch inventory for a dedicated follow-up batch:

- `OBJ_WEAPONS`: identified artefact ability/resistance text; otherwise possible empty result; unequipped wield/swap/slot-adjust advice; current-vs-best weapon skill comparison and training advice; ranged fire/target-mode instructions; melee walk-into-enemy instruction.
- `OBJ_MISSILES`: throwable-only prose; item possessive/name; fire command; inventory-slot-dependent and no-slot variants; singular/plural `this`/`these`; target-mode explanation.
- `OBJ_ARMOUR`: horns vs hard helmets; naga/armataur barding restrictions; wear/remove and mouse instructions; high-encumbrance warning for high Magic; shield/casting warning; Ranger offhand/two-handed warning; artefact identification/resistance/ability branches.
- `OBJ_WANDS`, `OBJ_SCROLLS`, `OBJ_JEWELLERY`, `OBJ_POTIONS`, `OBJ_BOOKS`, `OBJ_CORPSES`, `OBJ_STAVES`, and `OBJ_MISCELLANY`: respective evoke/read/wear/quaff/manual-vs-spellbook/corpse-use/school-boost/generic evoke guidance; several include ability/resistance or god-specific branches.
- `_hints_target_mode()`: cycle-target keys, fire/Enter/period paths, dynamic repeat command and `CMD_FIRE` vs `CMD_CAST_SPELL`; web and non-web wording differs.
- `_hints_abilities()`: base-type-dependent prerequisite wording and dynamic ability command.
- `_hints_throw_stuff()`: inventory slot, quantity, item name, and target mode, including singular/plural.

The complete hint batch should bind each branch to the source condition that selects it, keep shortcut and mouse tokens structural, and only emit a localized whole paragraph when every dynamic atom is supported. Otherwise fall back for that entire branch. Do not reverse-match the assembled `hints_describe_item()` output.

## Validation notes

The JSON contains independently reviewed English/Chinese oracle pairs for the compositional messages. The English in each entry is a literal or structure from the named producer, not a proposed reconstruction from a translated output. Existing source-key IDs noted above are intentionally referenced for reuse and not copied into this new file.
