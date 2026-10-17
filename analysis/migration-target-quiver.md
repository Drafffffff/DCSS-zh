# `target.cc` / `quiver.cc` 迁移审查

本轮只审查并建立候选目录，未改 C++。审查范围是玩家可见的瞄准失败提示，以及箭袋触发日志、菜单和确认文本。新增候选模板集中在 `localization/migration/luna-target-next-messages.json`；它们需要后续接入稳定 ID，不代表源码已迁移。

## `target.cc`

`targeter::valid_aim()` 的派生实现通过 `notify_fail()` 设定失败原因。常见、稳定全文包括：

- `targeter_beam::valid_aim`（约 269 行）：`There's something in the way.`、`You cannot see that place.`、`Out of range.`。同组阻挡/视线/射程提示在 smite、passwall、cloud、thunderbolt、cone、overgrow 等 `valid_aim` 重复出现，应该复用同一个稳定 ID。
- `targeter_reach::valid_aim`（约 967 行）及 `targeter_cleave::valid_aim`（约 1010 行）：`You can't get through.`、`Your weapon can't reach that far!`。
- `targeter_cloud::valid_aim`（约 1092 行）：`There's already a cloud there.`，另有通过 `_wallmsg(a)` 选择的动态墙体失败原因，需保留现有墙体语义来源，不能靠完整英文句反查。
- `targeter_radius::valid_aim`（约 1225 行）：`The effect is blocked.`。
- `targeter_overgrow::valid_aim`（约 1674 行）：`You cannot grow anything here.`。
- `targeter_unravelling::valid_aim`（约 801、808 行）：动态怪物名句子 `... has no magical effects to unravel.` 与 `You cannot do harm to ...`。接入时传 `zh_monster_arg` 结构化名字；若参数不受支持，整条提示回退 canonical English。
- `targeter_tempering::valid_aim`（约 2620 行）：Forgecraft 构装体的无目标、已强化、非自有目标三条提示。
- `targeter_bestial_takedown::valid_aim`（约 2806 行）：安全着陆提示及“必须指定处于恐惧状态的敌人”提示。

本文件其余许多派生 `valid_aim` 也有独立机制提示，例如挖掘、传送、灵魂束缚、重力、滚石、投射、召唤。它们未全部纳入本轮候选；实施阶段应从本审查范围向外确认调用入口与真实可见性，不应据此声称所有 targeting 文案已覆盖。`notify_fail("")` 是空状态处理，不产生可见文案。

## `quiver.cc`

- `action::quiver_description()`（约 143 行）为空箭袋产生 `Empty` / `Nothing quivered`，两者都使用 `darkgrey` 展示样式。翻译只替换文本节点，颜色标签应继续作为结构保留。
- 箭袋 action 的 `trigger()` 产生可见游戏日志。需重点迁移：资源不足时的 `You are too depleted to draw on your %s recklessly!`（参数仅为 health/magic）；拆解怪物时的 `You deconstruct %s.`；混乱攻击地形时的 `You attack %s.`；伸展攻击被友方挡住时的 `You fail to reach past %s.`；阻挡攻击时的 `... is in the way.`。参数必须来自可见 actor/地形接口或明确的不可见目标语义，不要从拼好的最终英文日志匹配。
- melee action 中已经有 `log.quiver.fixed.*` 稳定 ID（例如射程、接近失败等）。候选 JSON 不重复登记这些固定 ID。剩余 `mprf` 的动态全文尚在旧路径。
- `ActionSelectMenu::get_keyhelp()`、菜单 subtitle 与 `more_message` 包含键位、颜色标签及分类标题。可见词如 inventory、all spells、all abilities、focus mode、off/on、Spells、Abilities、无可用动作提示都要有专门展示模板或结构化参数；`<w>`/`<lightcyan>`/`<lightred>`、快捷键字母、宏键和命令键属于呈现/输入结构，不能当作普通待翻译文字。
- `set_to_quiver()`（约 2943 行）的 yes/no 确认提示为 `Really quiver %s?`，参数是 `item_def::name(DESC_INVENTORY)`。后续应使用物品显示名参数，保留 yesno 的默认拒绝行为。
- `quiver_description()` 的 spell/ability/item 完整名称来自不同 action 子类；应调用对应专名/物品/法术显示接口。不要翻译 save() 中的 action `type` / `param` 字段或从它们生成显示字符串。

## 必须保持内部英文/标识的区域

`targeter`/`aim` 状态、枚举、命令类型、目标坐标、存档键、Lua callback/参数与宏键都是控制数据，不翻译、不改值。`quiver.cc` 的 `save()`/`load()` 类型和参数、spell/ability/item enum、inscription、Lua targeting 参数同样是内部数据。只有面向玩家的文本和可见标签进入目录。动态目标名不支持时整条 canonical 回退，避免中英混排；未知专名允许保留原拼写。

## 后续接入与验证建议

1. 优先把通用 `notify_fail` 入口改为消费稳定 ID，而非在每个派生 targeter 改写同一常见提示；动态 `_wallmsg`、状态原因等按源语义拆分。
2. 用真实游戏场景覆盖：普通可见目标、不可见阻挡物、视线受阻、超距、友方阻挡、怪物名未知专名、玩家混乱攻击地形、无弹药/资源不足、捕网中不能攻击、箭袋确认取消、空箭袋及菜单键位着色。
3. 严格模式检查旧 `zh_translate`/legacy matcher 是否仍触及目标/箭袋 UI；对 Lua 控制路径另做回归，确保命令选择与保存内容逐字不变。
