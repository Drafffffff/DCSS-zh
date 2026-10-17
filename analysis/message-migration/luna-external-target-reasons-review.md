# Luna external target reasons and spell-log review

Reviewed the five requested production areas against their emitting branches and preserved their canonical English templates. The catalog contains 43 messages, each with a replay oracle: 25 external target/cast reasons and 18 spell-casting or channel logs.

- `god-abil.cc`: all seven Wu Jian wall-jump outcomes are covered. `terrain`, `monster`, and `blocker` are typed `name` parameters. The invisible blocker is also represented as its own stable name fragment (`target.external.wall_jump.unseen_blocker`) so the full blocked sentence can use the same template with either a visible actor name or the semantic hidden-actor name.
- `spl-other.cc`: the five `passwall_path::is_valid` outcomes are covered, and `cast_passwall` is reviewed through its `is_valid`/`check_moveto` flow. The deep-water and lava descriptions passed into the shared `check_moveto_terrain` warning path are registered in the separate `player.cc` common movement-confirmation work package; this batch does not pass Chinese control strings through that path.
- `spl-damage.cc`: absent/unseen targets, an existing Inner Flame, and infinite will are covered. The monster names remain typed semantic parameters.
- `spl-summoning.cc`: the three Simulacrum target reasons, the distinct cast-time immunity sentence, the success message with `monster_possessive:name`, and all four Surprising Crocodile failure outcomes are covered. The cast-time Simulacrum canonical keeps the source plural `simulacra`; its localized sentence follows the established spell term “拟像.”
- `spl-cast.cc`: all 18 requested surge, wand, miscast, insufficient-magic, stop-channel, and channel-reminder messages are covered. Miscast/channel spell names use `spell:name`; reminder messages preserve the `<w>%</w>` key markup and the source parentheses in the canonical English.

Terminology follows the reviewed spell list and established game text: “蹬墙跳”, “穿墙”, “内焰”, “拟像”, “灼热射线”, “烈焰波”, and “发条蜂”. The full templates are translated as sentences rather than assembled from English fragments. Dynamic examples and rendered Chinese forms are recorded beside each message in the JSON oracle.

The catalog is frozen at 43 entries. No C++ source, generated catalog include, or other catalog was edited in this review.

The wall-jump terrain parameter resolves through `feat_type_name` and the `terrain` glossary domain. Added all 17 outputs as zero-argument stable-name messages with oracles: door/门, wall/墙壁, grate/格栅, tree/树, statue/雕像, water/水, lava/岩浆, altar/祭坛, trap/陷阱, escape hatch/逃生舱口, portal/传送门, staircase/楼梯, shop/商店, fountain/喷泉, dais/台座, unknown terrain/未知地形, and floor/地面. Here `floor` means the ground tile, translated as “地面”; it does not mean dungeon depth or level. These names were checked against the reviewed Chinese terrain terms in `zh-catalog.inc` and `terrain.cc`'s complete `feat_type_name` branch list.

The catalog is now frozen at 60 entries, with 60 matching oracles.
