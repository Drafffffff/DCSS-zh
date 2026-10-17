# GPT-6.1-Sol：战斗与法术工作包

本包为**部分迁移，独立生产函数回归通过**，不代表战斗、法术或所属文件全部汉化。基线 `cc710081cd3f163eabf78c65b9144e040ef30aa8`；源码仅修改本分工所有权内的五个文件。54 条新增消息由 GPT-6.1-Sol 翻译及审校，JSON 的真实 `model` 为 `gpt-6.1-sol`；`luna-` 文件前缀仅兼容现有扫描工具。

## 已迁移的业务链路

- `attack.cc::attack::stab_message`：背刺的措手不及、从后方扑击/突袭、扑向未察觉目标、未能防御全部输出分支；保留随机分支、HELPLESS 属性的设置/清理，以及反身代词的规范英文。中文反身表达独立使用“自身”。
- `spl-selfench.cc`：`cast_deaths_door`、`remove_ice_armour`、`ice_armour`、`fiery_armour`、`cast_revivification`、`cast_swiftness`、`cast_fugue_of_the_fallen`、`do_fugue_wail`、`cast_silence`、`cast_liquefaction`、`cast_jinxbite`、`cast_detonation_catalyst`。覆盖首次/刷新、目标不可用、失败、持续时间、HP代价、特定消息频道。`jinxbite_targets_available` 保持业务判定并被真实函数测试覆盖。
- `spl-other.cc`：`cast_sublimation_of_blood`（死亡之门/无血/HP不足/MP已满/成功）、`cast_death_channel`、`cast_animate_dead`。`_dismiss_dead` 的旧召唤移除被真实函数测试覆盖。
- `spl-summoning.cc`：`player_summon_check` 无空间失败；`cast_summon_small_mammal`、`cast_call_canine_familiar`、`cast_summon_cactus`、`cast_awaken_armour`、`cast_summon_ice_beast`、`cast_monstrous_menagerie`、`cast_sphinx_sisters`、`cast_summon_hydra`、`cast_summon_mana_viper`。覆盖成功、无空间、创建失败、不可见、不穿护甲/物品槽不足、犬使魔召回/增益、双/单斯芬克斯及施法者所有格；选定入口的 `MSG_NOTHING_HAPPENS` 也迁移到完整消息，避免成功迁移而失败回落旧匹配。
- `spl-clouds.cc`：`cast_putrefaction`、`kindle_blastmotes`、`scroll_of_poison`。覆盖伤口所有格、已有云雾、无空地、未知卷轴/不可见占位影响返回值、创建成功/失败、伤害/消耗状态。

动态名字由 `zh_actor_arg`、`zh_monster_arg`、`zh_item_arg`、`zh_monster_type_arg` 生成；unsupported 子参数触发整句规范英文回退。没有最终英文句匹配，没有逐词 fallback。`cast_monstrous_menagerie` 的类型名字 API 默认返回无冠词规范英文，故保留其语义中文，并通过 `mons_type_name(type, DESC_A)` 设置该调用点原本的英文冠词；玩家/怪物两种动词以完整父模板分支表达。

`cast_swiftness` 原 `set_duration` 在发消息前清零旧持续时间，迁移保留此顺序；随机求值仍先于消息。`cast_jinxbite` 的意志削弱提示同原 `increase_duration` 在修改计时前发出。内部麻痹原因 `breaking free from death's doorway`、存档键、法术枚举、随机选择和效果数据保持规范英文/原控制值。

## 实际验证

执行：`python3 tools/test_sol61_combat_spells.py`

结果：`PASS 174768 real producer cases: canonical, channels, RNG, HP/MP, durations, props, creation, inventory, visibility and whole-parent fallback`。

测试从当前真实源码抽取 32 个生产函数（含三个无修改的业务辅助函数），与 fixture 冻结的迁移前英文函数独立运行。世界查询、实体名称和 RNG 以 seam 提供受控状态；函数的业务分支、消息组装、循环、返回值及副作用均取真实生产源码。对照包含：

- 2,048 组状态位、0/280/16000 持续时间、法力/生命边界、0/1/50/200 强度，以及失败路径。
- 原英文逐字一致、消息频道一致、RNG 的参数/次数/顺序、HP/MP、持续时间、属性、伤害、物品标记、召唤创建/移除/增益顺序一致。
- 普通/专名/幽灵/多头/带颜色及数字名字的组合，支持与不支持语义名，完整父句回退；斯芬克斯双/单/无创建、独立可见性组合。
- 背刺随机分支、是否有爪、不同背刺等级与临时属性清理。
- 新增消息占位符完整性和真实渲染器执行；测试在临时目录生成私有 catalog，不调用 `compile_catalog()`，不改共享生成文件。

未运行完整游戏构建、SSH、UI、真实存档回放或 Linux 构建；由主 agent 统一集成验证。独立测试不替代这些验证，也不宣称已验证完整世界模拟或共享名字实现。

## 剩余与依赖

- `fight.cc::stop_summoning_reason` / `stop_summoning_prompt` 的伤害光环召唤风险确认位于本分工所有权外，仍是旧边界；本包仅验证它们的返回结果不改变已选入口行为，**该确认链路不计迁移完成**。
- `spl-selfench.cc` 剩余：`cast_selective_amnesia` 的完整确认/外来 pre_msg；`cast_confusing_touch` 的手部形态、数量和亮度消息。
- `spl-clouds.cc` 剩余：`holy_flames` 的玩家/怪物分支；`explode_blastmotes_at` 通过 fineff 传递的普通/神祇抑制爆炸消息；`cast_freezing_cloud` 外部攻击风险确认（非直接输出调用，故不含在下面调用候选数中）。
- `spl-summoning.cc` 后段仍有龙群召唤及其MP失败、武器舞动、球状闪电、恶魔/蝴蝶/阴影/恐怖生物/森林/亡魂、魔法侍从、战斗法球、棱晶、植物、狐火、巨石、冰炮/迫击炮、灵魂分裂等日志；本包未宣称迁移。
- `spl-other.cc` 剩余包括召回、醉乱、束缚符文、尖刺发射器等日志。`attack.cc` 剩余吸血恢复、迷乱免疫、藤蔓束缚与圣佑偏转等。
- 本分工其余八个文件没有本包新增迁移：`melee-attack.cc`、`ranged-attack.cc`、`beam.cc`、`spl-cast.cc`、`spl-damage.cc`、`mon-cast.cc`、`mon-death.cc`、`mon-abil.cc`。既有迁移保持原样。

`audit.json` 提供13个所有权源文件的剩余调用候选完整位置及源码片段。当前候选数依次为：attack 7、melee-attack 73、ranged-attack 17、beam 170、spl-cast 32、spl-damage 117、spl-summoning 159、spl-selfench 3、spl-other 15、spl-clouds 2、mon-cast 126、mon-death 74、mon-abil 27。它们包含诊断/条件输出和间接子消费者，**是查漏候选数，不是玩家消息总数或完成率**；fineff/持续时间回调等无直接输出调用的文案也必须继续审计。
