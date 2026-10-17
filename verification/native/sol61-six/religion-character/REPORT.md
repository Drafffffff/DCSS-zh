# 神祇与角色迁移验收（GPT-6.1-Sol）

基线：`cc710081cd3f163eabf78c65b9144e040ef30aa8`。本工作包不是整个“神祇与角色”模块完成声明。新文案由 GPT-6.1-Sol 翻译和审校；兼容现有文件发现规则暂保留 `luna-sol61-` 文件前缀，JSON 的实际模型为 `gpt-6.1-sol`。

## 已交付

- 331 条完整模板/语义名称条目，其中 206 条去重固定模板。固定消息直接在原生产分支选择 ID，保留原频道及神祇参数；内部诊断、存档笔记、Lua数据不翻译。
- `god-prayer.cc`：多神祭坛提示、按键/神名列表、未知神改信确认、接受祈祷、口头/默祷、什一税金额。`god_prayer_reaction()` 仍供 chardump 使用规范英文。
- `religion.cc`：欢迎/再次欢迎、拒绝原谅与入教拒绝原因、入教服务费及余额、主要离教固定反馈；`dock_piety` 的四档完整内疚句、`ostracise_player` / `player_change_ostracism` 的完整消息与封顶/归零分支。
- `god-abil.cc`：捐款确认、预计虔诚七档×两类终止标点；神盾施放/续期/消退、净化、神圣活力、许多能力成功/失败固定反馈。捐款过小的 `simple_god_message` 与什一税迟交回应仍为明确旧边界。
- `god-passive.cc`：`qazlal_element_adapt` 四类元素×新增/加强完整模板与其他抗性消退消息；其他固定被动反馈。
- `mutation.cc`：六种属性变异×增减方向的完整句，以及 `temp_mutation_wanes` 部分/完全消退；一般 `mutation_def` 分级 gain/lose 数组与身体部位替换仍未迁移。
- `player-stats.cc`：属性提升说明、基础三属性数值、大小写键位选择；`modify_stat` / `notify_stat_change` 与 `_handle_stat_change` 的三属性增减、归零/恢复及标记位。能力/等级语义独立，未匹配最终英文。
- `god-wrath.cc` / `ability.cc` 的固定反馈直接选择完整模板，未据此声称全部业务函数完成。

## 用户截图回归

`20261018014054_1.jpg`：新增 `_ability_menu_cost_arg` 与 `_talent_menu_message` 以能力字段选择完整代价模板。Renounce Religion → 放弃信仰，None → 无；仍保留 `ability_name` / `make_cost_description` / `describe_talent` 的规范英文 API。菜单标题、两组条目、神祇能力小标题均标记 pretranslated；普通帮助与教程长提示经 `set_more_pretranslated` 输出，教程颜色是 typed colour，`!`/`?` 标记原样保留，不再进入旧逐词匹配。复杂诅咒/献祭/卡牌代价及未知名称整行回退，不拼接中英碎片。

`20261018014113_1.jpg` / `20261018014128_1.jpg`：`god-conduct.cc` 的 `_on_kill` 工厂直接绑定 `message_id`，`like_response::operator()` 据 ID 输出完整 `{god} accepts your kill.`；覆盖 Trog 等所有使用该工厂的神祇，不是单神特例。奥卡瓦鲁显式接受/荣光分支、费达斯生态贡献/接受分支同迁。`dislike_response` 与冻结源码完全一致，测试专门断言这一边界。

## 验证

运行：`python3 tools/test_sol61_religion_character.py`

结果：`PASS 16102 extracted production cases; canonical English, side effects, channels, RNG, ranks, flags, keys and complete fallback`。

测试从当前真实源码抽取生产函数，并与冻结英文函数在同一 C++ 测试程序中分别执行，比较规范英文、返回值、频道、状态写入、神祇/虔诚副作用事件、RNG调用、输入顺序、标记位。覆盖多神列表键位、未知神/能力整句或整行回退、样式标签、类型不匹配拒绝、捐款等级/标点、属性方向/归零、暂时层数消退、元素抗性撤销/刷新、真实 `_on_kill` 工厂与响应执行、真实菜单行和教程长提示生产函数。菜单接线另断言所有当前出口 pretranslated。测试现抽取真实 `unicode.cc` 的 UTF-8 解码、`strwidth` 与 `chop_string`，不再用字节宽度 seam；两种标题分别断言代价/失败率位于36/68显示列，并计入菜单标题1格缩进、条目5格热键前缀与名称32格字段。真实窗口渲染由主 agent 的原生截图确认。

测试构建自己的临时 catalog，不运行全局 `compile_catalog()`，不写 `zh-message-catalog.inc`、其他生成文件或共享接口。fixture 保存本包修改前的九个源文件作为英文规范参照。仅独占源文件与新文案/测试/报告发生修改，没有提交 Git。

## 明确剩余

`audit.json` 给出逐文件剩余 raw-call 候选清单（包含诊断及规范英文边界，不能把它直接当未翻译比例）。未完成的主要链路包括神祇能力 gain/loss 表与数据库神谕、外部 `god_speaks`/`simple_god_message` 业务消费者、一般变异数组/身体部位重写、祖灵/追随者复杂动态日志、宗教菜单详情与一般能力详情/复杂代价协议、未在本包测试的神罚和其他神祇行为动态日志。原生全构建、存档副本回放截图和 Linux 验收由主 agent 统一执行，本报告未将它们列为已通过。

## 标题列对齐补验

Mac 截图确认菜单碎片已修复，但代价与失败率标题仍偏右约两格。原因是标题中的两个模糊宽度长破折号在系统宽度计算与当前 CJK 字体中的占位不同。仅将两种标题的连接符换成明确宽度的全角冒号，并保留20格空白：标题1格缩进+36列=条目5格热键前缀+32格名称；下一列同为69列。英文完整模板与canonical完全不变，教程标记不变。新增真实 Unicode 宽度断言，最终复跑 `PASS 16102`。本补验只改文案与本测试/报告。
