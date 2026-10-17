# 世界交互：GPT-6.1-Sol 批次验收记录

本批是部分模块交付，不代表“世界交互”或九个源文件全部完成。源码基线为 `cc710081cd3f163eabf78c65b9144e040ef30aa8`；源变更包括 `stairs.cc`、`travel.cc`、`traps.cc`，以及后续补验明确授权的 `main.cc` 四个命令入口分支。新增 91 条完整消息，译文及审校模型均为 `gpt-6.1-sol`。

## 已完成业务链路

- 下一层警告：玩家注释/当前楼梯排除区、目标楼梯排除区、佐特回合限制 → 按原顺序输出 → 默认否的确认 → 拒绝时中断活动并复位注释标志。保留玩家原始注释和 `<yellow>` 标记。
- 上下楼动作：传送门、逃生舱口、大门、史莱姆楼梯、飞行与上下方向；方向无效反馈；混乱跌落的完整四类文案以及伤害/消耗回合/随机调用顺序。
- 竖井层数：按飞行状态和英文单复数选择完整模板，再填写 integer 层数；中文统一“下坠了 N 层”。生产 `_travel_destination` 调用新 helper；完整目标层计算尚未验收。
- 玩家蛛网/网捕获、免疫理由、quiet/real 属性、重绘与跑步/长动作停止、挣脱失败/成功和网耐久扣除；局部免疫理由的三个消费者统一改为 canonical 空值判断或 typed 输出。
- 自动探索安全检查、佐特确认、探索模式/地图已见格/提示状态与 berserk 命令入口；跨层绕行确认缓存、拒绝后重新询问、目标变化复位。
- 另接入同流程固定反馈与分支欢迎词，但这些大型父函数仍标为部分迁移。

## 验证

运行 `python3 tools/test_sol61_world_interaction.py --schema-only`：91 条 schema、参数、标记和生产绑定通过。

运行 `python3 tools/test_sol61_world_interaction.py --isolated-catalog`：153,468 个真实生产函数/消费者组合通过（原 6,012 个，加实际 main.cc 入口的 147,456 个组合）；61 条预期未知分支整句回退标记；无额外缺失 ID 或旧渲染标记。测试私有目录复制实际 zh-message.cc 并补入本包词库，不写共享生成 catalog。主协调者生成共享 catalog 后可直接运行不带参数的同一测试。

原英文 fixture 从 native 基线冻结，包含 16 个原始函数及原始竖井消息表达式。测试抽取当前实际生产函数，与原版比较英文逐字、频道、确认参数、返回值、活动/提示/地图/捕获状态、伤害和 RNG 调用；另检查中文层数量词、用户 UTF-8/颜色标记和未知名称全句回退。生产名称查询、世界状态与 RNG 是独立 seams；没有最终英文反匹配。

`python3 -m py_compile tools/test_sol61_world_interaction.py` 与三个所有权源文件的 `git diff --check` 通过。未启动完整构建、SSH、存档或 UI；这些由主协调者统一验收。

## 集成回放发现的命令入口补全

真实副本回放发现，`_take_stairs` 先调用 `main.cc::_can_take_stairs`，无效楼梯操作会在到达 `stairs.cc` 之前返回。本批补齐这里的上楼、下楼、石拱门和关闭商店四个反馈出口。前三项复用已审校 ID；商店原文实际是 `This shop appears to be closed.`，与 stairs.cc 的“废弃且无值物”原文不同，经主协调者明确授权新增 `world.stairs.invalid.shop_closed`，译为“这家商店似乎关门了。”，未改变规范英文。

测试冻结基线完整 `_can_take_stairs`，抽取当前实际函数，将四个 typed 输出还原后断言与冻结原版逐字一致；执行 147,456 个实际函数组合，比较英文、返回值与副作用，并对四个出口分别断言真实 ID 与中文。还校验 `_take_stairs` 的实际调用顺序及拒绝时立即返回。仅这四个出口计迁移；完整 main.cc、封印楼梯、符文限制等其余消息不计完成。没有生成共享 catalog、运行全量构建或提交。

## 语义及兼容边界

分支名称复用 `place.branch.*`，沿用佐特、潘德莫尼姆、金字塔、史莱姆坑、深渊等已审词。楼层数不作角色等级或法术等级处理。绕行 prompt 的 canonical 继续使用 D:3 等原缩写，显示侧用语义地点快照；未知分支全句回退并写标记。玩家注释是明确的用户内容原样透传，不能视为未翻译的引擎句子。

Lua/存档/里程碑字符串、内部排除区 cloud 检查、消息频道、yes/no 返回语义和随机流程保持原样。没有改共享 zh API、生成 catalog、公共镜像或其他组文件。

## 未完成入口

- main.cc 仅授权的四条命令入口反馈已补齐；其他消息不在本包，包括封印楼梯、重复商店/祭坛动作、迷惑/移动/符文/黏液限制。


- movement.cc: harmful/confused movement, doors, dangerous portal/descent confirmations and movement failure outputs.
- stairs.cc: moving-stair semantic terrain/verb names, rune insertion names, hell random database strings, branch entry/noise/rune external descriptions and deity-specific Abyss text remain. Full floor_transition and _travel_destination are partial.
- travel.cc: partly-explored summary, failed autopickup item lists and ignore/Always choice, barrier reasons, run-mode stop text, level selection, waypoint menus/assignment, discovery summaries and interlevel route errors require follow-up.
- traps.cc: full trap_def::trigger remains partial; actor/monster names, buff recipient lists, alarm/malevolence random messages, Zot/Golubria effects, and monster capture/escape require follow-up.
- abyss.cc, terrain.cc, exclude.cc, orb.cc and nearby-danger.cc received inventory only in this package; existing prior typed calls do not imply acceptance of the remaining module.

## 逐函数清单

这是顶层函数定义静态清单，排除注释/字符串伪签名；不是 C++ 语义分析。`无直接出口` 只表示未扫描到所列直接消息调用，不计完整审查或模块完成。全部可机读细节与行号见同目录 `audit.json`。

