# 共用限制理由与操作日志审校

本批以 `player.cc::player::no_tele_reason`、`invis_allowed`，`spl-transloc.cc` 全文件的无参数固定 `mpr/mprf`，`player-act.cc::go_berserk` 和 `transform.cc::check_transform_into` 为边界。固定日志使用 `source_context: shared.restriction.logs`，动态句式以稳定 ID 和命名参数绑定；没有把已拼好的英文句子当作可拆词语。`mprf` 的消息频道仍记录在 source anchor，接入时需保留原调用频道。

## 瞬移限制

`player.no_tele.blink` 与 `.teleport` 是两个完整父模板，分别保留闪现与传送语义。原因列表按 `no_tele_reason` 的 `problems` 顺序生成：次元锚、树形态根系、手持的禁止传送武器、穿戴的禁止传送物品。英文 canonical 仍采用源码 `comma_separated_line` 结果；中文列表应以顿号连接，最后两项之间用“及”。单个武器用 `player.no_tele.wielded` 的 `item:name` 参数，穿戴列表中的每个物品必须经既有物品名称语义接口后再组合，不能把英文列表作为已支持中文的普通参数。

穿戴物品多于源码阈值时，`player.no_tele.worn_many` 表达独立的数量原因。阈值仍取源码逻辑：没有先前限制原因时超过 3 件，有先前原因时超过 1 件。`count_word` 对应 `number_in_words`；`kind` 对应源码的 `items`/`artefacts` 分支。源码中 `found_nonartefact` 在当前函数路径里只初始化而没有更新，目录没有擅自改动这一判断。

固定早退消息分别为停滞、Dungeon Sprint 和 Gauntlet 魔法封印。中文沿用已审校的“地牢冲刺”；Gauntlet 在本上下文译作“险关”。

## 隐形限制

`invis_allowed` 的四种光源是 weapon、crown、armour、divine halo。光源显示名复用现有语义名称；列表由调用点本地化组合，不能逐词反查。`item.reason.invisibility.halo`、`.backlit` 和 `.backlit_current` 已在 `luna-consumable-display-messages.json` 审校，本批不重复定义。非 quiet 背光分支仍保留 yes/no 确认和默认否定键 `n`；新完整提示 `player.invisibility.backlit.confirm` 只负责确认文字，不改变控制键或状态逻辑。

## 操作日志

本批覆盖了 `spl-transloc.cc` 内所有无参数固定 `mpr/mprf`：包括 Jump/Hop、受控闪现目标校验、普通传送与环境变化、Gauntlet 通道封印、apport、传送通道、空间折叠与其他固定效果消息。宝珠、警告、错误频道等原 channel 保存在 source anchor 中，集成时必须保留。三条环境句按各自源码分支独立登记，避免把 flicker、slightly different、suddenly different 混成一个泛化文本。

`go_berserk` 的成功提示和状态消息均已登记。失败原因由既有 `item.reason.drink.*` 词条复用；变形前置状态失败沿用 `item.reason.transform.*`。危险地形分开登记溺水与灼伤完整句；降低最大生命值的确认提示也保留整句。

## 独立 oracle

JSON `test_cases` 覆盖闪现与传送动作区分、三种原因混合的中文顿号/末项“及”、穿戴神器数量、背光确认、传送环境两种差异程度、狂暴状态消息及危险地形失败。实际调用点仍需按语义 API 生成各参数；这些 oracle 只验证完整模板渲染，不代替主 agent 的真实路径测试。

## 明确未覆盖

- `spl-transloc.cc` 的 controlled blink replay 提示（`You can't repeat controlled blinks.`）来自 `cancel_cmd_all`，不是 `mpr/mprf`，因此不在本批固定消息清单中。
- `spl-transloc.cc` 中带格式参数或运行时字符串的日志（如 blinkbolt 目标限制、怪物随传送、动态武器/怪物名、物品数量、重力方向、动态 passage 失败原因）未纳入；需要独立完整模板及 actor/item/name 参数语义，不能由固定消息覆盖。
- `_teleport_player` 的 HUP 与 wizard destination 日志虽已登记，但只在 wizard/control 分支触发；正式游戏路径测试不一定覆盖。
- `invis_allowed` 的一般背光/光环逻辑由既有 ID 复用；实际列表单复数仍需实现时以光源数决定英文 `{s}`，中文不得照搬英语复数后缀。
- `no_tele_reason` 的结构化原因列表需由主 agent 实现中文列表连接器。未覆盖的未来新原因必须增加独立审校模板，不能回退到旧 matcher。
