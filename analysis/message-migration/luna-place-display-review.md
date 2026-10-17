# UI 地点显示模板：Luna 审校

本批新增 `localization/migration/luna-place-display-messages.json`。它给 `level_id` 提供不带英文介词的 UI 地点名，供物品来源等完整句子嵌入。只审校与记录了目录、源码和 oracle；没有改 C++、其他目录或构建。

## 源码规则与模板选择

`place.cc::prep_branch_level_name(level_id)` 先调用 `id.describe(true, true)`。如果结果首字母小写后以 `level` 开头，它前缀 `on `；其他名字前缀 `in `。所以它是给英文句子用的介词短语，不适合作为 UI 的独立地点标签。新的地点显示需从 `level_id.branch` 与 `level_id.depth` 生成不带介词的中文地点：

- 当 `brdepth[branch] != 1`，`travel.cc::level_id::describe(true, true)` 的真实模板是 `Level %d of %s`。`place.display.level` 用 `{depth}` integer 和 `{branch}` name，中文为 `{branch}第{depth}层`。branch 的 canonical 直接对应 `branches[branch].longname`；中文对应分支已审校简称，不保留英文冠词。
- 当 `brdepth[branch] == 1`，`level_id::describe(true, true)` 只返回 `branches[branch].longname`。`place.display.named` 显示纯分支名，不加介词或深度。适用于 Temple、Vestibule、Pandemonium 等单层或特殊地点。

`depth` 是 `level_id.depth` 的分支内层数，绝不复用法术等级、技能等级或角色经验。地点目录中特别用 `{depth}` 而不是含混的 `{level}`。中文地点模板显式写“第 N 层”，而不是把该层数并入名称。

## 分支名称映射

目录中的 `place.branch.*` 条目以 `branch-data.h` 的 `longname` 为 canonical，用于精确对应 `level_id::describe`；译文复用 `luna-hud-display-messages.json` 中已审校的对应短分支名。例：`the Dungeon` → `地牢`，`the Lair of Beasts` → `兽穴`。`the Vestibule of Hell` → `地狱前厅`，在已审校 Hell“地狱”的基础上表达 Vestibule 所指的前厅地点。若未来某版本新增 branch 或改 longname，调用方应在名称缺失时整条地点模板回退并记录，不拼接未审名称。

地点 oracle 覆盖多层 Dungeon/Lair/Depths，单层 Ecumenical Temple/Vestibule of Hell 和特殊 Pandemonium/Wizlab 名称。所有中文地点名均无“在/于/on/in”；它们可以作为 `{place}` 的值嵌入完整来源句。

## 与详情缺口目录的集成约定

我只读检查了 `luna-detail-gaps-messages.json` 当前版本。其 origin 模板的 `{place}` 参数现为 `text`；canonical 使用 `prep_branch_level_name` 的完整英文短语，localized 使用不带介词的地点名称。消息正文包含源码调用点前置的换行（例如 `item.origin.found_place` 的 `\nYou found it {place}.`），中文对应换行也保留。该协议与本批输出吻合：地点 helper 的 localized 值供 `{place}` 插入；英文 canonical 仍保留旧 `prep_branch_level_name` 的 `on/in + source location`。

需要纠正一个既有 oracle 的源文差异：`luna-detail-gaps-messages.json` 将 Lair 测例写为 `on level 5 of the Lair`，而 `branch-data.h` 的 longname 是 `the Lair of Beasts`，因此 `level_id::describe`/`prep_branch_level_name` 实际 canonical 应为 `on level 5 of the Lair of Beasts`。本任务不改既有目录；主接入者应在合并该目录时更新该 fixture。

对于具体接入：从 `level_id` 选 `place.display.level` 或 `.named`，以 branch-longname 的 `place.branch.*` 语义项获取译名；地点原文参数仍按 `prep_branch_level_name(id)` 保留 canonical。传给 item origin 模板的中文只放地点名，例如 `兽穴第5层`，由完整句模板提供中文“在”。不要把“在”或英文 `on/in` 重复放入参数，也不要从现成完整句拆地点。