### movement.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `player_displace_monster` | 69 | 可见入口待迁移 |
| `_check_adjacent` | 93 | 静态清单：无直接出口，不计验收 |
| `_cancel_barbed_move` | 123 | 可见入口待迁移 |
| `_apply_barbs_damage` | 142 | 可见入口待迁移 |
| `player_did_deliberate_movement` | 162 | 静态清单：无直接出口，不计验收 |
| `_cancel_ice_move` | 168 | 可见入口待迁移 |
| `cancel_harmful_move` | 196 | 静态清单：无直接出口，不计验收 |
| `remove_ice_movement` | 202 | 可见入口待迁移 |
| `_mark_potential_pursuers` | 220 | 静态清单：无直接出口，不计验收 |
| `apply_cloud_trail` | 247 | 静态清单：无直接出口，不计验收 |
| `cancel_confused_move` | 265 | 可见入口待迁移 |
| `open_door_action` | 338 | 可见入口待迁移 |
| `close_door_action` | 440 | 可见入口待迁移 |
| `prompt_dangerous_portal` | 515 | 可见入口待迁移 |
| `prompt_descent_shortcut` | 534 | 可见入口待迁移 |
| `_rampage_destination` | 545 | 静态清单：无直接出口，不计验收 |
| `get_rampage_target` | 553 | 静态清单：无直接出口，不计验收 |
| `_handle_trying_to_move_into_unpassable_terrain` | 623 | 可见入口待迁移 |
| `_adjust_confused_movement` | 665 | 可见入口待迁移 |
| `_get_move_verb` | 721 | 静态清单：无直接出口，不计验收 |
| `_cannot_step_into` | 740 | 静态清单：无直接出口，不计验收 |
| `_handle_player_step` | 751 | 可见入口待迁移 |
| `move_player_action` | 945 | 可见入口待迁移 |

### stairs.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `_shaft_fall_message` | 69 | 本批迁移并回归 |
| `_annotation_exclusion_warning` | 77 | 本批迁移并回归 |
| `_target_exclusion_warning` | 101 | 本批迁移并回归 |
| `_bezotting_warning` | 120 | 本批迁移并回归 |
| `check_next_floor_warning` | 132 | 本批迁移并回归 |
| `maybe_destroy_shaft` | 164 | 静态清单：无直接出口，不计验收 |
| `_player_change_level_reset` | 171 | 静态清单：无直接出口，不计验收 |
| `_player_change_level` | 180 | 静态清单：无直接出口，不计验收 |
| `_stair_moves_pre` | 186 | 可见入口待迁移 |
| `_climb_message` | 230 | 本批迁移并回归 |
| `_clear_golubria_traps` | 273 | 静态清单：无直接出口，不计验收 |
| `_remove_unstable_monsters` | 283 | 静态清单：无直接出口，不计验收 |
| `_complete_zig` | 292 | 部分迁移/父函数未完成 |
| `leaving_level_now` | 299 | 静态清单：无直接出口，不计验收 |
| `_update_travel_cache` | 333 | 静态清单：无直接出口，不计验收 |
| `_check_stairs` | 393 | 本批迁移并回归 |
| `_check_fall_down_stairs` | 417 | 本批迁移并回归 |
| `_rune_effect` | 445 | 部分迁移/父函数未完成 |
| `_maybe_use_runes` | 492 | 静态清单：无直接出口，不计验收 |
| `_gauntlet_effect` | 512 | 部分迁移/父函数未完成 |
| `_hell_effects` | 524 | 可见入口待迁移 |
| `_vainglory_arrival` | 558 | 部分迁移/父函数未完成 |
| `_new_level_amuses_xom` | 577 | 静态清单：无直接出口，不计验收 |
| `_travel_destination` | 627 | 部分迁移/父函数未完成 |
| `_level_transition_moves_player` | 728 | 静态清单：无直接出口，不计验收 |
| `level_above` | 740 | 静态清单：无直接出口，不计验收 |
| `rise_through_ceiling` | 757 | 部分迁移/父函数未完成 |
| `floor_transition` | 798 | 部分迁移/父函数未完成 |
| `take_stairs` | 1156 | 静态清单：无直接出口，不计验收 |
| `up_stairs` | 1184 | 静态清单：无直接出口，不计验收 |
| `stair_destination` | 1192 | 静态清单：无直接出口，不计验收 |
| `stair_destination` | 1204 | 可见入口待迁移 |
| `down_stairs` | 1356 | 静态清单：无直接出口，不计验收 |
| `_update_level_state` | 1361 | 静态清单：无直接出口，不计验收 |
| `new_level` | 1423 | 静态清单：无直接出口，不计验收 |

### traps.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `_net_immune_reason` | 59 | 本批迁移并回归 |
| `trap_def::active` | 68 | 静态清单：无直接出口，不计验收 |
| `trap_def::destroy` | 73 | 静态清单：无直接出口，不计验收 |
| `trap_def::prepare_ammo` | 87 | 静态清单：无直接出口，不计验收 |
| `trap_def::reveal` | 109 | 静态清单：无直接出口，不计验收 |
| `trap_def::name` | 114 | 静态清单：无直接出口，不计验收 |
| `trap_def::is_bad_for_player` | 134 | 静态清单：无直接出口，不计验收 |
| `trap_def::is_safe` | 147 | 部分迁移/父函数未完成 |
| `chaos_lace_criteria` | 187 | 静态清单：无直接出口，不计验收 |
| `_find_and_buff_trap_targets` | 197 | 静态清单：无直接出口，不计验收 |
| `held_status` | 259 | 静态清单：无直接出口，不计验收 |
| `find_golubria_on_level` | 269 | 静态清单：无直接出口，不计验收 |
| `_find_other_passage_side` | 288 | 静态清单：无直接出口，不计验收 |
| `_zot_trap` | 346 | 可见入口待迁移 |
| `trap_def::trigger` | 352 | 部分迁移/父函数未完成 |
| `destroy_trap` | 773 | 静态清单：无直接出口，不计验收 |
| `trap_at` | 779 | 静态清单：无直接出口，不计验收 |
| `get_trap_type` | 792 | 静态清单：无直接出口，不计验收 |
| `trap_def::feature` | 800 | 静态清单：无直接出口，不计验收 |
| `trap_feature` | 805 | 静态清单：无直接出口，不计验收 |
| `trap_type_from_feature` | 858 | 静态清单：无直接出口，不计验收 |
| `is_valid_shaft_level` | 901 | 静态清单：无直接出口，不计验收 |
| `_shafted_in` | 922 | 静态清单：无直接出口，不计验收 |
| `set_shafted` | 928 | 静态清单：无直接出口，不计验收 |
| `_is_valid_shaft_effect_level` | 938 | 静态清单：无直接出口，不计验收 |
| `roll_trap_effects` | 954 | 静态清单：无直接出口，不计验收 |
| `_malev_msg` | 963 | 静态清单：无直接出口，不计验收 |
| `_print_malev` | 969 | 可见入口待迁移 |
| `do_trap_effects` | 978 | 可见入口待迁移 |
| `generic_shaft_dest` | 1059 | 静态清单：无直接出口，不计验收 |
| `trap_rate_for_place` | 1105 | 静态清单：无直接出口，不计验收 |
| `random_trap_for_place` | 1130 | 静态清单：无直接出口，不计验收 |
| `place_webs` | 1177 | 静态清单：无直接出口，不计验收 |
| `player::trap_in_web` | 1225 | 本批迁移并回归 |
| `monster::trap_in_web` | 1240 | 可见入口待迁移 |
| `player::trap_in_net` | 1251 | 本批迁移并回归 |
| `monster::trap_in_net` | 1278 | 可见入口待迁移 |
| `player::struggle_against_net` | 1314 | 本批迁移并回归 |
| `player::stop_being_caught` | 1350 | 静态清单：无直接出口，不计验收 |
| `is_regular_trap` | 1376 | 静态清单：无直接出口，不计验收 |
| `is_removed_trap` | 1387 | 静态清单：无直接出口，不计验收 |

