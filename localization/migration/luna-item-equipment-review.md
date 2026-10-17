# 装备操作文案审校

本批覆盖入口菜单、穿脱/持用限制、装备槽可用性原因、候选替换菜单、危险确认、取消入口和即时卸下日志。稳定 ID 均使用 `operation.equipment.*`。`source.file` 指向当前源码，anchor 标明产生该字符串的 C++ 表达式/分支。

## C++ 表达式到参数映射

- `item-use.cc::_default_use_title`: `Options.equip_unequip` 的两分支分别使用 `menu.equip_both/equip`、`menu.wield_both/wield`、`menu.wear_both/wear`、`menu.jewellery_both/jewellery_puton`；固定的护甲脱下、首饰取下、通用卸下标题分别为 `menu.armour_takeoff/jewellery_remove/unequip`。`-` 表示空手，快捷键文字保留。
- `_can_generically_use_armour`: `species::skin_name(you.species)` → `skin:name`；`wear ? "wear" : "remove"` → `action:text`。完整句式包住理由，不把英语动词片段单独当作中文拼接。
- `_can_generically_use(OPER_PUTON/OPER_REMOVE)`: `oper == OPER_PUTON ? "wear" : "remove"` → `action:text`；突变决定后缀空串或 `" in your present form"` → `form_note:text`，保留空串分支。
- `try_equip_item` 与 `_move_item_from_floor_to_inv`: 固定的背包容量拒绝统一对应 `reason.inventory_full`；该文案也与既有 `talisman.reason.cannot_carry` 同义，供调用者复用，不要求旧 ID 改名。
- `can_equip_item`: 格槽原因的完整返回句直接固定 ID；`fit_armour_size` 的 `(bad_size > 0) ? "large" : "small"` → `size_relation:text`；头盔的体型分支复用 `helmet_size`；武器过大分支已单列 `reason.weapon_size`。
- `get_player_equip_slot_count`: `you.hand_name(false)` → `body_part:name`；`hand_name(true)`/`foot_name(true)` → `body_part:name`；四肢尺寸分支实际传入 `"too big"/"too small"` → `size_relation:text`；值词项只译为“大/小”，父模板保留“太”；龙人翅膀可选说明片段 → `wing_note:text`，允许空串。各首饰、变形和部位限制均有独立固定 ID。
- `find_removable_items_for_slot`: `cursed_item->name(DESC_YOUR)` → `item:name`；只在安静关闭且没有任何可替换候选、至少发现一件诅咒物品时打印。与主动尝试脱下诅咒物品共用 `reason.cursed` 的完整模板语义。
- `prompt_inscribe_item`: 固定标题 `Inscribe which item?` → `operation.equipment.menu.inscribe_item`（无参数，中文“要给哪件物品刻写？”）；`prompt_invent_item` 随后套用既有 `operation.inventory.selection.prompt`，完整显示 oracle 为 `Inscribe which item? (<w>?</w> for menu, <w>Esc</w> to quit)`，快捷键/颜色标记不变。
- `_item_swap_menu/_item_swap_prompt`: 两处相同标题共用 `prompt.swap_list`。`?`、`Esc`、`<`、`>`、`^`、数字候选键及颜色 markup 均保持原值；`prompt.swap_keys` 只翻译提示词，不改按键。
- `warn_about_changing_gear`: `to_equip->name(DESC_INVENTORY)` → `item:name`；`i_feel_safe(...,&reason)` 的完整理由 → `reason:text`；危险地形条件表达式产出 `outcome:text`（仅 `drown` 或 `burn`），物品名来自 `item->name(DESC_YOUR)` → `item:name`。警告刻写、取下警告由既有 `operation.inventory.warning.*` 完整模板及尾句/前缀值 ID 提供；本文件不重复声明装备域副本。
- `can_unequip_item`: melded/cursed 两个 `%s` 都映射 `item.name(DESC_YOUR)` → `item:name`；血斧与虚荣王冠理由为固定完整句。
- `do_equipment_change`: `item_unequip_verb(*item)` → `action:text`，`item->name(DESC_YOUR)` → `item:name`。中文使用完整模板“你把{item}{action}”，因此物品名自带的“你的/一把/一件”等呈现语义保持在独立名称参数中，中文动词置于其后。

