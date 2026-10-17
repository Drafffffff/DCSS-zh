# 迁移账本

本文由 modules.json 与真实源码调用清单生成。调用点是审查候选，不等于玩家可见文案或翻译完成率。

| 模块 | 当前边界 | 下一步 / 验收 |
|---|---|---|
| 接口与渲染 | 规范英文读取与旧匹配暂停已拆分；Mac自动测试及真实回放通过 | raw绘制不改变语言；Lua/存档仍规范英文；参数/标签/缺失校验通过 |
| 语义名称 | 普通物品/怪物/地点已有语义接口；本轮补未鉴定卷轴外观标签、普通尸体/骨架量词、丑陋之物颜色与HELPLESS_KEY限定；复杂专名/神器/其他未鉴定外观继续整名回退并报告 | 枚举/鉴定/数量/装备/专名组合测试；不解析最终英文名称 |
| 详情 | 物品/怪物/法术详情已分批接入；本批完成怪物伤势/装备/132枚举状态、状态DB引用展开、教学建议和命中父句/标题/体型/门交互；特殊统计与怪物首遇/固定喊叫由 monster-tutorial-shout-special 接续；幽灵生平/变异兽等仍待后续包 | 数据库正文语言选择、长文本、动作、不同来源/状态逐项核对；禁止旧matcher |
| 技能 | 主面板/查阅菜单/详情/帮助/tile提示已接入；本轮增强/削弱原因改稳定ID列表，并以实际生产函数覆盖全部原因组合；技能帮助与纸娃娃真实布局见sol61-six验收 | 主面板、?/k、条目、详情、帮助、训练/增强/削弱、tile提示全部走新链路 |
| 商店 | 菜单/确认/余额/购物清单主路径已接入，Mac严格回放通过；罕见命名回退仍登记 | 不同余额/数量/排序/颜色/键位/购买/空清单及名称回退 |
| HUD | 等级/地点/噪声/武器部分接入；其他字段未迁移 | 统一按字段语义接入；列宽/刷新/长短名/最大值；不能整体跳过旧层审计 |
| 战斗日志 | 既有战斗命中/失手/限制/目标/施法/怪物事件/随机对白分批接入；本轮补背刺、部分自我强化、血液/亡灵、九类召唤及云雾生产分支；melee/ranged/beam、其余法术与怪物业务日志仍待完整包 | 玩家/怪物/武器/状态/数值组合，全部成功失败分支保留英文控制数据 |
| 装备与物品操作 | 普通拾取/丢弃/穿脱/挥舞/使用已接入；本轮补最后类别鉴定、地面集合、专名武器问候/告别、Imbue/Imprint延迟与箭袋近战反馈；Orb启动、外部低语、旅行延迟及其他自定义提示仍待迁移 | 穿脱/挥舞/使用/失败/进度/中断完整消息；量词/所有格 |
| 瞄准、法术、能力、箭袋 | 目标理由、瞄准帮助/顶部/动作、箭袋/法术菜单及风险确认已接入；本批完成目标怪物伤势/装备/状态与全部现有typed效果回调消费者；能力其他菜单和业务日志仍待迁移 | 坐标/距离/法术等级分离；目标名称和无效目标；父视图/箭袋提示也需迁移 |
| 神祇与角色 | 本轮迁移祈祷/皈依/献金/敬重等级/逐出与多种能力固定日志、神祇击杀认可、部分变异和属性变化；能力菜单主体typed化；复杂神祇对白/惩戒/能力成本/变异数组及角色页仍有未迁移入口 | 每个实体、状态与等级语义分开；全流程日志/详情/菜单 |
| 世界与通用界面 | 本轮补楼梯警告/确认/行动、网与蛛网、部分旅行警告/绕路缓存；普通爬楼前置拦截按消费者补全；移动/旅行/陷阱其余分支、深渊/地形/排除区/Orb业务仍待迁移；纸娃娃编辑器17个旧入口归零 | 静态/动态生产点完整接入；输入/程序标识不翻译 |
| 帮助与文档 | 已有中文手册复用；本轮技能原因链、纸娃娃快捷键与布局完成指定工作包；command等剩余帮助入口和其他教程仍需独立包 | 选择正文语言；长文分页/标记/快捷键；无最终英文句匹配 |
| 旧历史兼容 | 旧存档英文历史无ID，保留明确兼容边界 | 与新实时消息隔离；不改原存档；不计入新架构迁移完成 |

## 按项目结构推进的路线