### travel.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `deviant_route_warning::new_dest` | 172 | 本批迁移并回归 |
| `deviant_route_warning::warn_continue_travel` | 182 | 本批迁移并回归 |
| `is_trap` | 213 | 静态清单：无直接出口，不计验收 |
| `_is_safe_cloud` | 218 | 静态清单：无直接出口，不计验收 |
| `_feature_traverse_cost` | 231 | 静态清单：无直接出口，不计验收 |
| `is_unknown_stair` | 248 | 静态清单：无直接出口，不计验收 |
| `is_unknown_transporter` | 263 | 静态清单：无直接出口，不计验收 |
| `feat_is_traversable_now` | 272 | 静态清单：无直接出口，不计验收 |
| `feat_is_traversable` | 314 | 静态清单：无直接出口，不计验收 |
| `is_waypoint` | 346 | 静态清单：无直接出口，不计验收 |
| `is_stash` | 351 | 静态清单：无直接出口，不计验收 |
| `_monster_blocks_travel` | 356 | 静态清单：无直接出口，不计验收 |
| `_feat_is_blocking_door` | 365 | 静态清单：无直接出口，不计验收 |
| `_feat_is_blocking_door_strict` | 379 | 静态清单：无直接出口，不计验收 |
| `_is_reseedable` | 408 | 静态清单：无直接出口，不计验收 |
| `is_stair_exclusion` | 472 | 静态清单：无直接出口，不计验收 |
| `is_travelsafe_square` | 484 | 静态清单：无直接出口，不计验收 |
| `_is_safe_move` | 557 | 静态清单：无直接出口，不计验收 |
| `travel_init_load_level` | 578 | 静态清单：无直接出口，不计验收 |
| `travel_init_new_level` | 586 | 静态清单：无直接出口，不计验收 |
| `_is_branch_stair` | 599 | 静态清单：无直接出口，不计验收 |
| `_check_interesting_square` | 622 | 静态清单：无直接出口，不计验收 |
| `_userdef_run_stoprunning_hook` | 634 | 静态清单：无直接出口，不计验收 |
| `_userdef_run_startrunning_hook` | 640 | 静态清单：无直接出口，不计验收 |
| `is_resting` | 646 | 静态清单：无直接出口，不计验收 |
| `_start_running` | 651 | 静态清单：无直接出口，不计验收 |
| `stop_running` | 664 | 静态清单：无直接出口，不计验收 |
| `_is_valid_explore_target` | 669 | 静态清单：无直接出口，不计验收 |
| `_level_has_unknown_transporters` | 697 | 静态清单：无直接出口，不计验收 |
| `_set_target_square` | 711 | 静态清单：无直接出口，不计验收 |
| `_explore_find_target_square` | 716 | 部分迁移/父函数未完成 |
| `explore_pickup_event` | 820 | 可见入口待迁移 |
| `_find_travel_pos` | 930 | 可见入口待迁移 |
| `_get_non_move_command` | 1013 | 静态清单：无直接出口，不计验收 |
| `travel` | 1057 | 可见入口待迁移 |
| `direction_to_command` | 1273 | 静态清单：无直接出口，不计验收 |
| `_fill_exclude_radius` | 1288 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::travel_pathfind` | 1315 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::~travel_pathfind` | 1327 | 静态清单：无直接出口，不计验收 |
| `_is_greed_inducing_square` | 1331 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::is_greed_inducing_square` | 1337 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::set_src_dst` | 1342 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::set_floodseed` | 1352 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::set_feature_vector` | 1361 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::explore_target` | 1372 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::pathfind` | 1389 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::get_features` | 1575 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::square_slows_movement` | 1613 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::check_square_greed` | 1642 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::path_flood` | 1665 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::good_square` | 1878 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::point_traverse_delay` | 1888 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::path_examine_point` | 1904 | 静态清单：无直接出口，不计验收 |
| `travel_pathfind::explore_status` | 1973 | 静态清单：无直接出口，不计验收 |
| `fill_travel_point_distance` | 1996 | 静态清单：无直接出口，不计验收 |
| `_find_parent_branch` | 2012 | 静态清单：无直接出口，不计验收 |
| `_trackback` | 2047 | 静态清单：无直接出口，不计验收 |
| `_track_intersect` | 2066 | 静态清单：无直接出口，不计验收 |
| `level_distance` | 2093 | 静态清单：无直接出口，不计验收 |
| `_get_trans_travel_dest` | 2144 | 静态清单：无直接出口，不计验收 |
| `_get_nearest_level_depth` | 2172 | 静态清单：无直接出口，不计验收 |
| `is_known_branch_id` | 2201 | 静态清单：无直接出口，不计验收 |
| `_is_known_branch` | 2225 | 静态清单：无直接出口，不计验收 |
| `_get_branches` | 2232 | 静态清单：无直接出口，不计验收 |
| `_is_valid_branch` | 2243 | 静态清单：无直接出口，不计验收 |
| `find_up_level` | 2599 | 静态清单：无直接出口，不计验收 |
| `_find_up_level` | 2623 | 静态清单：无直接出口，不计验收 |
| `find_down_level` | 2628 | 静态清单：无直接出口，不计验收 |
| `find_deepest_explored` | 2635 | 静态清单：无直接出口，不计验收 |
| `branch_entered` | 2656 | 静态清单：无直接出口，不计验收 |
| `_find_down_level` | 2663 | 静态清单：无直接出口，不计验收 |
| `_travel_depth_keyfilter` | 2668 | 静态清单：无直接出口，不计验收 |
| `_find_entrance` | 2683 | 静态清单：无直接出口，不计验收 |
| `_parse_travel_target` | 2735 | 静态清单：无直接出口，不计验收 |
| `_travel_depth_munge` | 2767 | 静态清单：无直接出口，不计验收 |
| `_prompt_travel_depth` | 2801 | 可见入口待迁移 |
| `prompt_translevel_target` | 2846 | 静态清单：无直接出口，不计验收 |
| `_start_translevel_travel` | 2917 | 部分迁移/父函数未完成 |
| `start_translevel_travel` | 2960 | 部分迁移/父函数未完成 |
| `_start_translevel_travel_prompt` | 3023 | 可见入口待迁移 |
| `_target_distance_from` | 3040 | 静态清单：无直接出口，不计验收 |
| `_find_transtravel_stair` | 3066 | 静态清单：无直接出口，不计验收 |
| `_loadlev_populate_stair_distances` | 3280 | 静态清单：无直接出口，不计验收 |
| `_populate_stair_distances` | 3288 | 静态清单：无直接出口，不计验收 |
| `_find_closest_adj` | 3307 | 静态清单：无直接出口，不计验收 |
| `_find_transtravel_square` | 3323 | 部分迁移/父函数未完成 |
| `start_travel` | 3422 | 可见入口待迁移 |
| `start_explore` | 3460 | 本批迁移并回归 |
| `do_explore_cmd` | 3485 | 本批迁移并回归 |
| `level_id::current` | 3496 | 静态清单：无直接出口，不计验收 |
| `level_id::absdepth` | 3502 | 静态清单：无直接出口，不计验收 |
| `level_id::get_next_level_id` | 3507 | 静态清单：无直接出口，不计验收 |
| `level_id::describe` | 3548 | 静态清单：无直接出口，不计验收 |
| `level_id::parse_level_id` | 3571 | 静态清单：无直接出口，不计验收 |
| `level_id::save` | 3600 | 静态清单：无直接出口，不计验收 |
| `level_id::load` | 3605 | 静态清单：无直接出口，不计验收 |
| `level_pos::current` | 3610 | 静态清单：无直接出口，不计验收 |
| `level_pos::save` | 3616 | 静态清单：无直接出口，不计验收 |
| `level_pos::load` | 3622 | 静态清单：无直接出口，不计验收 |
| `transporter_info::save` | 3628 | 静态清单：无直接出口，不计验收 |
| `stair_info::save` | 3635 | 静态清单：无直接出口，不计验收 |
| `transporter_info::load` | 3644 | 静态清单：无直接出口，不计验收 |
| `stair_info::load` | 3651 | 静态清单：无直接出口，不计验收 |
| `stair_info::describe` | 3660 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::set_level_excludes` | 3676 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::empty` | 3682 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::update_excludes` | 3687 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::update` | 3692 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::set_distance_between_stairs` | 3720 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::update_stair_distances` | 3730 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::update_transporter` | 3756 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::update_stair` | 3767 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::create_placeholder_stair` | 3805 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::sync_all_branch_stairs` | 3826 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::sync_branch_stairs` | 3841 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::clear_stairs` | 3854 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::know_transporter` | 3868 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::know_stair` | 3877 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::get_transporter_index` | 3899 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::get_stair_index` | 3908 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::correct_stair_list` | 3917 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::correct_transporter_list` | 3986 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::resize_stair_distances` | 4029 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::distance_between` | 4036 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::get_transporters` | 4052 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::get_stairs` | 4067 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::clear_distances` | 4082 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::is_known_branch` | 4088 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::save` | 4097 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::load` | 4130 | 静态清单：无直接出口，不计验收 |
| `LevelInfo::fixup` | 4181 | 静态清单：无直接出口，不计验收 |
| `TravelCache::update_stone_stair` | 4197 | 静态清单：无直接出口，不计验收 |
| `TravelCache::update_transporter` | 4241 | 静态清单：无直接出口，不计验收 |
| `TravelCache::know_transporter` | 4261 | 静态清单：无直接出口，不计验收 |
| `TravelCache::know_stair` | 4269 | 静态清单：无直接出口，不计验收 |
| `TravelCache::get_waypoint_descs` | 4277 | 静态清单：无直接出口，不计验收 |
| `TravelCache::list_waypoints` | 4292 | 可见入口待迁移 |
| `TravelCache::is_waypoint` | 4312 | 静态清单：无直接出口，不计验收 |
| `TravelCache::flush_invalid_waypoints` | 4321 | 静态清单：无直接出口，不计验收 |
| `TravelCache::update_waypoints` | 4331 | 静态清单：无直接出口，不计验收 |
| `TravelCache::delete_waypoint` | 4346 | 部分迁移/父函数未完成 |
| `TravelCache::add_waypoint` | 4385 | 部分迁移/父函数未完成 |
| `TravelCache::set_waypoint` | 4421 | 可见入口待迁移 |
| `_is_valid_waypoint_pos` | 4457 | 静态清单：无直接出口，不计验收 |
| `TravelCache::is_valid_waypoint` | 4465 | 静态清单：无直接出口，不计验收 |
| `TravelCache::get_waypoint_count` | 4472 | 静态清单：无直接出口，不计验收 |
| `TravelCache::clear_distances` | 4482 | 静态清单：无直接出口，不计验收 |
| `TravelCache::is_known_branch` | 4488 | 静态清单：无直接出口，不计验收 |
| `TravelCache::save` | 4495 | 静态清单：无直接出口，不计验收 |
| `TravelCache::load` | 4512 | 静态清单：无直接出口，不计验收 |
| `TravelCache::set_level_excludes` | 4555 | 静态清单：无直接出口，不计验收 |
| `TravelCache::update_excludes` | 4560 | 静态清单：无直接出口，不计验收 |
| `TravelCache::update` | 4565 | 静态清单：无直接出口，不计验收 |
| `TravelCache::update_daction_counters` | 4570 | 静态清单：无直接出口，不计验收 |
| `TravelCache::query_daction_counter` | 4575 | 静态清单：无直接出口，不计验收 |
| `TravelCache::clear_daction_counter` | 4588 | 静态清单：无直接出口，不计验收 |
| `TravelCache::fixup_levels` | 4594 | 静态清单：无直接出口，不计验收 |
| `TravelCache::known_levels` | 4600 | 静态清单：无直接出口，不计验收 |
| `can_travel_to` | 4610 | 静态清单：无直接出口，不计验收 |
| `can_travel_interlevel` | 4616 | 静态清单：无直接出口，不计验收 |
| `runrest::runrest` | 4624 | 静态清单：无直接出口，不计验收 |
| `runrest::initialise` | 4631 | 静态清单：无直接出口，不计验收 |
| `int` | 4671 | 静态清单：无直接出口，不计验收 |
| `_base_feat_type` | 4682 | 静态清单：无直接出口，不计验收 |
| `runrest::set_run_check` | 4691 | 静态清单：无直接出口，不计验收 |
| `runrest::check_stop_running` | 4699 | 静态清单：无直接出口，不计验收 |
| `runrest::run_should_stop` | 4711 | 可见入口待迁移 |
| `runrest::diag_run_passes_door` | 4753 | 静态清单：无直接出口，不计验收 |
| `runrest::stop` | 4769 | 静态清单：无直接出口，不计验收 |
| `runrest::is_rest` | 4791 | 静态清单：无直接出口，不计验收 |
| `runrest::is_explore` | 4796 | 静态清单：无直接出口，不计验收 |
| `runrest::is_any_travel` | 4801 | 静态清单：无直接出口，不计验收 |
| `runrest::runmode_name` | 4815 | 静态清单：无直接出口，不计验收 |
| `runrest::rest` | 4832 | 静态清单：无直接出口，不计验收 |
| `runrest::clear` | 4839 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::explore_discoveries` | 4854 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::cleaned_feature_description` | 4862 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::merge_feature` | 4876 | 静态清单：无直接出口，不计验收 |
| `_feat_is_branchlike` | 4890 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::found_feature` | 4899 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::add_stair` | 5009 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::add_item` | 5022 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::found_item` | 5057 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::has_duplicates` | 5097 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::say_any` | 5110 | 可见入口待迁移 |
| `explore_discoveries::apply_quantities` | 5137 | 静态清单：无直接出口，不计验收 |
| `explore_discoveries::stop_explore` | 5161 | 可见入口待迁移 |
| `do_interlevel_travel` | 5186 | 部分迁移/父函数未完成 |
| `_adjacent_cmd` | 5227 | 静态清单：无直接出口，不计验收 |
| `click_travel_safe` | 5247 | 静态清单：无直接出口，不计验收 |
| `click_travel` | 5254 | 静态清单：无直接出口，不计验收 |
| `check_for_interesting_features` | 5292 | 静态清单：无直接出口，不计验收 |
| `clear_level_target` | 5322 | 静态清单：无直接出口，不计验收 |
| `clear_travel_trail` | 5328 | 静态清单：无直接出口，不计验收 |
| `travel_trail_index` | 5337 | 静态清单：无直接出口，不计验收 |
| `stairs_destination_is_excluded` | 5347 | 静态清单：无直接出口，不计验收 |

