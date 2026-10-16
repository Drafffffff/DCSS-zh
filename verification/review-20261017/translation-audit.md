# Native Chinese translation audit — 2026-10-17

Reviewed all nine screenshots. This audit covers C++-generated combat, equipment, status and level text. Tutorial prose and static monster/item descriptions are being handled in a separate data review.

## C++ findings

- Monster examine panes reveal English leftovers in the generated notice chance and hit estimate. The chance sentence is assembled in `describe.cc::_monster_notice_chance`; hit estimates combine `describe_to_hit` and `describe_hit_chance`. The JSON supplies complete dynamic templates so Chinese word order can be controlled as a whole.
- Item detail text combines runtime numbers and prose. `describe.cc::_skill_target_desc` composes training percentage, target skill rank and an XL experience estimate. Chinese uses `级` for skill rank and “角色等级的经验” for XL; neither means dungeon floor. `At 100% training` contains a literal percent sign, while `%d%%` is used only in dynamic training percentages.
- The phrase `Welcome back to level %d!` in `player.cc:3011` means character experience level was restored after reaching a prior threshold, not returning to a dungeon floor. Character levels and skill ranks use `级`; dungeon locations use `层`.
- HUD labels need concise, consistent values: `Health/HP` → `生命：`, `Magic/MP` → `魔力：`, `Noise` → `噪声：`, ranged action `Fire` → `射击：`, `AC` → `护甲：`, `EV` → `闪避：`, and `SH` → `格挡：`.

## Integration interface

`DCSS/tools/native_catalog.py` generates `zh_entries` and `zh_terms` in `native/crawl-ref/source/zh-catalog.inc`. C++ lookup checks exact strings, tagged entries, complete printf patterns, lines, fragments, then terms. Duplicate exact strings use the first insertion, so the integration layer must explicitly let these reviewed overrides take precedence. Glossary entries are guidance unless integrated into `zh_terms` with deliberate ordering.

`DCSS/localization/luna-review-20261017.json` contains `entries` as `{en, zh, context, reason}` and a glossary as `{en, zh}`. Dynamic templates in this file use source-backed or source-composed wording and preserve printf tokens in source order. A separate data review is responsible for `data_entries` from `dat/descript/tutorial.txt` and the monster/item description data files.

## Additional source-backed templates

The supplemental JSON now also covers `throw.cc` player firing output, both `ranged-attack.cc` projectile-hit messages, `mon-death.cc` kill output, `items.cc::item_check` ground-item lines, the item-origin sentence assembled with `prep_branch_level_name`, the shortbow `Your skill` line built by `describe.cc::_your_skill_desc`, directn/throw target prompts, and the complete stair description assembled in `describe.cc`. The stair template keeps its argument order as feature name, traversal key, examine key, destination key. The `At 100% training` template keeps the literal percent sign in its Chinese translation.
