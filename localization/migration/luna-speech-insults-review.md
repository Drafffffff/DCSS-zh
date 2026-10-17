# 随机嘲讽文案审校

已逐项审校 `analysis/message-migration/speech-copy-spec-0.json` 的 557 条模板候选；原规范 557/557 条全部输出，另按补充范围加入 2 条完整喊叫模板（共 559 行），原规范条目按要求保留 `id`、`file`、`key`、`row` 与 `raw`。本批来自随机嘲讽词库，中文直接对应模板片段，不依赖最终英文句子的反向匹配。

- 已逐条核对动态占位符；`@...@` 标记及重复次数全部与原文相同。此批没有 `SOUND:`、`VISUAL:`、方括号选项或显式换行频道。
- 对明显误义和生硬表达作了修正，包括 `lily-hearted`（怯懦）、`straight-laced`（古板守旧）、`gudgeon`（容易上当的人）、`haggard`（憔悴者）、`pissant`（小人物）及若干旧式嘲讽词。占位符片段之间的中文标点按模板语序处理，复合嘲讽仍可自然拼接。
- 保留游戏/奇幻物种的既有通用译法，如 elf「精灵」、kobold「狗头人」、tengu「天狗」、mummy「木乃伊」；模板动态物种占位符本身原样保留，不在本层替换。
- 一些词是源词库刻意制造的怪诞复合词或冷僻词（如 `rhino-ravelling`、`spot-chasing`、`key-stepping`、`surfacer`、`tombling`、`nissette`）。原文无法支持唯一、稳定的字面释义，因此译文保留其嘲讽功能或荒诞意象；这些词不适合声称为精确词源释义。`nissette` 在本稿以“小家伙”作功能性处理。
- 几个源词存在多义，按嘲讽词表语境取义：`gudgeon` 译作易受骗者而非鱼名；`haggard` 译作憔悴者而非鹰隼；`bum-bailey` 按旧式小吏/执法差役讽刺处理；`clack-dish` 按乞讨者处理。

## 固定语法与词汇

- `@run_away@`：逃跑/逃命；`@give_up@`：认输/投降；`@run_or_give_up@`：按候选动态片段选择逃跑或认输。
- `thou/thy/thee`：按现代中文语气译作“你/你的”，不保留古英语代词。
- `whilst thou can` 等片段：译作“趁你还……”，保持为可接续的短语。
- `will/shall` 与 `feast on/devour`：组合为将要/必将享用或吞噬；身体、精神部位及食物槽位保留原标记。
- `@insult_adjective1@ @insult_adjective2@ @insult_noun@`：输出为“形容词、形容词的名词”，不改变槽位数量和顺序。

## 喊叫模板与语义标签

按补充范围加入 `speech.shout.demon_taunt` 与 `speech.shout.imp_taunt` 两条父模板，分别保留怪物名、语气动词和嘲讽文本标记各一次；中文标点置于语气动词与内容之间。顶层 `atoms` 覆盖所有指定的语气、称呼、神祇、地表及地形标签；语气标签沿用本地已审校词库（如 `says`「说」、`buggily says`「虫鸣般地说」），供语义枚举选择，不作为任意英文片段的兜底翻译表。

`efter` 按其位于名词词表的语境，并参照近形旧词 `eft`（方言/古称蝾螈）的释义，推断译作“蝾螈”；这是词形关联推断，不声称 `efter` 是标准现代英语拼法。其它生造复合词按上下文给出功能性中文意译，具体不确定组见上文。通用 fallback `{message}` 仅保留原文作报告，不提供普通可见中文译文。

## 补充语义标签与受话者短语

审校并扩展了 `atoms`：`you are` 为「你是」；`its god`、`his god`、`her god`、`their god` 分别保留代词差异；原 `to`、`at` 两个缺少宾语的残片已移除，完整的 `to {foe}`、`at {foe}` 作为 `speech.actor.*` 消息提供。另新增 `{name}'s` 所有格消息。三个参数均标为 `name`，消息源锚点对应 `mon-util.cc` 中受话者介词和所有格的实际展开处。


## 形容词组合语法复核

稳定组合模板为 `@insult_adjective1@、@insult_adjective2@的@insult_noun@`：形容词词条一律提供不带句末“的”的修饰语片段；第二槽后唯一的“的”由组合模板负责。此规则覆盖 `insult general adj1/adj2` 及 elf、felid、dwarf、tengu、mummy、vampire、undead 的专用词条，也覆盖动态 `@species_insult_adj1@` / `@species_insult_adj2@` 最终回落到的叶词。已将 `ditch-delivered`、`fool-born`、`hedge-born` 改为“阴沟所生”“傻子所生”“篱笆边所生”，并统一修订了半脸、鸽蛋大小、廉价帽子等名词性或数量短语，使它们可以直接接模板提供的“的”。本轮复核所有形容词叶词，确认没有具体译文以“的”结尾，因此不会再形成“的的”；动态占位符及形容词槽位顺序保持不变。模板内没有额外加入量词，词条中的度量/数量意象按修饰语处理。
