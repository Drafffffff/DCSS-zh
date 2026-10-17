# 消耗品可用性与名称显示文案审校

本批由 Luna 审校，消息目录为 `localization/migration/luna-consumable-display-messages.json`（`model: gpt-6-luna`）。目录现含 88 条新消息、17 条独立 oracle。没有复制既有的 `item.useless.*` 外壳、`item.evoker.charges`、`item.wand.damage`、`item.wand.noise`、`item.consumable.rarity` 或 `spell.noise.*` 等词条。

## 真实调用与集成范围

详情可用性由 `describe.cc::_uselessness_desc()` → `_cannot_use_reason()` 调用三类定义：卷轴 `item-name.cc::cannot_read_item_reason()`、药水 `item-name.cc::cannot_drink_item_reason()`、魔杖/杂项 `evoke.cc::cannot_evoke_item_reason()`。饮用原因还会调用 `potion.cc` 中 `PotionEffect::can_quaff()` 的具体实现。函数返回的英文原因目前传入既有 `item.useless.*` 模板。详情接入时应让原状态/可用性判断维持单一来源，在返回原因的生产分支选稳定 ID，再通过已有外壳显示；不可拿整句结果反向匹配。

`_uselessness_desc()` 的外壳已经覆盖永久无用、阅读无法/无效、饮用无法/无效、唤起无法、通用当前无用等状态，继续复用对应 `item.useless.*`。本批只提供完整固定原因和必要的命名参数模板。

## 可直接绑定的固定原因

- `cannot_read_item_reason()` 和 `_general_cannot_read_reason()`：Gehenna 烟尘、狂暴、困惑、禁止阅读卷轴、拒绝依赖卷轴、失去法术记忆控制、Trog 禁记法术、无法使用武器/护甲导致强化无用、没有待鉴定物品、identify 被动、禁止召唤、非卷轴、没有可遗忘法术、静风与无法绘图等固定分支均有完整模板。
- `cannot_drink_item_reason()`：不能饮用、当前状态不允许、拒绝药水、Cocytus 严寒、非药水等固定原因已覆盖。
- `cannot_evoke_item_reason()`：狂暴/困惑、无法唤起魔法物品、物品已移除、非可唤起物品、旧版本空魔杖、盟友限制、静风、Geryon号角沉默、XP 唤能器耗尽（带物品名参数）等已有模板。注意 `no_charges` 只对应 `TAG_MAJOR_VERSION == 34` 的旧版分支。
- `potion.cc`：治疗/治疗伤口药水的死亡之门、无病痛、无法/暂时无法恢复、生命已满；急速药水的静滞/Chei 限制；灵光药水的 Trog/既有 Folly 效果；取消药水无可取消效果；魔力药水无可恢复魔力/魔力已满；变异药水的当前限制与永久限制分别使用完整模板。
- `player-act.cc::player::can_go_berserk()`：狂暴中、狂暴恢复期、死亡之门、魅惑、Clarity、无生气亡灵、静滞等完整理由已覆盖。
- `_no_items_reason()` 使用的四个选择器——无未鉴定物、无可继续附魔护甲、无可附魔武器、无可赋予词缀武器——有 `invent.cc::no_selectables_message()` 的独立候选。相同“无法启动魔法物品”文案由 `item.reason.use.no_artifice` 共用，来源锚点同时指向唤起理由和 `OSEL_EVOKABLE`。
- `transform.cc::cant_transform_reason()` 五类固定状态，以及 `player.cc::invis_allowed()` 身体过亮、暂时背光和光环来源动态项均给出了完整句模板。中文保留了原状态因果，不把 form/god 状态误译成物品名称。

## 名称、数量与充能显示

`item-name.cc::item_def::name()` 生成的物品名本身不是可直接翻译的单句，需先按 subtype 选择已审校语义名，再生成局部格式：

- `OBJ_WANDS` 已鉴定名使用 `wand of {type}` 生成；完整 wand 名称应优先精确查找词库条目。已识别魔杖只有在 `charges > 0` 时附加 ` ({charges})`；本批提供 `item.wand.display.charges`，中文使用全角括号。基本名称不能对带动态充能数的最终整名查词。
- `OBJ_BOOKS` 通过 `sub_type_string()` 选择书名；手册依赖技能名，羊皮纸依赖法术名，其他书本名来自 `_book_type_name()`/特殊书名。`zh-catalog.inc` 已包含大量 `book of …`、`manual of …` 具体词条和 `book of `/`manual of ` 前缀；应优先复用完整精确词条，技能/法术名称继续走既有语义名接口。自定义神器书名若无 exact 命中，应整名回退。
- `OBJ_MISCELLANY` 由 `misc_type_name()` 返回数据名称；不得翻译 enum、属性 key 或存档键本身。目录中的已审校精确名可直接复用。`item_def::name()` 另会加锯齿迷宫完成数 `+{count}`、XP 唤能器强化值 `+{level}`，以及 XP 唤能器的 `(inert)` 或 `(charges/max)` 后缀；本批为这些局部格式提供了 UI 模板，其中“失活”沿用现有词库对 inert 的状态语义。
- 现有通用物品数量由 `item_def::name()` 在所有物品名完成后统一调用 `pluralise()`，并非统一的可移植英文后缀。中文重建时应按数量先生成数量词，再附完整语义名；本批分别列出书“本”、魔杖“根”、杂项“件”的 UI 组合模板。不可直接中文化 `pluralise()` 的英语输出，也不可把数据库物品 key 当作显示名。
- 消耗品稀有度 `describe_item_rarity()` 返回 `very rare/rare/uncommon/common/very common`，这些词已在 catalog 精确收录；药水/卷轴继续复用已有 `item.consumable.rarity` 模板，不复制稀有度条目。
- 玩家在 wizard 模式下，`spl-cast.cc::spell_noise_display_arg()` 在噪声等级后附加数值。本批新增 `spell.noise.display.wizard`，参数为 `rating:name` 与 `noise:integer`；等级继续复用现有 `spell.noise.*` 词项。

