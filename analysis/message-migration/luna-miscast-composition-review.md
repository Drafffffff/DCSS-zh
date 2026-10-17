# Miscast composition review

Reviewed `_miscast_damage_string` and `_player_spell_desc` against `describe.cc`.

- The active catalog owns the 11 flavor/effect atoms and the damage clause formerly staged in `pending/luna-spell-reasons-messages.json`; it intentionally omits the obsolete `spell.miscast.joined_clause` placeholder.
- Flavor lists preserve the source map order, use comma separators between non-final values, and use `or` for the final value. Effect lists preserve the special-effect order followed by damage, use semicolons between non-final values, and use `or` for the final value.
- Single and multiple consequence parent messages are complete. The multiple parent owns `either`; the list parameter does not duplicate it. `spell.miscast.damage_clause` owns the complete damage phrase and its flavor list.
- Oracle cases cover two- and three-item flavor lists, effect punctuation, and the complete single/multiple parent sentences.
- `spell.stats.range.not_applicable` localizes the fixed `N/A` range value as `不适用`, so a spell with no applicable range does not send English `N/A` through a generic text parameter.

No C++ source was changed in this review.
