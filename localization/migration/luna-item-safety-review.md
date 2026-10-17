# Luna shared item-safety and UseItemMenu review

本批新增 20 条消息，重点补齐 `nearby-danger.cc` 的警告标点闭环与 `_seen_monsters_announcement` 的完整可见/感知分支，并补上 `UseItemMenu` 的背包/地面分区标题、切换提示、地面单物品快捷提示及待传送卷轴标记。

## nearby-danger 共用安全理由

`i_feel_safe` 在安全原因后统一追加感叹号（`UNSAFE_MSG`，nearby-danger.cc:233）；新 ID `operation.safety.warning` 提供完整 `{reason}!` 警告模板。无标点原因由装备文案已有稳定 ID 提供，避免复制同一原因：

- 云雾：`operation.equipment.reason.unsafe.cloud`，`{cloud_type}` 对应 `cloud_type_name(type)`；现有可复用云名词项为 `movement.confirm.cloud_name.0` 至 `.38`。本文件的测试用例逐项复用这 39 个已审校中英名称，包括烈焰、有毒烟雾、冰冷蒸汽、毒气、各色烟雾、空间转移能量、森林火灾、蒸汽、尘埃、酸雾、雷暴等。
- 致命状态：`operation.equipment.reason.unsafe.lethal_poison`、`.lethal_contamination`、`.on_fire`、`.emergency_flight` 分别覆盖致命中毒、可能致命的魔法污染、身上着火和紧急飞行吸取。
- 附近目标：`operation.equipment.reason.unsafe.monster_one`（`{monster}` 为 `name(DESC_A)`）、`.monsters_many`（多个可见怪物）和 `.monster_sensed`（仅感知到、不可见）。装备 unsafe-delay 的父句沿用 `operation.equipment.confirm.unsafe_delay`，其 `{reason}` 引用这些完整语义原因。

`_seen_monsters_announcement` 复用于 `i_feel_safe` 和 `can_rest_here`。三个完整警告分别为单只可见怪物、多个可见怪物、只有不可见感知；复数分支按 `visible.size()>1` 表达为“附近有多只怪物！”，单数保留怪物的本地化完整名。warning channel 输出的标点也在模板中呈现。

## UseItemMenu 文案复用

`UseItemMenu` 的操作标题已在装备消息集中 typed，直接复用现有 ID：`operation.equipment.menu.{equip,equip_both,wield,wield_both,wear,wear_both,jewellery_puton,jewellery_both,drink,read,evoke,armour_takeoff,jewellery_remove,unequip}`。方向键描述帮助复用 `operation.equipment.menu.describe_selected`；Tab 装备/卸下帮助复用 `.keyhelp.equip_mode` / `.keyhelp.unequip_mode`；循环操作模式复用 `.mode_cycle`，其操作词从 `operation.equipment.value.action.*` 选择。

菜单标题区新增 `operation.safety.menu.header.inventory` / `.floor`。`operation.safety.menu.header.cycle` 对应跨背包与地面列表时的 `CMD_MENU_CYCLE_HEADERS` 提示；`.easy_floor` 对应唯一地面物品的快捷操作提示，`{action}` 复用 `operation.equipment.value.action.*`（例如 `quaff` → “喝下”、`read` → “阅读”、`evoke` → “激发”、`put on` → “戴上”）。按键参数使用 `key_markup`，保留原命令标记。已鉴定且当前正处于传送中的传送卷轴会附加 `operation.safety.menu.teleport_cancel`。

## 核对范围

固定菜单标题、操作名、Tab 帮助和模式循环帮助均已在装备消息 JSON 中有 stable IDs；本文件不重复定义。`UseItemMenu` 中仅空白 MEL_TITLE 行属于排版间距，不作可见文案迁移。`buggy` 默认标题是内部错误兜底，未作为正常玩家流程收录。未改源码；本文件通过跨文件 test_cases 检查共用安全 ID、云名、危险理由和菜单复用关系。

## 最后一轮补漏

新增短装备替换提示 `operation.safety.item_swap.candidate`：`{key}` 对应 `_item_swap_keys[i]`（`key`），`{item}` 对应 `candidates[i]->name(DESC_INVENTORY)`（`name`），保留 `<w>` 强调标记。

`InvMenu::set_title` 新增完整分页标题 Gear、Potions、Scrolls、Evocable Items，以及普通 Inventory 标题。Gear/Inventory 的 `{slots}` 采用已有 `operation.inventory.slot_description` 所给的完整 `slot_description()` 文本；分页标题保留 Left/Right/Tab 快捷键文案。对应源码为 `invent.cc:340-350`。

地面单物品检查的 `You see here {item}.` 覆盖 `item_check` 与物品识别后回显两个源位置；`{item}` 分别对应 `menu_colour_item_name(it, DESC_A)` / `item.name(DESC_A)`。堆叠摘要 `Items here: {items}.` 的 `{items}` 对应 `item_message(items)`，保留列表/颜色标记作为完整文本。`You can't pick that up.` 已复用现有 `operation.pickup.failed.stationary`，不在此文件重复定义。其它相邻地面输出（例如 `Things that are here:`、`There are many items here.`）按本轮指定范围不扩展。

信仰护身符忽略原因的完整父消息新增为 `operation.safety.faith_ignore`，`{god}` 对应 `god_speaker()` 的神名，`{reason}` 对应 `ignore_faith_reason()` 的四种已经审校的完整后缀。英文参数保留源码前导空格；中文后缀无需英文空格。测试用例覆盖戈扎格、阿申扎里、伊格尼斯和鲁四个分支。缠绕武器卸下提示新增 `operation.safety.vines_retreat`，`{item}` 对应 `msg` 中的物品名。

本文件现在有 20 条定义、72 个测试样例（包含既有共用安全理由、39 种云名、菜单复用项，以及最后一轮补齐的完整预期 `canonical` / `zh` 文本）。此前 `luna-item-use-messages.json` 的五个测试样例也补齐了完整预期文本。测试只补齐预期，没有绕过或删减既有断言。
