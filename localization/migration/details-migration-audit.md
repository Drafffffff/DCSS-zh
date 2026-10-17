# Luna detail-message migration audit

`luna-detail-messages.json` uses the single-layer `{name}` slot protocol and identifies `gpt-6-luna` as the translation model. Parameter types are limited to `text`, `name`, `integer`, `number`, `key`, and `colour`. Translate each complete display template first, then substitute current semantic values. Preserve literal percent signs, spaces and newlines that affect layout, shortcut keys, and color markup such as `<green>`, `<magenta>`, `<darkgrey>`, and `<w>`.

The catalog reuses wording already reviewed by Luna in `luna-review-20261017.json` and `luna-targeting-review-20261017.json` where source forms overlap. Its 38 entries cover item and monster details, skill notices and menu fields, targeting, feature instructions, mutations, and spell details.

## Source formats and argument order

Every message records a source file and function/format anchor. Where the source builds a displayed sentence from separate C++ pieces, the anchor identifies the complete composition and the message is explicitly described as normalized.

- `item.weapon.base_stats`: `hit_bonus` then `damage` (`%+d`, `%d`). `item.weapon.attack_delay_and_minimum`: `base_delay` (`%.1f`), `minimum_delay` (`%.1f`), then `skill_level` (`%d`). The source call is one complete two-line template with a newline between sentences.
- `item.weapon.armour_slow`: the body-armour name or `Your heavy armour` supplies `actor`; the numeric branch then supplies `delay` (`%.1f`).
- `item.projectile.stats_and_minimum_delay`: `damage` (`%d`), `base_delay` (`%.1f`), `minimum_delay` (`%.1f`), then `skill_level` (`%d`). The source call starts with two newlines and has a newline between the stat line and sentence. `item.projectile.destroy_chance` takes the denominator `chance` (`%d`) and also starts with two newlines.
- `item.potion.ac` takes one integer. Jewelry preview rows take one signed `amount` and start with two newlines. `item.stash.location` takes the rendered `loc.describe(true, true)` text as `depth`; the source string ends with two newlines.
- `skill.gain.single`: optional prefix, skill name, increases/decreases verb, resulting level. `skill.gain.multiple`: optional prefix, skill name, gained/lost verb, level delta, resulting level.
- `skill.target.training_complete` is assembled from two format calls. Slots are training percentage; optional `would ` verb; target skill level (source `%d.%d`); XP comparison (`about` or `the equivalent of`); and XP level equivalent (source `%d.%d`). Map the comparison to `约` or `相当于` before substitution. Split each semantic decimal into integer/fraction arguments only if the existing formatter still requires printf arguments.
- Skill enhanced/reduced hints take one causes-list string, with literal color tags. The target prompt takes a skill name. Training/progress cells display one integer percent each; the source `%%` means a literal percent sign.
- Monster notice and hit templates each take one integer percentage. `monster.will_chance` takes integer chance followed by the wizard suffix string.
- `target.hit_chance` rows are complete short stream forms from `describe.cc::describe_hit_chance`. The verbose rows preserve the source order: hit percentage, weapon name, and (for the blinded form) distance. The action prompt takes one configured key; the cycle prompt takes action, backward, then forward key. The help key `?` is a literal.
- `feature.abyss_depth` takes one integer. `feature.enter_key` takes destination then key. Mutation rank takes current then maximum rank. Spell level takes one integer; spell failure takes failure then reference percentages. The spell range row represents its label followed by rendered range text.

The two multiline weapon/projectile templates preserve the actual `make_stringf` boundaries and are complete templates rather than fragments. The projectiles' leading newlines and stash/jewelry trailing or leading spacing are retained from their source composition.
