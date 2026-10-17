# Luna menu and dynamic-message audit (2026-10-17)

Reviewed the shipped source under `output/release/repository/native/crawl-ref/source`, focusing on `shopping.cc`, `delay.cc` / `delay.h`, and `item-use.cc`. New player-visible entries are in `localization/luna-menu-review-20261017.json`.

| Source | Runtime text / behavior | New Chinese |
|---|---|---|
| `delay.h:238-240,274-276` | `You continue %s %s.` for each equipment-delay tick; verb plus complete item name | `你继续%s %s。` |
| `shopping.cc:1577` | Shopkeeper thanks player after purchase; `%s` is shop name | `感谢你光顾%s！` |
| `shopping.cc:1579,2324` | Shopping-list access key prompt | `按“$”键可查看购物清单。` |
| `shopping.cc:2549` | Confirmation after deleting final list entry | `你的购物清单现在为空。` |
| `item-use.cc:910` | No-armour mutation blocks wearing | `你无法穿戴任何护具。` |
| `item-use.cc:913` | No-armour mutation blocks removal; `%s` is species skin name | `抱歉，你无法脱下%s。` |
| `item-use.cc:921` | Current form cannot wear/remove armour; `%s` is `wear` or `remove` | `你目前的形态无法%s任何护具。` |
| `item-use.cc:979` | Current form blocks jewellery use; arguments are action and optional form phrase | `你无法%s珠宝%s。` |

The existing systematic Luna review already includes the shop welcome/menu controls, purchase confirmation and balance prompts, plus equipment start/stop/finish lines. I did not duplicate those. It also has the generic `You continue %s %s.` translation in the shipped `zh-catalog.inc`; this audit records it because it is the repeatedly visible equipment-delay line implicated by the screenshot. No changes were made to source code, the compiled catalog, or other review files.

## Runtime regression examples

`localization/luna-menu-review-20261017.json` also contains `test_cases`, which are input/output examples for runtime expansion and regression checks, not exact catalog keys. They include the captured equipment line repeated five times, a different amulet and its completion, the screenshot shop name, pressure-plate and Zot-trap movement prompts, and purchase confirmations with changed amounts, voucher text, and Y/y casing. The Chinese expectations follow the audited complete templates above; item/shop captures remain recognizable names.

## Oracle alignment update

The runtime checks use the agreed `佩戴` wording for the amulet continuation and completion messages. Purchase examples retain their source confirmation letters (`y` / `Y`), voucher warning, and the reviewed list wording `购买（购物清单）中的物品`.

The hard-coded Utarac screenshot entry was removed. Instead, the JSON includes expanded shop-title templates derived from `shop_name()` and `shop_type_name()` in `shopping.cc:1611-1695`. Each captures the keeper name before the source ASCII apostrophe-s (`%s's`) and translates the shop type. The templates cover all `shop_type_name()` cases: Weapon, Armour, Antique Weapon, Antique Armour, Jewellery, Book, Magic Scroll, Assorted Antiques, Distillery, General Store, plus the version-34 Gadget and Removed Food cases. Types with a generated suffix include each source suffix (`Shoppe`, `Boutique`, `Emporium`, `Shop`). The existing full-name `Welcome to %s! What would you like to do?` remains available as fallback for custom map-defined type or suffix names.

This keeps the single owner capture and its order while translating the type and suffix separately. The apostrophe is source literal text in the expanded runtime pattern, not part of the `%s` capture. Regression examples include Utarac's General Store and alternate owner/type/suffix combinations.

## Additional screenshot findings: balances, sort row, and shop floor

Added complete expanded balance entries for `shopping.cc:1126-1158`, covering the four singular/plural combinations for current gold and post-purchase gold. Each entry captures both `%d` values in source order and consumes the source's `gold piece(s)` wording, so an English plural suffix cannot leak after the second amount. Regression example: `<yellow>You have 260 gold pieces. After the purchase, you will have 134 gold pieces.</yellow>` → `<yellow>你有260枚金币，购买后还会有134枚金币。</yellow>`.

Added expanded sort-row entries for the three `shopping_order_names` values (`type`, `price`, `name`) from `shopping.cc:943-950,1192`. Each retains the exact width-padding and action-description captures and keeps `[<w>/</w>]` unchanged.

Added shop-floor entrance entries matching `directn.cc:2979-2987`: `describe_floor()` combines `There is an entrance to ` + `feature_description_at(...)` + ` here.`, and for a shop the feature description returns `shop_name()` from `directn.cc:3277-3278`. Templates now split the keeper capture from `'s` and the shop type, covering the same source shop types and generated suffixes as the welcome rows; the complete-name `%s` fallback remains available for custom map-defined names. Regression example: `There is an entrance to Utarac's General Store here.` → `这里有通往Utarac的杂货店入口。`.

The Mara shop-title regression sample uses the existing glossary form `玛拉`.

## Gold branch and shop-thanks coverage

Expanded entries now cover all source-composed shop balance branches in `shopping.cc:1126-1158`: balance only (singular/plural × voucher absent/present), voucher-assisted spend (current balance and spent amount independently singular/plural), shortfall (current balance, optional voucher, and shortfall independently varied), and after-purchase balance (current and remaining amounts independently varied, with and without a voucher). Full strings retain `<yellow>` / `<lightred>` boundaries and their spaces; integer captures stay in source order. Regression cases exercise voucher-only balance, voucher spend, shortfall, singular after-purchase, and a different gold-pickup amount.

`items.cc:1745-1749` emits `You now have %d gold piece%s%s.`; the new complete runtime forms cover singular/plural balances with and without `(gained %d)`, preserving both amounts where present. `shopping.cc:1540,1577` thanks the player with the complete `shop_name()` string, so the same owner + type + generated-suffix expansion patterns were added for every built-in shop type. The existing whole-name `%s` entry remains as fallback for custom map-defined names.