### abyss.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `_place_feature_near` | 85 | 静态清单：无直接出口，不计验收 |
| `_abyss_proto_feature` | 115 | 静态清单：无直接出口，不计验收 |
| `_write_abyssal_features` | 124 | 静态清单：无直接出口，不计验收 |
| `_abyssal_rune_roll` | 172 | 静态清单：无直接出口，不计验收 |
| `_abyss_fixup_vault` | 181 | 静态清单：无直接出口，不计验收 |
| `_abyss_place_map` | 199 | 静态清单：无直接出口，不计验收 |
| `_abyss_place_vault_tagged` | 223 | 静态清单：无直接出口，不计验收 |
| `_abyss_postvault_fixup` | 235 | 静态清单：无直接出口，不计验收 |
| `_sync_rune_knowledge` | 245 | 静态清单：无直接出口，不计验收 |
| `clear_abyssal_rune_knowledge` | 280 | 可见入口待迁移 |
| `_update_abyssal_map_knowledge` | 288 | 可见入口待迁移 |
| `_abyss_place_rune_vault` | 343 | 静态清单：无直接出口，不计验收 |
| `_abyss_place_rune` | 356 | 静态清单：无直接出口，不计验收 |
| `_who_banished` | 393 | 静态清单：无直接出口，不计验收 |
| `banished` | 398 | 可见入口待迁移 |
| `check_banished` | 439 | 可见入口待迁移 |
| `push_features_to_abyss` | 457 | 静态清单：无直接出口，不计验收 |
| `_abyss_check_place_feat` | 478 | 静态清单：无直接出口，不计验收 |
| `_abyss_pick_altar` | 530 | 静态清单：无直接出口，不计验收 |
| `_abyssal_rune_at` | 547 | 静态清单：无直接出口，不计验收 |
| `_abyss_lose_monster` | 610 | 可见入口待迁移 |
| `_abyss_move_sanctuary` | 630 | 静态清单：无直接出口，不计验收 |
| `_push_displaced_monster` | 645 | 静态清单：无直接出口，不计验收 |
| `_place_displaced_monsters` | 650 | 可见入口待迁移 |
| `_pushy_feature` | 671 | 静态清单：无直接出口，不计验收 |
| `_push_items` | 683 | 静态清单：无直接出口，不计验收 |
| `_abyss_wipe_square_at` | 731 | 静态清单：无直接出口，不计验收 |
| `_abyss_wipe_unmasked_area` | 789 | 静态清单：无直接出口，不计验收 |
| `_abyss_move_entities_at` | 797 | 静态清单：无直接出口，不计验收 |
| `_abyss_move_masked_vaults_by_delta` | 803 | 静态清单：无直接出口，不计验收 |
| `_abyss_update_transporter` | 838 | 静态清单：无直接出口，不计验收 |
| `_abyss_move_entities` | 870 | 静态清单：无直接出口，不计验收 |
| `_abyss_expand_mask_to_cover_vault` | 927 | 静态清单：无直接出口，不计验收 |
| `_abyss_identify_area_to_shift` | 939 | 静态清单：无直接出口，不计验收 |
| `_abyss_shift_level_contents_around_player` | 985 | 静态清单：无直接出口，不计验收 |
| `_abyss_generate_monsters` | 1030 | 静态清单：无直接出口，不计验收 |
| `maybe_shift_abyss_around_player` | 1047 | 静态清单：无直接出口，不计验收 |
| `save_abyss_uniques` | 1076 | 静态清单：无直接出口，不计验收 |
| `_in_wastes` | 1086 | 静态清单：无直接出口，不计验收 |
| `_get_random_level` | 1091 | 静态清单：无直接出口，不计验收 |
| `_abyss_grid` | 1153 | 静态清单：无直接出口，不计验收 |
| `_cloud_from_feat` | 1185 | 静态清单：无直接出口，不计验收 |
| `_veto_dangerous_terrain` | 1224 | 静态清单：无直接出口，不计验收 |
| `_update_abyss_terrain` | 1236 | 静态清单：无直接出口，不计验收 |
| `_destroy_all_terrain` | 1311 | 静态清单：无直接出口，不计验收 |
| `_ensure_player_habitable` | 1321 | 静态清单：无直接出口，不计验收 |
| `_abyss_apply_terrain` | 1339 | 静态清单：无直接出口，不计验收 |
| `_abyss_place_vaults` | 1409 | 静态清单：无直接出口，不计验收 |
| `_generate_area` | 1462 | 静态清单：无直接出口，不计验收 |
| `_initialize_abyss_state` | 1488 | 静态清单：无直接出口，不计验收 |
| `set_abyss_state` | 1500 | 静态清单：无直接出口，不计验收 |
| `abyss_area_shift` | 1513 | 静态清单：无直接出口，不计验收 |
| `destroy_abyss` | 1562 | 静态清单：无直接出口，不计验收 |
| `_roll_abyss_floor_colour` | 1573 | 静态清单：无直接出口，不计验收 |
| `_roll_abyss_rock_colour` | 1594 | 静态清单：无直接出口，不计验收 |
| `_abyss_generate_new_area` | 1615 | 静态清单：无直接出口，不计验收 |
| `generate_abyss` | 1646 | 静态清单：无直接出口，不计验收 |
| `_increase_depth` | 1682 | 静态清单：无直接出口，不计验收 |
| `abyss_morph` | 1697 | 静态清单：无直接出口，不计验收 |
| `abyss_default_depth` | 1723 | 静态清单：无直接出口，不计验收 |
| `_abyss_force_descent` | 1745 | 静态清单：无直接出口，不计验收 |
| `abyss_teleport` | 1759 | 可见入口待迁移 |
| `_place_corruption_seed` | 1811 | 静态清单：无直接出口，不计验收 |
| `_initialise_level_corrupt_seeds` | 1819 | 静态清单：无直接出口，不计验收 |
| `_incorruptible` | 1849 | 静态清单：无直接出口，不计验收 |
| `_spawn_corrupted_servant_near` | 1860 | 静态清单：无直接出口，不计验收 |
| `_spawn_corrupted_servant_near_monster` | 1892 | 静态清单：无直接出口，不计验收 |
| `_apply_corruption_effect` | 1916 | 静态清单：无直接出口，不计验收 |
| `run_corruption_effects` | 1938 | 静态清单：无直接出口，不计验收 |
| `_is_grid_corruptible` | 1949 | 静态清单：无直接出口，不计验收 |
| `_is_crowded_square` | 1987 | 静态清单：无直接出口，不计验收 |
| `_is_sealed_square` | 2008 | 静态清单：无直接出口，不计验收 |
| `_recolour_wall` | 2017 | 静态清单：无直接出口，不计验收 |
| `_corrupt_square_flavor` | 2022 | 静态清单：无直接出口，不计验收 |
| `_corrupt_square` | 2075 | 静态清单：无直接出口，不计验收 |
| `_corrupt_square_monster` | 2135 | 静态清单：无直接出口，不计验收 |
| `_corrupt_level_features` | 2177 | 静态清单：无直接出口，不计验收 |
| `_corrupt_level_features_monster` | 2216 | 静态清单：无直接出口，不计验收 |
| `_is_level_corrupted` | 2260 | 静态清单：无直接出口，不计验收 |
| `is_level_incorruptible` | 2268 | 可见入口待迁移 |
| `is_level_incorruptible_monster` | 2280 | 静态清单：无直接出口，不计验收 |
| `_corrupt_choose_colours` | 2288 | 静态清单：无直接出口，不计验收 |
| `lugonu_corrupt_level` | 2307 | 可见入口待迁移 |
| `lugonu_corrupt_level_monster` | 2330 | 静态清单：无直接出口，不计验收 |
| `splash_corruption` | 2353 | 静态清单：无直接出口，不计验收 |
| `_cleanup_temp_terrain_at` | 2363 | 静态清单：无直接出口，不计验收 |
| `abyss_maybe_spawn_xp_exit` | 2375 | 可见入口待迁移 |

