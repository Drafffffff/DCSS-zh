# GPT-6.1-Sol 界面与帮助工作包

状态：生产函数迁移和独立编译测试通过；等待主 agent 统一生成共享 catalog、Mac/Linux Tiles/console 构建以及真实存档副本截图。没有全量构建、SSH、UI操作、Git提交或原存档写入。

## 已交付范围

- `tilereg-doll.cc`：角色外观编辑器完整可见视图，包括标题、三个预览标签、16个部位类别、三种模式、当前部件/部位清单、造型编号、六行快捷键说明。基线17处 `zh_translate` 全部移除。40条模板使用稳定ID；四条动态模板使用命名整数/文本参数，类别/模式/部件状态保留typed子消息。
- 生产函数 `doll_part_value`、`doll_part_message`、`doll_index_message`、`doll_mode_message`、`doll_command_text` 同时供 `doll_layout()` 测量与 `DollEditRegion::render()` 绘制。测量的是完整实参文本，不是printf占位串或片段宽度之和。零件编号、无部件、显示装备均纳入最大宽度。选中箭头与非选中空格前缀独立测量；标签与快捷键分别成列。
- `DollEditRegion::run()` 标题通过 `formatted_string::parse_string_raw`；其余文本通过既有 `FontBuffer::add(string,...)` 原样绘制。没有新增全局skip或语言暂停。图标仍以32像素整数倍布局。该编辑器当前 `handle_mouse` 本来就返回0；本包没有新增鼠标命中区，实际操作仍由键盘命令处理。
- `skill-menu.cc`：增强/削弱帮助的完整生产链。原先 `vector<string>` 拼出神名所有格，再用 `zh_word_arg` 扫描最终英文；现在原因由状态分支直接选择既有 `skill.cause.*` 稳定ID，`vector<ZhArg>` 经 `zh_message_list` 保持支持状态，父句继续使用已有 `skill.menu.enhanced/reduced`。Ashenzari神力按神祇枚举选择；未知未来神力来源使完整父句回退英文，并记录缺失。原因顺序、英文and/comma语法、分支判断均保持。
- 核查并测试已有HUD等级/地点生产函数以及技能帮助pretranslated入口和折行边界。HUD源码未改；没有把整个HUD或帮助系统标为完成。

译文由本组GPT-6.1-Sol批量翻译并复审，`model` 和 `reviewer_model` 均为真实 `gpt-6.1-sol`。复用 `localization/luna-systematic-review-20261017.json` 的“角色外观、造型、部位、部件、附魔光效”等已审校术语，技能原因与父句复用既有审校词库。数字、箭头、快捷键、颜色标签和 `dolls.txt` 控制文件名保持原义；无最终英文句匹配或逐词兜底。

## 英文oracle与验证

`tools/fixtures/sol61-ui-help-english.json` 从指定基线 `cc710081cd3f163eabf78c65b9144e040ef30aa8` 冻结 `tilereg-doll.cc`、`skill-menu.cc`、`output.cc` 源码。新测试把冻结编辑器完整生产文件与当前编辑器分别放入C++命名空间，编译真实生产的布局、绘制、键盘循环、技能帮助及HUD字段函数；catalog和编译产物仅在私有临时目录生成，实际使用生产 `zh-message.cc` 与 `zh-localization.cc`。

运行命令（工作目录为仓库根目录）：

```sh
python3 tools/test_sol61_ui_help.py
python3 tools/test_skill_menu_layout.py
python3 tools/test_pretranslated_rendering.py
python3 tools/test_hud_layout.py
git -C native diff --check -- crawl-ref/source/tilereg-doll.cc crawl-ref/source/skill-menu.cc
```

结果：全部通过。

