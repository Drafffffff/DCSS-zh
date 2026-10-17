# 迁移账本

本文由 modules.json 与真实源码调用清单生成。调用点是审查候选，不等于玩家可见文案或翻译完成率。

| 模块 | 当前边界 | 下一步 / 验收 |
|---|---|---|
| 接口与渲染 | 规范英文读取与旧匹配暂停已拆分；Mac自动测试及真实回放通过 | raw绘制不改变语言；Lua/存档仍规范英文；参数/标签/缺失校验通过 |
| 语义名称 | 物品/怪物/地点已有接口；已鉴定魔杖、普通书籍/手册/羊皮纸、杂项及充能状态按语义字段生成；自定义/神器/未鉴定复杂名仍整名回退 | 枚举/鉴定/数量/装备/专名组合测试；不解析最终英文名称 |
| 详情 | 主边界、物品/怪物/法术正文与共用限制已接入；法术反噬、选择菜单及目标附加效果本批已接入；其他复杂状态、瞄准怪物伤势/装备正文仍待迁移 | 数据库正文语言选择、长文本、动作、不同来源/状态逐项核对；禁止旧matcher |
| 技能 | 主面板/查阅菜单/详情/帮助/tile提示已接入；增强/削弱特殊状态仍待真实分支补验 | 主面板、?/k、条目、详情、帮助、训练/增强/削弱、tile提示全部走新链路 |
| 商店 | 菜单/确认/余额/购物清单主路径已接入，Mac严格回放通过；罕见命名回退仍登记 | 不同余额/数量/排序/颜色/键位/购买/空清单及名称回退 |
| HUD | 等级/地点/噪声/武器部分接入；其他字段未迁移 | 统一按字段语义接入；列宽/刷新/长短名/最大值；不能整体跳过旧层审计 |
| 战斗日志 | 战斗命中/失手及共用限制、反噬组合、变形进出已分批接入；本批施法增强/魔杖增强/误施法、四类引导提醒与终止及魔力不足日志接入；剩余战斗/法术/怪物日志待逐包验收 | 玩家/怪物/武器/状态/数值组合，全部成功失败分支保留英文控制数据 |
| 装备与物品操作 | 护符穿戴理由/万变护符/确认/延迟已接入；本批变形进出与装备模拟/脱落日志已接入，退休形态整句回退报告；其他物品穿脱/拾取仍待迁移 | 穿脱/挥舞/使用/失败/进度/中断完整消息；量词/所有格 |
| 瞄准、法术、能力、箭袋 | 目标理由闭环、施法日志及反噬已接入；本批完成瞄准帮助/顶部与动作前缀、箭袋选择/动作名称、法术菜单/风险确认/目标效果；目标怪物伤势装备正文、能力其他菜单与操作日志仍待迁移 | 坐标/距离/法术等级分离；目标名称和无效目标；父视图/箭袋提示也需迁移 |
| 神祇与角色 | 等级/技能成长部分接入；神祇/变异/状态/能力大量入口待迁移 | 每个实体、状态与等级语义分开；全流程日志/详情/菜单 |
| 世界与通用界面 | 拾取初见教程已接入；本批完成共用危险地形/云雾/陷阱/排除区/穿墙确认；其他教程、旅行、交互与通用菜单仍待迁移 | 静态/动态生产点完整接入；输入/程序标识不翻译 |
| 帮助与文档 | 已审校中文手册可复用；入口及标题仍需归一 | 选择正文语言；长文分页/标记/快捷键；无最终英文句匹配 |
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
剩余：directn怪物目标伤势/装备正文仍有3处旧详情依赖，前缀已独立生成；箭袋/能力其他业务操作日志、wizard地形构建标题未在本包验收；未审校新名称整行/整父回退并报告缺失，不拼凑中文。

### terrain-move-confirmation — verified

所属模块：世界与通用界面。
文件：`player.cc`、`player.h`、`spl-other.cc`、`prompt.cc`、`prompt.h`。
生产函数：`check_moveto_terrain`、`check_moveto_cloud`、`check_moveto_trap`、`check_moveto_exclusions`、`confirm_prompt`。
显示/业务消费者：`check_moveto`、`check_move_over`、`passwall_path::check_moveto`。
验证：`tools/test_terrain_confirmation.py`。
兼容规则：yesno/confirm_prompt保留Lua英文及yes输入；确认顺序/接受取消/危险判定/RNG不变；移除typed确认提示200字节截断。
验收记录：[verification/native/prompt-terrain/REPORT.md](../../verification/native/prompt-terrain/REPORT.md)。
剩余：未知未来移动动词/云雾/陷阱名称及任意调用方警告完整回退并报告；其他移动业务日志、旅行及世界交互不在共用确认包内。


