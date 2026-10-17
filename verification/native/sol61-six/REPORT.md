# 六组 GPT-6.1-Sol 迁移与截图问题验收

本轮按用户明确指定，由六个独立 GPT-6.1-Sol 子 agent 分别翻译、审校并迁移六类工作包；主 agent 集成公共接口、统一构建和存档副本验收。并发限制为主 agent 加三个 worker，因此六组分两波执行，所有权不重叠。历史 `luna-` 文件名前缀仅用于既有 catalog glob；本轮文件中的实际 model/reviewer 均为 `gpt-6.1-sol`。

基线 native：`cc710081cd3f163eabf78c65b9144e040ef30aa8`，分支 `dcss-zh/0.34`；开始时工作树干净。期间另一个任务提交了辅助攻击详情修复 `c2df0d82370388ebb1d3704156a20eb2f2f731b8`，本批保留该父提交；公开仓库对应的 `c356ab3` 也予以保留，实际 describe.cc 逐字相同，35项生产回归通过。公开仓库基线 `dfd66ebd050a7d9212d7962ab5c4dc9d68b8aa60`。本批 native 提交为 `44ae418e12df902d13ca4f92b6ebba0dd8b3db35`。改动清单见 [changed-files.json](changed-files.json)，验收源内容哈希见 [source-hashes.json](source-hashes.json)。本批是部分工作包验收，不代表六个大模块全部完成。

## 本批范围

| 工作包 | 已迁移的生产链 | 新模板 | 生产函数回归 |
|---|---|---:|---:|
| [神祇与角色](religion-character/REPORT.md) | 祈祷、皈依、奉献、敬重等级和逐出；能力菜单与多种固定业务反馈；击杀认可；部分变异、属性变化 | 331 | 16102 |
| [战斗与法术](combat-spells/REPORT.md) | 背刺、部分自我强化、血液/亡灵、九类召唤和云雾分支 | 54 | 174768 |
| [世界交互](world-interaction/REPORT.md) | 楼梯警告/确认/行动，main 爬楼前置消费者，网/蛛网及部分旅行警告/绕路缓存 | 91 | 153468 |
| [物品边缘流程](item-edges/REPORT.md) | 最后类别鉴定、地面集合摘要、专名武器问候/告别、Imbue/Imprint 延迟及箭袋近战反馈 | 23 | 123753 |
| [名称与详情依赖](semantic-details/REPORT.md) | 未鉴定卷轴外观、普通尸体/骨架量词、可见丑陋之物颜色、结构化 helpless 限定 | 12 | 23215 |
| [界面与帮助](ui-help/REPORT.md) | 纸娃娃完整绘制/测量/键盘保存链；技能增强/削弱 typed 原因列表 | 40 | 576 绘制、16 保存、147456 帮助、160 HUD |

共新增 551 条审校模板；全 catalog 为 9132 条。这是模板数量，不是汉化覆盖率。每组报告列明具体函数、冻结英文 oracle、模拟依赖及尚未迁移入口。

公共接口补充 typed `mpr_nojoin` 和 `mpr_nocap`，保留 canonical、显示文本、频道、参数、首字母处理及合并行为；162 个真实 delivery 调用测试通过。格式化前选完整模板；名称从语义状态构建；未知名称或原因完整父句回退并记录缺失。未恢复通用逐词兜底。

## 用户截图及实际发现

原始三张 Steam 截图保存在 [user-screenshots](user-screenshots/)，最新为 `20261018014128_1.jpg`。来源为 Bazzite 的游戏 Steam 截图目录，读取后没有再出现更新截图。

- `Renounce Religion`、`None` 与能力菜单底部说明已接入模板；表头和行共用显示单元列宽，Mac/4K 的代价与失败率列对齐。
- `Trog accepts your kill.` 在实际 `_on_kill` 分支生成完整消息，不对最终英文句子匹配；两端副本均显示中文认可反馈。
- `a scroll labelled ...` 仅从外观随机标签生成显示名，保留随机文字；不读取未鉴定的真实效果。普通尸体/骨架使用“一具”与数量“具”。
- 背刺状态 `HELPLESS_KEY` 原先使名称整句回退。现在复制可见 monster_info，移除已处理限定后递归绑定名称，再套完整状态模板；原快照不变。普通怪物、多头蛇、丑陋之物和未知额外限定均有生产测试。该组合已由真实函数测试；本轮可见击杀场景是清醒老鼠，没有把它声称为 helpless 画面验收。
- 纸娃娃 17 处 `zh_translate` 调用归零；绘制与布局测量使用同一批完整实参文本；快捷键独立列，图块使用 32 像素整数倍。Mac 真实副本还切换、保存并重新载入了自定义方案。
- 副本回放发现普通楼梯命令首先在 `main.cc::_can_take_stairs` 拦截，绕过 `stairs.cc`。本批补齐四个重复消费者。关闭商店原文为“似乎关门”，与另一处“被遗弃、无值物”的语义不同，因此另建 `world.stairs.invalid.shop_closed`，不强制共用译文。

## 构建与验证

最终四个构建均退出 0，日志为 `builds/*-accepted.log`：

- Mac arm64 Tiles + SOUND、console。
- Bazzite x86_64 Linux Tiles + SOUND、console（既有 Podman builder）。

