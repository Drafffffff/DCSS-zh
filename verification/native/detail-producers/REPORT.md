# 详情生产点迁移：来源与紧凑法术列表

本批 native 提交：29b5967。继续遵循 analysis/message-migration/CONTRACT.md；Mac 为主调试平台，未修改或打开原始存档。

## 已完成

- origin_desc 保持规范英文，供 notes/Lua/存储使用。UI 新增 origin_display_desc，从原始来源字段选择发现、购买、获取、发明、牌组、wizard 创建、神赐、制服舞动武器、怪物掉落九类完整模板。
- zh_place_arg 从 level_id 的 branch/depth 选择地点模板；40 个分支 longname 使用 Luna 审校名称，英文介词与中文“在”分别由各自完整模板组织。来源怪物类型通过专用显示名称接口处理。
- terse_spell_list 在格式化前选择法术行模板；法术等级、名称、学派独立参数。中文顿号列表和英文末项 and 分别生成。任一名称/学派缺失时整份列表回退并报告，不产生混合句。
- 本批 53 个目录条目及文案由 Luna 提供；旧的 Dungeon 来源专用 ID 目前保留为未调用条目，生产入口已统一。

## 验证结果

- Mac tiles、console 构建成功；Mac 安装包已更新。
- 消息 schema/oracle：714 项通过。真实 origin_desc/origin_display_desc、terse_spell_list/_spell_schools_arg、zh_place_arg、level_id::describe、prep_branch_level_name 函数提取编译，连接真实消息运行时：通过。
- 上述函数测试覆盖九类正常来源及玩家幽灵、异常来源、未知怪物、原样绘制暂停与英文模式、40 个分支的单层/多层选择、法术等级1/5与学派、空列表、未知名称整句回退。分支审校名单与真实 branch-data.h 名称集合相等。
- 文本网格344组、raw renderer30组、技能长帮助生产布局helper、HUD生产helper回归通过。
- macos/results.json：8个存档副本场景通过（武器/护甲/法术/怪物详情、技能帮助/查阅详情、商店购买/详情），无缺失ID、缺失名称或运行错误。源fixture哈希不变。
- macos-canonical/smoke.json：Lua历史/物品描述保持规范英文，可保存退出。
- macos-item-detail.png 显示来源“你在地牢第1层发现了它。”；macos-skill-help.png 显示技能帮助与快捷键在面板内。Mac窗口约1746×1112，不将此称为物理4K验收。4K由已有布局helper测试覆盖，Linux原生4K仍待阶段冻结验收。

## 剩余边界

详情尚未全面迁移：curse技能说明、talisman表格及外部Form名称/融合描述、hints生产器、外部法术失败理由与部分数据库正文仍有显式整段回退。详情尾部搜索/着色前缀标签仍英文，紧随的Lua控制token须原样保留；Luna已在下一详情批次审校标签。macos-inventory-unmigrated.png 记录独立物品栏仍走旧入口，此菜单不属于本批来源/详情生产器完成范围。

普通来源已移除旧最终英文匹配入口；未知/损坏来源仍显式报告并完整回退。Linux本批未构建，没有创建release，不宣称全面迁移或100%汉化。
