# Luna item-use and evoke review

本轮为文案迁移审校，新增及审校 `luna-item-use-messages.json`，当前共 96 条稳定 ID，覆盖 `item-use.cc` 饮药、卷轴确认/选取/结果及武器和护甲附魔/赋缀；覆盖 `evoke.cc` 魔杖使用、野兽盒/蜘蛛袋、地底迷城雕像、幻影镜、震石/凝云器、通量宝珠及其他杂项使用提示。标记和快捷键按原样保留；中文对动态字段保留语义槽位。

## 参数核对

- `operation.use.drink.confirm`: `{name}` 对应 `potion->name(DESC_DBNAME).c_str()`；`{reason}` 对应条件附加的完整神罚句，普通情况为空。神罚文本单独登记为 `operation.use.drink.penance`，便于源端拼装。
- `operation.use.drink.victory`: `{name}` 对应护甲 `item->name(DESC_THE, false, true, false).c_str()`。
- `operation.use.drink.metabolism`: `{name}` 对应 `potion->name(DESC_QUALNAME).c_str()`。
- `operation.use.drink.drunken_weapon`: `{name}` 对应 `you.weapon()->name(DESC_YOUR).c_str()`。无武器分支为固定文案 `operation.use.drink.drunken_unarmed`。
- `operation.use.weapon.brand.*`: 所有 `{name}` 对应 `_item_name(wpn)`，即 `item.name(in_inventory(item) ? DESC_YOUR : DESC_THE)`。按赋予的品牌分别给出稳定 ID；赋缀名称分支分别保留。
- `operation.use.weapon.enchant` / `.max`: `{name}` 对应修改前缓存的 `_item_name(wpn)`；模板已完整区分仍可附魔与达到上限的持续时间，不含英文时长参数。
- `operation.use.armour.enchant*`: `{name}` 对应缓存的 `_item_name(arm)`；完整消息分别编码单复数护甲名称和仍可附魔/已达到上限的持续时间，不含英文动词或时长参数。
- `operation.use.scroll.success*`: `{name}` 对应 `scroll->name(DESC_QUALNAME).c_str()`；普通/雷鸣诵读及尘化/化烟现由四条完整模板表达。
- `operation.use.scroll.identify.result`: `{old_key}` 对应 `old_slot`，`{item}` 对应 `menu_colour_item_name(item, DESC_INVENTORY_EQUIP).c_str()`。两者间箭头属于固定模板符号。无换位分支会直接输出着色物品名，属于已有物品名渲染逻辑。
- `operation.use.scroll.quantity` / `.present`: `{name}` 对应 `scroll_name` 的本地化单数名称；是否已消耗决定过去/现在完整模板，不传英文冠词或复数词尾。
- `operation.evoke.beasts.fly` / `.leap`: `{monster}` 对应 `mons->name(DESC_A).c_str()`；飞行/跳跃由完整模板表达，不传英文动词。
- `operation.evoke.mirror.clone`: `{name}` 对应 `victim->name(DESC_THE)` 的反射目标名。
- `operation.evoke.flux`: `{body_part}` 对应 `you.hand_name(false).c_str()`，复用装备消息的身体部位名称语义域。

## 共用理由及边界

饮药、读卷和唤起限制理由由 `item-name.cc` / `evoke.cc` 的 `cannot_*_item_display_reason` 提供。这里不重复造 ID：已有 `luna-consumable-display-messages.json` 覆盖 `item.reason.use.*`（包括喝药、读卷的狂暴/困惑/禁读、错误物品、药水禁用及失忆卷轴等）；既有理由引用继续沿用其稳定 ID。阅读/药水单项效果的动态原因由各效果 `can_quaff` 返回，暂不扩展到逐药水效果。

`potion.cc` 中的饮用父流程限制和共享理由属于上述既有 `item.reason.use.*`，本轮不搬迁药水具体能力效果日志。后续入口包括 `potion.cc` 的 `potion_effect::can_quaff`、各药水效果 `effect`/`apply` 实现及其 `mpr`/`mprf` 输出。药水的逐项生效、抵抗、持续时间、增益/负面结果消息不在本文件覆盖范围内。

`evoke.cc` 此次覆盖直接在魔杖/杂项 evoke 流程及其核心杂项子流程中的玩家可见固定消息和动态效果模板。Lua 报错、`dprf` 调试输出、内部数据/描述接口、已迁移的护符流程，以及 `item-use.cc` 的抄写、拾取等非饮药/读卷操作均不迁移。未识别卷轴末尾的“buggy scroll”仅为内部异常兜底，保留在边界之外；版本 34 删除物品的提示只为旧版本兼容分支，本仓当前构建配置下通常不可达，仍收录以避免翻译残留。

## 本轮补充：确认闭环与有限变体

本轮在原有 81 条上追加并修订模板，当前 JSON 共 96 条。`read()` 的已知卷轴确认句按语义条件拆为完整模板，覆盖：神罚与有/无可影响敌人、危险/有害卷轴与有/无目标、无危险提示且无目标，以及 Victory 护甲附近有怪物时的确认。每条模板都以 `{name}` 接受 `scroll->name(DESC_DBNAME)`，不把 `verb_object` 中的英文 `read the` 直接传给中文。攻击目标警告仍由共享 `stop_attack_prompt` 生成，已属共享提示逻辑，不在此重复建 ID。

`operation.use.scroll.success*` 现为普通/雷鸣诵读 × 尘化/化烟四条完整消息，`{name}` 对应 `scroll->name(DESC_QUALNAME)`。`operation.use.scroll.quantity`（已消耗）及 `.present`（仍在）根据 `scroll->quantity < prev_quantity` 选择完整的过去/现在模板，只传本地化的单数卷轴名称；不传 `article_a()` 得到的英文冠词片段，也不传英语复数词尾。

附魔提示同样改为完整分支：武器使用 `operation.use.weapon.enchant`（还可继续附魔）和 `.max`（已达上限）；护甲使用 `.enchant` / `.enchant.plural` 和 `.enchant.max` / `.enchant.plural.max`，显式覆盖 `conjugate_verb("glow", plural)` 的两种英语词形及 `moment` / `while` 持续时间，不要求集成方临时翻译形态词。中文均用自然的“泛起……光，持续片刻/一阵”。

有限动作词也改成完整消息：野兽盒用 `.beasts.fly` 或 `.beasts.leap` 表达 `airborne() ? flies : leaps`，不再传 `flies` / `leaps`。通量宝珠的 `{body_part}` 使用已有身体部位名称域，复用装备文案中 `operation.equipment.reason.need_hand` 的 `body_part` 语义（`you.hand_name(false)`），避免传英语 anatomy 字串供中文拼接。镜像复制目标 `{name}` 对应 `victim->name(DESC_THE)`。

## 明确未覆盖的真实效果入口

已补齐本任务范围中 `item-use.cc` 的饮药与读卷流程，以及 `evoke.cc` 中直接列出的魔杖/杂项使用输出；具体药水效果消息仍未覆盖。后续入口是 `potion.cc` 各效果的 `can_quaff`、`effect`/`apply` 及其 `mpr`/`mprf` 输出，包括成功、抵抗、持续时间和状态变化消息。此外，唤起效果会调用法术/传送/定身等通用流程；这些由各自 subsystem 产生的命中、抵抗、施法失败或目标提示不属于本轮 `evoke.cc` 文案清单。护符使用流程已有 typed 消息并保留原迁移；卷轴目标器调用的通用攻击警告和目标描述亦沿用已迁移的共享提示。
