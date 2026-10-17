# Luna 中文展示名称语法审校

展示名需要由专门的 display-name 接口根据结构化字段渲染。不要把整句 English 当输入，也不要从 `item_def::name()`、`monster::name()` 或 `monster_info` 拼出的完整英文字符串反推成分。`item-name.cc` 的 `item_def::name()` 会依据 description level、数量、识别状态、artefact、装备槽、铭文和 curse 等条件组装输出；`mon-info.cc` 的 `common_name()` / `proper_name()` / `full_name()` 同样会组合种类、状态、定冠词、友好态度和专名。整句解析会丢失这些字段的来源和语义。

## 已审校语法

机器可读模板见 [luna-display-grammar.json](luna-display-grammar.json)。它提供 27 个完整模板，覆盖怪物名称、数量、专名、友方所有格、属性、状态组合，以及武器、护甲、药水、卷轴、戒指、护符、投射物、尸体和专名物品。模板中的 `{base}`、`{count}`、`{plus}`、`{brand}`、`{property}`、`{owner}`、`{status}` 等是接口参数，调用者需按对象字段填入。

审校要点：

- 怪物英语定冠词 `the` 不保留。中文单体名直接使用基础名；复数才加数字和量词。友方用“你的”，中立/敌对不加所有格。
- 怪物的专名、种类名、附加状态分别传入。未知专名保留原拼写，不擅自音译。专名与种类需同时出现时采用“专名（种类）”。
- 物品数量结构按中文量词组织：武器“把”、护甲“件”、药水“瓶”、卷轴“张”、戒指“枚”、护符“枚”。列表单件名不强加“一把/一件”；数量大于一才呈现数字量词。
- 加值 `plus`、品牌 `brand`、属性 `property` 和所有者 `owner` 必须来自独立字段；有语义时依模板排位。未知值按 JSON 中规则原样保留。
- `monster::name()`、`item_def::name()` 和对应 db name 仍是原有内部数据来源，供存档、Lua、数据库比较及逻辑继续使用。专门接口只生成 UI 展示副本；不能把其中文结果回写内部名称或存档。

## 与 C++ 枚举/字段的对应

- 怪物种类取 `monster_type` (`MONS_*`)；僵尸、残骸、感知目标可依据 `base_type` 确定展示种类。专名行为由 monster flags (`MF_NAME_*`) 和 monster-info flags 表达，代码中有 replace、adjective、suffix、unqualified、the 等命名语义。UI 的专名不等于所有 `mname`：`monster_info::has_proper_name()` 排除了 replace/adjective/suffix 名称，以及潘德莫尼乌姆领主、玩家幽灵和玩家幻象等特殊构造。
- 怪物状态来自 enchant (`ENCH_*`) 到 `monster_info_flags` (`MB_*`) 映射。`mon-info.cc::trivial_ench_mb_mappings` 包括 `ENCH_SLOW → MB_SLOWED`、`ENCH_POISON → MB_POISONED`、`ENCH_HASTE → MB_HASTED`、`ENCH_INVIS → MB_INVISIBLE` 等；有程度的中毒、污染、吸取等还经过专门分支判定。名称层只接收转换后的状态 ID/审校中文状态词，不从怪物整名拆词。
- 物品大类来自 `item_def::base_type` (`OBJ_*`)，具体物品来自 `sub_type`（如武器、护甲等相应子枚举）。数量由 `quantity`、加值由 `plus`、品牌由 `brand` / `special` 等字段提供；装备、识别、诅咒、伪神器名称和铭文状态也应作为各自标志传入。
- `item-name.cc` 中 `brand_type_name`、`brand_type_adj`、`weapon_brand_name`、`missile_brand_name`、`special_armour_type_name` 是品牌/词缀语义枚举的英文呈现函数，可用作枚举键映射来源；不要拿它们拼出的 item 全名做翻译输入。

## 可复用的已审校基础名

JSON 的 `lexicon.approved_bases` 记录了基础名、稳定 key 和来源文件。当前有审校证据的词条包括：老鼠、豺狼人、长矛、连枷、石头、箭、无形护盾、反射护符、护甲、卷轴。尤其 targeting review 样例中“矛”与另一条 review 中“长矛”不一致；此处统一选用既有完整物品名称“长矛”，避免产生同一物品多种译名。对没有这些审校来源的物种、物品、神器和专名，不要杜撰中文词条：普通名按接口 fallback 保留原文，专名更应原样保留。

这里的已审校基础名是 display-name 词条接口的数据源示例，不要求新增翻译 C++ 数据表。主接口应按稳定 `base_key` 查询此类词条，未来词库可扩展到所有 `MONS_*`、`OBJ_*`/`sub_type`，并提供明确回退。
