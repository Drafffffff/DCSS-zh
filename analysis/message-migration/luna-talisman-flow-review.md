# Luna talisman and transformation flow review

Audited `cannot_put_on_talisman_reason` and `use_talisman` in `native/crawl-ref/source/item-use.cc`, plus the transformation safety and delay paths. The new JSON covers all five fixed talisman-specific rejection reasons, carrying capacity, the Protean talisman conversion line, and the unsafe-start confirmation. The Protean message uses typed `item:name` and `form:name` arguments so the item name and generated form remain intact.

The danger prompts emitted by `transforming_is_unsafe` are recorded as complete templates for transforming/untransforming into lava or deep water and for shattering a cursed or fragile artefact. Shatter messages use `item:name`. Existing form eligibility messages from `cant_transform_reason` are already represented by the shared/consumable restriction migration and are intentionally reused.

`TransformDelay::start`, `tick`, and `try_interrupt` were checked. Their five user-facing lines already flow through established `log.delay.fixed.*` localization IDs, so this pack does not add duplicate copies. It adds the separately hard-coded `Keep transforming yourself?` prompt with its exact source anchor. Every new message has an oracle case.