按模块选择工作包；每包沿生产函数、业务消费者、显示出口完整迁移。
通过参数/规范英文/完整回退测试、Mac存档副本调试与两端构建后，才标为已验收；文件里存在新接口不代表文件完成。
源码调用清单用于查漏；未逐项验收的调用不计完成，不以词库条数或中文字占比计覆盖率。

1. 共用目标理由闭环
2. 施法动态日志与持续施法
3. 法术/箭袋/瞄准菜单及风险标签
4. 通用移动确认与危险地形
5. 物品操作日志
6. 战斗实体与状态日志
7. 神祇与角色
8. 世界交互/剩余教程/文档入口

## 可验收工作包

### target-external-reasons — verified

所属模块：瞄准、法术、能力、箭袋。
文件：`god-abil.cc`、`god-abil.h`、`spl-other.cc`、`spl-other.h`、`spl-damage.cc`、`spl-damage.h`、`spl-summoning.cc`、`spl-summoning.h`、`target.cc`、`target.h`。
生产函数：`wu_jian_can_wall_jump`、`passwall_path::is_valid`、`mons_inner_flame_immune_reason`、`mons_simulacrum_immune_reason`、`surprising_crocodile_unusable_reason`。
显示/业务消费者：`targeter_walljump::valid_aim`、`targeter_passwall::valid_aim`、`targeter_inner_flame::valid_aim`、`targeter_simulacrum::valid_aim`、`targeter_surprising_crocodile::valid_aim`、`cast_passwall`、`cast_inner_flame`、`cast_simulacrum`、`cast_surprising_crocodile`。
验证：`tools/test_external_target_reasons.py`、`tools/test_target_notifications.py`。
兼容规则：旧理由接口仅返回canonical；分支与隐藏信息规则不变；string notify_fail入口应移除。
验收记录：[verification/native/external-target/REPORT.md](../../verification/native/external-target/REPORT.md)。
剩余：通用危险地形移动确认属于player.cc，单列后续工作包。

### casting-channel-logs — verified

所属模块：战斗日志。
文件：`spl-cast.cc`、`spl-cast.h`。
生产函数：`surge_power`、`surge_power_wand`、`_casting_spell_log`、`start_channelling_spell`、`handle_channelled_spell`、`stop_channelling_spells`。
显示/业务消费者：`surge_power`、`surge_power_wand`、`start_channelling_spell`、`handle_channelled_spell`、`stop_channelling_spells`。
验证：`tools/test_casting_logs.py`。
兼容规则：力量档位、单次状态副作用、按键替换与规范英文逐项对照旧源码。
验收记录：[verification/native/external-target/REPORT.md](../../verification/native/external-target/REPORT.md)。
剩余：施法选择/风险确认/箭袋描述与名称列表未包含在本包。

### target-quiver-prompts — verified

所属模块：瞄准、法术、能力、箭袋。
文件：`directn.cc`、`directn.h`、`quiver.cc`、`quiver.h`、`throw.cc`、`spl-cast.cc`。
生产函数：`_target_key_prompt`、`_target_prefix_arg`、`_quiver_caption`、`_quiver_named_description`、`_spell_menu_action`、`_spell_failure_rate_arg`、`_spellcasting_aborted`、`desc_wl_success_chance`。
显示/业务消费者：`direction_chooser::print_key_hints`、`direction_chooser::print_top_prompt`、`list_spells`、`cast_a_spell`、`target_spell_desc`。
验证：`tools/test_target_quiver_prompts.py`、`tools/test_spell_prompts.py`、`tools/test_spell_target_effects.py`。
兼容规则：规范英文提示与冻结旧生成函数对照；Lua target_spell_desc/throw内部提示保留英文；控制键与颜色类型校验；Unicode表头列宽。
验收记录：[verification/native/prompt-terrain/REPORT.md](../../verification/native/prompt-terrain/REPORT.md)。
剩余：目标怪物伤势/装备/状态依赖已由target-monster-details-logs接续迁移；物品/地形/云雾外层悬停仍待后续工作包；箭袋/能力其他业务操作日志、wizard地形构建标题未在本包验收；未审校新名称整行/整父回退并报告缺失，不拼凑中文。

### terrain-move-confirmation — verified

