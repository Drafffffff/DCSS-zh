# 详情语义缺口：Luna 审校

审校范围是 `describe.cc::get_item_description` 中的来源行和详情回退、`items.cc::origin_desc` 的真实上游分支，以及 `describe-spells.cc::terse_spell_list` 的完整一行法术列表。新消息目录为 `localization/migration/luna-detail-gaps-messages.json`，模型标记 `gpt-6-luna`。本文和目录仅供后续接入；本批没有改 C++、既有目录或数据文件，也没有运行构建。

## 可直接结构化的 item 来源模板

`get_item_description` 只在 `verbose && origin_describable(item)` 时追加来源。它先检查 `orig_monnum == 0 && orig_place.branch == BRANCH_DUNGEON`，现有 `item.origin.found_dungeon` 已明确以 `{depth}` 表示 Dungeon 深度，可继续复用。其他可安全识别的来源应由 `items.cc::origin_desc` 的原始字段决定模板，而不是把最终的 `origin_desc()` 字符串反查：

| 新 ID | 源分支 | 命名参数 |
|---|---|---|
| `item.origin.found_place` | `orig_monnum == 0`，非标准 Dungeon 路径 | `place`：由 `orig_place` 生成并单独本地化的地点短语 |
| `item.origin.shop_purchase` | `IT_SRC_SHOP` | `place` |
| `item.origin.acquirement` | `AQ_SCROLL` | `place` |
| `item.origin.invented` | `AQ_INVENTED` | `place` |
| `item.origin.genie_draw` | `AQ_CARD_GENIE`，仅 `TAG_MAJOR_VERSION == 34` | `place` |
| `item.origin.wizard_created` | `AQ_WIZMODE` | `place` |
| `item.origin.god_gift` | `orig_monnum` 编码合法 god ID | `god`、`place` |
| `item.origin.dancing_weapon` | `orig_monnum == MONS_DANCING_WEAPON` | `place` |
| `item.origin.taken_from_monster` | 正数怪物来源（舞动武器除外） | `monster`、`place` |

目录中的模板按源代码的前缀和 `_origin_place_desc(item)` 后缀完整组成英文 canonical。`place` 是地点短语参数，不能拿它冒充单纯整数层数；接入时应从 `level_id` 的 branch/depth 生成中文地点，而不是对英文句子做反查。Dungeon 第 5 层、Lair 第 5 层应分别显示成“地下城第5层”和“兽穴第5层”。法术等级只能绑定到 `spell_level`，不得从地点短语或 depth 推导。

`god` 来源参数来自 `god_name`；`monster` 来自 `_origin_monster_name` / `mons_type_name`，应走对应神名、怪物名 display 接口。若参数未命中已审词项，模板必须整句回退并记缺失，不能留下中文句框包英文名称。

`origin_desc` 还包含两个不应臆造中文的分支：`IT_SRC_START` 的 “Buggy Original Equipment” 是源码明确标成 buggy 的异常来源；未知负来源类型的默认分支也注释为 “Bug really”。这两类继续走已有 `item.origin.english_fallback` 整句回退并记录即可。`_origin_is_original_equip` 返回的 “Original Equipment” 对应 Dungeon depth 0 特殊项；`origin_describable` 排除了该特殊位置，所以它不是当前物品详情来源弹窗的可达行。`origin_desc` 也供 `items.cc` 的 note/storage 路径使用，详情迁移应留在 `get_item_description`，不要改变它的原始返回语义。

独立测试案例在 JSON 中覆盖了 Lair 第 5 层下的 found、shop、acquirement、invented、genie、wizard-created、god-gift、dancing-weapon、monster-taken 分支，并包含 Xom、yak 示例。地点参数固定用 `place`，避免误认为法术等级或普通数值。

## 紧凑法术列表

`describe-spells.cc::terse_spell_list` 对每个 `spells_in_book(item)` 生成 `spell_title(spell) + " (L" + spell_difficulty(spell) + " " + _spell_schools(spell) + ")"`，然后用 `comma_separated_line` 连接，最前面加 `Spells: `。目录将其拆成：

- `spell.book.terse.row`：完整法术行；`spell` 复用 `spell.name.*` 原子，`spell_level` 是 `spell_difficulty` 整数，`schools` 由 `_spell_schools` 中的每个学派通过现有 `spell.school.*` 原子组成。
- `spell.book.terse.list`：完整列表标题与已本地化行串，`spells` 仅在所有行名称/学派都受支持后标记 supported。

源列表使用英文逗号和末项 `and`（`comma_separated_line` 默认行为）；中文列表用顿号连接。目录 oracle 包含 Magic Dart 法术等级 1、Fireball 法术等级 5、塑能/火焰学派，以及单项和双项完整列表结果。这里的 `L1`/`L5` 是**法术等级**，与 `level_id` 的地牢层数完全无关。此紧凑行不是 `spellset.table.row` 的列式书本表格；不要复用该表的 `known`、列宽或学派列拼接协议。

## 当前整句回退及其上游

- `detail.english_fallback` 实际由 `describe.cc::_detail_english_fallback` 调用，当前服务 `_detail_database_text`：`getLongDescription` 与 `getQuoteString` 先在 `ZhTranslationPause` 下取 canonical，再读当前选定数据库文本；未翻译时整段英文保留。上游是 database/quote 数据，不是 native 静态句子，应交给对应 DB 数据迁移者。目录中的 `detail.database.english_fallback` 记录不等于当前 helper 的实际调用 ID。
- `item.origin.english_fallback` 是 `get_item_description` 的来源 catch-all；已识别分支可按本批模板迁移，未知/buggy 分支继续整句回退。
- `item.curse.skills_english_fallback` 来自 `describe.cc::_describe_item_curse` → `god-abil.cc::desc_curse_skills`。它按 curse data 动态选 curse 名称与当前可训练技能，再由逗号格式器合并；后续应把 curse 名、skill 名和 list separator 结构化，不能把汇总句直接贴进模板。
- `item.talisman.form_english_fallback` 来自 `describe.cc::_describe_talisman_form`。它根据 `Form` 数据、当前 shapeshifting skill 生成 min/max/current 数值表和多种特例行，并带 `<red>/<white>/<lightgrey>` 等颜色标签。后续 owner 应按静态列头/属性标签、数值、颜色分开迁移；不应在本批臆造一份固定表或翻译颜色 key。
- `item.hints.english_fallback` 来自 `describe_item_popup` → `hints_describe_item` (`hints.cc`)。该函数依物品种类、装备/鉴定/教程状态选取多段提示，含 `%` 快捷键替换、`<w>` 颜色标记、tile 鼠标说明和 `_hints_abilities` 动态文本。应由 hints producer owner按完整源句和 key/colour 参数迁移；快捷键和颜色标记原样保留。

以上三个复杂生成器仍属于明示回退范围；它们没有被本批结构模板覆盖。数据库正文与 quotes 也继续由 DB owner逐条审校。这样在严格模式下能够区分“已完整翻译的模板”与“完整保留的英文块”，不混成半中半英。