## 公共旧入口

- `cio.cc:243` — `string buf = zh_translate(vmake_stringf(s, args));`
- `cio.cc:328` — `string buf = zh_translate(vmake_stringf(s, args));`
- `cio.cc:347` — `string buf = zh_translate(vmake_stringf(s, args));`
- `command.cc:629` — `line += ": " + zh_translate(untag_tiles_console(desc)) + "\n";`
- `command.cc:642` — `desc = zh_translate(desc);`
- `command.cc:652` — `desc = zh_translate(desc);`
- `command.cc:1145` — `text = zh_translate(text);`
- `directn.cc:1847` — `{prefix, zh_text("description", text, zh_translate(text))}), MSGCH_PROMPT);`
- `directn.cc:3647` — `desc = zh_translate(desc);`
- `directn.cc:3649` — `item_desc = zh_translate(item_desc);`
- `format.cc:99` — `return parse_string_raw(zh_translate(s), main_colour);`
- `format.cc:127` — `parse_string_to_multiple_raw(zh_translate(s), out, wrap_col);`
- `format.cc:331` — `ops.emplace_back(zh_translate(other));`
- `format.cc:604` — `ops.push_back(zh_translate(s));`
- `libgui.cc:99` — `const string localized = zh_translate(buffer);`
- `libunix.cc:935` — `const string localized = zh_translate(buffer);`
- `menu.cc:3619` — `vector<string> segs = split_string("\n", zh_translate(s), false, true);`
- `message.cc:93` — `? (localized.empty() ? zh_translate(text) : localized) : text) + rep;`
- `message.cc:640` — `if (!presentation) text = zh_translate(text);`
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
- `tilereg-doll.cc:116` — `minimum_cell = max(minimum_cell, (width(zh_translate(label)) + 1) / 2);`
- `tilereg-doll.cc:119` — `l.left = max(10 * l.cell, width(zh_translate("Doll index %d / %d")) + 6 * static_cast<int>(font->char_width()));`
- `tilereg-doll.cc:121` — `l.left = max(l.left, width(zh_translate("Doll Mode: %s")) + width(zh_translate(mode)));`
- `tilereg-doll.cc:121` — `l.left = max(l.left, width(zh_translate("Doll Mode: %s")) + width(zh_translate(mode)));`
- `tilereg-doll.cc:124` — `category_width = max(category_width, width(zh_translate(category)));`
- `tilereg-doll.cc:125` — `l.info = category_width + width(" -> : ") + max(width(zh_translate("(show equip)")), width("99999/99999"));`
- `tilereg-doll.cc:130` — `column_widths[col] = max(column_widths[col], width(col % 2 ? string(row[col]) : zh_translate(row[col])));`
- `tilereg-doll.cc:229` — `const string label = zh_translate(labels[i]);`
- `tilereg-doll.cc:288` — `string item_str = zh_translate(doll_categories[m_cat_idx]) + ": "`
- `tilereg-doll.cc:292` — `: zh_translate(part_name));`
- `tilereg-doll.cc:298` — `doll_name = make_stringf(zh_translate("Doll index %d / %d").c_str(), m_doll_idx, NUM_MAX_DOLLS - 1);`
- `tilereg-doll.cc:303` — `doll_name = make_stringf(zh_translate("Doll Mode: %s").c_str(),`
- `tilereg-doll.cc:304` — `zh_translate(doll_modes[m_mode]).c_str());`
- `tilereg-doll.cc:321` — `const string category = zh_translate(doll_categories[i]);`
- `tilereg-doll.cc:322` — `const string value = part == TILEP_SHOW_EQUIP ? zh_translate("(show equip)")`
- `tilereg-doll.cc:323` — `: !part ? zh_translate("(none)")`
- `tilereg-doll.cc:336` — `: zh_translate(doll_commands[row][col]), VColour::white,`
- `zh-localization.cc:479` — `std::string zh_translate(const std::string &text) {`

## 边界声明

规范英文读取使用 ZhTranslationPause；只阻止旧匹配的原样渲染使用 ZhLegacyPause。两种职责不可互换。
模块完成需覆盖主入口、选择、详情、帮助、悬停、成功/失败反馈及渲染出口；同文件有新接口不代表整个文件完成。
旧存档没有消息 ID 的历史兼容单列，不能据此保留新实时消息的旧匹配。
所有新增/修改游戏译文由 Luna 批量审校，主 agent 负责代码。Mac 为主调试平台；Linux 在里程碑验收。