所属模块：世界与通用界面。
文件：`player.cc`、`player.h`、`spl-other.cc`、`prompt.cc`、`prompt.h`。
生产函数：`check_moveto_terrain`、`check_moveto_cloud`、`check_moveto_trap`、`check_moveto_exclusions`、`confirm_prompt`。
显示/业务消费者：`check_moveto`、`check_move_over`、`passwall_path::check_moveto`。
验证：`tools/test_terrain_confirmation.py`。
兼容规则：yesno/confirm_prompt保留Lua英文及yes输入；确认顺序/接受取消/危险判定/RNG不变；移除typed确认提示200字节截断。
验收记录：[verification/native/prompt-terrain/REPORT.md](../../verification/native/prompt-terrain/REPORT.md)。
剩余：未知未来移动动词/云雾/陷阱名称及任意调用方警告完整回退并报告；其他移动业务日志、旅行及世界交互不在共用确认包内。

### target-monster-details-logs — verified

所属模块：瞄准、法术、能力、箭袋。
文件：`directn.cc`、`directn.h`、`mon-info.cc`、`mon-info.h`、`describe.cc`、`describe.h`、`spl-cast.cc`、`spl-cast.h`、`throw.cc`、`player-notices.cc`、`mon-util.cc`、`quiver.cc`、`ability.cc`、`item-use.cc`、`spl-goditem.cc`、`evoke.cc`、`hints.cc`、`hints.h`、`database.cc`、`zh-database.h`、`zh-message.cc`。
生产函数：`get_monster_equipment_desc_message`、`cell_monster_description_message`、`get_monster_status_descriptor_messages`、`monster_info::attributes_messages`、`monster_info::wounds_description_message`、`monster_info::constriction_description_message`、`_abyss_monster_creation_message`、`_handle_encounter_messages`、`print_wounds`、`hints_describe_monster_display`、`zh_database_description`、`_description_message_tree`、`_monster_player_hit_message`、`_monster_detail_size_message`、`_monster_door_message`、`_monster_detail_title_message`。
显示/业务消费者：`direction_chooser::print_target_monster_description`、`get_square_desc`、`describe_monster`、`fire_target_behaviour::get_monster_desc_messages`。
验证：`tools/test_target_monster_details.py`、`tools/test_monster_info_messages.py`、`tools/test_monster_detail_logs.py`、`tools/test_spell_target_effects.py`、`tools/test_target_monster_callbacks.py`、`tools/test_monster_hints.py`、`tools/test_monster_status_database.py`、`tools/test_monster_detail_parents.py`。
兼容规则：保留英文字符串API与Lua数据；typed回调贯通父句；状态枚举、名称快照、英文冻结生成函数与伤势日志逐项对照。
验收记录：[verification/native/target-monster/REPORT.md](../../verification/native/target-monster/REPORT.md)。
剩余：玩家幽灵完整生平、未审校复杂名称整父回退并报告；悬停格子外层物品/地形/云雾段落仍旧显示链路；特殊统计、首遇教程及固定喊叫由 monster-tutorial-shout-special 接续；随机对白仍待独立包；其他怪物业务日志、物品操作日志按模块账本后续验收。

### monster-tutorial-shout-special — verified

所属模块：教程、怪物与详情。
文件：`hints.cc`、`hints.h`、`shout.cc`、`describe.cc`、`player-notices.cc`、`database.cc`、`database.h`、`zh-display-name.cc`、`tilesdl.cc`、`tilesdl.h`、`tileweb.cc`、`tileweb.h`、`tilereg-dgn.cc`、`tilereg-dgn.h`。
生产函数：`hints_monster_seen`、`monster_shout`、`_monster_intrinsic_prose`、`_summoned_alert_message`、`_wyrmbane_alert_message`、`_gozag_incite_message`、`getShoutStringCanonical`、`_monster_visible_species_arg`。
显示/业务消费者：`learned_something_new`、`describe_monster`、`seen_monster`、`_check_monster_alert`。
验证：`tools/test_monster_notice_events.py`、`tools/test_special_monster_details.py`、`tools/test_first_encounter_hints.py`、`tools/test_monster_shouts.py`、`tools/test_monster_semantic_names.py`、`tools/test_pretranslated_rendering.py`、`tools/test_hydra_lore_unwrap.py`。
兼容规则：数据库原始固定模板在参数填入之前绑定稳定ID；规范英文、事件标记、频道、噪声与随机调用保持不变。
验收记录：[verification/native/monster-events/REPORT.md](../../verification/native/monster-events/REPORT.md)。
剩余：随机嘲讽、谜语与其他玩家喊叫流程需要独立类型协议迁移；变形者神祇警告及其他怪物业务日志仍在账本排队；幽灵生平与变异兽详细数据库描述不是本包验收范围。

