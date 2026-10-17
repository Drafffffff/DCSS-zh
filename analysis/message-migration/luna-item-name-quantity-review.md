# 物品显示名数量词与法杖语义名审校

审校范围：`native/crawl-ref/source/zh-display-name.cc` 的 `item_classifier()`、`semantic_item_base()`、`translated_item_name()`；投掷物枚举见 `item-prop-enum.h::missile_type` 和 `item-prop.cc::Missile_prop[]`。未改 C++ 或词库。

## 投掷物数量词

现有 `item_classifier()` 对武器、护甲、药水、卷轴、首饰分别返回“把、件、瓶、张、枚”，没有 `OBJ_MISSILES` 分支。因此只要投掷物数量大于 1，`translated_item_name()` 就会因 classifier 为空而整体回退英文；单个投掷物则直接拼数量前缀以外的已审校名称。

建议按可见具体 subtype 选择量词，而不是把所有投掷物都笼统归成“枚”。这样能同时覆盖形状差异明显的网、石块、飞镖、回旋镖、标枪：

| subtype | 已审校 base 名 | 建议量词 | 数量示例 |
| --- | --- | --- | --- |
| `MI_DART` | dart → 飞镖 | 枚 | 3枚飞镖 |
| `MI_JAVELIN` | javelin → 标枪 | 支 | 2支标枪 |
| `MI_STONE` | stone → 石头 | 块 | 4块石头 |
| `MI_LARGE_ROCK` | large rock → 大石块 | 块 | 2块大石块 |
| `MI_THROWING_NET` | throwing net → 投掷网 | 张 | 2张投掷网 |
| `MI_BOOMERANG` | boomerang → 回旋镖 | 枚 | 2枚回旋镖 |

上表名称均可在当前生成的 `native/crawl-ref/source/zh-catalog.inc` 精确查到：`dart/stone/javelin/boomerang/large rock/throwing net`。其中“大石块”前用“块”虽有“块块”字面重复感，但量词和物品名边界清楚；若希望避免重复，建议先把大石块的物品名词项规范为“大石”，再用“块”，不建议在数量逻辑里另造物品名。

旧版 `TAG_MAJOR_VERSION == 34` 还定义 `MI_NEEDLE`、`MI_ARROW`、`MI_BOLT`、`MI_SLING_BULLET`、`MI_SLUG`。若这条语义接口也需兼容该版本，建议分别用“枚、支、支、颗、枚”；它们不属于当前版本的 `Missile_prop[]` 主清单。不要把旧版弩矢或弹丸误映射成当前投掷物。

实现时分类器需要取得 `item.sub_type`，或新增 `missile_classifier(missile_type)`；当前 `item_classifier(object_class_type)` 只有基础类别信息，无法依据上述语义区分。若工程希望降低实现复杂度，所有投掷物统一用中性量词“枚”也能避免无量词，但不如按 subtype 的建议自然，尤其是“网”和石块。

## 法杖名称

`semantic_item_base()` 目前没有 `OBJ_STAVES` 分支，因此 `translated_item_name()` 无法得到基础中文名；识别出的普通法杖也会整名回退。已有 exact catalog 可直接支持完整 `staff of …` 形式，不必逐词拼接：

- `staff of air` → 空气法杖
- `staff of alchemy` → 炼金法杖
- `staff of cold` → 寒冷法杖
- `staff of conjuration` → 咒法法杖
- `staff of necromancy` → 死灵法杖
- `staff of earth` → 大地法杖
- `staff of fire` → 火焰法杖
- `staff of Olgreb` → 奥尔格瑞布之杖
- `staff of the Meek` → 温顺之杖

这些条目可在 `zh-catalog.inc` 中精确查到。基础泛称 `staff` → “法杖”也已在同一词库。建议识别状态下优先把完整 `item_base_name(OBJ_STAVES, subtype)` 交给 exact lookup，这样具体类型以已审校长名命中；未知/随机神器或带自定义名的法杖仍按现有整名 fallback 边界处理。

法杖适合用量词“根”：例如“2根空气法杖”。这是细长手持法杖的自然量词；无需把法杖误判成“把武器”或“件装备”。`item_classifier()` 现在按 object class 可返回“把”，但 `OBJ_STAVES` 在此前并未纳入语义基础名；建议为 `OBJ_STAVES` 单列“根”，并仅在确实以物品数量显示时应用。

## 边界

- 不要为未鉴定法杖暴露 staff subtype；当前 `translated_item_name()` 对未鉴定的非武器/护甲物品已整体 fallback，这个保护应继续生效。
- `staff of …` 的 exact phrase 已审校；不需要把 `air/cold/fire` 单独拼成“空气/寒冷/火焰”再临时组词。这样可保留“寒冷法杖”等当前命名选择。
- 品牌、诅咒、神器、自定义铭文名仍受现有 fallback 检查约束。本报告只建议基础身份与数量词，不改变这些可见语义的安全边界。
