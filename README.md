# DCSS 中文版

基于 Dungeon Crawl Stone Soup **0.34.1 稳定版**的非官方简体中文原生版本，提供 macOS Apple Silicon 与 Bazzite / Fedora x86_64 图形版和终端版。

[上游 DCSS](https://github.com/crawl/crawl) · [像素字体来源](https://github.com/TakWolf/fusion-pixel-font)

## 下载与运行

从 [GitHub Release](https://github.com/Drafffffff/DCSS-zh/releases/latest) 下载对应运行包，解压后启动。Release 同时提供游戏源码、适用的第三方依赖源码与 SHA256 校验文件。

| 系统 | 下载文件 | 启动方式 |
| --- | --- | --- |
| macOS 26+，Apple Silicon | `DCSS-zh-0.34.1-zh.2-macos-arm64.zip` | 打开应用；终端版使用同目录的 `.command` |
| Bazzite / Fedora 43+，x86_64 | `DCSS-zh-0.34.1-zh.2-bazzite-x86_64.tar.gz` | 运行 `./dcss-zh`；4K 屏使用 `./dcss-zh-4k`；终端版使用 `./dcss-zh-console` |

macOS 包已包含运行库，无需另装 Homebrew；应用未经过 Apple 公证。首次打开若被系统拦截，可在“系统设置 → 隐私与安全性”中允许打开。
Linux 包包含 SDL2_image / SDL2_mixer，SDL2 与基础系统库使用 Bazzite / Fedora 43+ 提供的版本；不需要 Proton。已在 Bazzite 验证，其他 Linux 发行版尚未验证。

在 Steam 桌面模式选择“添加非 Steam 游戏”，4K 屏选择 `dcss-zh-4k`，普通屏选择 `dcss-zh`。4K 入口通过启动参数应用配置，不覆盖用户配置。

存档独立保存：macOS 使用 `~/Library/Application Support/DCSS-zh/0.34`，Linux 使用 `${XDG_DATA_HOME:-~/.local/share}/dcss-zh/0.34`。更新时替换运行包即可，保留该目录。

## 汉化与画面

- 中文词库包含 24,003 条有效条目；数据文件 5,803 个条目全部具备中文正文。
- 图形技能菜单、技能说明、装备详情、帮助和消息均接入中文显示；保留用于存档、Lua 和输入解析的英文内部标识。
- 初始游戏文案由本机 Pi Agent 的 DeepSeek Flash 翻译，当前模型为 `cc-switch-deep-seek/deepseek-flash`。已保存的翻译记录可用于重建，无需模型服务。
- 2026-10-17 文案审校由 `gpt-6-luna` 子 agent 完成：累计 1,004 条消息与动态模板，以及教程、提示和物品/怪物正文。升级和技能等级使用“级”，地牢位置使用“层”。
- 中文文本缓冲区、背景条与光标统一按终端列绘制；属性表和攻击表先翻译再计算宽度；合并战斗消息按原消息边界逐条翻译；详情表格的长标签和数值限制在各自列宽内。
- 使用 **DCSS Pixel SC**：以 Fusion Pixel 12px 简体等宽字体为基础，13 个汉字和“∞”使用 Noto Sans SC Regular 补齐。覆盖当前词库的全部可见字符。
- 4K 原生全屏：地图 96px（3 倍），侧栏图块 64px（2 倍）；菜单/状态文字 48px，消息/提示 36px。关闭平滑插值。
- 修复中文字体列宽估算、精确菜单翻译入口、动态说明拆行匹配，以及侧栏分类标签放大后的命中区域偏移。
- Steam 继承 `LC_ALL=C` 时自动回退到 UTF-8 字符处理，避免中文消息宽度被算成零、越过物品栏。
- 人偶编辑器根据字体度量布局；状态页先翻译再计算列宽；中文长帮助页的字形缓存扩为 4,096 个槽位，避免花字和串字；长文本分块和双格字覆盖边缘也已修复。

![Bazzite 4K 实际游戏画面](screenshots/bazzite-4k.png)

![技能菜单验证画面（独立存档副本）](screenshots/skills-4k.png)

覆盖率是数据条目与已测试界面的统计，不代表所有随机事件都已穷尽。运行跟踪包含物品、技能、法术、帮助等已执行路径，排除玩家姓名、路径与按键标识后未发现未分类英文。发现遗漏可提交截图与触发步骤。

本轮[截图问题分析、修复计划与验收记录](verification/review-20261017/fix-plan.md)，以及[战斗日志](verification/review-20261017/combat-log-4k.png)、[怪物详情](verification/review-20261017/monster-4k.png)、[短弓说明](verification/review-20261017/shortbow-4k.png)的修复后 4K 截图。

补充的[同类问题审查与修复记录](verification/systematic-20261017/verification.md)覆盖商店颜色参数、金币复数、动态所有格、装备进度、格挡与反射、陷阱确认、地形说明、瞄准提示，以及中文手册、入门指南和图形版帮助。

## 从源码构建

完整游戏源码与当前构建所需的 contrib 依赖源码位于 `native/crawl-ref/`；已随仓库提供，不需要初始化子模块。

macOS：

```sh
brew install pkg-config freetype sdl2 sdl2_image sdl2_mixer
sh scripts/build-macos.sh
```

Fedora / Bazzite 的可写开发容器：

```sh
sudo dnf install gcc-c++ make pkgconf-pkg-config ncurses-devel SDL2-devel SDL2_image-devel SDL2_mixer-devel freetype-devel sqlite-devel zlib-devel which diffutils python3
sh scripts/build-linux.sh
```

字体已预生成。需要重建衍生字体时，安装 `requirements-fonts.txt` 并运行 `python3 tools/build_pixel_font.py`。
使用 Pi 增补翻译时，运行 `tools/native_catalog.py translate`；词库编译与回归检查使用：

```sh
python3 tools/native_catalog.py compile
python3 tools/test_native_catalog.py
python3 tools/test_native_text_grid.py
```

## 验证与许可

验证包含两端原生构建、C++ 翻译模板回归、独立存档 PTY 测试、Lua 消息兼容性、图形技能菜单截图和 Bazzite Steam 实际点击检查。数据及界面审计记录在 `verification/`。

游戏遵循上游 `LICENSE`（GPL-2.0-or-later），原作者与素材声明保留在 `native/` 中。字体使用 SIL OFL 1.1；衍生字体已更名，完整声明在 `fonts/OFL.txt` 与 `fonts/fusion-pixel-licenses/`。
macOS 打包脚本会收集第三方运行库的许可证与版本清单；相关源码地址位于 `verification/macos-library-sources.json`。Release 中的 third-party-sources 附件提供适用的 GPL/LGPL 源码、构建配方和补丁。SteamGridDB 封面素材不包含在仓库中。

## 消息模板迁移（进行中）

最新一批按账本迁移普通物品操作主链路：拾取、合并、丢弃、穿脱、挥舞、饮药、读卷轴及魔杖/杂项使用的直接提示。完整模板在参数填入前选择，数量与附魔前名称先快照；装备限制理由直接传递 typed 参数，保留规范英文和内部数据。文案由 Luna 分工审校。Mac/Linux 四种构建、两端各十个存档副本操作场景、Mac 实际菜单与 Bazzite 原生 4K 操作截图通过；详见[本批验收报告](verification/native/item-operations/REPORT.md)。

迁移沿[项目模块账本](analysis/message-migration/LEDGER.md)记录生产函数、消费者、测试和剩余入口。本批仍未完成专名武器问候/告别、最后类别鉴定、地面集合摘要、外部数据库低语，以及物品使用后进入法术/怪物/神祇/状态模块的其他消息。内嵌 Lua 白话、复杂语义名称、其余教程与动态日志也继续排队，不能称为全面迁移或 100% 汉化。此前[随机对白及引号修复验收](verification/native/random-speech/REPORT.md)保留。

第一批已建立生成处完整模板、命名类型参数和独立显示名接口，移除通用逐词兜底；Mac 与 Bazzite 构建及存档副本场景已验证。仍有旧渲染入口与未迁移文案，详情见[迁移范围、验证和限制](verification/native/message-migration/REPORT.md)及[架构记录](analysis/message-migration/architecture.md)。
