# Luna priority-copy batch review

Scope: fixed and semantic copy for the skill `?/K` chooser plus a source-level audit of `describe.cc`, `describe-spells.cc`, `shopping.cc`, and `skill-menu.cc`. This batch adds only `localization/migration/luna-priority-boundaries-messages.json`; it does not alter C++ or existing catalog files.

The new catalog contains four reviewed chooser messages:

| ID | Generated text and inputs | Review |
| --- | --- | --- |
| `skill.lookup.prompt` | `DescMenu::set_prompt()` fixed title, “Describe which? ” | “要查阅哪项？ ” preserves the trailing separator. |
| `skill.lookup.keyhelp` | Scrollable single-select `Menu::get_keyhelp()` row; dynamic select/page/exit key markup plus fixed labels | All key tokens remain intact; labels are translated as navigation actions. |
| `skill.lookup.keyhelp.position` | The `[<w>XXX</w>]` scrolling-position pad element | Leaves the runtime position untouched and preserves `<w>` tags. Padding remains a layout concern. |
| `skill.lookup.no_matches` | `_keylist_invalid_reason()` skill branch with `{query}` | Translates the whole sentence and retains an empty/nonempty query as data. The current skill selector enumerates all available skills and normally cannot reach this branch. |

Skill detail titles already use reviewed `skill.name.*` atoms. The dynamic armour/dodging/shields detail additions and invocation/god messages already have `detail.skill.*` IDs. The main skill-description body is still fetched from `getLongDescription(skill_name)` inside `get_skill_description()` while `ZhLegacyGuard("detail.skill.producer")` is active. That means a database row without an explicitly selected localized source can remain wholly English; no safe generic Chinese body can be authored from the enum alone. Next batch should either bind each exact database row to a stable `skill.description.*` source key or route an unsupported complete row through existing `detail.english_fallback` with its whole body, keeping the English fallback explicit. Do not translate the database key or construct a guessed paragraph from the skill name.

The exact `zh_source()` scan found no uncovered fixed literal in these four producer files. The apparent missing spell-description string is already registered in `luna-details-complete-messages.json` as `spell.no_description.fixed` and `spell.no_description.debug.fixed` under `detail.spell.fixed`; these IDs should be reused. Runtime DB strings still depend on exact context-and-literal coverage: `_monster_db_source()` and `_monster_quote_source()` intentionally return the entire source English text on a miss. That is a complete fallback, not partial translation. `_detail_table_label()` also returns the original label when it is not in its reviewed enum map; compact resistance symbols are intentionally unchanged, while a new prose label needs an explicit entry.

Other module findings:

- `describe.cc`: explicit whole-English fallback IDs already cover unknown description text, item curse/hints, item origin, monster hints, and talisman-form prose. The main uncovered generated player-facing path is skill database body selection described above. The fixed spell “no description” branches are covered by existing IDs. If a new static `zh_source` literal is added later, register the exact full literal and context; do not map an interpolated or formatted sentence as a source key.
- `describe-spells.cc`: the structured spellset rows, spell names, schools, effects, and table labels already use typed IDs/semantic-name lookups. Unsupported name atoms make the containing row fall back as a whole. `terse_spell_list()` remains an English-generation path: it concatenates `"Spells: "` with English spell titles, levels, and schools. It needs a localized prefix plus a producer that builds a localized semantic list (spell name, level, school); avoid translating the assembled English list.
- `shopping.cc`: no `zh_source()` calls remain. The shop and shopping-list UI paths found in the file use typed `shop.*` / `shopping_list.*` IDs, including prompts, errors, and fixed log text. A missing shop or item-name atom must continue to fall back as the complete canonical shop/name message; never display a translated shell around an unsupported English name.
- `skill-menu.cc`: no `zh_source()` calls remain; fixed controls/help and generated training feedback use `skill.menu.*` messages. Skill names and wizard skill details use the reviewed skill-name glossary. Any new skill label must be added as a semantic atom, not passed through legacy matching.

Chooser behavior to verify after integration: open the help index with `?`, choose `K` (skills), inspect Air/Earth/Fire/Ice Magic, Long Blades, Maces & Flails, Ranged Weapons, Short Blades, and Unarmed Combat, then select one and confirm its database entry still resolves from the original English key. Verify both a scrolling list (raw key-help plus position marker) and any empty-list branch available to the build.

Validation performed without generating C++: JSON parse, message-ID uniqueness against all existing Luna catalogs, named-placeholder parity, and style-tag parity passed. The full catalog compiler/build was intentionally not run because this batch is restricted to the two review artifacts.