[binaries.json](binaries.json) 记录最终实际测试二进制 SHA-256 和版本；源哈希与构建同步记录一并保留。Mac 的 Homebrew SDL/Freetype 依赖产生目标版本 11 与依赖版本 26 的链接警告；已在本机运行，不能据此宣称支持未经测试的旧 macOS。Linux 运行使用既有打包 `game/lib` 动态库。

公共验证：消息 ID/类型/参数完整性/颜色/快捷键 6821 项、raw/pretranslated 30 项、typed delivery 162 项、已有语义怪物名 310 项，以及技能/HUD 布局测试通过。六组 `parent-test.log` 均由主 agent 重跑；这些组合测试编译实际生产函数，按冻结英文与副作用对照，依赖桩的范围见各组报告，不能替代整个游戏的可见验收。

真实游戏路径：

- [Mac 控制台](macos-console/results.json) 与 [Linux 控制台](linux-console/results.json) 各 7 个新增场景：迅捷、无效爬楼、能力菜单、实际击杀、未鉴定卷轴、尸体、地面物品集合。启用 strict-source / forbid-legacy；预期完整模板不仅出现 ID，也在 PTY 转录中出现填入实参后的全文；缺失 ID、名称及运行错误均为零，源副本哈希未变。
- 两端各 5 个既有回归场景：武器详情、技能、技能帮助、商店选择及购买。购买后余额实际为 838，均无缺失记录，源副本哈希未变。
- [Bazzite 原生 3840×2160](linux-4k/results.json) 共 9 个新增/布局场景，主 agent 已逐张打开截图复核：技能帮助、迅捷、无效爬楼、能力菜单、击杀消息历史、卷轴、尸体、地面集合、纸娃娃。中文日志留在左侧区域，教程长段落没有侵入物品栏；能力菜单和编辑器文字在边界内，技能帮助 footer 可见。
- [额外 4K 回归](linux-regression-4k/results.json) 3 场景通过并逐图复核：武器详情、商店选择/购买。长详情、快捷键与样式无溢出，预览余额 838 与购买后实际余额 838 一致。详情中的 inventory/Staves/identified 等搜索词保留为程序可用英文关键字，不作为普通文案翻译。
- Mac 本地实际 SDL 窗口截图见 [macos-ui](macos-ui/)。最终构建再次复核普通爬楼、能力菜单和纸娃娃；其余名称与日志截图来自本批集成构建，相关源函数与最终构建相同。Mac 真实窗口为 1747×1112，并没有伪称本机是 4K。

4K 使用独立 Xvfb `:96` 和独立 QA 二进制，所有回放复制输入 fixture 到各自临时目录；不向 Steam 的玩家进程发送按键，不打开、覆盖原始玩家存档。测试结束的 SIGTERM/信号 15 报告属于脚本关闭自己的进程。Mac GUI 源 hints fixture 在整个操作前后哈希一致。

初次集成曾暴露两类非通过结果：Linux 编译器对枚举/整数 initializer_list 类型推断失败（现已显式类型转换）；回放的法师命令输入残留使场景落到获取物品菜单，以及 main 前置入口仍旧层。已修正输入、补消费者并重跑。最终通过证据以 `*-accepted.log` 和最终 results.json 为准，早期日志保留用于解释修复过程。

## 仍未完成

- 神祇数据库对白、惩戒/能力复杂组合、变异描述数组、角色详情；截图中的旧欢迎历史与 Trog 名字的历史译法尚有差异。
- melee/ranged/beam 主体、更多法术、mon-cast/mon-death/mon-abil 及其他外部业务消费者；内嵌 Lua 白话仍有明确回退边界。
- 移动/深渊/地形/Orb、旅行层级和失败拾取、完整陷阱触发；main 的其他反馈（如未知命令/封印楼梯）未纳入这四个前置分支。
- Orb 逃离启动、外部武器/帽子低语、旅行延迟与其他特殊物品提示。
- 自定义/神器与复杂尸体、其他未鉴定外观、玩家幽灵生平和变异兽详情继续整父/整名回退并报告。
- output 的角色/概览/状态字段、command 的帮助组装及其他教程入口仍待迁移。纸娃娃无旧调用不代表整个图形界面完成；技能组合已做生产函数全组合测试，本轮 4K 实际截图只覆盖当前 fixture 的技能帮助，没有覆盖每种神力增强状态的可见画面。

全源码仍有 31 处显式 `zh_translate` hook（主要 output、command 与公共渲染兼容层），另有尚未接入 typed 的普通生产函数；这不是剩余文案数量或覆盖率。[模块账本](../../../analysis/message-migration/LEDGER.md) 与每组 audit 是后续工作入口。未恢复逐词兜底，未宣称 100% 汉化。

本批已安装 Bazzite：根目录及 Steam 的 game/ 各有 Tiles/console 两个程序，四条启动路径均逐一核对为最终 QA 二进制哈希。采用备份和原子替换，没有重启玩家进程；存档、配置和素材未改。[安装记录](installation.json) 包含备份路径及前后哈希，测试期间另一任务产生的重编二进制也保留在 final-reconcile。当前已打开的旧进程需下次启动才使用新文件。没有创建新 GitHub Release。