### monster-random-speech — verified

所属模块：怪物对白、喊叫与行为日志。
文件：`database.cc`、`database.h`、`zh-speech.cc`、`zh-speech.h`、`mon-util.cc`、`mon-speak.cc`、`mon-speak.h`、`shout.cc`、`mon-behv.cc`、`mon-cast.cc`。
生产函数：`getSpeakSpeech`、`getShoutSpeech`、`zh_render_speech`、`zh_mon_speech_message`、`zh_speech_actor_arg`。
显示/业务消费者：`mons_speaks_msg`、`monster_shout`、`mons_speaks`、`maybe_mons_speaks`。
验证：`tools/test_speech_protocol.py`、`tools/test_speech_actor_args.py`、`tools/test_speech_display.py`、`tools/test_monster_shouts.py`、`tools/test_pixel_font_quotes.py`。
兼容规则：数据库选择保留原始叶模板/递归树；规范英文与随机调用只执行一次；控制值/频道/可见性/副作用顺序保持原义；不按最终英文反向匹配。
验收记录：[verification/native/random-speech/REPORT.md](../../verification/native/random-speech/REPORT.md)。
剩余：18条内嵌Lua语法保留原协议，整父规范英文回退并报告；53条纯控制值不属于待翻译文案；god_is非无神分支、部分方位别体及未知自定义语义名称仍整父回退；mon-cast其余施法组合、mon-death、mon-abil、god-companions等getSpeakString消费者尚未迁移；武器噪声、神祇对白与玩家谜语独立包；其他教程与动态日志仍在模块账本排队。

### item-operations — verified

所属模块：装备与物品操作。
文件：`items.cc`、`invent.cc`、`invent.h`、`item-use.cc`、`item-use.h`、`player-equip.cc`、`player-equip.h`、`evoke.cc`、`potion.cc`、`delay.cc`、`quiver.cc`、`nearby-danger.cc`、`religion.cc`、`spl-transloc.cc`、`zh-display-name.cc`、`zh-message.cc`。
生产函数：`get_gold`、`enchant_weapon`、`enchant_armour`、`no_selectables_display_reason`、`get_player_equip_slot_count`、`can_equip_item`、`ignore_faith_display_reason`、`zh_item_quantity_arg`、`zh_item_menu_arg`。
显示/业务消费者：`drink`、`read`、`try_equip_item`、`try_unequip_item`、`use_an_item_menu`、`prompt_invent_item`、`maybe_warn_about_removing`、`check_warning_inscriptions`。
验证：`tools/test_item_operations.py`、`tools/test_message_ids.py`、`tools/test_consumable_producers.py`、`tools/test_shared_restrictions.py`、`tools/test_pretranslated_rendering.py`、`tools/replay_saved_console.py`、`tools/replay_message_migration.py`。
兼容规则：模板在格式化前选择；数量、名字与附魔前状态快照；规范英文 wrapper、随机调用、Lua和存档控制数据保持；颜色和快捷键分参。
验收记录：[verification/native/item-operations/REPORT.md](../../verification/native/item-operations/REPORT.md)。
剩余：专名武器问候/告别、最后类别鉴定、地面集合及Imbue/Imprint/箭袋近战反馈由 sol61-item-edges 接续；Orb逃离启动仍待迁移；外部数据库低语及法术/怪物/神祇/状态效果消费者须另包迁移；其他 const char* 自定义物品提示与复杂名称仍保留明确旧边界或整父回退；旅行及其他跨模块延迟/效果消费者尚未完成。

### sol61-religion-character — verified

所属模块：神祇与角色。
文件：`religion.cc`、`god-abil.cc`、`god-prayer.cc`、`god-passive.cc`、`god-wrath.cc`、`god-conduct.cc`、`mutation.cc`、`ability.cc`、`player-stats.cc`。
生产函数：`_ability_menu_cost_arg`、`_talent_menu_message`、`_ability_menu_hints_message`、`_on_kill`。
显示/业务消费者：`choose_ability_menu`、`_on_kill`。
验证：`tools/test_sol61_religion_character.py`。
兼容规则：从基线冻结实际英文生成路径；规范英文/业务副作用/RNG/频道逐项对照；未知语义整父回退并报告。
验收记录：[verification/native/sol61-six/religion-character/REPORT.md](../../verification/native/sol61-six/religion-character/REPORT.md)。
剩余：神祇数据库对白及惩戒/能力复杂组合；变异数组、角色详情和其他未迁移分支。

