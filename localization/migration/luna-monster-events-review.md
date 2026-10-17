# 怪物事件文案审校

本目录合并了首遇教程、怪物叫喊、特殊怪物信息和三条相邻怪物事件，共 156 条完整模板；每条 ID 都有独立 typed oracle。文本按完整句式翻译，动态怪物名、按键、颜色、数值和语义片段继续作为参数传入。

首遇提示保留 `<w>`、`<tiles>`、`<console>`、`<localtiles>`、`<nomouse>` 等控制标记及源文换行。字形参数是颜色与按键标记生成的显示内容，因此原样保留。叫喊文案区分玩家听到的声音与可见怪物发出的动作；怪物所有格参数在中文父句中通过“的”表达。特殊怪物段落中的 `subject` 始终指怪物，津恩法则、栖息环境、速度及伤害等句式均保留完整语义。

`Wyrmbane` 沿用游戏中的原名；Gozag 煽动句明确以怪物为受煽动对象。该模块不翻译怪物名、物品名或按键名，也不把不同上下文的完整模板合并成子串规则。

验证：`python3 tools/test_message_ids.py` 通过（2160 条 named-message oracle/校验，3543 个稳定 ID）。特殊怪物生产者测试 `python3 tools/test_special_monster_details.py` 通过（11726 个实际描述与能量场景）。首遇函数测试已通过（终端与 Tiles 各 6156 组）；喊叫 14146 组真实函数对照及中英文数据库共存/递归路径测试通过。临时测试装配器的默认参数花括号识别问题已修正。

Mac 严格存档 QA 追加了三条实际可达图鉴原文（hydra、acid blob、jiangshi），其 `detail.monster.lore` source keys 使用数据库 getter 解包后的固定条目文本，与实际绑定 API 的输入一致；hydra 段落保留 `unwrap_desc` 输出的两个实际换行。另增加 `{heads}-headed {species}` 的完整名称模板，中文按实际头数表达，不把九头蛇固定成某个头数。Royal Jelly 的 `the` / 无冠词区分属于名称参数边界，按实现约定无需新增翻译模板。

Hydra source-key 校验可用 `python3 tools/test_hydra_lore_unwrap.py` 独立运行：它从 native 描述原文提取条目，按 `unwrap_desc` 规则折叠单换行并保留段落换行，再逐字比对目录 canonical 与 oracle。

最后补入龙族共享引用 `__cap-D_suffix`，沿用 `zh/quotes.txt` 中完整的孔子与龙诗歌译文。英文 canonical 按 quote getter 的 `unwrap_desc` 输出保留段内缩进、自然换行与段落分隔；`tools/test_hydra_lore_unwrap.py` 现在同时从 native `monsters.txt` 和 `quotes.txt` 抽取原文，验证 hydra lore 与共享引用的实际 getter 文本及中英文 oracle。

追加 Royal Jelly lore：英文 source 使用 `getLongDescription("Royal Jelly")` 经 `unwrap_desc` 与 `trimmed_string` 后的单段 canonical；中文参考 native 中文数据库并审校为“胶冻”游戏术语，另有独立 oracle。