## 仍有动态依赖

1. `cannot_read_item_reason()` 的 Blinking/Teleportation 与 stasis 路径调用 `you.no_tele_reason()`；Blinking 的原因取决于当前状态与目标传送类型。它应由其生产函数提供稳定原因 ID，本批没有将动态英文原因作为 text 参数。
2. `cannot_drink_item_reason()` 会读取不同 potion effect 的 `can_quaff()`。本批检查了现有具体覆盖；`PotionInvisibility` 仍委托 `player.cc::invis_allowed()`，其中 halo 的 weapon/crown/armour/divine halo 来源列表需要逐项语义翻译、中文列表连接以及单复数处理。目录模板提供了参数接口，但在来源枚举落地前不能将任意英文 `{sources}` 标为已支持。
3. `PotionBerserk` 还委托 `player::can_go_berserk()`，已把该函数的固定理由全部列出。若以后该函数加入新动态理由，应更新独立模板目录。
4. `PotionLignify`、flux bauble、`cannot_evoke_item_reason()` 的 flux bauble 分支委托 `cant_transform_reason()`。本批列出了该函数当前完整固定返回分支；若外围新添 form 专属检查，需新增审校项。高阶来源理由仍不应由 `item-use.cc` 的操作执行反馈替代。
5. XP 唤能器耗尽原因包含具体物品名；需用 `item.name(DESC_DBNAME)` 的稳定显示名参数，完整名未命中时整句回退。不能把存档子类型名或内部键直接填入 `{item}`。
6. 书籍/杂项完整名称空间来自数据表，catalog 并非保证每种自定义/随机神器名都齐全。本批没有臆造长尾书名或杂项翻译；缺少精确语义名称的名称必须整体回退。
7. `item-use.cc` 中真正执行读/饮/唤起时的失败反馈与确认提示不属于物品详情，本批没有纳入；详情理由和操作结果继续由各自调用入口负责。

## 本轮补充修订

- `describe_item_rarity()` 的六种返回值 `very rare/rare/uncommon/common/very common/buggy` 已分别为 potion 与 scroll 提供完整句模板，共 12 条。每条模板使用完整 canonical 英文且稀有度只出现一次（例如 `It is an uncommon potion.`）；不把 `article_a(rarity)` 的结果（其中已包含稀有度词）与 rarity 再次拼接。中文直接使用瓶/张量词和审校过的稀有度词，不传 `a/an` 冠词参数。`buggy` 是 rarity 默认/异常分支，译作“稀有度异常”。
- 新增 `item.reason.use.no_summons` 与 `item.reason.use.flux_already`，分别对应卷轴召唤限制和 flux bauble 已充满不稳定能量的固定完整返回句。
- `_can_mutate()` 的可变片段已拆成 `item.reason.drink.cannot_mutate_currently` 与 `item.reason.drink.cannot_mutate_permanently` 两个完整 ID；移除了旧的 `time` 片段模板。当前变异受限、永久无法变异分别用独立 oracle。
- `item-name.cc::sub_type_string()` 的 `BOOK_MANUAL` 与 `BOOK_PARCHMENT` 名称模板已补齐；技能名和法术名分别为 `{skill:name}` 与 `{spell:name}`。未鉴定或 `plus == 0` 的羊皮纸仍显示普通 parchment 名，不应套用法术羊皮纸模板。
- `MISC_ZIGGURAT` 的 `+{count}` 是已完成锯齿迷宫进度前缀，改为 `item.miscellany.display.ziggurat_progress`，中文使用“次”，不把它读成物品数量或“座数”。XP 唤能器的 `+{level}` 仍表示强化等级，与数量分开处理。
- Trog 与 Cheibriados 的新中文均复用词库已审校的“特洛格”和“切布拉多斯”。
- 补充了稀有度 `an`、当前/永久变异限制、法术书名称、锯齿迷宫完成进度、数量 1/3 的代表性 oracle。原有快捷键/颜色标记未出现在新增文案中；物品内部 subtype、book 数据键仍只用于语义查找，不作为可译显示参数。
