# Luna spell reason messages review

Audited the 85 existing entries in `localization/migration/pending/luna-spell-reasons-messages.json` against `native/crawl-ref/source/spl-util.cc`, including the complete fixed return reasons from `casting_uselessness_reason` and `spell_uselessness_reason`. Those entries cover all fixed lowercase reasons in those functions; the only missing fixed reason was `spell.reason.no_hostiles`, now added with its exact canonical sentence, `you can't see any hostile targets that would be affected.` The old count of 85 therefore becomes 86. Every message ID now has an oracle case.

Dynamic `you.no_tele_reason(true)` results remain delegated to the existing no-tele reason catalog. The details renderer already has the `spell.player.useless_reason` parent for a typed reason, and its separate no-visible-hostiles parent remains available. No `describe.cc` source change is included here. The no-hostiles reason has its own ID so detail choice can distinguish it from the generic uselessness reason.

Each reason ID has an oracle case. Existing IDs and translations were preserved; this change only appends the omitted fixed reason.

集成记录：本批实际绑定的64条 spell.reason 移入顶层活跃目录；剩余22条记忆流程/反噬文案继续保留 pending，不计作已迁移。
