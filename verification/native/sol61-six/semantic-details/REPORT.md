# GPT-6.1-Sol 语义名称与特殊详情工作包

基线：`cc710081cd3f163eabf78c65b9144e040ef30aa8`。翻译、审校模型均为 `gpt-6.1-sol`；12 条新模板已在本包逐条审校。仅修改 `zh-display-name.cc`，没有改 canonical 名称生成、Lua、存档字段、共享消息实现、生成 catalog 或词库。

## 已交付

- 截图 `20261018014128_1.jpg`：未鉴定卷轴从 `subtype_rnd` 调用既有 `make_name(..., MNAME_SCROLL)` 取得可见标签；完整模板输出 `c - 标签为“GIOJOT FEUBA”的卷轴`。标签是原样专名参数，禁止调用隐藏效果名称生产点，绝不读取真实 subtype 来选择中文效果。
- 截图 `20261018014113_1.jpg`：普通尸体使用 `mon_type` 的已审校物种名，加身体/骸骨枚举选择完整模板，输出 `一具飞镖蛞蝓尸体`。尸体/骸骨单数不定冠词使用“一具”，复数使用“{数量}具”；普通名词和所有格名称保持对应语义，父句无需猜测量词。独特命名、形容词、后缀、唯一怪物省略来源和未知来源均整名回退并报告。
- `MONS_UGLY_THING` / `MONS_VERY_UGLY_THING`：由 snapshot 的 `_colour` 经既有 colour offset 选择红/褐/绿/青/紫/白六个完整模板。live-monster 和 monster-info 共用；库存/地面/日志等已有 typed 消费者复用新名称。额外命名/幽灵化/吸血仆从/变形者/多头等字段直接触发整父回退，不匹配最终英文来选中文。
- 颜色标签、库存键位仍在既有 typed menu wrapper 中组装；普通颜色形容词没有冒充控制参数。

## 验证

`python3 tools/test_sol61_semantic_details.py`：**PASS 23,215**。

测试抽取并编译真实 `translated_item_name`、`zh_item_arg`、quantity/menu wrapper、`_monster_visible_species_arg`、live-monster/info wrapper。冻结基线原 wrapper、原 `translated_item_name`、完整 `item_def::name` 和 `name_aux` 的原前后处理及卷轴/尸体分支作为独立英文 oracle。6,336 个物品状态组合覆盖鉴定状态、两种卷轴 subtype、四种标签（含大小写和专有字符）、尸体/骸骨来源、未知来源、数量、地面/库存、所有名称层级；另核对移动数量快照、键位、颜色标签、六色及高亮色和语义回退。两条截图的确切 canonical/localized 输出有断言。未鉴定卷轴断言隐藏效果 API 调用次数为零。

私有临时 catalog 含本包12个ID及既有已审校 headed/stab-defend 两个ID；编译真实 renderer，禁用 legacy matcher。未生成共享文件。原 `item_def::name` 和上述 `name_aux` 来源片段与冻结基线严格逐字对照。测试 seam 明确包含未改的 `make_name` API 和怪物可见信息 snapshot；实际标签随机生成算法和完整怪物名字生成不在本包重测。颜色名称/offset 采用冻结原生产函数。

`git diff --check` 通过。未做全量构建、SSH、UI、git 提交；native 联编和存档副本回放由主 agent 统一完成。因此本包不宣称 native 最终验收完成。

## 主 agent 存档副本触发场景

1. 使用用户截图附近的**副本**存档，在未鉴定卷轴上拾取/丢弃/查看地面；确认 `c - ...` 的键位保持，显示标签卷轴而非真实效果；同一外观的不同真实 subtype 不泄露差异。
2. 飞镖蛞蝓尸体格子：走到格子、查看地面摘要、查看物品，确认物种源自尸体字段；测试普通骸骨和多具尸体。
3. 生成或遭遇六色丑陋之物及非常丑陋之物，查看目标、详情标题、伤势/装备日志；测试幽灵化/命名/变形者分支应完整英文回退并记录。
4. 自定义题字物品、命名尸体和未知语义维持整父回退；颜色及快捷键原样。

## 余项

未鉴定药水/魔杖/法杖/首饰外观、命名尸体的各种姓名模式、神器与自定义题字、玩家幽灵完整生平、变异兽及潘领主详情均未完成。`describe.cc` / `describe-spells.cc` / `mon-info.cc/.h` 其余文案没有被本包宣称完成。地面集合摘要父消费者由物品边缘组承接。旧 `test_monster_semantic_names.py` 的 snapshot seam 需要添加本次新增 ugly enums/flags/props 依赖，已告知主 agent；本包新测试具备这些生产语义。

## Mac 击杀复现接续：HELPLESS_KEY

主 agent 的真实 GUI 击杀复现中，`attack::stab_message` 会临时写入布尔属性 `HELPLESS_KEY`，使名称变为 `the helpless rat`，旧未知限定词 guard 导致整父英文回退。本包增加完整模板 `helpless {species}` → `无助的{species}`，复用已审校“无助的”术语。

生产点先检查结构化属性，只在私有 monster_info 快照中移除该属性，再调用原物种/头数/颜色生产链并用模板包裹；canonical 仍从原 snapshot 取得，包括 helpless。未知形容词仍由原语义 guard 完整回退，不拆词、不从最终英文匹配。原 monster/snapshot 的属性都保持原样。

新增 3,024 个组合覆盖 HELPLESS_KEY 开关 × 老鼠/兽人/多头蛇/两种丑陋之物/未知物种 × 头数1/8/11/27 × 三色 × 额外未知限定词 × 冠词/所有格/名称层级。live-monster 与 snapshot 路径均抽取真实函数编译；另用真实已审校刺杀父模板断言 `the helpless rat fails to defend itself.` → `无助的老鼠未能保护自身。`。主 agent 可重新联编后重做原 GUI 击杀；正式截图在 `macos-ui/conduct-kill.png`。