### terrain.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `actor_at` | 63 | 静态清单：无直接出口，不计验收 |
| `feat_is_malign_gateway_suitable` | 74 | 静态清单：无直接出口，不计验收 |
| `feat_is_wall` | 81 | 静态清单：无直接出口，不计验收 |
| `feat_is_stone_stair_down` | 88 | 静态清单：无直接出口，不计验收 |
| `feat_is_stone_stair_up` | 97 | 静态清单：无直接出口，不计验收 |
| `feat_is_stone_stair` | 106 | 静态清单：无直接出口，不计验收 |
| `feat_is_staircase` | 113 | 静态清单：无直接出口，不计验收 |
| `feat_is_hell_subbranch_exit` | 136 | 静态清单：无直接出口，不计验收 |
| `FEATFN_MEMOIZED` | 172 | 静态清单：无直接出口，不计验收 |
| `FEATFN_MEMOIZED` | 188 | 静态清单：无直接出口，不计验收 |
| `FEATFN_MEMOIZED` | 204 | 静态清单：无直接出口，不计验收 |
| `FEATFN_MEMOIZED` | 230 | 静态清单：无直接出口，不计验收 |
| `feat_is_portal` | 253 | 静态清单：无直接出口，不计验收 |
| `feat_is_stair` | 262 | 静态清单：无直接出口，不计验收 |
| `feat_is_travelable_stair` | 269 | 静态清单：无直接出口，不计验收 |
| `feat_is_escape_hatch` | 279 | 静态清单：无直接出口，不计验收 |
| `feat_is_gate` | 288 | 静态清单：无直接出口，不计验收 |
| `feat_stair_direction` | 328 | 静态清单：无直接出口，不计验收 |
| `feat_is_opaque` | 375 | 静态清单：无直接出口，不计验收 |
| `feat_is_solid` | 382 | 静态清单：无直接出口，不计验收 |
| `feat_can_wall_jump_against` | 389 | 静态清单：无直接出口，不计验收 |
| `cell_is_solid` | 400 | 静态清单：无直接出口，不计验收 |
| `cell_is_invalid_target` | 407 | 静态清单：无直接出口，不计验收 |
| `feat_has_solid_floor` | 414 | 静态清单：无直接出口，不计验收 |
| `feat_has_dry_floor` | 422 | 静态清单：无直接出口，不计验收 |
| `feat_is_door` | 429 | 静态清单：无直接出口，不计验收 |
| `feat_is_closed_door` | 436 | 静态清单：无直接出口，不计验收 |
| `feat_is_open_door` | 447 | 静态清单：无直接出口，不计验收 |
| `feat_is_sealed` | 457 | 静态清单：无直接出口，不计验收 |
| `feat_is_runed` | 467 | 静态清单：无直接出口，不计验收 |
| `cell_is_runed` | 474 | 静态清单：无直接出口，不计验收 |
| `feat_is_statuelike` | 482 | 静态清单：无直接出口，不计验收 |
| `feat_is_permarock` | 492 | 静态清单：无直接出口，不计验收 |
| `feat_is_endless` | 499 | 静态清单：无直接出口，不计验收 |
| `feat_is_diggable` | 507 | 静态清单：无直接出口，不计验收 |
| `feat_is_trap` | 520 | 静态清单：无直接出口，不计验收 |
| `feat_is_deep_water` | 530 | 静态清单：无直接出口，不计验收 |
| `feat_is_shallow_water` | 538 | 静态清单：无直接出口，不计验收 |
| `feat_is_water` | 547 | 静态清单：无直接出口，不计验收 |
| `feat_is_lava` | 555 | 静态清单：无直接出口，不计验收 |
| `feat_altar_god` | 601 | 静态清单：无直接出口，不计验收 |
| `altar_for_god` | 615 | 静态清单：无直接出口，不计验收 |
| `FEATFN_MEMOIZED` | 626 | 静态清单：无直接出口，不计验收 |
| `feat_is_player_altar` | 636 | 静态清单：无直接出口，不计验收 |
| `feat_is_tree` | 643 | 静态清单：无直接出口，不计验收 |
| `feat_is_flammable` | 651 | 静态清单：无直接出口，不计验收 |
| `feat_is_metal` | 660 | 静态清单：无直接出口，不计验收 |
| `feat_is_bidirectional_portal` | 667 | 静态清单：无直接出口，不计验收 |
| `feat_is_descent_exitable` | 681 | 静态清单：无直接出口，不计验收 |
| `feat_is_fountain` | 693 | 静态清单：无直接出口，不计验收 |
| `feat_is_food` | 704 | 静态清单：无直接出口，不计验收 |
| `feat_is_reachable_past` | 713 | 静态清单：无直接出口，不计验收 |
| `FEATFN_MEMOIZED` | 726 | 静态清单：无直接出口，不计验收 |
| `feat_is_valid_border` | 737 | 静态清单：无直接出口，不计验收 |
| `feat_is_mimicable` | 753 | 静态清单：无直接出口，不计验收 |
| `feat_is_shaftable` | 776 | 静态清单：无直接出口，不计验收 |
| `count_neighbours_with_func` | 783 | 静态清单：无直接出口，不计验收 |
| `_find_connected_identical` | 795 | 静态清单：无直接出口，不计验收 |
| `find_connected_identical` | 822 | 静态清单：无直接出口，不计验收 |
| `get_door_description` | 832 | 静态清单：无直接出口，不计验收 |
| `_precompute_slime_wall_neighbours` | 852 | 静态清单：无直接出口，不计验收 |
| `unwind_slime_wall_precomputer::unwind_slime_wall_precomputer` | 865 | 静态清单：无直接出口，不计验收 |
| `unwind_slime_wall_precomputer::~unwind_slime_wall_precomputer` | 880 | 静态清单：无直接出口，不计验收 |
| `slime_wall_neighbour` | 886 | 静态清单：无直接出口，不计验收 |
| `count_adjacent_slime_walls` | 902 | 静态清单：无直接出口，不计验收 |
| `slime_wall_corrosion` | 912 | 静态清单：无直接出口，不计验收 |
| `slime_wall_damage` | 923 | 可见入口待迁移 |
| `count_adjacent_icy_walls` | 948 | 静态清单：无直接出口，不计验收 |
| `near_visible_wall` | 959 | 静态清单：无直接出口，不计验收 |
| `feat_splash_noise` | 972 | 可见入口待迁移 |
| `FEATFN_MEMOIZED` | 993 | 静态清单：无直接出口，不计验收 |
| `feat_destroys_items` | 1017 | 静态清单：无直接出口，不计验收 |
| `feat_eliminates_items` | 1024 | 静态清单：无直接出口，不计验收 |
| `_dgn_find_nearest_square` | 1033 | 静态清单：无直接出口，不计验收 |
| `_item_safe_square` | 1076 | 静态清单：无直接出口，不计验收 |
| `_item_traversable_square` | 1084 | 静态清单：无直接出口，不计验收 |
| `_item_visible_square` | 1089 | 静态清单：无直接出口，不计验收 |
| `_dgn_shift_item` | 1095 | 静态清单：无直接出口，不计验收 |
| `_is_feature_shift_target` | 1117 | 静态清单：无直接出口，不计验收 |
| `dgn_move_entities_at` | 1138 | 静态清单：无直接出口，不计验收 |
| `_dgn_shift_feature` | 1229 | 静态清单：无直接出口，不计验收 |
| `dgn_check_terrain_items` | 1242 | 静态清单：无直接出口，不计验收 |
| `_dgn_check_terrain_monsters` | 1268 | 静态清单：无直接出口，不计验收 |
| `_dgn_check_terrain_covering` | 1277 | 静态清单：无直接出口，不计验收 |
| `_dgn_check_terrain_player` | 1302 | 静态清单：无直接出口，不计验收 |
| `_current_terrain_changed` | 1316 | 静态清单：无直接出口，不计验收 |
| `_permanent_terrain_changed` | 1375 | 静态清单：无直接出口，不计验收 |
| `dungeon_terrain_changed` | 1397 | 静态清单：无直接出口，不计验收 |
| `dungeon_change_base_terrain` | 1411 | 静态清单：无直接出口，不计验收 |
| `_announce_swap_real` | 1432 | 可见入口待迁移 |
| `_announce_swap` | 1485 | 静态清单：无直接出口，不计验收 |
| `swap_features` | 1514 | 可见入口待迁移 |
| `_ok_dest_cell` | 1719 | 静态清单：无直接出口，不计验收 |
| `slide_feature_over` | 1744 | 静态清单：无直接出口，不计验收 |
| `fall_into_a_pool` | 1783 | 可见入口待迁移 |
| `init_feat_desc_cache` | 1802 | 静态清单：无直接出口，不计验收 |
| `feat_by_desc` | 1815 | 静态清单：无直接出口，不计验收 |
| `feat_preposition` | 1833 | 静态清单：无直接出口，不计验收 |
| `stair_climb_verb` | 1896 | 静态清单：无直接出口，不计验收 |
| `dungeon_feature_by_name` | 1915 | 静态清单：无直接出口，不计验收 |
| `dungeon_feature_matches` | 1948 | 静态清单：无直接出口，不计验收 |
| `destroy_wall` | 1984 | 静态清单：无直接出口，不计验收 |
| `feat_type_name` | 1998 | 静态清单：无直接出口，不计验收 |
| `set_terrain_changed` | 2035 | 静态清单：无直接出口，不计验收 |
| `cell_triggers_conduct` | 2078 | 静态清单：无直接出口，不计验收 |
| `is_boring_terrain` | 2086 | 静态清单：无直接出口，不计验收 |
| `orig_terrain` | 2114 | 静态清单：无直接出口，不计验收 |
| `orig_terrain_no_mimic` | 2127 | 静态清单：无直接出口，不计验收 |
| `temp_change_terrain` | 2134 | 静态清单：无直接出口，不计验收 |
| `_revert_terrain_to` | 2199 | 静态清单：无直接出口，不计验收 |
| `revert_terrain_change` | 2258 | 静态清单：无直接出口，不计验收 |
| `is_temp_terrain` | 2312 | 静态清单：无直接出口，不计验收 |
| `plant_forbidden_at` | 2321 | 静态清单：无直接出口，不计验收 |
| `get_push_spaces` | 2386 | 静态清单：无直接出口，不计验收 |
| `has_push_spaces` | 2450 | 静态清单：无直接出口，不计验收 |
| `push_items_from` | 2465 | 静态清单：无直接出口，不计验收 |
| `push_actor_from` | 2488 | 静态清单：无直接出口，不计验收 |
| `push_or_teleport_actor_from` | 2516 | 静态清单：无直接出口，不计验收 |
| `dgn_close_door` | 2547 | 静态清单：无直接出口，不计验收 |
| `dgn_open_door` | 2565 | 静态清单：无直接出口，不计验收 |
| `dgn_break_door` | 2584 | 静态清单：无直接出口，不计验收 |
| `ice_wall_damage` | 2599 | 可见入口待迁移 |
| `frigid_walls_damage` | 2638 | 可见入口待迁移 |
| `_feat_is_descent_upstairs` | 2682 | 静态清单：无直接出口，不计验收 |
| `descent_crumble_stairs` | 2694 | 可见入口待迁移 |
| `_descent_reveal_around` | 2719 | 静态清单：无直接出口，不计验收 |
| `descent_reveal_stairs` | 2740 | 静态清单：无直接出口，不计验收 |
| `feat_at_no_mimic` | 2751 | 静态清单：无直接出口，不计验收 |