### sol61-combat-spells — verified

所属模块：战斗日志。
文件：`attack.cc`、`spl-selfench.cc`、`spl-other.cc`、`spl-summoning.cc`、`spl-clouds.cc`。
生产函数：`_dismiss_dead`、`attack::stab_message`、`cast_animate_dead`、`cast_awaken_armour`、`cast_call_canine_familiar`、`cast_death_channel`、`cast_deaths_door`、`cast_detonation_catalyst`、`cast_fugue_of_the_fallen`、`cast_jinxbite`、`cast_liquefaction`、`cast_monstrous_menagerie`、`cast_putrefaction`、`cast_revivification`、`cast_silence`、`cast_sphinx_sisters`、`cast_sublimation_of_blood`、`cast_summon_cactus`、`cast_summon_hydra`、`cast_summon_ice_beast`、`cast_summon_mana_viper`、`cast_summon_small_mammal`、`cast_swiftness`、`do_fugue_wail`、`fiery_armour`、`ice_armour`、`jinxbite_targets_available`、`kindle_blastmotes`、`player_summon_check`、`remove_ice_armour`、`scroll_of_poison`。
显示/业务消费者：`attack::stab_message`、`cast_swiftness`、`cast_sublimation_of_blood`、`cast_animate_dead`、`cast_putrefaction`。
验证：`tools/test_sol61_combat_spells.py`。
兼容规则：从基线冻结实际英文生成路径；规范英文/业务副作用/RNG/频道逐项对照；未知语义整父回退并报告。
验收记录：[verification/native/sol61-six/combat-spells/REPORT.md](../../verification/native/sol61-six/combat-spells/REPORT.md)。
剩余：melee/ranged/beam主体及其余法术；mon-cast/mon-death/mon-abil业务消费者。

### sol61-world-interaction — verified

所属模块：世界与通用界面。
文件：`stairs.cc`、`traps.cc`、`travel.cc`、`main.cc`。
生产函数：`_check_stairs`、`_can_take_stairs`、`deviant_route_warning::warn_continue_travel`。
显示/业务消费者：`_take_stairs`、`trap_def::trigger`、`deviant_route_warning::warn_continue_travel`。
验证：`tools/test_sol61_world_interaction.py`。
兼容规则：从基线冻结实际英文生成路径；规范英文/业务副作用/RNG/频道逐项对照；未知语义整父回退并报告。
验收记录：[verification/native/sol61-six/world-interaction/REPORT.md](../../verification/native/sol61-six/world-interaction/REPORT.md)。
剩余：movement/abyss/terrain/exclude/orb/nearby-danger其余消息；旅行层级/路线/失败拾取及完整trap trigger。

### sol61-item-edges — verified

所属模块：装备与物品操作。
文件：`items.cc`、`items.h`、`delay.cc`、`quiver.cc`。
生产函数：`item_message_display_arg`、`item_check`、`_identify_last_item`、`_weapon_display_name_arg`、`maybe_name_weapon`、`say_farewell_to_weapon`、`ImbueDelay::try_interrupt`、`ImbueDelay::start`、`ImprintDelay::start`、`ImprintDelay::finish`。
显示/业务消费者：`item_check`、`maybe_name_weapon`、`say_farewell_to_weapon`、`quiver::melee_action::trigger`。
验证：`tools/test_sol61_item_edges.py`。
兼容规则：从基线冻结实际英文生成路径；规范英文/业务副作用/RNG/频道逐项对照；未知语义整父回退并报告。
验收记录：[verification/native/sol61-six/item-edges/REPORT.md](../../verification/native/sol61-six/item-edges/REPORT.md)。
剩余：Orb启动及外部武器/帽子低语；法术记忆神祇组合、旅行/自动战斗及其他物品提示。

### sol61-semantic-details — verified

所属模块：语义名称。
文件：`zh-display-name.cc`。
生产函数：`translated_item_name`、`_monster_visible_species_arg`。
显示/业务消费者：`zh_item_arg`、`zh_item_quantity_arg`、`zh_item_menu_arg`、`zh_monster_info_arg`。
验证：`tools/test_sol61_semantic_details.py`。
兼容规则：从基线冻结实际英文生成路径；规范英文/业务副作用/RNG/频道逐项对照；未知语义整父回退并报告。
验收记录：[verification/native/sol61-six/semantic-details/REPORT.md](../../verification/native/sol61-six/semantic-details/REPORT.md)。
剩余：复杂尸体/自定义/神器与其他未鉴定外观；幽灵生平和变异兽详情。

