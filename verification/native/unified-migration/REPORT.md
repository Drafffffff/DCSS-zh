# 统一迁移第一批：公共协议与优先模块

基线为 native edab0e49；保留其后现有修改。执行路线和逐调用索引分别见 analysis/message-migration/CONTRACT.md、LEDGER.md、callsites.json。源码扫描是词法审查候选，不是汉化完成率。

## 本批变更

- 将规范英文读取 ZhTranslationPause 与原样绘制 ZhLegacyPause 分开。raw绘制不会使新模板、数据库或名称接口退回英文；canonical/Lua读取仍明确返回英文。
- 怪物数据库正文/引文先读取固定规范源文，再于规范读取作用域外选择完整译文；空的可选引文/前后缀不报告缺失。
- 技能查阅菜单统一使用枚举技能名称、完整标题/导航帮助/无结果模板及原样渲染；数据库key保留英文。技能详情正文明确选数据库语言，并对缺失正文完整报告。
- 收录已有详情、技能、商店和部分HUD迁移；游戏文案由Luna审校，代码集成由主agent完成。

## Mac 验证

- tiles及console构建通过。消息schema/oracle 694项、raw parser/widget 30项、文本grid 344组、技能长帮助及HUD实际helper/producer边界测试通过。
- test_translation_boundaries.py 编译真实怪物DB读取函数和技能菜单生产函数，连接真实消息协议实现；验证规范读取、raw作用域、可选空字段及34个技能词条的中英文显示和原数据库key保持。
- macos-priority-combined.json 汇总17个真实存档副本场景：技能查阅/详情、物品/法术/怪物详情、商店详情/选择/确认/购买/购物清单、技能主面板/帮助/说明/长帮助、普通及wizard HUD。实测场景missing/name报告均为空，无运行时错误；购买后余额为838。
- macos-canonical/smoke.json 验证Lua历史与物品描述保持规范英文，测试角色可保存退出。
- Mac GUI截图人工检查技能查阅全部名称和详情正文。窗口约1746×1143；没有宣称Mac物理4K验收。4K几何由生产helper测试覆盖，最终Linux原生4K验收在阶段冻结后执行。
- 所有场景使用临时目录中的存档副本，源存档哈希未变。未打开正在游玩的角色。

## 明确未完成

本批没有声称全项目迁移，也没有按ID数量或中文字数计算覆盖率。详情复杂来源、curse/talisman/hints及外部失败理由仍有登记的整段英文回退；技能增强/削弱等状态组合尚未逐一真实回放。HUD剩余字段、瞄准/箭袋、神祇/能力/世界/通用菜单等仍有旧入口，见账本。通用逐词兜底未恢复。

本批以Mac为主调试；Linux已有前一轮构建记录，但尚未对本批全部源码进行最终构建验收。没有创建release。