### exclude.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `_mon_needs_auto_exclude` | 34 | 静态清单：无直接出口，不计验收 |
| `_need_auto_exclude` | 56 | 静态清单：无直接出口，不计验收 |
| `_get_full_exclusion_radius` | 80 | 静态清单：无直接出口，不计验收 |
| `add_auto_excludes` | 90 | 可见入口待迁移 |
| `travel_exclude::travel_exclude` | 127 | 静态清单：无直接出口，不计验收 |
| `travel_exclude::travel_exclude` | 147 | 静态清单：无直接出口，不计验收 |
| `travel_exclude::set_los` | 156 | 静态清单：无直接出口，不计验收 |
| `travel_exclude::affects` | 167 | 可见入口待迁移 |
| `travel_exclude::in_bounds` | 182 | 静态清单：无直接出口，不计验收 |
| `exclude_set::exclude_set` | 191 | 静态清单：无直接出口，不计验收 |
| `exclude_set::clear` | 195 | 静态清单：无直接出口，不计验收 |
| `exclude_set::erase` | 201 | 静态清单：无直接出口，不计验收 |
| `exclude_set::add_exclude` | 214 | 静态清单：无直接出口，不计验收 |
| `exclude_set::add_exclude` | 220 | 静态清单：无直接出口，不计验收 |
| `exclude_set::add_exclude_points` | 228 | 静态清单：无直接出口，不计验收 |
| `exclude_set::update_excluded_points` | 246 | 静态清单：无直接出口，不计验收 |
| `exclude_set::recompute_excluded_points` | 259 | 静态清单：无直接出口，不计验收 |
| `exclude_set::is_excluded` | 271 | 静态清单：无直接出口，不计验收 |
| `exclude_set::is_exclude_root` | 276 | 静态清单：无直接出口，不计验收 |
| `exclude_set::get_exclude_root` | 281 | 静态清单：无直接出口，不计验收 |
| `exclude_set::size` | 286 | 静态清单：无直接出口，不计验收 |
| `exclude_set::empty` | 291 | 静态清单：无直接出口，不计验收 |
| `exclude_set::begin` | 296 | 静态清单：无直接出口，不计验收 |
| `exclude_set::end` | 301 | 静态清单：无直接出口，不计验收 |
| `exclude_set::begin` | 306 | 静态清单：无直接出口，不计验收 |
| `exclude_set::end` | 311 | 静态清单：无直接出口，不计验收 |
| `_mark_excludes_non_updated` | 318 | 静态清单：无直接出口，不计验收 |
| `init_exclusion_los` | 327 | 静态清单：无直接出口，不计验收 |
| `_is_gate_that_spreads_exclusion` | 332 | 静态清单：无直接出口，不计验收 |
| `_exclude_gate` | 352 | 静态清单：无直接出口，不计验收 |
| `_update_gate_exclusions` | 365 | 静态清单：无直接出口，不计验收 |
| `update_exclusion_los` | 394 | 静态清单：无直接出口，不计验收 |
| `is_excluded` | 408 | 静态清单：无直接出口，不计验收 |
| `is_exclude_root` | 413 | 静态清单：无直接出口，不计验收 |
| `get_exclusion_radius` | 418 | 静态清单：无直接出口，不计验收 |
| `get_exclusion_desc` | 430 | 静态清单：无直接出口，不计验收 |
| `_tile_exclude_gmap_update` | 439 | 静态清单：无直接出口，不计验收 |
| `_exclude_update` | 450 | 静态清单：无直接出口，不计验收 |
| `_exclude_update` | 456 | 静态清单：无直接出口，不计验收 |
| `deferred_exclude_update` | 471 | 静态清单：无直接出口，不计验收 |
| `clear_excludes` | 480 | 静态清单：无直接出口，不计验收 |
| `cycle_exclude_radius` | 502 | 静态清单：无直接出口，不计验收 |
| `del_exclude` | 521 | 静态清单：无直接出口，不计验收 |
| `set_exclude` | 528 | 静态清单：无直接出口，不计验收 |
| `maybe_remove_autoexclusion` | 584 | 静态清单：无直接出口，不计验收 |
| `exclude_set::get_exclusion_desc` | 609 | 静态清单：无直接出口，不计验收 |
| `marshallExcludes` | 694 | 静态清单：无直接出口，不计验收 |
| `unmarshallExcludes` | 711 | 静态清单：无直接出口，不计验收 |