### sol61-ui-help — verified

所属模块：技能、界面与帮助。
文件：`tilereg-doll.cc`、`skill-menu.cc`。
生产函数：`doll_part_message`、`doll_index_message`、`doll_mode_message`、`doll_command_text`、`doll_layout`、`_skill_cause_arg`、`_skill_power_cause_arg`。
显示/业务消费者：`DollEditRegion::render`、`DollEditRegion::run`、`SkillMenuSwitch::get_help`。
验证：`tools/test_sol61_ui_help.py`。
兼容规则：从基线冻结实际英文生成路径；规范英文/业务副作用/RNG/频道逐项对照；未知语义整父回退并报告。
验收记录：[verification/native/sol61-six/ui-help/REPORT.md](../../verification/native/sol61-six/ui-help/REPORT.md)。
剩余：output角色/概览/状态字段与command帮助入口；其他教程/提示和技能包外特殊分支。


## 公共旧入口

- `cio.cc:243` — `string buf = zh_translate(vmake_stringf(s, args));`
- `cio.cc:328` — `string buf = zh_translate(vmake_stringf(s, args));`
- `cio.cc:347` — `string buf = zh_translate(vmake_stringf(s, args));`
- `command.cc:629` — `line += ": " + zh_translate(untag_tiles_console(desc)) + "\n";`
- `command.cc:642` — `desc = zh_translate(desc);`
- `command.cc:652` — `desc = zh_translate(desc);`
- `command.cc:1145` — `text = zh_translate(text);`
- `format.cc:99` — `return parse_string_raw(zh_translate(s), main_colour);`
- `format.cc:127` — `parse_string_to_multiple_raw(zh_translate(s), out, wrap_col);`
- `format.cc:331` — `ops.emplace_back(zh_translate(other));`
- `format.cc:604` — `ops.push_back(zh_translate(s));`
- `libgui.cc:99` — `const string localized = zh_translate(buffer);`
- `libunix.cc:935` — `const string localized = zh_translate(buffer);`
- `menu.cc:3619` — `vector<string> segs = split_string("\n", zh_translate(s), false, true);`
- `message.cc:103` — `? (localized.empty() ? zh_translate(text) : localized) : text) + rep;`
- `message.cc:650` — `if (!presentation) text = zh_translate(text);`
- `output.cc:1477` — `string title = zh_translate(filtered_lang(player_title()));`
- `output.cc:1499` — `title = trimmed_name + ", " + zh_translate(filtered_lang(player_title(false)));`
- `output.cc:1521` — `string species = zh_translate(player_species_name());`
- `output.cc:1555` — `god = zh_translate(god);`
- `output.cc:2128` — `bar += chop_string(zh_translate("Stlth"), label_length);`
- `output.cc:2233` — `string title = zh_translate(player_title());`
- `output.cc:2236` — `string species_job = zh_translate(make_stringf("(%s %s)",`
- `output.cc:2241` — `string time_turns = zh_translate(make_stringf(" Turns: %d, Time: ", you.num_turns))`
- `output.cc:2576` — `out += chop_string(zh_translate(name), spacing);`
- `output.cc:2636` — `const bool localized = zh_translate("rNeg") != "rNeg";`
- `output.cc:2670` — `out += chop_string(zh_translate("HPRegen"), cwidth);`
- `output.cc:2675` — `out += chop_string(zh_translate("MPRegen"), cwidth);`
- `precision-menu.cc:693` — `m_render_text = m_pretranslated ? m_text : zh_translate(m_text); // editing stays canonical`
- `precision-menu.cc:977` — `m_font_buf.add(m_pretranslated ? m_text : zh_translate(m_text),`
- `zh-localization.cc:479` — `std::string zh_translate(const std::string &text) {`

## 边界声明

规范英文读取使用 ZhTranslationPause；只阻止旧匹配的原样渲染使用 ZhLegacyPause。两种职责不可互换。
模块完成需覆盖主入口、选择、详情、帮助、悬停、成功/失败反馈及渲染出口；同文件有新接口不代表整个文件完成。
旧存档没有消息 ID 的历史兼容单列，不能据此保留新实时消息的旧匹配。
历史工作包由 Luna 审校；本轮 sol61-six 按用户明确指定，由六个 GPT-6.1-Sol 子 agent 分工翻译、审校与生产函数验证，主 agent 负责公共接口、集成和总验收。Mac 为主调试平台；Linux 在里程碑验收。
