# 消息生成处迁移记录

基线：native `dcss-zh/0.34` / `b8f0e88341fac10f3860861c99f22bcbd3fc0da4`；既有修复另存发布仓库提交 `3291563`。不重置分支，不覆盖并行 agent 文件。

参考实际 BROGUE：`port/zh_catalog.h`、`tools/prepare-port.py` 的独立 monster display helper、`port/item_name_core.inc`、`work/message-history-source/src/brogue/Combat.c`。它在 sprintf 前选择 br_tr 完整模板，显示名称独立于保存/SeedCatalog 名称；部分历史代码仍有片段拼接，不照搬这些不足。

## 新接口

`ZhMessage` 保存 id / canonical / localized，`ZhArg` 携带名字、语义类型、英文值、显示值及 supported。模板与 schema 由 Luna JSON 生成；消息 ID 不跟随源码行号，固定消息 ID 由模块加源文摘要确定，动态消息使用语义名字。完整模板选择在命名值填充之前，禁止从结果英文提取参数。

人物经验等级、技能等级、法术等级、变异阶级、地牢深度分别绑定各自消息 ID/context；不建一个通用 level 译词。参数类型必须完整匹配，重复、未知、缺失参数均拒绝。colour/key 类型只收程序结构 token，文案译者不能替换其值。

`mpr(ZhMessage)` 把 canonical 交给颜色过滤、Lua hook、more/flash/join 规则及存档；显示候选只放 transient message_particle，不改变存档结构或 Lua history。重复折叠同时比较英文与显示文本，避免不同语义上下文合并。中文/英文与暂停翻译在显示时选择。Lua item/monster description 入口显式暂停翻译。

`zh_item_arg` / `zh_monster_arg` / `zh_actor_arg` 从类型、数量、加值、鉴定状态等语义字段生成显示名称，保留原 name()。未知专名可原样保留；不完整普通名称将 supported 设 false，整条消息英文回退并记录缺失。不会解析最终英文名称或逐词替换。

## 迁移次序与文件责任

1. 消息传递层、参数协议、审计/生成/测试：主 agent。
2. 玩家等级、技能等级/训练目标、装备动作/进度：主 agent。
3. 商店余额/名称/颜色/帮助及物品列表：Luna shopping owner。
4. 物品/怪物详情、命中率及技能面板：Luna detail owner。
5. 动态战斗日志与名字语法：Luna combat/name owner。
6. 固定 mpr/mprf：Luna 逐条审校后由工具改真实生成点，保留所有 source/context。

所有新增与修改的游戏中文来自 Luna；主 agent 不撰写游戏文案。已审校词库、外部中文文档和字体成果继续复用。

## 过渡与限制

通用逐词兜底已删除。未迁移的 formatted_string、cio 等显示入口暂时保留旧完整模板/片段匹配，必须在最终报告列出；这不是全面迁移。旧存档中只有英文消息，没有稳定 ID/参数，恢复的历史仍走旧层；不会修改原存档字段来伪造完成率。

`mpr(ZhMessage)` 的实时消息与历史回放直接使用显示候选并暂停旧翻译；商店帮助行也使用局部 raw parser。详情与技能 widget 仍组合新旧字符串，最终 parse_string 可再次经过旧层，因此该类尚未完成渲染边界迁移。不能对整个混合界面暂停翻译，否则会使旧内容失去汉化。尚未能结构化显示的神器、未鉴定或复杂状态名称明确报告并整条英文回退。验收按实际生成点和场景计数，不用中文字符占比作为覆盖率。