### orb.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `_orb_noise` | 32 | 静态清单：无直接出口，不计验收 |
| `orb_pickup_noise` | 60 | 可见入口待迁移 |
| `orb_limits_translocation` | 83 | 静态清单：无直接出口，不计验收 |
| `start_orb_run` | 89 | 可见入口待迁移 |

### nearby-danger.cc

| 函数 | 行 | 状态 |
| --- | ---: | --- |
| `mons_is_irrelevant` | 46 | 静态清单：无直接出口，不计验收 |
| `mons_is_always_safe` | 95 | 静态清单：无直接出口，不计验收 |
| `mons_is_safe` | 108 | 静态清单：无直接出口，不计验收 |
| `_seen_monsters_announcement` | 148 | 静态清单：无直接出口，不计验收 |
| `_announce_monsters` | 164 | 可见入口待迁移 |
| `get_nearby_monsters` | 193 | 静态清单：无直接出口，不计验收 |
| `i_feel_safe` | 242 | 静态清单：无直接出口，不计验收 |
| `can_rest_here` | 316 | 静态清单：无直接出口，不计验收 |
| `there_are_monsters_nearby` | 341 | 静态清单：无直接出口，不计验收 |
| `_monster_threat_values` | 351 | 静态清单：无直接出口，不计验收 |
| `player_in_a_dangerous_place` | 379 | 静态清单：无直接出口，不计验收 |
| `bring_to_safety` | 393 | 静态清单：无直接出口，不计验收 |
| `revive` | 444 | 可见入口待迁移 |


### main.cc（补验限域，不是全文件清单）

| 函数 | 范围与状态 |
| --- | --- |
| `_can_take_stairs` | 完整实际函数与基线等价回归；仅上/下/石拱/关闭商店四个显示出口迁移，其余部分待迁移 |
| `_take_stairs` | 实际调用顺序与拒绝早退静态断言；没有修改，不计整函数验收 |