- 576个纸娃娃绘制场景：3模式×16类别×3值类型×4字体比例(8/16、12/24、24/40、32/56)。每个场景比较基线英文所有绘制文本，检查当前中英两种语言的像素边界、快捷键列间距、32像素整数缩放，以及中文切回英文后文本一致。
- 16个真实 `run()` 场景：4套命令脚本×未加载/三种已加载模式；分别在中英文下与基线对照事件顺序、复制粘贴、随机造型、部位切换、装备开关、编号选择、模式选择、加载文件名、保存模式/编号/部件及最终 `player_doll`。真实键盘命令业务循环被编译执行；宏键解析、文件IO、RNG和图形驱动由接口桩代替。
- 147456个技能帮助分支：1024原因组合×16标志组合×9帮助状态。英文与基线生产函数逐项相等；中文使用真实消息渲染器后在20/78/100/158显示单元宽度下折行，验证每行边界。未知神力完整父句回退并验证缺失日志。
- 160个已有HUD等级字段边界案例；含中英文、等级/进度极值、最高等级、紧凑布局。地点含中文层数、无层数及未知分支完整回退；未知分支的缺失日志也逐项验证。
- 既有技能菜单布局测试通过（长帮助在100列下106行，增长受可用高度和完整footer保留范围约束）；raw parser/pretranslated回归30例通过；HUD噪声/静音/武器显示宽度回归通过。HUD既有逻辑有一条 `&& within ||` 编译警告，未改变原业务表达式。

测试的字体接口桩按CJK双列、ASCII单列计宽，不能代替SDL真实字体栅格和4K截图。图形驱动、真实按键绑定映射、真实 `dolls.txt` IO及存档兼容仍由主agent集成验收；没有宣称本组已完成这些验收。

## 可复制的存档副本场景

1. 使用主agent已隔离的存档、配置和 `dolls.txt` 副本，3840×2160启动。按默认 `-` 打开角色外观编辑器，核对“角色外观编辑器”标题、三个预览标签、完整右侧部位清单和六行快捷键表。
2. `m` 轮换当前装备/自定义外观/职业默认外观；`0`、`9`切换造型；上下方向键遍历16个部位，左右键切换部件，`*`切换装备显示。核对当前行和右侧同类别编号一致，箭头、冒号和零件值均不相互覆盖。
3. `Ctrl-C`、切换编号、`Ctrl-V`、`Ctrl-R`，再 `Ctrl-S`。重新打开副本核对模式、编号和外观保留；对照英文启动重复相同步骤。该流程会写副本的 `dolls.txt`，因此不要使用原配置目录。
4. 在具有增强或削弱状态的副本上按 `m` 打开技能菜单，`_`切换增强/基础级别，核对绿色增强/洋红色削弱完整原因提示；`?`打开完整帮助并返回。建议状态副本分别覆盖英勇、阿什恩扎里神力或惩戒、交叉训练、隐士吊坠、变形、骗子宝珠、抄写知识、业余者之灾。无需在同一个正常角色上强造所有组合；全组合已由生产函数测试覆盖。
5. 在相同4K配置中核对等级/地点不覆盖右侧HUD、长技能帮助不覆盖footer按钮；已有用户三张截图中的能力菜单与名字问题分别由神祇/名称组处理，本组没有重复修改。

## 余项与依赖

- 本包没有迁移整个 `output.cc`。其中仍有12处显式旧翻译调用，主要在角色称号/种族/神名、概览页和抗性/回复字段；输出HUD无武器名称、状态灯、箭袋外层等也需要独立生产链审计。显式旧调用数只用于定位，不代表待译文案数。
- `command.cc`仍有4处旧翻译调用，命令帮助组装/插键及其他帮助正文入口需要逐包处理。已有 `show_specific_helps` 从 `getHelpString` 到raw parser的主链已核查，未据此宣称所有帮助完整迁移。
- `hints.cc`、`tutorial.cc`、`lookup-help.cc`未做源码修改；零显式 `zh_translate` 不代表所有消息均有typed生产点。本包不声称这些文件完成。
- 技能主菜单除本次原因链外的既有提示/详情边界仍按总账本验收；本包只确认选定原因链及既有布局测试。未知未来神祇的 `bondage_skill_boost` 提供者需新增审校模板，当前明确整父回退。
- 主agent需要将本组40条消息纳入最终共享catalog后再统一构建。现有 `skill.menu.*`、`skill.cause.*`、`hud.*` 定义保持复用；本组没有改共享catalog、全局渲染、能力菜单或名称API。