## 有限参数值 ID

本文件为所有可枚举的动态文本参数提供了 `operation.equipment.value.*` 无参数词项：操作动词（含 `equip/unequip/wear/remove/unwield/take off/put on` 及相邻菜单操作）、空值、装备销毁/神罚/即将传送尾句、形体说明、尺寸、危险结果、神器品牌失效短语、再生装备状态与代词、动作步态、神性修饰语、单复数英语词尾、regen_attune 实际输入 `" as they attune themselves"`/`"s as it attunes itself"`（中文值为空并由整句模板承载），以及 `tingle/tingles/pass/passes` 动词。调用端用这些固定词项映射到父模板参数，不从原始英文拼接。`hands_act("tingle", "!")`、穿透武器手部动词由 hand_name/conjugate_verb 映射成 `hands/verb` 参数，`verb` 分别选既有无参 tingle/tingles ID。`i_feel_safe` 的 reason 除云类型/单个可见怪物名外也有独立完整原因 ID；云类型来自 `cloud_type_name` 本地化文本，怪物名来自 `name(DESC_A)`。

装备危险原因 canonical 与中文值见 `operation.equipment.reason.unsafe.*`，云毒/致命毒/濒死魔法污染/着火/紧急飞行消耗/附近怪物/奇怪动静均已独立定义；单个怪物原因是完整模板并带 `monster:name`。

## 已有文案与接续入口

`EquipOnDelay::try_interrupt`、`EquipOffDelay::try_interrupt` 的三种完整确认句已增加 ID；狂暴/空手的 MSG_TOO_BERSERK、MSG_EMPTY_HANDED_* 及 Tab 装备模式、描述选中物品和循环模式帮助也有独立 ID；装备后 `DESC_INVENTORY_EQUIP` 成功物品行使用 `operation.equipment.log.equipped_item`，其 `item` 参数类型为 `name`，对应物品显示名称接口。`equip_start`、`equip_continue`、`equip_finish`、`equip.stop` 及 `equip.action.*`、`equip.slot.*` 已在 `luna-priority-messages.json` 中有 typed 定义；`EquipOnDelay`/`EquipOffDelay` 的开始、逐回合、结束和中断继续复用这些 ID，不复制或更名。护符原因/确认/变形文案保留在 `luna-talisman-flow-messages.json`；本批不重复迁移 talisman 专属分支。

`item-prop.cc::is_equippable_item` 只做布尔判定并返回，没有新的玩家可见提示。装备槽最终拒绝文字实际从 `player-equip.cc::get_player_equip_slot_count`、`can_equip_item` 和 `find_removable_items_for_slot` 返回，已作为此批来源处理。

## 困难入口与边界

- 双持/副手、Coglin 的 weapon-or-offhand 灵活槽、八爪鱼戒指槽、护符额外槽及神器增槽都经 `get_player_equip_slot_count` 与替换候选菜单流转；不根据槽位推断新的文案。
- 候选列表可能有 1 件、多件相同物品或混合物品；模板仅包住标题和按键帮助，物品显示由物品名格式化层负责。
- 装备延迟提示按目标装备使用现有 `equip.*`，瞬时卸下才走新增 `operation.equipment.log.unequip`。延迟被取消时使用已存在的 `equip.stop`。
- `MSG_TOO_BERSERK`、`MSG_EMPTY_HANDED_ALREADY` 等 `canned_msg` 由集中式固定消息目录处理；本次不复制该公共消息定义。
- `item-use.cc` 1–1830 中无关的饮用、阅读、激活、拾取、刻写等内容不属于装备操作入口；对应分支未纳入本批。程序诊断、Lua 语音数据及内部枚举/ID 不翻译。
