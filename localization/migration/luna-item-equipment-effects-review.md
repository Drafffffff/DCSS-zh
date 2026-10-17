# 装备效果日志审校补充

本补充归属装备操作审校；只记录 `player-equip.cc` 内由穿戴、脱下、持用或摘下装备触发的玩家可见效果文字。逐条以对应 switch/属性分支的完整句子为单位迁移，名称参数沿用 `item_name`（通常为 `item.name(DESC_INVENTORY_EQUIP)` 或 `item.name(DESC_THE)`），不会把颜色、物品标记快捷键或程序状态拼入翻译参数。

## 入口与参数映射

- `player_equip_set::find_removable_items_for_slot`（约 749–798）：诅咒候选全部不可移除时的提示由主文件 `operation.equipment.reason.cursed_slot` 提供；`cursed_item->name(DESC_YOUR)` → `item:name`。
- `equip_item` / `unequip_item` 的装备效果主流程（约 1100–1350、1650 以后）：穿脱导致的融合/解除融合、物品品牌/神器反馈、装备属性启停效果、护符/戒指能力提示均为玩家日志，应使用本文件对应完整效果模板。任何完整物品名作为 `name`；手/脚等由 `you.hand_name(true)`/`foot_name(true)` 返回的完整名用 `name`；动作采用枚举分支对应的固定文案，不把物品词尾、英文复数或冠词拆给翻译。
- `%s` 后缀若来自 `plural ? ... : ...`，中文值为空；若后缀承载实质语义（如 `regen_attune` 的两种实际字符串），使用精确有限值 ID 映射为空，由完整中文模板承载语义，不将英文单复数词尾拼进中文。
- `getSpeakString` 中 Zonguldrok 头盔语音是数据驱动文本，不在此迁移；`dprf`、`ASSERT` 等诊断不属于玩家可见消息。

## 覆盖边界

本附加目录已逐条收录 `player-equip.cc` 中装备/卸装效果主体的玩家可见完整文案，包括融合与解除融合、神器及武器品牌反馈、首饰被动效果、属性启停、再生调谐和诅咒粉碎。`getSpeakString` 中 Zonguldrok 头盔语音属于 Lua/数据驱动文本，不在本批；`dprf`、`ASSERT` 等程序诊断也不迁移。
