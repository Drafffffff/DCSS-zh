# 迁移账本

本文由 modules.json 与真实源码调用清单生成。调用点是审查候选，不等于玩家可见文案或翻译完成率。

| 模块 | 当前边界 | 下一步 / 验收 |
|---|---|---|
| 接口与渲染 | 规范英文读取与旧匹配暂停已拆分；Mac自动测试及真实回放通过 | raw绘制不改变语言；Lua/存档仍规范英文；参数/标签/缺失校验通过 |
| 语义名称 | 物品/怪物已有专用接口；新增地点及来源怪物类型接口；复杂名称仍有完整回退 | 枚举/鉴定/数量/装备/专名组合测试；不解析最终英文名称 |
| 详情 | 主边界、正常来源、紧凑法术列表、诅咒技能与护符形态表已迁移；hints及外部失败理由仍待迁移，复杂名称保留明确整段回退 | 数据库正文语言选择、长文本、动作、不同来源/状态逐项核对；禁止旧matcher |
| 技能 | 主面板/查阅菜单/详情/帮助/tile提示已接入；增强/削弱特殊状态仍待真实分支补验 | 主面板、?/k、条目、详情、帮助、训练/增强/削弱、tile提示全部走新链路 |
| 商店 | 菜单/确认/余额/购物清单主路径已接入，Mac严格回放通过；罕见命名回退仍登记 | 不同余额/数量/排序/颜色/键位/购买/空清单及名称回退 |
| HUD | 等级/地点/噪声/武器部分接入；其他字段未迁移 | 统一按字段语义接入；列宽/刷新/长短名/最大值；不能整体跳过旧层审计 |
| 战斗日志 | 已提交部分动态击中/未命中；大量其余生产点待迁移 | 玩家/怪物/武器/状态/数值组合，全部成功失败分支保留英文控制数据 |
| 装备与物品操作 | 装备延迟操作部分接入；player-equip/item-use等未完整迁移 | 穿脱/挥舞/使用/失败/进度/中断完整消息；量词/所有格 |
| 瞄准、法术、能力、箭袋 | 少量提示已接入；固定失败候选已审校，尚未绑定 | 坐标/距离/法术等级分离；目标名称和无效目标；父视图/箭袋提示也需迁移 |
| 神祇与角色 | 等级/技能成长部分接入；神祇/变异/状态/能力大量入口待迁移 | 每个实体、状态与等级语义分开；全流程日志/详情/菜单 |
| 世界与通用界面 | 地形、旅行、交互、通用菜单及部分教程仍旧层 | 静态/动态生产点完整接入；输入/程序标识不翻译 |
| 帮助与文档 | 已审校中文手册可复用；入口及标题仍需归一 | 选择正文语言；长文分页/标记/快捷键；无最终英文句匹配 |
| 旧历史兼容 | 旧存档英文历史无ID，保留明确兼容边界 | 与新实时消息隔离；不改原存档；不计入新架构迁移完成 |

## 公共旧入口

- `cio.cc:243` — `string buf = zh_translate(vmake_stringf(s, args));`
- `cio.cc:328` — `string buf = zh_translate(vmake_stringf(s, args));`
- `cio.cc:347` — `string buf = zh_translate(vmake_stringf(s, args));`
- `command.cc:629` — `line += ": " + zh_translate(untag_tiles_console(desc)) + "\n";`
- `command.cc:642` — `desc = zh_translate(desc);`
- `command.cc:652` — `desc = zh_translate(desc);`
- `command.cc:1145` — `text = zh_translate(text);`
- `directn.cc:3592` — `desc = zh_translate(desc);`
- `directn.cc:3594` — `item_desc = zh_translate(item_desc);`
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
- `quiver.cc:257` — `key_hint = zh_translate(key_hint);`
- `quiver.cc:402` — `qdesc.cprintf("%s%c) ", zh_translate(uppercase_first(verb) + ": ").c_str(),`
- `quiver.cc:506` — `qdesc.cprintf("%s%c) ", zh_translate(uppercase_first(verb) + ": ").c_str(),`
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
- `zh-localization.cc:478` — `std::string zh_translate(const std::string &text) {`

## 边界声明

规范英文读取使用 ZhTranslationPause；只阻止旧匹配的原样渲染使用 ZhLegacyPause。两种职责不可互换。
模块完成需覆盖主入口、选择、详情、帮助、悬停、成功/失败反馈及渲染出口；同文件有新接口不代表整个文件完成。
旧存档没有消息 ID 的历史兼容单列，不能据此保留新实时消息的旧匹配。
所有新增/修改游戏译文由 Luna 批量审校，主 agent 负责代码。Mac 为主调试平台；Linux 在里程碑验收。
