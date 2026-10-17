# 物品边缘流程迁移

本批基线为 native `cc710081cd3f163eabf78c65b9144e040ef30aa8`。新增译文及复核均由 **gpt-6.1-sol** 完成；JSON 中的历史 `luna-` 文件名前缀不代表模型。复用了已审校的魔杖、魔法长杖、卷轴、药水、护身符、仆从与白金英杰术语。本报告只覆盖下列生产链路，不宣称八个所属文件完成。

## 已迁移链路

- `items.cc::item_check`：单项、短集合、物品堆 glyph 摘要与过长列表父提示接入完整模板。新增 `item_message_display_arg` 传递语义物品名快照，颜色沿现有 `zh_item_menu_arg` 规则；集合分隔符是独立结构。任一名称不支持时整个集合/父句回退，避免半行翻译。glyph排序、颜色、50项上限原样保留。`item_message` 的规范英文字符串 API 不变。
- `_identify_last_item`：最后类别鉴定日志接入具名类别参数；六类有限语义标签由类别/子类型生产结果查表，不按最终英文句子匹配。原鉴定、自动拾取属性、槽位分配和库存显示顺序不变。
- `maybe_name_weapon`、`say_farewell_to_weapon`：新名字/再次迎接/告别各用完整模板。显示快照按原函数排除铭文；随机昵称是原样专名数据，保持引号、数字及所有字节。`name_weapon`、`get_weapon_name`、存档属性和昵称生成随机调用不变。神器/自定义名称仍依赖语义名称层，未支持时整父句回退。
- `ImbueDelay::start/try_interrupt`：灌注开始与继续确认接入typed消息；既有完成/中断静态消息一并作回归。`ImprintDelay::start/finish`：伙伴塑形开始与完成接入物品名参数；既有中断同样作回归。typed yesno保留规范英文和原确认行为。
- `quiver::melee_action::trigger`：受困、混乱攻击地形、无法越过友方、阻挡者与拆解五类动态反馈接入 typed 模板。复用既有审校 quiver 日志ID；新增有限受困标签与不可见阻挡者消息。不改变目标、时间消耗、死亡处理或随机顺序，不读取不可见阻挡者名称。

地面外层通过主agent添加的 typed `mpr_nojoin` / `mpr_nocap` 接口保持原channel、合并和首字母规则；这两个共享接口不由本子agent修改。截图中未鉴定卷轴名称由 semantic-details 组负责；本批只闭合父句和集合摘要。`items.h` 导出 typed 集合参数供其父视图使用。

## 验证

`python3 tools/test_sol61_item_edges.py`：**PASS，123,753 个真实生产函数场景**。

冻结fixture来自上述基线原文件；测试分别抽取旧/新完整函数，而非用新模板反推英文oracle。执行实际 `item_check`、集合算法、最后类别鉴定、武器命名/告别、灌注/塑形生命周期和完整近战箭袋trigger。只将世界状态、命名服务、UI/输入和RNG引擎作seam；模板选择与填参使用真实 `zh-message.cc`。词库只写临时私有目录，开启 `DCSS_ZH_FORBID_LEGACY=1`，不生成共享catalog。

检查规范英文及标点、channel/nojoin/cap、数量、混合支持名称整父回退、50/51/65项glyph边界、名称和铭文状态、灌注接受/取消/禁用确认/重入标记、塑形与灌注存储、近战target/回合/时间/死亡、RNG调用轨迹和不可见名称访问。五个本批近战动态分支均实际到达；包含特殊昵称、引号、标记、复数名和英文语言模式。`git diff --check` 在本批native四个文件通过。

命名服务为测试seam，故这些测试不替代 semantic-details 名称生产测试；实际消息UI为seam，不替代统一原生构建和存档副本回放。本子agent未运行全量构建、SSH、UI或提交。主agent负责集成共享catalog及最终平台验收。

## 全所属范围剩余

- `items.cc`：Orb逃离启动的 `start_orb_run` 外部consumer在 `orb.cc`；wizard/debug符文/书籍选择和诊断；外部使用 `item_message` 的父视图另组接续；复杂名称依赖名称层。
- `invent.cc`：任意跨模块 `const char*` 自定义库存提示路径。
- `item-use.cc`：刻写时无物品提示、神祇阻止饮药、卷轴噪声的 `noisy` 字符串consumer、Lua/异常卷轴诊断，以及外部法术/状态/神祇effects。
- `player-equip.cc`：Zonguldrok帽子随机低语及 `simple_god_message` 信仰反馈。低语仍需raw数据库类型协议，保留原始可选key检查和最终随机抽取次数；不能匹配最终组合英文来假装闭环。
- `evoke.cc`：本批未改。扫描无剩余直接mpr英文literal，不据此认定外部法术/怪物/神祇effects完成。
- `potion.cc`：记忆与变异净化的神祇consumer、外部变异/状态/神祇effects。
- `delay.cc`：记忆法术时神祇赐予知识、旅行混乱中断、自动拾取切换键警告、怪物接近/出现日志与Lua诊断。
- `quiver.cc`：自动攻击资源不足、`ranged_action::trigger`拆解反馈、Lua诊断及任意控制/兼容API；本批完整验收的是 `melee_action::trigger` 的上述反馈链路。

`audit.json` 给出逐文件余项和带行号调用候选。候选包括诊断及控制值，数量不是未翻译条数；不以词库条数表示覆盖率。未知/自定义/神器语义名称仍允许整父规范英文回退并报告。

## 适合存档副本触发的场景

1. 地面分别放1件未鉴定卷轴、2件普通物品、含未知复杂名的混合集合，以及50/51件堆叠；核对底部父句、数量、颜色和摘要glyph，原始存档不覆盖。
2. 仅剩一个未鉴定类别时拾取/持有最后一种魔杖、长杖、卷轴、药水、戒指及护身符，分别核对自动鉴定与无用物品自动拾取标记。
3. 使用钢铁之魂武器命名机制生成一次昵称、卸下告别、再次装备，并带已有铭文与神器各测一次；昵称和铭文存储不变。
4. 灌注仆从时开始、取消/继续/强制中断及完成；白金英杰塑形时开始、中断和完成，核对spell/weapon属性。
5. 箭袋近战被网/蛛网困住；混乱攻击墙壁；伸展攻击被友方、可见敌方和不可见敌方挡住；拆解目标；核对目标、回合消耗与隐藏信息。
