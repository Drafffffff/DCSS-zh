# 瞬移实体动态日志文案审校

本批仅覆盖 `spl-transloc.cc` 中指定的带动态实体/数量日志，不修改 C++。每个变化分支使用独立完整消息 ID；物品、怪物、地形和所有格名称均通过 `name` 参数传入，数据键与控制信息不进入译文。

## 已审校消息

- `_teleport_player_mons`：周围只有一只或多只怪物时，分别使用 `.follow.monster` 和 `.follow.monsters`，保留原句 `a monster` / `some monsters`。跟随传送的施法者使用 `.source_arrives`，怪物名称由 `source->name(DESC_THE)` 提供，原 `MSGCH_WARN` 频道保持不变。
- 重力波日志：无怪物/非实体地形时用 `.gravitas.inward`；目标怪物存在时用 `.around_monster`；没有怪物但目标地形为实心时用 `.around_terrain`。条件顺序对应源码 `mons ? monster : solid terrain ? feature : empty`，避免把地形名误当怪物名。被重力束缚的可见怪物由 `.gravitas.pinned` 表达。
- `beckon`：按 `conj_verb("hurl")` 实际返回 `hurls` 或 `hurl`，使用 `.beckon.singular` / `.beckon.plural` 两个完整英文模板。中文不暴露屈折词，只本地化实体名并表达被召引向前。
- `piledriver`：一个目标时使用 `.piledriver.one` 并传语义怪物名；多个目标时使用 `.piledriver.many`，`count_word` 保留英文 `number_in_words` canonical，localized 仅提供数字值，模板负责中文量词“只”，不会丢失目标数量。
- 其余目标包括电流冲锋遇到固定怪物、冲锋未能移开阻挡者（`remain` / `remains` 两个实源屈折分支）、远程武器维度链接、秋之刀的空间折叠所有格，以及怪物被引力吸向玩家。

所有条目各自带有 `test_cases` oracle，覆盖实体名、地形名、所有格、单复数和数量。已逐项复核 17 个 canonical 与源码格式串一致，包括 `You are hurled through space towards a monster!` 的感叹号、两条 gravitas/beckon/charge 变体及其余句末标点。`.manifold.blade` 中的 `actor` 专指 `agent.name(DESC_ITS)` 返回的所有格形式（如 `its` / `your`），中文参数应相应提供“它的”/“你的”；现有 oracle 的“它的刀刃”与 `{actor}刀刃` 拼接正确。英文 canonical 模板不额外添加 `'s`，因为源码 `DESC_ITS` 已返回 `its`/`your` 这类所有格词。

## 尚未覆盖

- `spl-transloc.cc` 其他带动态动词、目标或物品名的日志不属于本批：例如 `_real_teleport_cleanup` 外的目标选择消息、hop/apport 的目标和物品反馈、传送失败原因、多个怪物移动/重力变向等。后续需要按完整源句和具体语义参数分别迁移，不能把名称或数值硬编码进文案。
- 本批仅审校消息模板，不提供 C++ 接入、名称接口选择或运行时路径验证；由主 agent 根据 `source` 锚点集成并验证实体名与所有格参数的 canonical/localized 配对。
