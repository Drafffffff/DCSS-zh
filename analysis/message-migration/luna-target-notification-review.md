# Target notification review

Reviewed all 40 fixed `notify_fail` literals in `target.cc` and the dynamic reason producers currently using stable IDs.

- Fixed reasons use the complete source sentence and `source_context: target.reason`; each has a stable `target.reason.*` ID and a zero-argument oracle.
- Dynamic templates use semantic parameters: `wall:name`, `monster:name`, and transference `self:text`. The transference child defaults to “itself” and the producer may replace canonical with the actual reflexive; its localized value is “自身”.
- Covered dynamic IDs: `target.reason.wall`, `target.reason.unravelling.no_effects`, `target.reason.unravelling.cannot_harm`, `target.reason.poisonous_vapours.immune`, `target.reason.transference.self`, and `target.reason.transference.ancestor`.
- The fixed `Out of range.` entry retains `target.reason.out_of_range` for the current interface.
- External wall-jump/passwall, inner-flame, simulacrum, and crocodile reasons remain explicitly unsupported here; they are outside this `target.cc` fixed/dynamic catalog.

The complete fixed literal-to-ID map and all oracles are in `luna-target-notification-messages.json`.
